#!/usr/bin/env python3
"""
Direct LLM Fraud Detection: Audio → LLM → FRAUD/LEGITIMATE
Zero manual processing - just feed audio transcript with prompt to LLM
"""

import whisper
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import numpy as np
import json

class DirectLLMFraudDetector:
    def __init__(self):
        self.whisper_model = None
        self.llm_model = None
        self.tokenizer = None
        
    def load_models(self):
        """Load Whisper + LLM models"""
        print("🚀 Loading Whisper + LLM for direct fraud detection...")
        
        try:
            # Load Whisper for audio transcription
            self.whisper_model = whisper.load_model("base")
            print("✅ Whisper loaded")
            
            # Load small LLM (TinyLlama or similar)
            model_name = "microsoft/DialoGPT-small"  # Lightweight conversational model
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.llm_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                device_map="cpu"
            )
            
            # Add padding token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            print("✅ LLM loaded")
            return True
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False
    
    def detect_fraud_from_audio(self, audio_data: np.ndarray) -> dict:
        """
        Direct pipeline: Audio → Whisper → LLM with prompt → FRAUD/LEGITIMATE
        """
        try:
            # Step 1: Audio → Text
            transcript = self.whisper_model.transcribe(audio_data)["text"]
            print(f"📝 Transcript: {transcript[:100]}...")
            
            # Step 2: Create fraud detection prompt
            prompt = self._create_fraud_prompt(transcript)
            
            # Step 3: LLM analysis
            result = self._ask_llm(prompt)
            
            # Step 4: Parse LLM response
            fraud_result = self._parse_llm_response(result, transcript)
            
            return fraud_result
            
        except Exception as e:
            return {
                'is_fraud': False,
                'confidence': 0.0,
                'reasoning': f'Error: {str(e)}',
                'transcript': ''
            }
    
    def _create_fraud_prompt(self, transcript: str) -> str:
        """Create a direct fraud detection prompt"""
        prompt = f"""Analyze this phone call transcript for fraud/scam indicators.

TRANSCRIPT:
"{transcript}"

TASK: Determine if this is a fraud/scam call.

FRAUD INDICATORS:
- Urgency (immediate action required)
- Personal info requests (SSN, bank details)
- Threats (account closure, arrest)
- Pressure tactics (limited time, act now)
- Impersonation (bank, government, tech support)
- Prize/money offers
- Verification requests

RESPOND WITH:
FRAUD or LEGITIMATE
Confidence: [0-100]%
Reason: [brief explanation]

ANALYSIS:"""
        
        return prompt
    
    def _ask_llm(self, prompt: str) -> str:
        """Send prompt to LLM and get response"""
        try:
            # Tokenize input
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=512,
                padding=True
            )
            
            # Generate response
            with torch.no_grad():
                outputs = self.llm_model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new part (after the prompt)
            new_response = response[len(prompt):].strip()
            return new_response
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def _parse_llm_response(self, llm_response: str, transcript: str) -> dict:
        """Parse LLM response into structured result"""
        response_lower = llm_response.lower()
        
        # Determine fraud status
        is_fraud = False
        confidence = 0.5
        
        if 'fraud' in response_lower:
            is_fraud = True
            confidence = 0.8
        elif 'scam' in response_lower:
            is_fraud = True
            confidence = 0.8
        elif 'legitimate' in response_lower:
            is_fraud = False
            confidence = 0.7
        
        # Extract confidence if mentioned
        import re
        conf_match = re.search(r'confidence:?\s*(\d+)', response_lower)
        if conf_match:
            confidence = int(conf_match.group(1)) / 100.0
        
        return {
            'is_fraud': is_fraud,
            'confidence': confidence,
            'reasoning': llm_response,
            'transcript': transcript,
            'raw_llm_response': llm_response
        }

def test_direct_llm_detector():
    """Test the direct LLM fraud detector"""
    detector = DirectLLMFraudDetector()
    
    if not detector.load_models():
        print("❌ Failed to load models")
        return
    
    # Test with fake audio (text simulation)
    test_transcripts = [
        "Your bank account has been suspended due to suspicious activity. Please press 1 to verify your account immediately or it will be permanently closed.",
        "Hi, this is Sarah from ABC Company calling to confirm your appointment tomorrow at 2 PM. Please call back if you need to reschedule.",
        "Congratulations! You've been selected to receive a free vacation package worth $5000. This offer expires in 24 hours. Press 9 to claim now.",
        "Hello, I'm calling from tech support. We've detected a virus on your computer. We need remote access to fix it immediately."
    ]
    
    print("\n🧪 Testing Direct LLM Fraud Detection:")
    print("=" * 60)
    
    for i, transcript in enumerate(test_transcripts, 1):
        print(f"\nTest {i}: {transcript[:50]}...")
        
        # Simulate audio data (in real use, this would be actual audio)
        # For testing, we'll directly use the transcript
        prompt = detector._create_fraud_prompt(transcript)
        llm_response = detector._ask_llm(prompt)
        result = detector._parse_llm_response(llm_response, transcript)
        
        print(f"Result: {'🚨 FRAUD' if result['is_fraud'] else '✅ LEGITIMATE'}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"LLM Response: {result['reasoning'][:100]}...")

def create_simple_prompt_detector():
    """Create an even simpler version using just prompts"""
    print("\n🎯 Creating Ultra-Simple Prompt-Based Detector...")
    
    def simple_fraud_check(transcript: str) -> dict:
        """Ultra-simple fraud detection using just prompts"""
        
        # Direct prompt approach
        fraud_keywords = [
            'suspended', 'verify immediately', 'press 1', 'account closed',
            'social security', 'urgent', 'final notice', 'act now',
            'congratulations', 'winner', 'free', 'limited time',
            'virus detected', 'remote access', 'tech support'
        ]
        
        transcript_lower = transcript.lower()
        fraud_indicators = sum(1 for keyword in fraud_keywords if keyword in transcript_lower)
        
        is_fraud = fraud_indicators >= 2
        confidence = min(fraud_indicators * 0.3, 1.0)
        
        return {
            'is_fraud': is_fraud,
            'confidence': confidence,
            'reasoning': f'Detected {fraud_indicators} fraud indicators',
            'transcript': transcript
        }
    
    # Test simple approach
    test_text = "Your bank account has been suspended. Press 1 to verify immediately."
    result = simple_fraud_check(test_text)
    
    print(f"Simple test: {'🚨 FRAUD' if result['is_fraud'] else '✅ LEGITIMATE'}")
    print(f"Confidence: {result['confidence']:.2f}")
    
    return simple_fraud_check

if __name__ == "__main__":
    print("🚀 Direct LLM Fraud Detection")
    print("=" * 40)
    
    # Option 1: Full LLM approach
    test_direct_llm_detector()
    
    # Option 2: Ultra-simple prompt approach
    create_simple_prompt_detector()
    
    print("\n✅ Direct audio-to-fraud detection ready!")
    print("🎯 Zero manual processing required")
    print("📱 Just: Audio → LLM → FRAUD/LEGITIMATE")
