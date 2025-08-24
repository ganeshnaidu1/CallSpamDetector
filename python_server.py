#!/usr/bin/env python3
"""
Python WebSocket server for real-time audio processing
Receives audio from Android and processes with Whisper + LLM
"""

import asyncio
import logging
import numpy as np
import websockets
import json
from collections import deque
from datetime import datetime
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.ml.whisper_processor import WhisperProcessor
from src.ml.llm_analyzer import LLMAnalyzer
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.config = Config()
        self.whisper = WhisperProcessor(self.config)
        self.llm = LLMAnalyzer(self.config)
        self.audio_buffer = deque(maxlen=int(16000 * 3))  # 3 seconds buffer
        self.is_processing = False
        
    async def initialize(self):
        """Initialize ML models"""
        await self.whisper.initialize()
        await self.llm.initialize()
        logger.info("Audio processor initialized")
        
    def add_audio_chunk(self, audio_data: bytes):
        """Add audio chunk to buffer"""
        # Convert bytes to numpy array (16-bit PCM)
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        self.audio_buffer.extend(audio_array)
        
    async def process_buffer(self):
        """Process current buffer with Whisper and LLM"""
        if len(self.audio_buffer) < 16000 * 0.5:  # Less than 0.5 seconds
            return None
            
        # Convert buffer to numpy array
        audio_data = np.array(list(self.audio_buffer), dtype=np.float32)
        
        # Transcribe with Whisper
        transcription = await self.whisper.transcribe_audio(audio_data)
        
        if not transcription.strip():
            return None
            
        # Analyze with LLM
        analysis = await self.llm.analyze_conversation(transcription)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'transcription': transcription,
            'risk_score': analysis.get('risk_score', 0.0),
            'is_suspicious': analysis.get('is_suspicious', False),
            'confidence': analysis.get('confidence', 0.0),
            'reasoning': analysis.get('reasoning', ''),
            'detected_keywords': analysis.get('detected_keywords', []),
            'detected_phrases': analysis.get('detected_phrases', [])
        }

async def handle_websocket(websocket, path):
    """Handle WebSocket connection"""
    processor = AudioProcessor()
    await processor.initialize()
    
    logger.info(f"WebSocket client connected from {websocket.remote_address}")
    
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                # Audio data
                processor.add_audio_chunk(message)
                
                # Process buffer every 1 second
                if not processor.is_processing:
                    processor.is_processing = True
                    result = await processor.process_buffer()
                    processor.is_processing = False
                    
                    if result:
                        # Send result back to Android
                        await websocket.send(json.dumps(result))
                        
                        # Log high-risk calls
                        if result['risk_score'] > 0.7:
                            logger.warning(f"🚨 HIGH RISK CALL DETECTED!")
                            logger.warning(f"Risk Score: {result['risk_score']:.2f}")
                            logger.warning(f"Transcription: {result['transcription'][:100]}...")
                            logger.warning(f"Keywords: {result['detected_keywords']}")
                            logger.warning(f"Reasoning: {result['reasoning']}")
                        elif result['risk_score'] > 0.5:
                            logger.info(f"⚠️ Medium risk call - Score: {result['risk_score']:.2f}")
                            
    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

async def main():
    """Start WebSocket server"""
    host = "0.0.0.0"  # Listen on all interfaces
    port = 8765
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    logger.info("Waiting for Android app to connect...")
    
    async with websockets.serve(handle_websocket, host, port):
        logger.info("✅ WebSocket server is running!")
        logger.info("📱 Android app should connect to: ws://YOUR_IP:8765/stream")
        logger.info("🛑 Press Ctrl+C to stop")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
