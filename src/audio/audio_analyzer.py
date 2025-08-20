"""
Audio Feature Analyzer
Extracts audio features and calculates risk scores based on voice characteristics
"""

import logging
import numpy as np
from typing import Dict, Any, Optional
from scipy import signal
from scipy.stats import skew, kurtosis
import librosa

logger = logging.getLogger(__name__)

class AudioAnalyzer:
    """Audio feature extraction and analysis for fraud detection"""
    
    def __init__(self, config):
        self.config = config
        
    def extract_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Extract comprehensive audio features"""
        try:
            if len(audio_data) == 0:
                return self._empty_features()
            
            # Ensure audio is float32
            audio_data = audio_data.astype(np.float32)
            
            # Basic statistics
            volume_stats = self._extract_volume_features(audio_data)
            
            # Frequency domain features
            frequency_stats = self._extract_frequency_features(audio_data, sample_rate)
            
            # Voice quality features
            voice_quality = self._extract_voice_quality_features(audio_data, sample_rate)
            
            # Temporal features
            temporal_features = self._extract_temporal_features(audio_data, sample_rate)
            
            return {
                'volume_stats': volume_stats,
                'frequency_stats': frequency_stats,
                'voice_quality': voice_quality,
                'temporal_features': temporal_features,
                'duration': len(audio_data) / sample_rate
            }
            
        except Exception as e:
            logger.error(f"Error extracting audio features: {e}")
            return self._empty_features()
    
    def _extract_volume_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """Extract volume-based features"""
        try:
            # RMS energy
            rms = np.sqrt(np.mean(audio_data ** 2))
            
            # Peak amplitude
            peak = np.max(np.abs(audio_data))
            
            # Dynamic range
            dynamic_range = peak - np.min(np.abs(audio_data[audio_data != 0])) if np.any(audio_data != 0) else 0
            
            # Zero crossing rate
            zero_crossings = np.sum(np.diff(np.sign(audio_data)) != 0)
            zcr = zero_crossings / len(audio_data) if len(audio_data) > 0 else 0
            
            # Statistical measures
            mean_amplitude = np.mean(np.abs(audio_data))
            std_amplitude = np.std(np.abs(audio_data))
            
            return {
                'rms_energy': float(rms),
                'peak_amplitude': float(peak),
                'dynamic_range': float(dynamic_range),
                'zero_crossing_rate': float(zcr),
                'mean_amplitude': float(mean_amplitude),
                'std_amplitude': float(std_amplitude)
            }
            
        except Exception as e:
            logger.error(f"Error extracting volume features: {e}")
            return {}
    
    def _extract_frequency_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Extract frequency domain features"""
        try:
            # FFT
            fft = np.fft.fft(audio_data)
            magnitude = np.abs(fft)
            freqs = np.fft.fftfreq(len(fft), 1/sample_rate)
            
            # Only use positive frequencies
            positive_freqs = freqs[:len(freqs)//2]
            positive_magnitude = magnitude[:len(magnitude)//2]
            
            if len(positive_magnitude) == 0:
                return {}
            
            # Spectral centroid
            spectral_centroid = np.sum(positive_freqs * positive_magnitude) / np.sum(positive_magnitude)
            
            # Spectral bandwidth
            spectral_bandwidth = np.sqrt(np.sum(((positive_freqs - spectral_centroid) ** 2) * positive_magnitude) / np.sum(positive_magnitude))
            
            # Spectral rolloff (85% of energy)
            cumsum = np.cumsum(positive_magnitude)
            rolloff_idx = np.where(cumsum >= 0.85 * cumsum[-1])[0]
            spectral_rolloff = positive_freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else 0
            
            # Dominant frequency
            dominant_freq_idx = np.argmax(positive_magnitude)
            dominant_frequency = positive_freqs[dominant_freq_idx]
            
            return {
                'spectral_centroid': float(spectral_centroid),
                'spectral_bandwidth': float(spectral_bandwidth),
                'spectral_rolloff': float(spectral_rolloff),
                'dominant_frequency': float(dominant_frequency)
            }
            
        except Exception as e:
            logger.error(f"Error extracting frequency features: {e}")
            return {}
    
    def _extract_voice_quality_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Extract voice quality indicators"""
        try:
            features = {}
            
            # Fundamental frequency (F0) estimation using autocorrelation
            f0 = self._estimate_f0(audio_data, sample_rate)
            features['fundamental_frequency'] = float(f0) if f0 is not None else 0.0
            
            # Jitter (F0 variation)
            jitter = self._calculate_jitter(audio_data, sample_rate)
            features['jitter'] = float(jitter)
            
            # Shimmer (amplitude variation)
            shimmer = self._calculate_shimmer(audio_data)
            features['shimmer'] = float(shimmer)
            
            # Harmonics-to-noise ratio
            hnr = self._calculate_hnr(audio_data, sample_rate)
            features['hnr'] = float(hnr)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting voice quality features: {e}")
            return {}
    
    def _extract_temporal_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Extract temporal features"""
        try:
            # Speech rate estimation (very basic)
            # Count energy peaks as potential syllables
            frame_length = int(0.025 * sample_rate)  # 25ms frames
            hop_length = int(0.01 * sample_rate)     # 10ms hop
            
            frames = []
            for i in range(0, len(audio_data) - frame_length, hop_length):
                frame = audio_data[i:i + frame_length]
                energy = np.sum(frame ** 2)
                frames.append(energy)
            
            frames = np.array(frames)
            
            # Find peaks in energy
            if len(frames) > 0:
                threshold = np.mean(frames) + np.std(frames)
                peaks = np.where(frames > threshold)[0]
                speech_rate = len(peaks) / (len(audio_data) / sample_rate)  # peaks per second
            else:
                speech_rate = 0.0
            
            # Pause detection
            silence_threshold = np.mean(np.abs(audio_data)) * 0.1
            silent_frames = np.sum(np.abs(audio_data) < silence_threshold)
            pause_ratio = silent_frames / len(audio_data)
            
            return {
                'speech_rate': float(speech_rate),
                'pause_ratio': float(pause_ratio)
            }
            
        except Exception as e:
            logger.error(f"Error extracting temporal features: {e}")
            return {}
    
    def _estimate_f0(self, audio_data: np.ndarray, sample_rate: int) -> Optional[float]:
        """Estimate fundamental frequency using autocorrelation"""
        try:
            # Autocorrelation
            autocorr = np.correlate(audio_data, audio_data, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # Find the first peak after the zero lag
            min_period = int(sample_rate / 500)  # 500 Hz max
            max_period = int(sample_rate / 50)   # 50 Hz min
            
            if len(autocorr) <= max_period:
                return None
            
            search_range = autocorr[min_period:max_period]
            if len(search_range) == 0:
                return None
            
            peak_idx = np.argmax(search_range) + min_period
            f0 = sample_rate / peak_idx
            
            return f0 if 50 <= f0 <= 500 else None
            
        except Exception:
            return None
    
    def _calculate_jitter(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Calculate jitter (F0 variation)"""
        try:
            # Simple jitter approximation using zero crossing rate variation
            frame_size = int(0.025 * sample_rate)
            hop_size = int(0.01 * sample_rate)
            
            zcr_values = []
            for i in range(0, len(audio_data) - frame_size, hop_size):
                frame = audio_data[i:i + frame_size]
                zcr = np.sum(np.diff(np.sign(frame)) != 0) / len(frame)
                zcr_values.append(zcr)
            
            if len(zcr_values) > 1:
                return float(np.std(zcr_values))
            return 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_shimmer(self, audio_data: np.ndarray) -> float:
        """Calculate shimmer (amplitude variation)"""
        try:
            # Frame-based amplitude variation
            frame_size = 1024
            amplitudes = []
            
            for i in range(0, len(audio_data) - frame_size, frame_size):
                frame = audio_data[i:i + frame_size]
                amplitude = np.sqrt(np.mean(frame ** 2))
                amplitudes.append(amplitude)
            
            if len(amplitudes) > 1:
                return float(np.std(amplitudes) / np.mean(amplitudes)) if np.mean(amplitudes) > 0 else 0.0
            return 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_hnr(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Calculate harmonics-to-noise ratio"""
        try:
            # Simple HNR approximation using spectral analysis
            fft = np.fft.fft(audio_data)
            magnitude = np.abs(fft)
            
            # Find harmonic peaks vs noise floor
            sorted_mag = np.sort(magnitude)
            signal_power = np.mean(sorted_mag[-len(sorted_mag)//10:])  # Top 10%
            noise_power = np.mean(sorted_mag[:len(sorted_mag)//2])     # Bottom 50%
            
            if noise_power > 0:
                hnr = 10 * np.log10(signal_power / noise_power)
                return float(hnr)
            return 0.0
            
        except Exception:
            return 0.0
    
    def calculate_audio_risk_score(self, features: Dict[str, Any]) -> float:
        """Calculate risk score based on audio features"""
        try:
            risk_factors = []
            
            # Volume-based risk factors
            volume_stats = features.get('volume_stats', {})
            
            # Very low or very high RMS energy can be suspicious
            rms = volume_stats.get('rms_energy', 0)
            if rms < 0.01 or rms > 0.8:
                risk_factors.append(0.2)
            
            # Unusual dynamic range
            dynamic_range = volume_stats.get('dynamic_range', 0)
            if dynamic_range < 0.1 or dynamic_range > 0.9:
                risk_factors.append(0.15)
            
            # Frequency-based risk factors
            freq_stats = features.get('frequency_stats', {})
            
            # Unusual spectral characteristics
            spectral_centroid = freq_stats.get('spectral_centroid', 0)
            if spectral_centroid < 500 or spectral_centroid > 4000:
                risk_factors.append(0.1)
            
            # Voice quality risk factors
            voice_quality = features.get('voice_quality', {})
            
            # High jitter/shimmer indicates voice stress or artificial generation
            jitter = voice_quality.get('jitter', 0)
            shimmer = voice_quality.get('shimmer', 0)
            
            if jitter > 0.02:  # High jitter
                risk_factors.append(0.15)
            
            if shimmer > 0.1:  # High shimmer
                risk_factors.append(0.15)
            
            # Low HNR indicates poor voice quality
            hnr = voice_quality.get('hnr', 0)
            if hnr < 10:
                risk_factors.append(0.1)
            
            # Temporal risk factors
            temporal = features.get('temporal_features', {})
            
            # Unusual speech rate
            speech_rate = temporal.get('speech_rate', 0)
            if speech_rate > 8 or speech_rate < 1:  # Too fast or too slow
                risk_factors.append(0.1)
            
            # High pause ratio might indicate reading from script
            pause_ratio = temporal.get('pause_ratio', 0)
            if pause_ratio > 0.4:
                risk_factors.append(0.1)
            
            # Calculate final risk score
            if not risk_factors:
                return 0.0
            
            # Sum risk factors but cap at 1.0
            total_risk = min(sum(risk_factors), 1.0)
            
            return total_risk
            
        except Exception as e:
            logger.error(f"Error calculating audio risk score: {e}")
            return 0.0
    
    def _empty_features(self) -> Dict[str, Any]:
        """Return empty feature set"""
        return {
            'volume_stats': {},
            'frequency_stats': {},
            'voice_quality': {},
            'temporal_features': {},
            'duration': 0.0
        }
