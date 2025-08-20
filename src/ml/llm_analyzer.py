"""
LLM Conversation Analyzer
Analyzes conversation content for fraud detection patterns
"""

import asyncio
import logging
import re
from typing import Dict, List, Any
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """LLM-based conversation analyzer for fraud detection"""
    
    def __init__(self, config):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.classifier = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize LLM model for conversation analysis"""
        try:
            logger.info("Loading LLM model for conversation analysis...")
            
            # Load model in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)
            
            self.is_initialized = True
            logger.info("LLM model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            return False
    
    def _load_model(self):
        """Load the model synchronously"""
        try:
            # Use a lightweight sentiment analysis model
            self.classifier = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=-1  # CPU
            )
        except Exception as e:
            logger.warning(f"Failed to load transformer model, using rule-based analysis: {e}")
            self.classifier = None
    
    async def analyze_conversation(self, transcription: str) -> Dict[str, Any]:
        """Analyze conversation for fraud indicators"""
        if not transcription.strip():
            return self._empty_analysis()
        
        try:
            # Rule-based analysis
            rule_analysis = self._rule_based_analysis(transcription)
            
            # ML-based analysis (if available)
            ml_analysis = await self._ml_based_analysis(transcription)
            
            # Combine analyses
            combined_analysis = self._combine_analyses(rule_analysis, ml_analysis)
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            return self._empty_analysis()
    
    def _rule_based_analysis(self, transcription: str) -> Dict[str, Any]:
        """Rule-based fraud detection analysis"""
        transcription_lower = transcription.lower()
        
        # Detect keywords
        keyword_matches = []
        for keyword in self.config.FRAUD_KEYWORDS:
            if keyword.lower() in transcription_lower:
                keyword_matches.append(keyword)
        
        # Detect suspicious phrases
        phrase_matches = []
        for phrase in self.config.SUSPICIOUS_PHRASES:
            if phrase.lower() in transcription_lower:
                phrase_matches.append(phrase)
        
        # Detect emotional triggers
        emotional_triggers = []
        for trigger in self.config.EMOTIONAL_TRIGGERS:
            if trigger.lower() in transcription_lower:
                emotional_triggers.append(trigger)
        
        # Calculate rule-based risk score
        keyword_score = len(keyword_matches) * self.config.KEYWORD_WEIGHT
        phrase_score = len(phrase_matches) * self.config.PHRASE_WEIGHT
        emotional_score = len(emotional_triggers) * self.config.EMOTIONAL_WEIGHT
        
        rule_risk = min(keyword_score + phrase_score + emotional_score, 1.0)
        
        # Additional pattern checks
        urgency_patterns = self._detect_urgency_patterns(transcription_lower)
        financial_patterns = self._detect_financial_patterns(transcription_lower)
        verification_patterns = self._detect_verification_patterns(transcription_lower)
        
        return {
            'keyword_matches': keyword_matches,
            'phrase_matches': phrase_matches,
            'emotional_triggers': emotional_triggers,
            'urgency_patterns': urgency_patterns,
            'financial_patterns': financial_patterns,
            'verification_patterns': verification_patterns,
            'rule_risk_score': rule_risk,
            'keyword_count': len(keyword_matches),
            'phrase_count': len(phrase_matches),
            'trigger_count': len(emotional_triggers)
        }
    
    async def _ml_based_analysis(self, transcription: str) -> Dict[str, Any]:
        """ML-based sentiment and fraud analysis"""
        if not self.classifier:
            return {'ml_risk_score': 0.0, 'sentiment': 'neutral', 'confidence': 0.0}
        
        try:
            # Run sentiment analysis in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._analyze_sentiment,
                transcription
            )
            
            # Convert sentiment to risk score
            sentiment = result.get('label', 'NEUTRAL').lower()
            confidence = result.get('score', 0.0)
            
            # High confidence negative sentiment might indicate fraud
            ml_risk = 0.0
            if sentiment == 'negative' and confidence > 0.7:
                ml_risk = confidence * 0.6  # Scale down
            elif sentiment == 'positive' and confidence > 0.8:
                # Overly positive (too good to be true) can also be suspicious
                ml_risk = confidence * 0.3
            
            return {
                'ml_risk_score': ml_risk,
                'sentiment': sentiment,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Error in ML analysis: {e}")
            return {'ml_risk_score': 0.0, 'sentiment': 'neutral', 'confidence': 0.0}
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment synchronously"""
        try:
            result = self.classifier(text)[0]
            return result
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {'label': 'NEUTRAL', 'score': 0.0}
    
    def _combine_analyses(self, rule_analysis: Dict, ml_analysis: Dict) -> Dict[str, Any]:
        """Combine rule-based and ML-based analyses"""
        rule_risk = rule_analysis.get('rule_risk_score', 0.0)
        ml_risk = ml_analysis.get('ml_risk_score', 0.0)
        
        # Weighted combination
        combined_risk = (rule_risk * 0.7) + (ml_risk * 0.3)
        
        # Determine if suspicious
        is_suspicious = (
            combined_risk > self.config.MEDIUM_RISK_THRESHOLD or
            rule_analysis.get('keyword_count', 0) >= 3 or
            rule_analysis.get('phrase_count', 0) >= 2
        )
        
        # Calculate confidence
        confidence = min(combined_risk + 0.1, 1.0)
        
        return {
            'risk_score': combined_risk,
            'is_suspicious': is_suspicious,
            'confidence': confidence,
            'detected_keywords': rule_analysis.get('keyword_matches', []),
            'detected_phrases': rule_analysis.get('phrase_matches', []),
            'emotional_triggers': rule_analysis.get('emotional_triggers', []),
            'urgency_patterns': rule_analysis.get('urgency_patterns', []),
            'financial_patterns': rule_analysis.get('financial_patterns', []),
            'verification_patterns': rule_analysis.get('verification_patterns', []),
            'sentiment': ml_analysis.get('sentiment', 'neutral'),
            'ml_confidence': ml_analysis.get('confidence', 0.0),
            'reasoning': self._generate_reasoning(rule_analysis, ml_analysis, combined_risk)
        }
    
    def _detect_urgency_patterns(self, text: str) -> List[str]:
        """Detect urgency-related patterns"""
        patterns = [
            r'act (now|immediately|fast|quickly)',
            r'(urgent|emergency|asap)',
            r'(expires?|deadline) (today|soon|in \d+)',
            r'(last|final) (chance|opportunity|warning)',
            r'(limited|short) time'
        ]
        
        matches = []
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(pattern)
        
        return matches
    
    def _detect_financial_patterns(self, text: str) -> List[str]:
        """Detect financial-related patterns"""
        patterns = [
            r'(bank|credit card|account) (number|details|information)',
            r'(social security|ssn) number',
            r'(send|wire|transfer) money',
            r'(gift card|bitcoin|cryptocurrency)',
            r'(refund|rebate|prize|lottery)',
            r'\$\d+|\d+ dollars'
        ]
        
        matches = []
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(pattern)
        
        return matches
    
    def _detect_verification_patterns(self, text: str) -> List[str]:
        """Detect verification-related patterns"""
        patterns = [
            r'(verify|confirm|validate) (your|account|identity)',
            r'(security|verification) (code|pin|password)',
            r'(update|provide) (your|personal) (information|details)',
            r'(suspended|locked|frozen) (account|card)',
            r'(unauthorized|suspicious) (activity|transaction)'
        ]
        
        matches = []
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(pattern)
        
        return matches
    
    def _generate_reasoning(self, rule_analysis: Dict, ml_analysis: Dict, risk_score: float) -> str:
        """Generate human-readable reasoning for the analysis"""
        reasons = []
        
        if rule_analysis.get('keyword_count', 0) > 0:
            reasons.append(f"Found {rule_analysis['keyword_count']} fraud keywords")
        
        if rule_analysis.get('phrase_count', 0) > 0:
            reasons.append(f"Found {rule_analysis['phrase_count']} suspicious phrases")
        
        if rule_analysis.get('trigger_count', 0) > 0:
            reasons.append(f"Found {rule_analysis['trigger_count']} emotional triggers")
        
        if ml_analysis.get('sentiment') == 'negative':
            reasons.append(f"Negative sentiment detected (confidence: {ml_analysis.get('confidence', 0):.2f})")
        
        if not reasons:
            reasons.append("No significant fraud indicators detected")
        
        return "; ".join(reasons)
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis result"""
        return {
            'risk_score': 0.0,
            'is_suspicious': False,
            'confidence': 0.0,
            'detected_keywords': [],
            'detected_phrases': [],
            'emotional_triggers': [],
            'urgency_patterns': [],
            'financial_patterns': [],
            'verification_patterns': [],
            'sentiment': 'neutral',
            'ml_confidence': 0.0,
            'reasoning': 'No text to analyze'
        }
