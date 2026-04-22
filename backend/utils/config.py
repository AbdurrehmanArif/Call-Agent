"""
Configuration management for the call agent.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")

class Config:
    """Application configuration."""

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    # STT Specific (Defaults to OpenAI if not set)
    STT_API_KEY = os.getenv("STT_API_KEY", OPENAI_API_KEY)
    STT_BASE_URL = os.getenv("STT_BASE_URL", "https://api.openai.com/v1")
    STT_MODEL = os.getenv("STT_MODEL", "whisper-1")

    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")



    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # Audio
    SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
    CHANNELS = int(os.getenv("CHANNELS", "1"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1024"))

    # Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", "./backend/database/call_logs.db")

    # ElevenLabs Voice Settings
    ELEVENLABS_VOICE_ID = "Rachel"  # Default voice
    ELEVENLABS_MODEL = "eleven_turbo_v2_5"



    ELEVENLABS_STABILITY = 0.5
    ELEVENLABS_SIMILARITY_BOOST = 0.75

    # OpenAI Settings
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "meta/llama-3.3-70b-instruct")
    MAX_TOKENS = 150
    TEMPERATURE = 0.7


    # Speech Recognition
    SPEECH_RECOGNITION_LANGUAGE = "en-US"

    # Sentiment Analysis Thresholds
    NEGATIVE_SENTIMENT_THRESHOLD = -0.3
    POSITIVE_SENTIMENT_THRESHOLD = 0.3


config = Config()

