"""
Response generation service using OpenAI.
"""
from typing import List, Dict, Optional
from openai import OpenAI
from pathlib import Path
from backend.utils.config import config


class ResponseGenerator:
    """Generate AI responses for conversations."""

    def __init__(self):
        self.client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL
        ) if config.OPENAI_API_KEY else None

        self.model = config.OPENAI_MODEL
        self.max_tokens = config.MAX_TOKENS
        self.temperature = config.TEMPERATURE
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load system prompt from file."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "system_prompt.txt"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return """You are a helpful AI call assistant. Be professional, empathetic, and concise."""

    def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict] = None
    ) -> tuple[str, str]:
        """
        Generate a response to user message.

        Args:
            user_message: Latest user message
            conversation_history: List of message dicts with role/content
            context: Additional context (intent, sentiment, etc.)

        Returns:
            Tuple of (response_text, error_message)
        """
        if not self.client:
            return "", "OpenAI API key not configured"

        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Add context if available
        if context:
            context_str = f"Context - Intent: {context.get('intent', 'unknown')}, "
            context_str += f"Sentiment: {context.get('sentiment', 'neutral')}"
            messages.append({"role": "system", "content": context_str})

        # Add conversation history
        # Note: dialogue_manager already appends the latest user_message to history
        if conversation_history:
            messages.extend(conversation_history[-10:])  # Last 10 messages
        else:
            # Fallback if history was empty for some reason
            messages.append({"role": "user", "content": user_message})


        try:
            print(f"[DEBUG] NVIDIA NIM Request - Model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            response_text = response.choices[0].message.content.strip()
            return response_text, ""
        except Exception as e:
            print(f"[ERROR] NVIDIA NIM Error: {str(e)}")
            return "", f"Response generation error: {str(e)}"


    def generate_greeting(self) -> str:
        """Generate a greeting message."""
        greetings = [
            "Hello! Thank you for calling. How can I help you today?",
            "Hi there! I'm here to assist you. What can I do for you?",
            "Welcome! I'd be happy to help. What brings you in today?"
        ]
        return greetings[0]  # Could be randomized or AI-generated

    def generate_escalation_message(self) -> str:
        """Generate a message for escalating to human agent."""
        return "I understand this requires special attention. Let me connect you with a human agent who can better assist you. Please hold for a moment."

    def generate_goodbye(self) -> str:
        """Generate a goodbye message."""
        return "Thank you for calling. Have a great day! Goodbye."


# Singleton instance
response_generator = ResponseGenerator()
