"""
Audio Transcription Module using Local Whisper

This module provides audio transcription functionality using the 
offline openai-whisper package (not the OpenAI API).
No API keys or HTTP requests are used.
"""

import whisper
import tempfile
import os

# Load Whisper model at module level (only happens once on import)
# This avoids the 3-5 second load time on every function call
model = whisper.load_model("base")


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio bytes to text using local Whisper model.
    
    Args:
        audio_bytes: The raw audio data as bytes
    
    Returns:
        str: The transcribed text (stripped of whitespace)
             Returns empty string if transcription fails
    """
    temp_file_path = None
    
    try:
        # Create a named temporary file with .wav extension
        # delete=False means we manually control when it's deleted
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            # Write the audio bytes to the temporary file
            temp_file.write(audio_bytes)
            
            # Store the file path for use after closing
            temp_file_path = temp_file.name
        
        # Transcribe the audio file using the Whisper model
        result = model.transcribe(temp_file_path)
        
        # Extract and return the transcribed text
        return result["text"].strip()
        
    except Exception:
        # If anything fails, return empty string
        return ""
        
    finally:
        # Always clean up the temporary file, whether success or failure
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
