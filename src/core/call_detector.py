#!/usr/bin/env python3
"""
Call Detection Service
Orchestrates call monitoring, recording, and analysis
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from src.ml.whisper_processor import WhisperProcessor
from src.ml.llm_analyzer import LLMAnalyzer
from src.database.call_repository import CallRepository

logger = logging.getLogger(__name__)

class CallDetectionService:
    def __init__(self, config):
        self.config = config
        self.whisper = WhisperProcessor(config)
        self.llm = LLMAnalyzer(config)
        self.repository = CallRepository(config)
        self.is_monitoring = False
        
    async def initialize(self) -> bool:
        """Initialize all components"""
        try:
            logger.info("Initializing Call Detection Service...")
            
            # Initialize ML components
            whisper_ok = await self.whisper.initialize()
            if not whisper_ok:
                logger.error("Failed to initialize Whisper")
                return False
            
            llm_ok = await self.llm.initialize()
            if not llm_ok:
                logger.error("Failed to initialize LLM Analyzer")
                return False
            
            # Initialize database
            db_ok = await self.repository.initialize()
            if not db_ok:
                logger.error("Failed to initialize database")
                return False
            
            logger.info("Call Detection Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Call Detection Service: {e}")
            return False
    
    async def start_monitoring(self):
        """Start call monitoring"""
        self.is_monitoring = True
        logger.info("Call monitoring started")
        
        # In a real implementation, this would listen for call events
        # For now, we'll just log that monitoring is active
        while self.is_monitoring:
            await asyncio.sleep(1)
    
    async def stop_monitoring(self):
        """Stop call monitoring"""
        self.is_monitoring = False
        logger.info("Call monitoring stopped")
    
    async def process_call_audio(self, audio_data: bytes, call_id: str) -> Dict[str, Any]:
        """Process call audio and return analysis results"""
        try:
            logger.info(f"Processing call audio for call_id: {call_id}")
            
            # Convert audio data to numpy array
            import numpy as np
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe with Whisper
            transcription = await self.whisper.transcribe_audio(audio_array)
            
            if not transcription.strip():
                logger.warning("No transcription generated from audio")
                return {
                    'call_id': call_id,
                    'transcription': '',
                    'risk_score': 0.0,
                    'is_suspicious': False,
                    'confidence': 0.0,
                    'reasoning': 'No speech detected',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Analyze with LLM
            analysis = await self.llm.analyze_conversation(transcription)
            
            # Add call_id to result
            result = {
                'call_id': call_id,
                'transcription': transcription,
                **analysis
            }
            
            # Save to database
            await self.repository.save_call_record(result)
            
            logger.info(f"Call analysis completed: Risk={result['risk_score']:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process call audio: {e}")
            return {
                'call_id': call_id,
                'transcription': '',
                'risk_score': 0.0,
                'is_suspicious': False,
                'confidence': 0.0,
                'reasoning': f'Processing error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_call_history(self, limit: int = 10) -> list:
        """Get recent call history"""
        try:
            return await self.repository.get_recent_calls(limit)
        except Exception as e:
            logger.error(f"Failed to get call history: {e}")
            return []
    
    async def get_call_by_id(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get specific call by ID"""
        try:
            return await self.repository.get_call_by_id(call_id)
        except Exception as e:
            logger.error(f"Failed to get call by ID: {e}")
            return None
