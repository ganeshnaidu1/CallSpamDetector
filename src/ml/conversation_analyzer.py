#!/usr/bin/env python3
"""
Enhanced Conversation Analyzer for Two-Sided Audio
Specifically designed for fraud detection in phone calls
"""

import logging
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ConversationAnalyzer:
    def __init__(self, config):
        self.config = config
        self.fraud_keywords = config.FRAUD_KEYWORDS
        self.suspicious_phrases = config.SUSPICIOUS_PHRASES
        
        # Two-sided conversation patterns
        self.caller_pressure_words = [
            "you must", "you need to", "required by law", "immediately", 
            "urgent", "now", "quickly", "press 1", "don't hang up"
        ]
        
        self.victim_confusion_words = [
            "what?", "i don't understand", "why?", "i didn't know", 
            "really?", "are you sure?", "i'm confused", "wait"
        ]
        
        self.fraud_tactics = [
            "account suspended", "verify immediately", "final notice",
            "act now or", "limited time", "don't tell anyone",
            "this is confidential", "for security purposes"
        ]
        
    async def initialize(self):
        """Initialize the conversation analyzer"""
        logger.info("Initializing Enhanced Conversation Analyzer")
        logger.info("✅ Two-sided conversation analysis enabled")
        return True
    
    async def analyze_two_sided_conversation(self, transcription: str) -> Dict[str, Any]:
        """Analyze two-sided conversation for fraud patterns"""
        
        if not transcription.strip():
            return self._empty_result("No transcription to analyze")
        
        try:
            # Split conversation into turns
            conversation_turns = self._split_conversation(transcription)
            
            # Analyze conversation flow
            flow_analysis = self._analyze_conversation_flow(conversation_turns)
            
            # Detect speaker roles and behaviors
            speaker_analysis = self._analyze_speaker_behaviors(conversation_turns)
            
            # Calculate fraud indicators
            fraud_indicators = self._detect_fraud_indicators(transcription, conversation_turns)
            
            # Calculate overall risk score
            risk_score = self._calculate_conversation_risk_score(
                flow_analysis, speaker_analysis, fraud_indicators
            )
            
            # Generate detailed reasoning
            reasoning = self._generate_conversation_reasoning(
                flow_analysis, speaker_analysis, fraud_indicators, risk_score
            )
            
            result = {
                'risk_score': risk_score,
                'is_suspicious': risk_score >= self.config.RISK_THRESHOLD,
                'confidence': self._calculate_confidence(conversation_turns, fraud_indicators),
                'reasoning': reasoning,
                'conversation_analysis': {
                    'turns_count': len(conversation_turns),
                    'caller_pressure_level': speaker_analysis['caller_pressure'],
                    'victim_confusion_level': speaker_analysis['victim_confusion'],
                    'fraud_tactics_detected': fraud_indicators['tactics_count'],
                    'conversation_flow': flow_analysis['flow_type']
                },
                'detected_keywords': fraud_indicators['keywords'],
                'detected_phrases': fraud_indicators['phrases'],
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Two-sided analysis: Risk={risk_score:.2f}, Turns={len(conversation_turns)}")
            return result
            
        except Exception as e:
            logger.error(f"Conversation analysis failed: {e}")
            return self._empty_result(f"Analysis error: {str(e)}")
    
    def _split_conversation(self, transcription: str) -> List[Dict[str, str]]:
        """Split transcription into conversation turns"""
        turns = []
        
        # Simple speaker detection patterns
        speaker_patterns = [
            r"(caller|agent|representative):\s*(.*?)(?=victim:|$)",
            r"(victim|customer|user):\s*(.*?)(?=caller:|agent:|representative:|$)"
        ]
        
        # If no speaker labels, split by sentences and alternate
        if not any(re.search(pattern, transcription.lower()) for pattern in speaker_patterns):
            sentences = re.split(r'[.!?]+', transcription)
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    speaker = "caller" if i % 2 == 0 else "victim"
                    turns.append({
                        'speaker': speaker,
                        'text': sentence.strip(),
                        'turn_number': i + 1
                    })
        else:
            # Extract labeled speakers
            for pattern in speaker_patterns:
                matches = re.finditer(pattern, transcription.lower(), re.IGNORECASE)
                for match in matches:
                    speaker = match.group(1).lower()
                    text = match.group(2).strip()
                    if text:
                        turns.append({
                            'speaker': speaker,
                            'text': text,
                            'turn_number': len(turns) + 1
                        })
        
        return sorted(turns, key=lambda x: x['turn_number'])
    
    def _analyze_conversation_flow(self, turns: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze the flow and pattern of conversation"""
        if not turns:
            return {'flow_type': 'unknown', 'pressure_escalation': False}
        
        caller_turns = [t for t in turns if 'caller' in t['speaker'].lower()]
        victim_turns = [t for t in turns if 'victim' in t['speaker'].lower()]
        
        # Analyze pressure escalation
        pressure_escalation = False
        if len(caller_turns) > 1:
            early_pressure = sum(1 for word in self.caller_pressure_words 
                               if word in caller_turns[0]['text'].lower())
            late_pressure = sum(1 for word in self.caller_pressure_words 
                              if word in caller_turns[-1]['text'].lower())
            pressure_escalation = late_pressure > early_pressure
        
        # Determine conversation flow type
        flow_type = 'normal'
        if len(caller_turns) > len(victim_turns) * 1.5:
            flow_type = 'caller_dominant'
        elif any(word in ' '.join([t['text'] for t in caller_turns]).lower() 
                for word in self.fraud_tactics):
            flow_type = 'suspicious_pattern'
        
        return {
            'flow_type': flow_type,
            'pressure_escalation': pressure_escalation,
            'caller_dominance': len(caller_turns) / max(len(victim_turns), 1),
            'total_turns': len(turns)
        }
    
    def _analyze_speaker_behaviors(self, turns: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze behaviors of different speakers"""
        caller_turns = [t for t in turns if 'caller' in t['speaker'].lower()]
        victim_turns = [t for t in turns if 'victim' in t['speaker'].lower()]
        
        # Analyze caller pressure level
        caller_pressure = 0
        for turn in caller_turns:
            text_lower = turn['text'].lower()
            caller_pressure += sum(1 for word in self.caller_pressure_words 
                                 if word in text_lower)
        
        # Analyze victim confusion level
        victim_confusion = 0
        for turn in victim_turns:
            text_lower = turn['text'].lower()
            victim_confusion += sum(1 for word in self.victim_confusion_words 
                                  if word in text_lower)
        
        return {
            'caller_pressure': min(caller_pressure / max(len(caller_turns), 1), 1.0),
            'victim_confusion': min(victim_confusion / max(len(victim_turns), 1), 1.0),
            'caller_turn_ratio': len(caller_turns) / max(len(turns), 1)
        }
    
    def _detect_fraud_indicators(self, full_text: str, turns: List[Dict[str, str]]) -> Dict[str, Any]:
        """Detect fraud indicators in the conversation"""
        text_lower = full_text.lower()
        
        # Find keywords and phrases
        detected_keywords = [kw for kw in self.fraud_keywords if kw.lower() in text_lower]
        detected_phrases = [ph for ph in self.suspicious_phrases if ph.lower() in text_lower]
        
        # Count fraud tactics
        tactics_count = sum(1 for tactic in self.fraud_tactics if tactic.lower() in text_lower)
        
        return {
            'keywords': detected_keywords,
            'phrases': detected_phrases,
            'tactics_count': tactics_count,
            'urgency_indicators': sum(1 for word in ['urgent', 'immediate', 'now', 'quickly'] 
                                    if word in text_lower)
        }
    
    def _calculate_conversation_risk_score(self, flow_analysis: Dict, speaker_analysis: Dict, 
                                         fraud_indicators: Dict) -> float:
        """Calculate risk score based on conversation analysis"""
        base_score = 0.0
        
        # Flow analysis contribution (30%)
        if flow_analysis['flow_type'] == 'suspicious_pattern':
            base_score += 0.3
        elif flow_analysis['flow_type'] == 'caller_dominant':
            base_score += 0.15
        
        if flow_analysis['pressure_escalation']:
            base_score += 0.1
        
        # Speaker behavior contribution (40%)
        base_score += speaker_analysis['caller_pressure'] * 0.2
        base_score += speaker_analysis['victim_confusion'] * 0.2
        
        # Fraud indicators contribution (30%)
        base_score += len(fraud_indicators['keywords']) * 0.05
        base_score += len(fraud_indicators['phrases']) * 0.08
        base_score += fraud_indicators['tactics_count'] * 0.1
        base_score += fraud_indicators['urgency_indicators'] * 0.02
        
        return min(base_score, 1.0)
    
    def _generate_conversation_reasoning(self, flow_analysis: Dict, speaker_analysis: Dict, 
                                       fraud_indicators: Dict, risk_score: float) -> str:
        """Generate human-readable reasoning for conversation analysis"""
        reasons = []
        
        # Flow analysis reasons
        if flow_analysis['flow_type'] == 'suspicious_pattern':
            reasons.append("Suspicious conversation pattern detected")
        if flow_analysis['pressure_escalation']:
            reasons.append("Caller pressure escalated during conversation")
        
        # Speaker behavior reasons
        if speaker_analysis['caller_pressure'] > 0.5:
            reasons.append(f"High caller pressure level ({speaker_analysis['caller_pressure']:.2f})")
        if speaker_analysis['victim_confusion'] > 0.3:
            reasons.append(f"Victim confusion indicators ({speaker_analysis['victim_confusion']:.2f})")
        
        # Fraud indicators
        if fraud_indicators['keywords']:
            reasons.append(f"Fraud keywords: {', '.join(fraud_indicators['keywords'][:3])}")
        if fraud_indicators['phrases']:
            reasons.append(f"Suspicious phrases: {', '.join(fraud_indicators['phrases'][:2])}")
        if fraud_indicators['tactics_count'] > 0:
            reasons.append(f"{fraud_indicators['tactics_count']} fraud tactics detected")
        
        # Overall assessment
        if risk_score > 0.7:
            reasons.append("HIGH RISK: Multiple fraud indicators present")
        elif risk_score > 0.4:
            reasons.append("MEDIUM RISK: Some suspicious patterns detected")
        else:
            reasons.append("LOW RISK: Conversation appears normal")
        
        return "; ".join(reasons) if reasons else "No specific indicators detected"
    
    def _calculate_confidence(self, turns: List[Dict], fraud_indicators: Dict) -> float:
        """Calculate confidence in the analysis"""
        confidence = 0.6  # Base confidence for two-sided analysis
        
        # More turns = higher confidence
        if len(turns) > 4:
            confidence += 0.2
        elif len(turns) > 2:
            confidence += 0.1
        
        # Clear indicators = higher confidence
        if fraud_indicators['keywords'] or fraud_indicators['phrases']:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _empty_result(self, reason: str) -> Dict[str, Any]:
        """Return empty analysis result"""
        return {
            'risk_score': 0.0,
            'is_suspicious': False,
            'confidence': 0.0,
            'reasoning': reason,
            'conversation_analysis': {},
            'detected_keywords': [],
            'detected_phrases': [],
            'timestamp': datetime.now().isoformat()
        }
