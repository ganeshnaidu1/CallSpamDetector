#!/usr/bin/env python3
"""
Main Entry Point for Call Fraud Detection System
Clean, structured implementation with proper imports
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.call_detector import CallDetectionService
from config import Config

# Setup logging
def setup_logging():
    """Setup logging configuration"""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'call_detector.log'),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)

class CallFraudDetectorApp:
    """Main application class for call fraud detection"""
    
    def __init__(self):
        self.config = Config()
        self.service = None
        self.running = False
        
    async def initialize(self):
        """Initialize the application"""
        try:
            logger.info("Initializing Call Fraud Detection System...")
            
            # Create service
            self.service = CallDetectionService(self.config)
            
            # Initialize all components
            success = await self.service.initialize()
            if not success:
                raise Exception("Failed to initialize call detection service")
            
            logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            return False
    
    async def start(self):
        """Start the call detection service"""
        if not await self.initialize():
            return
        
        try:
            logger.info("Starting Call Fraud Detection System...")
            
            # Start monitoring
            self.running = True
            await self.service.start_monitoring()
            
            logger.info("Call detection service started successfully")
            
            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the service"""
        logger.info("Stopping call detection service...")
        self.running = False
        
        if self.service:
            await self.service.stop_monitoring()
        
        logger.info("Service stopped")
    
    async def simulate_call(self, duration: int = 30):
        """Simulate a call for testing purposes"""
        if not self.service:
            logger.error("Service not initialized")
            return
        
        logger.info(f"Simulating call for {duration} seconds...")
        
        # Simulate call start
        await self.service.on_call_started("555-0123")
        
        # Wait for duration
        await asyncio.sleep(duration)
        
        # Simulate call end
        await self.service.on_call_ended()
        
        logger.info("Call simulation completed")

def main():
    """Main entry point"""
    setup_logging()
    
    app = CallFraudDetectorApp()
    
    try:
        # Check command line arguments
        if len(sys.argv) > 1 and sys.argv[1] == "--simulate":
            # Run simulation mode
            asyncio.run(app.simulate_call())
        else:
            # Run normal monitoring mode
            asyncio.run(app.start())
            
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()
