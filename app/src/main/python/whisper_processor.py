import os
import sys
import numpy as np
import torch
import torchaudio
import tempfile
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Whisper model (will be loaded on first use)
model = None
device = "cuda" if torch.cuda.is_available() else "cpu"

def transcribe_audio(audio_path):
    """
    Transcribe audio file using Whisper
    
    Args:
        audio_path (str): Path to the audio file
        
    Returns:
        str: Transcribed text or empty string if an error occurs
    """
    global model
    
    # Validate input file
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return ""
        
    file_size = os.path.getsize(audio_path)
    if file_size == 0:
        logger.error(f"Audio file is empty: {audio_path}")
        return ""
        
    logger.info(f"Transcribing audio file: {audio_path} (size: {file_size} bytes)")
    
    try:
        # Lazy load the model
        if model is None:
            logger.info("Loading Whisper model...")
            try:
                import whisper
                model = whisper.load_model("base").to(device)
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {str(e)}", exc_info=True)
                return ""
        
        # Load and preprocess audio
        try:
            logger.debug("Loading and preprocessing audio...")
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            logger.debug(f"Audio loaded: {len(audio)} samples")
        except Exception as e:
            logger.error(f"Error loading audio: {str(e)}", exc_info=True)
            return ""
        
        # Create log-Mel spectrogram
        try:
            logger.debug("Creating log-Mel spectrogram...")
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
        except Exception as e:
            logger.error(f"Error creating spectrogram: {str(e)}", exc_info=True)
            return ""
        
        # Detect language
        try:
            logger.debug("Detecting language...")
            _, probs = model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)
            logger.info(f"Detected language: {detected_lang} (confidence: {probs[detected_lang]:.2f})")
        except Exception as e:
            logger.warning(f"Language detection failed, continuing with English: {str(e)}")
            detected_lang = "en"
        
        # Decode the audio
        try:
            logger.debug("Decoding audio...")
            options = whisper.DecodingOptions(
                language=detected_lang,
                fp16=False,  # Disable FP16 for better compatibility
                temperature=0.0  # Disable sampling for deterministic results
            )
            result = whisper.decode(model, mel, options)
            
            if not result.text.strip():
                logger.warning("Received empty transcription")
                return ""
                
            logger.info(f"Transcription successful: {result.text[:100]}...")
            return result.text
            
        except Exception as e:
            logger.error(f"Error during audio decoding: {str(e)}", exc_info=True)
            return ""
            
    except Exception as e:
        logger.error(f"Unexpected error in transcribe_audio: {str(e)}", exc_info=True)
        return ""

def process_audio_chunk(audio_data, sample_rate=16000):
    """
    Process a chunk of audio data for transcription using Whisper
    
    Args:
        audio_data (bytes): Raw audio data as bytes (16-bit PCM)
        sample_rate (int): Sample rate of the audio (must be 16000)
        
    Returns:
        str: Transcribed text
    """
    temp_audio_path = None
    try:
        # Validate input
        if not isinstance(audio_data, (bytes, bytearray)):
            logger.error(f"Expected bytes, got {type(audio_data)}")
            return ""
            
        if not audio_data:
            logger.warning("Received empty audio data")
            return ""
            
        logger.info(f"Processing audio chunk: {len(audio_data)} bytes, sample rate: {sample_rate}Hz")
        
        # Create a temporary file to store the audio data
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
            
            try:
                # Convert bytes to numpy array (16-bit PCM)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # Check for silent audio
                if np.all(audio_array == 0):
                    logger.warning("Received silent audio")
                    return ""
                
                # Normalize to float32 for Whisper (range [-1, 1])
                audio_array = audio_array.astype(np.float32) / 32768.0
                
                # Convert to PyTorch tensor and ensure proper shape [channels, samples]
                waveform = torch.from_numpy(audio_array).unsqueeze(0)  # [1, samples]
                
                # Save as WAV file
                torchaudio.save(
                    temp_audio_path, 
                    waveform, 
                    sample_rate,
                    bits_per_sample=16,
                    encoding="PCM_S"
                )
                
                logger.info(f"Saved audio to {temp_audio_path}, size: {os.path.getsize(temp_audio_path)} bytes")
                
            except Exception as e:
                logger.error(f"Error processing audio data: {str(e)}", exc_info=True)
                return ""
        
        # Transcribe the temporary file
        text = transcribe_audio(temp_audio_path)
        return text
        
    except Exception as e:
        logger.error(f"Unexpected error in process_audio_chunk: {str(e)}", exc_info=True)
        return ""
        
    finally:
        # Clean up temporary file
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except Exception as e:
                logger.warning(f"Could not delete temp file {temp_audio_path}: {str(e)}")
