#!/usr/bin/env python3
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
        self.assets_dir = assets_dir or os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'src', 'main', 'assets')
        
    async def initialize(self) -> bool:
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
    
    async def analyze_conversation(self, text: str) -> Dict[str, Any]:
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
            # In a real app, you'd want to fine-tune this based on your model's output
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
    
    
    def _calculate_risk_score(self, keywords: list, phrases: list, text: str) -> float:
        """
        Calculate risk score based on detected patterns and keywords
        
        Args:
            keywords: List of detected fraud keywords
            phrases: List of detected suspicious phrases
            text: Original text for additional context
            
        Returns:
            Risk score between 0.0 and 1.0
        """
        if not (keywords or phrases):
            return 0.0
            
        base_score = 0.0
        
        # Add score for each keyword
        base_score += len(keywords) * 0.2
        
        # Add score for each phrase (higher weight)
        base_score += len(phrases) * 0.4
        
        # Add score for text length (longer conversations might be more suspicious)
        if len(text) > 100:
            base_score += 0.1
        
        # Add score for urgency indicators
        urgency_words = ['urgent', 'immediate', 'now', 'quick', 'fast', 'hurry']
        urgency_count = sum(1 for word in urgency_words if word in text.lower())
        base_score += urgency_count * 0.1
        
        # Cap at 1.0
        return min(base_score, 1.0)
    
    def _detect_keywords(self, text_lower: str) -> list:
        """Detect fraud keywords in text"""
        return [kw for kw in self.fraud_keywords if kw.lower() in text_lower]
    
    def _detect_phrases(self, text_lower: str) -> list:
        """Detect suspicious phrases in text"""
        return [phrase for phrase in self.suspicious_phrases if phrase.lower() in text_lower]
    
    def _format_result(
        self,
        risk_score: float,
        is_suspicious: bool,
        confidence: float,
        detected_keywords: list,
        detected_phrases: list,
        model_used: str
    ) -> Dict[str, Any]:
        """Format the analysis result into a standardized dictionary"""
        reasoning = self._generate_reasoning(detected_keywords, detected_phrases, risk_score)
        
        return {
            'risk_score': min(1.0, max(0.0, risk_score)),
            'is_suspicious': is_suspicious,
            'confidence': min(1.0, max(0.0, confidence)),
            'reasoning': reasoning,
            'detected_keywords': detected_keywords,
            'detected_phrases': detected_phrases,
            'model_used': model_used,
            'timestamp': datetime.now().isoformat()
        }
    
    def _empty_result(self, message: str) -> Dict[str, Any]:
        """Return an empty result with the given message"""
        return {
            'risk_score': 0.0,
            'is_suspicious': False,
            'confidence': 0.0,
            'reasoning': message,
            'detected_keywords': [],
            'detected_phrases': [],
            'model_used': 'none',
            'timestamp': datetime.now().isoformat()
        }
    
    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Return an error result"""
        return {
            'risk_score': 0.0,
            'is_suspicious': False,
            'confidence': 0.0,
            'reasoning': error_message,
            'detected_keywords': [],
            'detected_phrases': [],
            'model_used': 'error',
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_reasoning(self, keywords: list, phrases: list, risk_score: float) -> str:
        """
        Generate human-readable reasoning for the analysis
        
        Args:
            keywords: List of detected fraud keywords
            phrases: List of detected suspicious phrases
            risk_score: Calculated risk score
            
        Returns:
            Human-readable explanation of the analysis
        """
        if not (keywords or phrases):
            return "No suspicious patterns detected."
            
        reasons = []
        if keywords:
            reasons.append(f"Detected potential fraud keywords: {', '.join(keywords[:5])}" + 
                         (" and more..." if len(keywords) > 5 else ""))
        if phrases:
            reasons.append(f"Detected suspicious patterns in the conversation.")
            
        # Add risk level
        if risk_score > 0.7:
            risk_level = "high"
        elif risk_score > 0.4:
            risk_level = "moderate"
        else:
            risk_level = "low"
            
        reasons.append(f"Overall risk level: {risk_level} (score: {risk_score:.2f})")
        return " ".join(reasons)
        return "; ".join(reasons) if reasons else "No specific indicators detected"
    
    def _calculate_confidence(self, keywords: List[str], phrases: List[str], text: str) -> float:
        """Calculate confidence in the analysis"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence with more detected patterns
        if keywords:
            confidence += 0.2
        if phrases:
            confidence += 0.3
        
        # Higher confidence with longer text (more data to analyze)
        if len(text) > 50:
            confidence += 0.1
        
        return min(confidence, 1.0)
