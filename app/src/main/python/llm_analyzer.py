"""
LLM Analyzer for Spam/Fraud Detection
Uses GPT-2 model from assets for analysis
"""

import os
import json
import logging
import torch
from typing import Dict, Any
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    def __init__(self, assets_dir=None):
        """
        Initialize the LLM Analyzer
        
        Args:
            assets_dir: Path to directory containing model assets
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = None
        self.tokenizer = None
        
        # Set up assets directory
        if assets_dir is None:
            # Default path when running on Android
            self.assets_dir = "/data/data/com.callscam.detector/files"
            if not os.path.exists(self.assets_dir):
                self.assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
        else:
            self.assets_dir = assets_dir

    def initialize(self) -> bool:
        """Initialize the analyzer and load the GPT-2 model from assets"""
        try:
            logger.info("Initializing LLM Analyzer")
            
            # Load tokenizer
            tokenizer_path = os.path.join(self.assets_dir, 'gpt2_medium_fp16_tokenizer')
            logger.info(f"Loading tokenizer from {tokenizer_path}")
            self.tokenizer = GPT2Tokenizer.from_pretrained(tokenizer_path)
            
            # Load model
            model_path = os.path.join(self.assets_dir, 'gpt2_medium_fp16.pt')
            logger.info(f"Loading model from {model_path}")
            
            # Load model config
            config_path = os.path.join(self.assets_dir, 'gpt2_medium_fp16_info.json')
            with open(config_path, 'r') as f:
                model_config = json.load(f)
            
            # Initialize model with config
            self.model = GPT2LMHeadModel.from_pretrained(
                pretrained_model_name_or_path=None,
                config=model_config,
                state_dict=torch.load(model_path, map_location=self.device)
            ).to(self.device)
            self.model.eval()
            
            logger.info(f"GPT-2 model loaded on {self.device.upper()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM Analyzer: {e}", exc_info=True)
            return False
    
    def analyze_conversation(self, text: str) -> Dict[str, Any]:
        """
        Analyze conversation text using the GPT-2 model
        
        Args:
            text: The conversation text to analyze
            
        Returns:
            Dict containing analysis results with is_suspicious and confidence
        """
        if not text.strip():
            return {
                'is_suspicious': False,
                'confidence': 0.0,
                'reasoning': 'No text to analyze',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Prepare the prompt
            prompt = f"Analyze this conversation for potential fraud or scam indicators:\n\n{text}\n\nAnalysis:"
            
            # Tokenize the input text
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding='max_length'
            ).to(self.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=len(inputs.input_ids[0]) + 100,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode the response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Simple heuristic to determine if it's suspicious
            is_suspicious = any(word in response.lower() 
                              for word in ['scam', 'fraud', 'suspicious', 'high risk'])
            
            # Calculate confidence based on response length and content
            confidence = min(0.9, len(response) / 100)  # Simple heuristic
            
            return {
                'is_suspicious': is_suspicious,
                'confidence': confidence,
                'reasoning': response,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}", exc_info=True)
            return {
                'is_suspicious': False,
                'confidence': 0.0,
                'reasoning': f'Analysis error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
