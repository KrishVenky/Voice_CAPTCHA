"""
Voice Authentication Module for TTS Detection

This module implements threshold-based voice classification to distinguish
between synthetic (TTS) and real human voices using librosa audio features.
No machine learning models are used - only acoustic feature analysis.
"""

import librosa
import numpy as np
import tempfile
import os
import soundfile as sf


def extract_features(audio_bytes: bytes) -> dict:
    """
    Extract acoustic features from audio to distinguish synthetic from real voices.
    
    Extracts four key features:
    - pitch_std: Standard deviation of pitch (f0) variation
    - mfcc_var: Variance in mel-frequency cepstral coefficients
    - spectral_flux: Mean spectral flux (onset strength)
    - zcr_var: Variance in zero-crossing rate
    
    Args:
        audio_bytes: Raw audio data as bytes
    
    Returns:
        dict: Feature values, or all zeros if extraction fails
    """
    temp_file_path = None
    
    try:
        # Create a named temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            # Write the audio bytes to the temporary file
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
        
        # Load the audio file with librosa at 16kHz sample rate
        y, sr = librosa.load(temp_file_path, sr=16000)
        
        # Feature 1: Pitch standard deviation
        # Extract fundamental frequency (f0) using probabilistic YIN algorithm
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=50, fmax=400, sr=sr)
        
        # Remove NaN values from the f0 array
        f0_clean = f0[~np.isnan(f0)]
        
        # Calculate standard deviation of pitch variation
        if len(f0_clean) > 0:
            pitch_std = float(np.std(f0_clean))
        else:
            pitch_std = 0.0
        
        # Feature 2: MFCC variance
        # Extract mel-frequency cepstral coefficients
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # Calculate mean of variance across time axis
        mfcc_var = float(np.mean(np.var(mfccs, axis=1)))
        
        # Feature 3: Spectral flux
        # Calculate onset strength (spectral flux)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        
        # Calculate mean spectral flux
        spectral_flux = float(np.mean(onset_env))
        
        # Feature 4: Zero-crossing rate variance
        # Calculate zero-crossing rate
        zcr = librosa.feature.zero_crossing_rate(y)
        
        # Calculate variance of zero-crossing rate
        zcr_var = float(np.var(zcr))
        
        # Return all extracted features
        return {
            "pitch_std": pitch_std,
            "mfcc_var": mfcc_var,
            "spectral_flux": spectral_flux,
            "zcr_var": zcr_var
        }
        
    except Exception:
        # If anything fails, return zero values for all features
        return {
            "pitch_std": 0,
            "mfcc_var": 0,
            "spectral_flux": 0,
            "zcr_var": 0
        }
        
    finally:
        # Always clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def is_synthetic(audio_bytes: bytes) -> bool:
    """
    Determine if audio is synthetic (TTS) or real human voice.
    
    Uses threshold-based classification on acoustic features:
    - Synthetic voices have lower pitch variation
    - Synthetic voices have lower MFCC variance
    - Synthetic voices have lower spectral flux
    - Synthetic voices have lower zero-crossing rate variance
    
    Args:
        audio_bytes: Raw audio data as bytes
    
    Returns:
        bool: True if voice is likely synthetic, False if likely real human
    """
    # Extract acoustic features from the audio
    features = extract_features(audio_bytes)
    
    # Initialize synthetic score
    score = 0
    
    # Check each feature against thresholds characteristic of synthetic voices
    # Add 1 point for each threshold that indicates synthetic voice
    
    if features["pitch_std"] < 15:
        score += 1
    
    if features["mfcc_var"] < 40:
        score += 1
    
    if features["spectral_flux"] < 2:
        score += 1
    
    if features["zcr_var"] < 0.0001:
        score += 1
    
    # Consider synthetic if 2 or more indicators are present
    return score >= 2
