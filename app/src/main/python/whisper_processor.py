import os
import numpy as np
import torch
import torchaudio
import tempfile
from pathlib import Path

def transcribe_audio(audio_path):
    """
    Transcribe audio file using Whisper
    
    Args:
        audio_path (str): Path to the audio file
        
    Returns:
        str: Transcribed text
    """
    try:
        # Load the Whisper model (it will be cached after first load)
        model = torch.hub.load('snakers4/silero-models', 'silero_stt', 'en_v2')
        
        # Load audio file
        waveform, sample_rate = torchaudio.load(audio_path)
        
        # Resample if needed (Whisper expects 16kHz)
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
            waveform = resampler(waveform)
        
        # Convert to mono if stereo
        if len(waveform.shape) > 1 and waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        # Transcribe
        text = model(waveform[0], sample_rate=16000)
        
        return text
        
    except Exception as e:
        print(f"Error in transcription: {str(e)}")
        return ""

def process_audio_chunk(audio_data, sample_rate=16000):
    """
    Process a chunk of audio data
    
    Args:
        audio_data (bytes): Raw audio data
        sample_rate (int): Sample rate of the audio
        
    Returns:
        str: Transcribed text
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
            
            # Convert bytes to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            
            # Convert to float32 and normalize to [-1, 1]
            audio_np = audio_np.astype(np.float32) / 32768.0
            
            # Save as WAV file
            torchaudio.save(
                temp_audio_path,
                torch.from_numpy(audio_np).unsqueeze(0),
                sample_rate
            )
        
        # Transcribe the temporary file
        result = transcribe_audio(temp_audio_path)
        
        # Clean up
        os.unlink(temp_audio_path)
        
        return result
        
    except Exception as e:
        print(f"Error processing audio chunk: {str(e)}")
        return ""
