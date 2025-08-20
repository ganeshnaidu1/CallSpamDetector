"""
Whisper Speech-to-Text Processor
Handles real-time speech transcription using OpenAI Whisper
"""

import asyncio
import logging
import numpy as np
from typing import Optional, List
import whisper
import torch

logger = logging.getLogger(__name__)

class WhisperProcessor:
    """Whisper-based speech-to-text processor"""
    
    def __init__(self, config):
        self.config = config
        self.model = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize Whisper modell"""
        try:
            logger.info(f"Loading Whisper model: {self.config.WHISPER_MODEL_SIZE}")
            
            # Load model in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                whisper.load_model, 
                self.config.WHISPER_MODEL_SIZE
            )
            
            self.is_initialized = True
            logger.info("Whisper model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            return False
    
    async def transcribe_chunk(self, audio_chunk: np.ndarray) -> str:
        """Transcribe a small audio chunk for real-time processing"""
        if not self.is_initialized or self.model is None:
            return ""
            
        try:
            # Ensure audio is in the right format
            if len(audio_chunk) < self.config.SAMPLE_RATE * 0.5:  # Less than 0.5 seconds
                return ""
            
            # Normalize audio
            audio_chunk = audio_chunk.astype(np.float32)
            if np.max(np.abs(audio_chunk)) > 0:
                audio_chunk = audio_chunk / np.max(np.abs(audio_chunk))
            
            # Transcribe in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                audio_chunk
            )
            
            return result.get("text", "").strip()
            
        except Exception as e:
            logger.error(f"Error transcribing audio chunk: {e}")
            return ""
    
    async def transcribe_audio(self, audio_data: np.ndarray) -> str:
        """Transcribe complete audio data"""
        if not self.is_initialized or self.model is None:
            return ""
            
        try:
            # Normalize audio
            audio_data = audio_data.astype(np.float32)
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Transcribe in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                audio_data
            )
            
            return result.get("text", "").strip()
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return ""
    
    def _transcribe_sync(self, audio_data: np.ndarray) -> dict:
        """Synchronous transcription method"""
        try:
            result = self.model.transcribe(
                audio_data,
                language=self.config.WHISPER_LANGUAGE,
                task="transcribe"
            )
            return result
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return {"text": ""}
    
    def detect_fraud_keywords(self, transcription: str) -> dict:
        """Detect fraud-related keywords in transcription"""
        transcription_lower = transcription.lower()
        
        keyword_matches = []
        phrase_matches = []
        emotional_triggers = []
        
        # Check for fraud keywords
        for keyword in self.config.FRAUD_KEYWORDS:
            if keyword.lower() in transcription_lower:
                keyword_matches.append(keyword)
        
        # Check for suspicious phrases
        for phrase in self.config.SUSPICIOUS_PHRASES:
            if phrase.lower() in transcription_lower:
                phrase_matches.append(phrase)
        
        # Check for emotional triggers
        for trigger in self.config.EMOTIONAL_TRIGGERS:
            if trigger.lower() in transcription_lower:
                emotional_triggers.append(trigger)
        
        return {
            'keyword_matches': keyword_matches,
            'phrase_matches': phrase_matches,
            'emotional_triggers': emotional_triggers,
            'keyword_count': len(keyword_matches),
            'phrase_count': len(phrase_matches),
            'trigger_count': len(emotional_triggers)
        }
