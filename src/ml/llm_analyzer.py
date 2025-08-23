#!/usr/bin/env python3
"""
LLM Analyzer for Spam/Fraud Detection
Performs rule-based analysis on transcribed text
"""

import logging
import re
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    def __init__(self, config):
        self.config = config
        self.fraud_keywords = config.FRAUD_KEYWORDS
        self.suspicious_phrases = config.SUSPICIOUS_PHRASES
        self.risk_threshold = config.RISK_THRESHOLD
        
    async def initialize(self):
        """Initialize the analyzer"""
        try:
            logger.info("Initializing LLM Analyzer")
            logger.info(f"Loaded {len(self.fraud_keywords)} fraud keywords")
            logger.info(f"Loaded {len(self.suspicious_phrases)} suspicious phrases")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize LLM Analyzer: {e}")
            return False
    
    async def analyze_conversation(self, text: str) -> Dict[str, Any]:
        """Analyze conversation text for fraud indicators"""
        if not text.strip():
            return {
                'risk_score': 0.0,
                'is_suspicious': False,
                'confidence': 0.0,
                'reasoning': 'No text to analyze',
                'detected_keywords': [],
                'detected_phrases': []
            }
        
        try:
            # Convert to lowercase for matching
            text_lower = text.lower()
            
            # Find detected keywords
            detected_keywords = []
            for keyword in self.fraud_keywords:
                if keyword.lower() in text_lower:
                    detected_keywords.append(keyword)
            
            # Find detected phrases
            detected_phrases = []
            for phrase in self.suspicious_phrases:
                if phrase.lower() in text_lower:
                    detected_phrases.append(phrase)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(detected_keywords, detected_phrases, text)
            
            # Determine if suspicious
            is_suspicious = risk_score >= self.risk_threshold
            
            # Generate reasoning
            reasoning = self._generate_reasoning(detected_keywords, detected_phrases, risk_score)
            
            # Calculate confidence
            confidence = self._calculate_confidence(detected_keywords, detected_phrases, text)
            
            result = {
                'risk_score': risk_score,
                'is_suspicious': is_suspicious,
                'confidence': confidence,
                'reasoning': reasoning,
                'detected_keywords': detected_keywords,
                'detected_phrases': detected_phrases,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Analysis result: Risk={risk_score:.2f}, Suspicious={is_suspicious}")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                'risk_score': 0.0,
                'is_suspicious': False,
                'confidence': 0.0,
                'reasoning': f'Analysis error: {str(e)}',
                'detected_keywords': [],
                'detected_phrases': []
            }
    
    def _calculate_risk_score(self, keywords: List[str], phrases: List[str], text: str) -> float:
        """Calculate risk score based on detected patterns"""
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
    
    def _generate_reasoning(self, keywords: List[str], phrases: List[str], risk_score: float) -> str:
        """Generate human-readable reasoning for the analysis"""
        reasons = []
        
        if keywords:
            reasons.append(f"Detected {len(keywords)} fraud keywords: {', '.join(keywords)}")
        
        if phrases:
            reasons.append(f"Detected {len(phrases)} suspicious phrases: {', '.join(phrases)}")
        
        if risk_score > 0.7:
            reasons.append("High risk score indicates potential fraud")
        elif risk_score > 0.4:
            reasons.append("Moderate risk score - exercise caution")
        else:
            reasons.append("Low risk score - appears legitimate")
        
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
