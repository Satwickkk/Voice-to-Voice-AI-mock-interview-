"""
Utility functions for the AI Voice-to-Voice Mock Interview System
"""

import os
import wave
import numpy as np
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Tuple
import json

def save_audio_chunk(audio_data: bytes, filename: str, sample_rate: int = 16000) -> str:
    """
    Save audio chunk to WAV file
    
    Args:
        audio_data: Raw audio bytes
        filename: Name of the file to save
        sample_rate: Audio sample rate
        
    Returns:
        Path to saved audio file
    """
    filepath = os.path.join("temp_audio", filename)
    
    with wave.open(filepath, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)
    
    return filepath

def load_audio_file(filepath: str) -> Tuple[np.ndarray, int]:
    """
    Load audio file and return numpy array with sample rate
    
    Args:
        filepath: Path to audio file
        
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    with wave.open(filepath, 'rb') as wav_file:
        sample_rate = wav_file.getframerate()
        audio_data = wav_file.readframes(wav_file.getnframes())
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
    
    return audio_array, sample_rate

def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
    """
    Normalize audio data to float32 range [-1, 1]
    
    Args:
        audio_data: Raw audio array
        
    Returns:
        Normalized audio array
    """
    return audio_data.astype(np.float32) / 32768.0

def format_time(seconds: float) -> str:
    """
    Format time in seconds to MM:SS format
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def calculate_speaking_rate(words: int, duration: float) -> float:
    """
    Calculate speaking rate in words per minute
    
    Args:
        words: Number of words spoken
        duration: Duration in seconds
        
    Returns:
        Speaking rate in WPM
    """
    if duration <= 0:
        return 0
    return (words / duration) * 60

def generate_session_id() -> str:
    """
    Generate unique session ID for interview
    
    Returns:
        Unique session ID
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"interview_{timestamp}"

def save_interview_data(session_id: str, data: Dict[str, Any]) -> str:
    """
    Save interview data to JSON file
    
    Args:
        session_id: Unique session identifier
        data: Interview data to save
        
    Returns:
        Path to saved data file
    """
    filepath = os.path.join("reports", f"{session_id}_data.json")
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    return filepath

def load_interview_data(session_id: str) -> Dict[str, Any]:
    """
    Load interview data from JSON file
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Loaded interview data
    """
    filepath = os.path.join("reports", f"{session_id}_data.json")
    
    if not os.path.exists(filepath):
        return {}
    
    with open(filepath, 'r') as f:
        return json.load(f)

def clean_text(text: str) -> str:
    """
    Clean and normalize text for analysis
    
    Args:
        text: Raw text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Remove common filler words
    filler_words = ["um", "uh", "like", "you know", "sort of", "kind of"]
    for filler in filler_words:
        text = text.replace(filler, "")
    
    return text.strip()

def calculate_word_count(text: str) -> int:
    """
    Calculate word count in text
    
    Args:
        text: Input text
        
    Returns:
        Word count
    """
    if not text:
        return 0
    return len(text.split())

def get_confidence_level(score: float) -> str:
    """
    Convert numerical score to confidence level
    
    Args:
        score: Confidence score (0-100)
        
    Returns:
        Confidence level string
    """
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Very Good"
    elif score >= 70:
        return "Good"
    elif score >= 60:
        return "Fair"
    elif score >= 50:
        return "Poor"
    else:
        return "Very Poor"

def format_feedback(feedback: Dict[str, Any]) -> str:
    """
    Format feedback data for display
    
    Args:
        feedback: Feedback dictionary
        
    Returns:
        Formatted feedback string
    """
    if not feedback:
        return "No feedback available."
    
    formatted = []
    
    if "score" in feedback:
        formatted.append(f"**Overall Score:** {feedback['score']:.1f}/100")
    
    if "strengths" in feedback and feedback["strengths"]:
        formatted.append(f"**Strengths:** {', '.join(feedback['strengths'])}")
    
    if "weaknesses" in feedback and feedback["weaknesses"]:
        formatted.append(f"**Areas for Improvement:** {', '.join(feedback['weaknesses'])}")
    
    if "suggestions" in feedback and feedback["suggestions"]:
        formatted.append(f"**Suggestions:** {', '.join(feedback['suggestions'])}")
    
    return "\n\n".join(formatted)

def cleanup_temp_files():
    """
    Clean up temporary audio files
    """
    temp_dir = "temp_audio"
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            if file.endswith('.wav'):
                os.remove(os.path.join(temp_dir, file))
