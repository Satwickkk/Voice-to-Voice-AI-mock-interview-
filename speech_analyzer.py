"""
Speech analysis module for tone and confidence analysis
"""

import numpy as np
import librosa
import webrtcvad
import wave
import os
from typing import Dict, List, Tuple, Optional
from scipy import signal
from scipy.stats import stats
from config import CONFIDENCE_WEIGHTS
from utils import normalize_audio, calculate_speaking_rate, calculate_word_count

class SpeechAnalyzer:
    """
    Analyzes speech for tone, confidence, and speaking patterns
    """
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2 (moderate)
        
    def analyze_speech(self, audio_file: str, transcript: str = "") -> Dict:
        """
        Comprehensive speech analysis
        
        Args:
            audio_file: Path to audio file
            transcript: Text transcript of speech
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Load audio
            audio_data, sr = self._load_audio(audio_file)
            
            # Perform various analyses
            pitch_analysis = self._analyze_pitch(audio_data, sr)
            tempo_analysis = self._analyze_tempo(audio_data, sr)
            energy_analysis = self._analyze_energy(audio_data, sr)
            pause_analysis = self._analyze_pauses(audio_data, sr)
            clarity_analysis = self._analyze_clarity(audio_data, sr)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                pitch_analysis, tempo_analysis, energy_analysis, 
                pause_analysis, clarity_analysis
            )
            
            # Analyze transcript if provided
            content_analysis = {}
            if transcript:
                content_analysis = self._analyze_content(transcript)
            
            return {
                "pitch": pitch_analysis,
                "tempo": tempo_analysis,
                "energy": energy_analysis,
                "pauses": pause_analysis,
                "clarity": clarity_analysis,
                "confidence_score": confidence_score,
                "content": content_analysis,
                "overall_analysis": self._generate_overall_analysis(
                    pitch_analysis, tempo_analysis, energy_analysis,
                    pause_analysis, clarity_analysis, confidence_score
                )
            }
            
        except Exception as e:
            print(f"Speech analysis error: {e}")
            return self._get_default_analysis()
    
    def _load_audio(self, audio_file: str) -> Tuple[np.ndarray, int]:
        """
        Load audio file and resample if necessary
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        # Load audio with librosa
        audio_data, sr = librosa.load(audio_file, sr=None)
        
        # Resample if necessary
        if sr != self.sample_rate:
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)
            sr = self.sample_rate
        
        return audio_data, sr
    
    def _analyze_pitch(self, audio_data: np.ndarray, sr: int) -> Dict:
        """
        Analyze pitch characteristics
        
        Args:
            audio_data: Audio data
            sr: Sample rate
            
        Returns:
            Pitch analysis results
        """
        try:
            # Extract pitch using librosa
            pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sr)
            
            # Get voiced frames
            voiced_frames = magnitudes > 0.1 * np.max(magnitudes)
            voiced_pitches = pitches[voiced_frames]
            
            if len(voiced_pitches) == 0:
                return self._get_default_pitch_analysis()
            
            # Calculate pitch statistics
            pitch_mean = np.mean(voiced_pitches)
            pitch_std = np.std(voiced_pitches)
            pitch_range = np.max(voiced_pitches) - np.min(voiced_pitches)
            
            # Calculate pitch stability (lower std = more stable)
            pitch_stability = max(0, 100 - (pitch_std / pitch_mean * 100)) if pitch_mean > 0 else 0
            
            return {
                "mean_pitch": float(pitch_mean),
                "pitch_std": float(pitch_std),
                "pitch_range": float(pitch_range),
                "pitch_stability": float(pitch_stability),
                "pitch_score": float(pitch_stability / 100)
            }
            
        except Exception as e:
            print(f"Pitch analysis error: {e}")
            return self._get_default_pitch_analysis()
    
    def _analyze_tempo(self, audio_data: np.ndarray, sr: int) -> Dict:
        """
        Analyze speaking tempo and rhythm
        
        Args:
            audio_data: Audio data
            sr: Sample rate
            
        Returns:
            Tempo analysis results
        """
        try:
            # Extract tempo
            tempo, _ = librosa.beat.beat_track(y=audio_data, sr=sr)
            
            # Calculate speaking rate (approximate)
            # This is a simplified calculation
            duration = len(audio_data) / sr
            speaking_rate = tempo / 2  # Approximate conversion
            
            # Score based on ideal speaking rate (120-150 WPM)
            if 120 <= speaking_rate <= 150:
                tempo_score = 100
            elif 100 <= speaking_rate <= 180:
                tempo_score = 80
            elif 80 <= speaking_rate <= 200:
                tempo_score = 60
            else:
                tempo_score = 40
            
            return {
                "tempo_bpm": float(tempo),
                "speaking_rate_wpm": float(speaking_rate),
                "duration_seconds": float(duration),
                "tempo_score": float(tempo_score / 100)
            }
            
        except Exception as e:
            print(f"Tempo analysis error: {e}")
            return self._get_default_tempo_analysis()
    
    def _analyze_energy(self, audio_data: np.ndarray, sr: int) -> Dict:
        """
        Analyze energy and volume characteristics
        
        Args:
            audio_data: Audio data
            sr: Sample rate
            
        Returns:
            Energy analysis results
        """
        try:
            # Calculate RMS energy
            rms = librosa.feature.rms(y=audio_data)[0]
            
            # Calculate energy statistics
            energy_mean = np.mean(rms)
            energy_std = np.std(rms)
            energy_max = np.max(rms)
            energy_min = np.min(rms)
            
            # Calculate energy consistency
            energy_consistency = max(0, 100 - (energy_std / energy_mean * 100)) if energy_mean > 0 else 0
            
            # Calculate dynamic range
            dynamic_range = energy_max - energy_min
            
            return {
                "mean_energy": float(energy_mean),
                "energy_std": float(energy_std),
                "max_energy": float(energy_max),
                "min_energy": float(energy_min),
                "dynamic_range": float(dynamic_range),
                "energy_consistency": float(energy_consistency),
                "energy_score": float(energy_consistency / 100)
            }
            
        except Exception as e:
            print(f"Energy analysis error: {e}")
            return self._get_default_energy_analysis()
    
    def _analyze_pauses(self, audio_data: np.ndarray, sr: int) -> Dict:
        """
        Analyze pauses and silence patterns
        
        Args:
            audio_data: Audio data
            sr: Sample rate
            
        Returns:
            Pause analysis results
        """
        try:
            # Convert to 16-bit PCM for VAD
            audio_16bit = (audio_data * 32767).astype(np.int16)
            
            # Frame size for VAD (30ms)
            frame_size = int(0.03 * sr)
            frames = []
            
            # Split audio into frames
            for i in range(0, len(audio_16bit), frame_size):
                frame = audio_16bit[i:i + frame_size]
                if len(frame) == frame_size:
                    frames.append(frame.tobytes())
            
            # Analyze voice activity
            voice_frames = 0
            total_frames = len(frames)
            
            for frame in frames:
                if self.vad.is_speech(frame, sr):
                    voice_frames += 1
            
            # Calculate pause statistics
            voice_ratio = voice_frames / total_frames if total_frames > 0 else 0
            pause_ratio = 1 - voice_ratio
            
            # Score based on optimal pause ratio (10-20%)
            if 0.1 <= pause_ratio <= 0.2:
                pause_score = 100
            elif 0.05 <= pause_ratio <= 0.3:
                pause_score = 80
            elif 0.02 <= pause_ratio <= 0.4:
                pause_score = 60
            else:
                pause_score = 40
            
            return {
                "voice_ratio": float(voice_ratio),
                "pause_ratio": float(pause_ratio),
                "total_frames": total_frames,
                "voice_frames": voice_frames,
                "pause_score": float(pause_score / 100)
            }
            
        except Exception as e:
            print(f"Pause analysis error: {e}")
            return self._get_default_pause_analysis()
    
    def _analyze_clarity(self, audio_data: np.ndarray, sr: int) -> Dict:
        """
        Analyze speech clarity and articulation
        
        Args:
            audio_data: Audio data
            sr: Sample rate
            
        Returns:
            Clarity analysis results
        """
        try:
            # Calculate spectral centroid (brightness)
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sr)[0]
            
            # Calculate spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sr)[0]
            
            # Calculate zero crossing rate
            zero_crossing_rate = librosa.feature.zero_crossing_rate(audio_data)[0]
            
            # Calculate clarity metrics
            centroid_mean = np.mean(spectral_centroids)
            rolloff_mean = np.mean(spectral_rolloff)
            zcr_mean = np.mean(zero_crossing_rate)
            
            # Simplified clarity score based on spectral characteristics
            # Higher centroid and rolloff generally indicate clearer speech
            clarity_score = min(100, (centroid_mean / 2000 + rolloff_mean / 4000) * 50)
            
            return {
                "spectral_centroid": float(centroid_mean),
                "spectral_rolloff": float(rolloff_mean),
                "zero_crossing_rate": float(zcr_mean),
                "clarity_score": float(clarity_score / 100)
            }
            
        except Exception as e:
            print(f"Clarity analysis error: {e}")
            return self._get_default_clarity_analysis()
    
    def _analyze_content(self, transcript: str) -> Dict:
        """
        Analyze transcript content for filler words and structure
        
        Args:
            transcript: Speech transcript
            
        Returns:
            Content analysis results
        """
        try:
            words = transcript.lower().split()
            word_count = len(words)
            
            # Count filler words
            filler_words = ["um", "uh", "like", "you know", "sort of", "kind of", "basically", "actually"]
            filler_count = sum(1 for word in words if word in filler_words)
            
            # Calculate filler ratio
            filler_ratio = filler_count / word_count if word_count > 0 else 0
            
            # Score based on filler word usage
            if filler_ratio <= 0.05:
                content_score = 100
            elif filler_ratio <= 0.1:
                content_score = 80
            elif filler_ratio <= 0.15:
                content_score = 60
            else:
                content_score = 40
            
            return {
                "word_count": word_count,
                "filler_count": filler_count,
                "filler_ratio": float(filler_ratio),
                "content_score": float(content_score / 100)
            }
            
        except Exception as e:
            print(f"Content analysis error: {e}")
            return {"word_count": 0, "filler_count": 0, "filler_ratio": 0, "content_score": 0}
    
    def _calculate_confidence_score(self, pitch: Dict, tempo: Dict, 
                                  energy: Dict, pauses: Dict, clarity: Dict) -> float:
        """
        Calculate overall confidence score
        
        Args:
            pitch: Pitch analysis results
            tempo: Tempo analysis results
            energy: Energy analysis results
            pauses: Pause analysis results
            clarity: Clarity analysis results
            
        Returns:
            Overall confidence score (0-100)
        """
        try:
            # Get individual scores with better normalization
            pitch_score = pitch.get("pitch_score", 0) * 100  # Convert to 0-100 scale
            tempo_score = tempo.get("tempo_score", 0) * 100
            energy_score = energy.get("energy_score", 0) * 100
            pause_score = pauses.get("pause_score", 0) * 100
            clarity_score = clarity.get("clarity_score", 0) * 100
            
            # Apply weights from config
            weighted_score = (
                pitch_score * CONFIDENCE_WEIGHTS["pitch_stability"] +
                tempo_score * CONFIDENCE_WEIGHTS["speaking_rate"] +
                energy_score * CONFIDENCE_WEIGHTS["energy_consistency"] +
                pause_score * CONFIDENCE_WEIGHTS["pause_frequency"] +
                clarity_score * CONFIDENCE_WEIGHTS["clarity"]
            )
            
            # Add bonus for good overall performance
            if weighted_score > 70:
                weighted_score = min(100, weighted_score + 5)  # Bonus for good performance
            elif weighted_score < 30:
                weighted_score = max(20, weighted_score - 5)  # Penalty for poor performance
            
            # Ensure score is within valid range
            final_score = max(20, min(100, weighted_score))
            
            return final_score
            
        except Exception as e:
            print(f"Confidence score calculation error: {e}")
            return 60.0  # Return a reasonable default score
    
    def _generate_overall_analysis(self, pitch: Dict, tempo: Dict, energy: Dict,
                                 pauses: Dict, clarity: Dict, confidence_score: float) -> Dict:
        """
        Generate overall analysis summary
        
        Args:
            pitch: Pitch analysis results
            tempo: Tempo analysis results
            energy: Energy analysis results
            pauses: Pause analysis results
            clarity: Clarity analysis results
            confidence_score: Overall confidence score
            
        Returns:
            Overall analysis summary
        """
        strengths = []
        weaknesses = []
        suggestions = []
        
        # Analyze pitch (more lenient threshold)
        pitch_stability = pitch.get("pitch_stability", 0)
        if pitch_stability > 60:  # Lowered from 70
            strengths.append("Good pitch stability")
        elif pitch_stability > 40:
            strengths.append("Acceptable pitch variation")
        else:
            weaknesses.append("Unstable pitch")
            suggestions.append("Practice maintaining consistent pitch")
        
        # Analyze tempo (more realistic thresholds)
        tempo_score = tempo.get("tempo_score", 0)
        speaking_rate = tempo.get("speaking_rate_wpm", 0)
        if tempo_score > 0.6:  # Lowered from 0.7
            strengths.append("Good speaking pace")
        elif speaking_rate > 0 and speaking_rate < 300:  # Reasonable range
            strengths.append("Acceptable speaking rate")
        else:
            weaknesses.append("Speaking pace needs adjustment")
            suggestions.append("Practice speaking at 120-200 words per minute")
        
        # Analyze energy (more lenient)
        energy_consistency = energy.get("energy_consistency", 0)
        if energy_consistency > 60:  # Lowered from 70
            strengths.append("Consistent voice energy")
        elif energy_consistency > 40:
            strengths.append("Acceptable voice energy")
        else:
            weaknesses.append("Inconsistent voice energy")
            suggestions.append("Practice maintaining steady volume")
        
        # Analyze pauses (more realistic)
        pause_score = pauses.get("pause_score", 0)
        pause_ratio = pauses.get("pause_ratio", 0)
        if pause_score > 0.6:  # Lowered from 0.7
            strengths.append("Good use of pauses")
        elif pause_ratio > 0.05 and pause_ratio < 0.5:  # Reasonable pause range
            strengths.append("Natural pause usage")
        else:
            weaknesses.append("Pause usage needs improvement")
            suggestions.append("Practice using natural pauses for emphasis")
        
        # Analyze clarity (more lenient)
        clarity_score = clarity.get("clarity_score", 0)
        if clarity_score > 0.6:  # Lowered from 0.7
            strengths.append("Clear articulation")
        elif clarity_score > 0.4:
            strengths.append("Acceptable articulation")
        else:
            weaknesses.append("Articulation needs improvement")
            suggestions.append("Practice enunciating words clearly")
        
        # If no strengths found, add some encouraging feedback
        if not strengths:
            strengths.append("Good effort in the interview")
            strengths.append("Willingness to participate")
        
        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestions": suggestions,
            "confidence_level": self._get_confidence_level(confidence_score)
        }
    
    def _get_confidence_level(self, score: float) -> str:
        """Get confidence level description"""
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
    
    # Default analysis methods
    def _get_default_analysis(self) -> Dict:
        return {
            "pitch": self._get_default_pitch_analysis(),
            "tempo": self._get_default_tempo_analysis(),
            "energy": self._get_default_energy_analysis(),
            "pauses": self._get_default_pause_analysis(),
            "clarity": self._get_default_clarity_analysis(),
            "confidence_score": 50.0,
            "content": {},
            "overall_analysis": {
                "strengths": [],
                "weaknesses": ["Unable to analyze audio"],
                "suggestions": ["Please ensure clear audio recording"],
                "confidence_level": "Unknown"
            }
        }
    
    def _get_default_pitch_analysis(self) -> Dict:
        return {"mean_pitch": 0, "pitch_std": 0, "pitch_range": 0, "pitch_stability": 0, "pitch_score": 0}
    
    def _get_default_tempo_analysis(self) -> Dict:
        return {"tempo_bpm": 0, "speaking_rate_wpm": 0, "duration_seconds": 0, "tempo_score": 0}
    
    def _get_default_energy_analysis(self) -> Dict:
        return {"mean_energy": 0, "energy_std": 0, "max_energy": 0, "min_energy": 0, "dynamic_range": 0, "energy_consistency": 0, "energy_score": 0}
    
    def _get_default_pause_analysis(self) -> Dict:
        return {"voice_ratio": 0, "pause_ratio": 0, "total_frames": 0, "voice_frames": 0, "pause_score": 0}
    
    def _get_default_clarity_analysis(self) -> Dict:
        return {"spectral_centroid": 0, "spectral_rolloff": 0, "zero_crossing_rate": 0, "clarity_score": 0}
