"""
Core Call Detection Service
Handles call monitoring, audio recording, and fraud detection orchestration
"""

import asyncio
import logging
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any
import numpy as np

from ..ml.whisper_processor import WhisperProcessor
from ..ml.llm_analyzer import LLMAnalyzer
from ..audio.audio_analyzer import AudioAnalyzer
from ..database.call_repository import CallRepository
from config import Config

logger = logging.getLogger(__name__)

class CallDetectionService:
    """Main service for call fraud detection"""
    
    def __init__(self, config: Config):
        self.config = config
        self.is_monitoring = False
        self.current_call_id = None
        
        # Initialize components
        self.whisper_processor = WhisperProcessor(config)
        self.llm_analyzer = LLMAnalyzer(config)
        self.audio_analyzer = AudioAnalyzer(config)
        self.call_repository = CallRepository(config)
        
        # Audio recording
        self.audio_buffer = []
        self.is_recording = False
        
    async def initialize(self):
        """Initialize all ML models and components"""
        try:
            logger.info("Initializing Call Detection Service...")
            
            # Initialize ML models
            await self.whisper_processor.initialize()
            await self.llm_analyzer.initialize()
            
            # Initialize database
            self.call_repository.initialize()
            
            logger.info("Call Detection Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Call Detection Service: {e}")
            return False
    
    async def start_monitoring(self):
        """Start call monitoring"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        logger.info("Started call monitoring")
        
        # Start monitoring loop
        await self._monitoring_loop()
    
    async def stop_monitoring(self):
        """Stop call monitoring"""
        self.is_monitoring = False
        if self.is_recording:
            await self.stop_call_recording()
        logger.info("Stopped call monitoring")
    
    async def on_call_started(self, phone_number: str = None):
        """Handle incoming call detection"""
        if self.is_recording:
            return
            
        self.current_call_id = self._generate_call_id()
        logger.info(f"Call started: {self.current_call_id}")
        
        # Start recording and analysis
        await self.start_call_recording()
        
    async def on_call_ended(self):
        """Handle call end"""
        if not self.is_recording:
            return
            
        logger.info(f"Call ended: {self.current_call_id}")
        
        # Stop recording and process final results
        await self.stop_call_recording()
        await self._process_final_results()
        
        self.current_call_id = None
    
    async def start_call_recording(self):
        """Start audio recording and real-time analysis"""
        self.is_recording = True
        self.audio_buffer = []
        
        # Start real-time processing
        asyncio.create_task(self._real_time_processing())
        
    async def stop_call_recording(self):
        """Stop audio recording"""
        self.is_recording = False
        
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Check for incoming calls (placeholder - would integrate with Android APIs)
                # For now, simulate call detection
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _real_time_processing(self):
        """Real-time audio processing and fraud detection"""
        while self.is_recording:
            try:
                # Simulate audio chunk (in real implementation, get from microphone)
                audio_chunk = self._get_audio_chunk()
                
                if audio_chunk is not None:
                    # Add to buffer
                    self.audio_buffer.extend(audio_chunk)
                    
                    # Process chunk for transcription
                    transcription = await self.whisper_processor.transcribe_chunk(audio_chunk)
                    
                    if transcription.strip():
                        # Analyze conversation
                        conversation_analysis = await self.llm_analyzer.analyze_conversation(transcription)
                        
                        # Analyze audio features
                        audio_features = self.audio_analyzer.extract_features(audio_chunk, self.config.SAMPLE_RATE)
                        audio_risk = self.audio_analyzer.calculate_audio_risk_score(audio_features)
                        
                        # Handle real-time results
                        await self._handle_real_time_result(transcription, conversation_analysis, audio_risk)
                
                await asyncio.sleep(self.config.DETECTION_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in real-time processing: {e}")
                await asyncio.sleep(1)
    
    async def _handle_real_time_result(self, transcription: str, conversation_analysis: Dict, audio_risk: float):
        """Handle real-time detection results"""
        combined_risk = (conversation_analysis.get('risk_score', 0) + audio_risk) / 2
        
        logger.info(f"Real-time analysis - Risk: {combined_risk:.2f}, Text: {transcription[:50]}...")
        
        # Alert if high risk
        if combined_risk > self.config.HIGH_RISK_THRESHOLD:
            logger.warning(f"HIGH RISK CALL DETECTED! Risk: {combined_risk:.2f}")
            # TODO: Trigger notification/alert
    
    async def _process_final_results(self):
        """Process final call results and save to database"""
        if not self.audio_buffer or not self.current_call_id:
            return
            
        try:
            # Convert audio buffer to numpy array
            audio_data = np.array(self.audio_buffer, dtype=np.float32)
            
            # Final transcription
            final_transcription = await self.whisper_processor.transcribe_audio(audio_data)
            
            # Final conversation analysis
            conversation_analysis = await self.llm_analyzer.analyze_conversation(final_transcription)
            
            # Final audio analysis
            audio_features = self.audio_analyzer.extract_features(audio_data, self.config.SAMPLE_RATE)
            audio_risk = self.audio_analyzer.calculate_audio_risk_score(audio_features)
            
            # Calculate final risk score
            final_risk = (conversation_analysis.get('risk_score', 0) + audio_risk) / 2
            is_fraud = final_risk > self.config.MEDIUM_RISK_THRESHOLD
            
            # Save call record
            call_record = {
                'id': self.current_call_id,
                'timestamp': datetime.now().isoformat(),
                'duration': len(audio_data) / self.config.SAMPLE_RATE,
                'transcription': final_transcription,
                'risk_score': final_risk,
                'is_fraud': is_fraud,
                'conversation_analysis': conversation_analysis,
                'audio_features': audio_features,
                'audio_risk': audio_risk
            }
            
            self.call_repository.save_call_record(call_record)
            
            logger.info(f"Call analysis complete - Risk: {final_risk:.2f}, Fraud: {is_fraud}")
            
        except Exception as e:
            logger.error(f"Error processing final results: {e}")
    
    def _get_audio_chunk(self) -> Optional[np.ndarray]:
        """Get audio chunk from microphone (placeholder)"""
        # In real implementation, this would capture audio from microphone
        # For now, return None to simulate no audio
        return None
    
    def _generate_call_id(self) -> str:
        """Generate unique call ID"""
        return f"call_{int(time.time() * 1000)}"
