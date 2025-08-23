#!/usr/bin/env python3
"""
Whisper Processor for Audio-to-Text Conversion
Handles loading and using Whisper model for transcription
"""

import logging
import numpy as np
import whisper
from typing import Optional

logger = logging.getLogger(__name__)

class WhisperProcessor:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.model_name = config.WHISPER_MODEL_NAME
        
    async def initialize(self):
        """Initialize Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            return False
    
    async def transcribe_audio(self, audio_data: np.ndarray) -> str:
        """Transcribe audio data to text"""
        if self.model is None:
            logger.error("Whisper model not initialized")
            return ""
        
        try:
            # Ensure audio is in the right format for Whisper
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Whisper expects audio to be in range [-1, 1]
            if audio_data.max() > 1.0 or audio_data.min() < -1.0:
                audio_data = np.clip(audio_data, -1.0, 1.0)
            
            # Transcribe
            result = self.model.transcribe(audio_data)
            transcription = result["text"].strip()
            
            logger.info(f"Transcription: {transcription}")
            return transcription
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
    
    def get_model_info(self) -> dict:
        """Get model information"""
        if self.model is None:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "model_name": self.model_name,
            "model_type": type(self.model).__name__
        }
