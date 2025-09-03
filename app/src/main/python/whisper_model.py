import os
import torch
import torchaudio
import numpy as np
from pathlib import Path

class WhisperModel:
    def __init__(self, model_path=None):
        self.model = None
        self.model_path = model_path or "base"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sample_rate = 16000
        
    def load_model(self):
        """Load the Whisper model"""
        try:
            print("Loading Whisper model...")
            self.model = torch.hub.load('snakers4/silero-models', 'silero_stt', 'en_v2')
            print("Whisper model loaded successfully")
            return True
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            return False
    
    def transcribe_audio(self, audio_data, sample_rate=16000):
        """Transcribe audio data to text"""
        if not self.model:
            if not self.load_model():
                return ""
        
        try:
            # Convert bytes to numpy array if needed
            if isinstance(audio_data, bytes):
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_np = audio_data
                
            # Convert to tensor
            audio_tensor = torch.from_numpy(audio_np).float().to(self.device)
            
            # Transcribe
            with torch.no_grad():
                result = self.model(audio_tensor, sample_rate=16000)
                
            return result
            
        except Exception as e:
            print(f"Error in transcription: {e}")
            return ""

# Global instance
whisper_model = WhisperModel()

def process_audio_chunk(audio_data, sample_rate=16000):
    """Process audio chunk and return transcription"""
    global whisper_model
    return whisper_model.transcribe_audio(audio_data, sample_rate)

def transcribe_audio_file(file_path):
    """Transcribe an audio file"""
    global whisper_model
    try:
        # Load audio file
        waveform, sample_rate = torchaudio.load(file_path)
        
        # Convert to mono if needed
        if len(waveform.shape) > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
            
        # Convert to numpy array
        audio_np = waveform.numpy().squeeze()
        
        # Transcribe
        return whisper_model.transcribe_audio(audio_np, sample_rate)
        
    except Exception as e:
        print(f"Error processing audio file: {e}")
        return ""
