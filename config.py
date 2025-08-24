"""
Configuration settings for Call Fraud Detection System
"""

from pathlib import Path

class Config:
    """Configuration class for the call fraud detection system"""
    
    def __init__(self):
        # Base directory
        self.BASE_DIR = Path(__file__).parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.MODELS_DIR = self.BASE_DIR / "models"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        
        # Create directories
        self.DATA_DIR.mkdir(exist_ok=True)
        self.MODELS_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
        
        # Audio settings
        self.SAMPLE_RATE = 16000
        self.CHUNK_SIZE = 1024
        self.CHANNELS = 1
        self.AUDIO_FORMAT = "float32"
        self.RECORDING_DURATION = 300  # 5 minutes max
        
        # Whisper model settings
        self.WHISPER_MODEL_SIZE = "base"  # tiny, base, small, medium, large
        self.WHISPER_MODEL_NAME = "base"  # For compatibility
        self.WHISPER_LANGUAGE = "en"
        self.WHISPER_DEVICE = "cpu"
        
        # LLM settings
        self.LLM_MODEL_NAME = "distilbert-base-uncased"
        self.LLM_MAX_LENGTH = 512
        self.LLM_DEVICE = "cpu"
        
        # Fraud detection patterns
        self.FRAUD_KEYWORDS = [
            "bank account", "credit card", "social security", "urgent", "verify",
            "suspended", "expired", "immediate action", "press 1", "call back",
            "refund", "prize", "winner", "congratulations", "free", "limited time",
            "act now", "final notice", "you've been selected", "confirm your identity",
            "IRS", "tax", "arrest", "lawsuit", "police", "FBI", "government"
        ]
        
        self.SUSPICIOUS_PHRASES = [
            "don't tell anyone", "keep this confidential", "this offer expires",
            "you must act immediately", "your account will be closed",
            "we need to verify", "for security purposes", "this is your final warning",
            "you have been selected", "congratulations you've won", "claim your prize",
            "send money", "wire transfer", "gift cards", "bitcoin", "cryptocurrency"
        ]
        
        self.EMOTIONAL_TRIGGERS = [
            "urgent", "emergency", "immediately", "now", "quickly", "hurry",
            "deadline", "expires", "last chance", "final", "limited time",
            "don't miss out", "act fast", "time sensitive"
        ]
        
        # Analysis weights
        self.KEYWORD_WEIGHT = 0.3
        self.PHRASE_WEIGHT = 0.4
        self.EMOTIONAL_WEIGHT = 0.2
        self.AUDIO_WEIGHT = 0.1
        
        # Risk thresholds
        self.RISK_THRESHOLD = 0.6  # Main threshold used in LLMAnalyzer
        self.LOW_RISK_THRESHOLD = 0.3
        self.MEDIUM_RISK_THRESHOLD = 0.6
        self.HIGH_RISK_THRESHOLD = 0.8
        
        
        # Monitoring settings
        self.REAL_TIME_PROCESSING = True
        self.CHUNK_DURATION = 2.0  # seconds
        self.DETECTION_INTERVAL = 0.5  # seconds
