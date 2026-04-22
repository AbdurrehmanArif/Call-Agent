"""
Dialogue management service for conversation flow.
"""
from typing import Dict, List, Optional
from datetime import datetime
import uuid
from backend.database.db import db
from backend.services.response_generator import response_generator
from backend.services.sentiment_analyzer import sentiment_analyzer


class DialogueState:
    """Dialogue state enumeration."""
    GREETING = "greeting"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    ESCALATING = "escalating"
    CLOSING = "closing"
    ENDED = "ended"


class DialogueManager:
    """Manage conversation state and flow."""

    def __init__(self):
        self.sessions: Dict[str, Dict] = {}

    def create_session(self, caller_id: Optional[str] = None) -> str:
        """
        Create a new dialogue session.

        Args:
            caller_id: Optional caller identifier

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "id": session_id,
            "caller_id": caller_id,
            "state": DialogueState.GREETING,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "messages": [],
            "intent_history": [],
            "sentiment_history": [],
            "escalation_requested": False,
            "call_ended": False
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def add_message(
        self,
        session_id: str,
        role: str,
        message: str,
        intent: Optional[str] = None,
        sentiment: Optional[str] = None
    ) -> bool:
        """
        Add a message to the conversation.

        Args:
            session_id: Session ID
            role: "user" or "assistant"
            message: Message text
            intent: Detected intent (optional)
            sentiment: Detected sentiment (optional)

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if not session:
            return False

        session["messages"].append({
            "role": role,
            "message": message,
            "timestamp": datetime.now(),
            "intent": intent,
            "sentiment": sentiment
        })

        session["last_activity"] = datetime.now()

        if intent:
            session["intent_history"].append(intent)
        if sentiment:
            session["sentiment_history"].append(sentiment)

        # Save to database
        db.add_dialogue_entry(session_id, role, message)

        return True

    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history in OpenAI format.

        Args:
            session_id: Session ID

        Returns:
            List of message dicts with role/content
        """
        session = self.get_session(session_id)
        if not session:
            return []

        return [
            {"role": msg["role"], "content": msg["message"]}
            for msg in session["messages"][-20:]  # Last 20 messages
        ]

    def process_user_input(
        self,
        session_id: str,
        user_message: str,
        intent: str,
        sentiment: str
    ) -> Dict:
        """
        Process user input and generate response.

        Args:
            session_id: Session ID
            user_message: User's message
            intent: Detected intent
            sentiment: Detected sentiment

        Returns:
            Response dict with reply and metadata
        """
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found", "reply": ""}

        # Check for escalation request
        if intent == "escalation" or session.get("escalation_requested"):
            session["escalation_requested"] = True
            session["state"] = DialogueState.ESCALATING
            reply = response_generator.generate_escalation_message()
            self.add_message(session_id, "user", user_message, intent, sentiment)
            self.add_message(session_id, "assistant", reply)
            return {
                "reply": reply,
                "escalation": True,
                "state": DialogueState.ESCALATING
            }

        # Check for goodbye
        if intent == "goodbye":
            session["state"] = DialogueState.CLOSING
            reply = response_generator.generate_goodbye()
            self.add_message(session_id, "user", user_message, intent, sentiment)
            self.add_message(session_id, "assistant", reply)
            session["call_ended"] = True
            session["state"] = DialogueState.ENDED
            return {
                "reply": reply,
                "call_ended": True,
                "state": DialogueState.ENDED
            }

        # Normal conversation flow
        session["state"] = DialogueState.PROCESSING

        # Add user message
        self.add_message(session_id, "user", user_message, intent, sentiment)

        # Generate response
        context = {"intent": intent, "sentiment": sentiment}
        history = self.get_conversation_history(session_id)
        reply, error = response_generator.generate_response(
            user_message,
            history,
            context
        )

        if error:
            reply = "I apologize, but I'm having trouble processing your request. Could you please repeat?"

        # Add assistant response
        self.add_message(session_id, "assistant", reply)
        session["state"] = DialogueState.LISTENING

        return {
            "reply": reply,
            "error": error,
            "escalation": False,
            "call_ended": False,
            "state": session["state"]
        }

    def end_session(self, session_id: str) -> Dict:
        """
        End a dialogue session and return summary.

        Args:
            session_id: Session ID

        Returns:
            Session summary
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        session["call_ended"] = True
        session["state"] = DialogueState.ENDED

        # Build transcript
        transcript = "\n".join(
            f"{msg['role'].capitalize()}: {msg['message']}"
            for msg in session["messages"]
        )

        # Calculate duration
        duration = (session["last_activity"] - session["created_at"]).total_seconds()

        # Get most common intent
        intents = session["intent_history"]
        primary_intent = max(set(intents), key=intents.count) if intents else "unknown"

        # Get average sentiment
        sentiments = session["sentiment_history"]
        avg_sentiment = "neutral"
        if sentiments:
            positive_count = sentiments.count("positive")
            negative_count = sentiments.count("negative")
            if positive_count > negative_count:
                avg_sentiment = "positive"
            elif negative_count > positive_count:
                avg_sentiment = "negative"

        # Log to database
        db.log_call(
            session_id=session_id,
            caller_id=session.get("caller_id"),
            duration_seconds=duration,
            transcript=transcript,
            detected_intent=primary_intent,
            sentiment_label=avg_sentiment,
            resolution_status="completed" if not session["escalation_requested"] else "escalated"
        )

        return {
            "session_id": session_id,
            "duration_seconds": duration,
            "message_count": len(session["messages"]),
            "primary_intent": primary_intent,
            "sentiment": avg_sentiment,
            "escalated": session["escalation_requested"]
        }

    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return [
            sid for sid, session in self.sessions.items()
            if session["state"] not in [DialogueState.ENDED]
        ]


# Singleton instance
dialogue_manager = DialogueManager()
