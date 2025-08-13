"""
Audio processing module for real-time audio capture and manipulation
"""

import os
import wave
import numpy as np
import sounddevice as sd
import threading
import queue
import time
from typing import Optional, Callable, List
from config import AUDIO_SAMPLE_RATE, AUDIO_CHUNK_SIZE, AUDIO_CHANNELS, AUDIO_FORMAT
from utils import save_audio_chunk, normalize_audio

class AudioProcessor:
    """
    Handles real-time audio capture and processing
    """
    
    def __init__(self, sample_rate: int = AUDIO_SAMPLE_RATE, 
                 chunk_size: int = AUDIO_CHUNK_SIZE):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.recording_thread = None
        self.audio_buffer = []
        self.recording_start_time = None
        
    def start_recording(self, callback: Optional[Callable] = None):
        """
        Start recording audio from microphone
        
        Args:
            callback: Optional callback function for real-time processing
        """
        if self.is_recording:
            return
            
        self.is_recording = True
        self.audio_buffer = []
        self.recording_start_time = time.time()
        
        def audio_callback(indata, frames, time, status):
            """Callback for audio input"""
            if status:
                print(f"Audio status: {status}")
            
            # Convert to bytes and add to queue
            audio_chunk = indata.tobytes()
            self.audio_queue.put(audio_chunk)
            
            # Add to buffer for full recording
            self.audio_buffer.append(indata.copy())
            
            # Call custom callback if provided
            if callback:
                callback(indata, frames, time, status)
        
        # Start recording thread
        self.recording_thread = threading.Thread(
            target=self._record_audio,
            args=(audio_callback,)
        )
        self.recording_thread.start()
    
    def _record_audio(self, callback):
        """Internal method to handle audio recording"""
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=AUDIO_CHANNELS,
                dtype=AUDIO_FORMAT,
                blocksize=self.chunk_size,
                callback=callback
            ):
                while self.is_recording:
                    time.sleep(0.1)
        except Exception as e:
            print(f"Audio recording error: {e}")
            self.is_recording = False
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording and save audio file
        
        Returns:
            Path to saved audio file or None if no recording
        """
        if not self.is_recording:
            return None
            
        self.is_recording = False
        
        if self.recording_thread:
            self.recording_thread.join()
        
        if not self.audio_buffer:
            return None
        
        # Combine all audio chunks
        full_audio = np.concatenate(self.audio_buffer, axis=0)
        
        # Save to file
        timestamp = int(time.time())
        filename = f"recording_{timestamp}.wav"
        
        return save_audio_chunk(full_audio.tobytes(), filename, self.sample_rate)
    
    def get_recording_duration(self) -> float:
        """
        Get current recording duration in seconds
        
        Returns:
            Recording duration in seconds
        """
        if not self.recording_start_time:
            return 0.0
        return time.time() - self.recording_start_time
    
    def get_audio_level(self) -> float:
        """
        Get current audio level (RMS)
        
        Returns:
            Audio level as float
        """
        if not self.audio_buffer:
            return 0.0
        
        # Get the most recent chunk
        latest_chunk = self.audio_buffer[-1]
        rms = np.sqrt(np.mean(latest_chunk**2))
        return float(rms)

class AudioPlayer:
    """
    Handles audio playback
    """
    
    def __init__(self, sample_rate: int = AUDIO_SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.is_playing = False
        
    def play_audio_file(self, filepath: str):
        """
        Play audio file
        
        Args:
            filepath: Path to audio file
        """
        if not os.path.exists(filepath):
            print(f"Audio file not found: {filepath}")
            return
        
        try:
            # Load audio data
            audio_data, sample_rate = self._load_audio(filepath)
            
            # Play audio
            self.is_playing = True
            sd.play(audio_data, sample_rate)
            sd.wait()  # Wait for playback to complete
            self.is_playing = False
            
        except Exception as e:
            print(f"Audio playback error: {e}")
            self.is_playing = False
    
    def _load_audio(self, filepath: str) -> tuple:
        """
        Load audio file
        
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
    
    def play_audio_data(self, audio_data: np.ndarray, sample_rate: int = None):
        """
        Play audio data directly
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate (uses default if None)
        """
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        try:
            self.is_playing = True
            sd.play(audio_data, sample_rate)
            sd.wait()
            self.is_playing = False
        except Exception as e:
            print(f"Audio playback error: {e}")
            self.is_playing = False
    
    def stop_playback(self):
        """Stop current audio playback"""
        sd.stop()
        self.is_playing = False

class AudioAnalyzer:
    """
    Basic audio analysis utilities
    """
    
    @staticmethod
    def calculate_rms(audio_data: np.ndarray) -> float:
        """
        Calculate Root Mean Square of audio data
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            RMS value
        """
        return np.sqrt(np.mean(audio_data**2))
    
    @staticmethod
    def calculate_peak(audio_data: np.ndarray) -> float:
        """
        Calculate peak amplitude
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Peak amplitude
        """
        return np.max(np.abs(audio_data))
    
    @staticmethod
    def detect_silence(audio_data: np.ndarray, threshold: float = 0.01) -> bool:
        """
        Detect if audio chunk is mostly silence
        
        Args:
            audio_data: Audio data as numpy array
            threshold: RMS threshold for silence detection
            
        Returns:
            True if audio is mostly silence
        """
        rms = AudioAnalyzer.calculate_rms(audio_data)
        return rms < threshold
    
    @staticmethod
    def get_audio_statistics(audio_data: np.ndarray) -> dict:
        """
        Get comprehensive audio statistics
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Dictionary of audio statistics
        """
        rms = AudioAnalyzer.calculate_rms(audio_data)
        peak = AudioAnalyzer.calculate_peak(audio_data)
        
        return {
            "rms": float(rms),
            "peak": float(peak),
            "dynamic_range": float(peak / rms) if rms > 0 else 0,
            "is_silent": AudioAnalyzer.detect_silence(audio_data)
        }
