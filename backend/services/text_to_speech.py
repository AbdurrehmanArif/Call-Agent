"""
Text-to-Speech service using ElevenLabs API.
"""
from typing import Tuple, Optional
import requests
from backend.utils.config import config


class TextToSpeech:
    """Convert text to speech audio."""

    def __init__(self):
        self.api_key = config.ELEVENLABS_API_KEY if config.ELEVENLABS_API_KEY else None
        self.voice_id = self._get_voice_id(config.ELEVENLABS_VOICE_ID)
        self.model = config.ELEVENLABS_MODEL
        self.base_url = "https://api.elevenlabs.io/v1"

    def _get_voice_id(self, voice_name: str) -> str:
        """Get voice ID from voice name."""
        voice_map = {
            "Sarah": "EXAVITQu4vr4xnSDxMaL",
            "Alice": "Xb7hH8MSUJpSbSDYk0k2",
            "George": "JBFqnCBsd6RMkjVDRZzb",
            "Liam": "TX3LPaxmHKxFdv7VOQHJ",
            "Bella": "hpp4J3VqNfWAUOO0d1Us",
        }
        return voice_map.get(voice_name, "EXAVITQu4vr4xnSDxMaL")



    def generate_speech(self, text: str) -> Tuple[Optional[bytes], str]:
        """
        Generate speech audio from text.

        Args:
            text: Text to convert to speech

        Returns:
            Tuple of (audio_bytes, error_message)
        """
        if not self.api_key:
            return None, "ElevenLabs API key not configured"

        if not text:
            return None, "Empty text provided"

        try:
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            data = {
                "text": text,
                "model_id": config.ELEVENLABS_MODEL,

                "voice_settings": {
                    "stability": config.ELEVENLABS_STABILITY,
                    "similarity_boost": config.ELEVENLABS_SIMILARITY_BOOST
                }
            }

            response = requests.post(url, headers=headers, json=data)


            
            if response.status_code != 200:
                error_detail = f"ElevenLabs API Error: {response.status_code} - {response.text}"
                print(f"[ERROR] {error_detail}")
                return None, error_detail

            return response.content, ""

        except Exception as e:
            error_msg = f"TTS Connection error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return None, error_msg


    def get_available_voices(self) -> list:
        """Get list of available voices."""
        if not self.api_key:
            return []

        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            return [
                {"name": v.get("name", "Unknown"), "voice_id": v.get("voice_id", "")}
                for v in data.get("voices", [])
            ]
        except Exception:
            return []

    def set_voice(self, voice_name: str) -> bool:
        """
        Set the voice to use for TTS.

        Args:
            voice_name: Name of the voice to use

        Returns:
            True if voice was set successfully
        """
        voice_id = self._get_voice_id(voice_name)
        if voice_id:
            self.voice_id = voice_id
            return True
        return False


# Singleton instance
tts = TextToSpeech()
