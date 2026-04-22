"""
Speech-to-Text service using OpenAI Whisper API.
"""
import io
import wave
from typing import Optional, Tuple
import numpy as np
from openai import OpenAI
from backend.utils.config import config


class SpeechToText:
    """Convert speech audio to text."""

    def __init__(self):
        self.client = OpenAI(
            api_key=config.STT_API_KEY,
            base_url=config.STT_BASE_URL
        ) if config.STT_API_KEY else None
        self.model = config.STT_MODEL
        self.sample_rate = config.SAMPLE_RATE

    def transcribe_audio(self, audio_data: bytes) -> Tuple[Optional[str], str]:
        """
        Transcribe audio bytes to text.

        Args:
            audio_data: Raw audio bytes

        Returns:
            Tuple of (transcribed_text, error_message)
        """
        if not self.client:
            return None, "OpenAI API key not configured"

        try:
            # Create audio file from bytes
            # We use .webm as it's the most common format from browsers
            # Whisper will automatically detect the format if the extension is supported
            audio_file = io.BytesIO(audio_data)
            
            # Simple check for WebM header (1A 45 DF A3)
            if audio_data.startswith(b'\x1a\x45\xdf\xa3'):
                audio_file.name = "audio.webm"
            else:
                audio_file.name = "audio.wav"

            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file
            )


            return response.text.strip(), ""

        except Exception as e:
            return None, f"Transcription error: {str(e)}"

    def transcribe_audio_file(self, file_path: str) -> Tuple[Optional[str], str]:
        """
        Transcribe audio from a file.

        Args:
            file_path: Path to audio file

        Returns:
            Tuple of (transcribed_text, error_message)
        """
        if not self.client:
            return None, "OpenAI API key not configured"

        try:
            with open(file_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language="en"
                )

            return response.text.strip(), ""

        except Exception as e:
            return None, f"Transcription error: {str(e)}"

    def audio_to_bytes(self, audio_array: np.ndarray) -> bytes:
        """
        Convert numpy audio array to WAV bytes.

        Args:
            audio_array: Numpy array of audio samples

        Returns:
            WAV format bytes
        """
        # Normalize to 16-bit range
        if audio_array.dtype == np.float32 or audio_array.dtype == np.float64:
            audio_array = (audio_array * 32767).astype(np.int16)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_array.tobytes())

        return buffer.getvalue()


# Singleton instance
stt = SpeechToText()
