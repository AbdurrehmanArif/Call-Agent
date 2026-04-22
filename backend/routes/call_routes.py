"""
API routes for call handling.
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, Response
from typing import Optional
import uuid
import base64


from backend.services.speech_to_text import stt
from backend.services.text_to_speech import tts
from backend.services.intent_detector import intent_detector
from backend.services.sentiment_analyzer import sentiment_analyzer
from backend.services.dialogue_manager import dialogue_manager
from backend.utils.audio_utils import audio_utils
from backend.database.db import db


router = APIRouter()


@router.post("/start")
async def start_call(caller_id: Optional[str] = Form(None)):
    """
    Start a new call session.

    Returns:
        Session ID and greeting
    """
    session_id = dialogue_manager.create_session(caller_id)
    greeting = tts.generate_speech("Hello! Thank you for calling. How can I help you today?")

    return JSONResponse({
        "session_id": session_id,
        "greeting_audio": base64.b64encode(greeting[0]).decode('utf-8') if greeting[0] else None,
        "greeting_text": "Hello! Thank you for calling. How can I help you today?",
        "tts_error": greeting[1] if not greeting[0] else None
    })




@router.post("/process")
async def process_audio(
    session_id: str = Form(...),
    audio: Optional[UploadFile] = None,
    text: Optional[str] = Form(None)
):


    """
    Process user audio input and return response.

    Args:
        session_id: Session ID from start_call
        audio: Audio file upload

    Returns:
        Response with text and audio
    """
    # Validate session
    session = dialogue_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.get("call_ended"):
        raise HTTPException(status_code=400, detail="Call has ended")

    # Use provided text or transcribe audio
    user_text = ""
    stt_error = ""

    if text:
        user_text = text
    elif audio:
        audio_bytes = await audio.read()
        user_text, stt_error = stt.transcribe_audio(audio_bytes)
    else:
        raise HTTPException(status_code=400, detail="Either audio or text must be provided")

    if stt_error:
        raise HTTPException(status_code=400, detail=f"Speech recognition failed: {stt_error}")
    
    if not user_text and not stt_error:
        # Avoid empty content errors
        return JSONResponse({"status": "ignored", "detail": "Empty input"})


    # Detect intent
    intent, intent_confidence = intent_detector.detect(user_text)

    # Analyze sentiment
    sentiment_label, sentiment_score = sentiment_analyzer.get_sentiment_label(user_text)

    # Process through dialogue manager
    result = dialogue_manager.process_user_input(
        session_id,
        user_text,
        intent,
        sentiment_label
    )

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    # Generate TTS response
    tts_audio, tts_error = tts.generate_speech(result["reply"])

    return JSONResponse({
        "session_id": session_id,
        "user_text": user_text,
        "assistant_text": result["reply"],
        "assistant_audio": base64.b64encode(tts_audio).decode('utf-8') if tts_audio else None,
        "tts_error": tts_error if not tts_audio else None,
        "intent": intent,
        "intent_confidence": intent_confidence,
        "sentiment": sentiment_label,
        "sentiment_score": sentiment_score,
        "escalation": result.get("escalation", False),
        "call_ended": result.get("call_ended", False)
    })




@router.post("/end")
async def end_call(session_id: str = Form(...)):
    """
    End a call session.

    Returns:
        Call summary
    """
    summary = dialogue_manager.end_session(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")

    return JSONResponse({
        "status": "success",
        "summary": summary
    })


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Get session details.

    Returns:
        Session information
    """
    session = dialogue_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return JSONResponse({
        "session_id": session_id,
        "state": session["state"],
        "message_count": len(session["messages"]),
        "escalation_requested": session["escalation_requested"],
        "call_ended": session["call_ended"]
    })


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """
    Get conversation history.

    Returns:
        Message history
    """
    session = dialogue_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return JSONResponse({
        "session_id": session_id,
        "messages": [
            {
                "role": msg["role"],
                "message": msg["message"],
                "timestamp": str(msg["timestamp"]),
                "intent": msg.get("intent"),
                "sentiment": msg.get("sentiment")
            }
            for msg in session["messages"]
        ]
    })


@router.get("/voices")
async def get_voices():
    """
    Get available TTS voices.

    Returns:
        List of available voices
    """
    voices = tts.get_available_voices()
    return JSONResponse({"voices": voices})


@router.post("/set-voice")
async def set_voice(
    session_id: str = Form(...),
    voice_name: str = Form(...)
):
    """
    Set TTS voice for a session.

    Returns:
        Success status
    """
    success = tts.set_voice(voice_name)
    if not success:
        raise HTTPException(status_code=400, detail="Voice not found")

    return JSONResponse({"status": "success", "voice": voice_name})


@router.get("/calls/recent")
async def get_recent_calls(limit: int = 10):
    """
    Get recent call logs.

    Returns:
        List of recent calls
    """
    calls = db.get_recent_calls(limit)
    return JSONResponse({"calls": calls})


@router.get("/calls/{session_id}")
async def get_call(session_id: str):
    """
    Get specific call details.

    Returns:
        Call details
    """
    call = db.get_call_by_session(session_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    return JSONResponse({"call": call})
