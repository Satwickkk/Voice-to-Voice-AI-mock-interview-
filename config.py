"""
Configuration settings for the AI Voice-to-Voice Mock Interview System
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Audio Settings
AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
AUDIO_CHUNK_SIZE = int(os.getenv("AUDIO_CHUNK_SIZE", "1024"))
AUDIO_CHANNELS = 1
AUDIO_FORMAT = "int16"

# Interview Settings
DEFAULT_QUESTIONS = int(os.getenv("INTERVIEW_QUESTIONS", "10"))
INTERVIEW_TYPES = {
    "Software Engineer": "technical",
    "Data Scientist": "technical",
    "Product Manager": "behavioral",
    "Sales Representative": "behavioral",
    "Marketing Manager": "behavioral",
    "General": "mixed"
}

# AI Model Settings
WHISPER_MODEL = "whisper-1"
GEMINI_MODEL = "gemini-pro"
TTS_VOICE = "en"

# Analysis Settings
CONFIDENCE_WEIGHTS = {
    "pitch_stability": 0.2,
    "speaking_rate": 0.15,
    "energy_consistency": 0.2,
    "pause_frequency": 0.15,
    "clarity": 0.3
}

# UI Settings
STREAMLIT_THEME = {
    "primaryColor": "#FF6B6B",
    "backgroundColor": "#FFFFFF",
    "secondaryBackgroundColor": "#F0F2F6",
    "textColor": "#262730"
}

# File Paths
TEMP_AUDIO_DIR = "temp_audio"
REPORTS_DIR = "reports"

# Create directories if they don't exist
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
