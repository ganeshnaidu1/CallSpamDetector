import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Dict, Any
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpamDetector:
    def __init__(self, model_name: str = "mrm8488/bert-tiny-finetuned-sms-spam-detection"):
        """
        Initialize the spam detector with a pre-trained model.
        
        Args:
            model_name: Name or path of the pre-trained model to use for spam detection
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self.labels = ["HAM", "SPAM"]
        
    def load(self):
        """Load the model and tokenizer."""
        try:
            logger.info(f"Loading tokenizer and model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def is_spam(self, text: str, threshold: float = 0.7) -> bool:
        """
        Check if the given text is spam.
        
        Args:
            text: The text to classify
            threshold: Confidence threshold for spam classification (0-1)
            
        Returns:
            bool: True if the text is classified as spam, False otherwise
        """
        if not self.model or not self.tokenizer:
            if not self.load():
                logger.error("Model not loaded")
                return False
        
        try:
            # Tokenize the input text
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=128,
                padding="max_length"
            ).to(self.device)
            
            # Get model predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Get probabilities
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            probs = probs.cpu().numpy()[0]
            
            # Get predicted label and confidence
            predicted_idx = np.argmax(probs)
            confidence = probs[predicted_idx]
            predicted_label = self.labels[predicted_idx]
            
            logger.info(f"Prediction: {predicted_label} (confidence: {confidence:.2f})")
            
            # Return True if predicted as SPAM with confidence above threshold
            return predicted_label == "SPAM" and confidence >= threshold
            
        except Exception as e:
            logger.error(f"Error during spam detection: {str(e)}")
            return False

# Global instance for Chaquopy
detector = SpamDetector()

# Function to be called from Kotlin
def is_spam(text: str) -> bool:
    """
    Check if the given text is spam.
    This function is called from Kotlin via Chaquopy.
    
    Args:
        text: The text to classify
        
    Returns:
        bool: True if the text is classified as spam, False otherwise
    """
    global detector
    return detector.is_spam(text)
