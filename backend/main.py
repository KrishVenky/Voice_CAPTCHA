"""
FastAPI Voice CAPTCHA Verification System

This module implements a three-layer voice CAPTCHA verification system:
- Layer 1: Answer correctness verification
- Layer 2: Response latency verification
- Layer 3: Voice authenticity verification
"""

import uuid
import json
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from challenge import generate_challenge, verify_answer
from voice_auth import is_synthetic
from transcribe import transcribe_audio

# Initialize FastAPI application
app = FastAPI()

# Enable CORS middleware for all origins, methods, and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for challenge data
challenges = {}


@app.get("/challenge")
async def get_challenge():
    """
    Generate a new CAPTCHA challenge.
    
    Returns:
        dict: Contains challenge ID and challenge text
    """
    # Generate the challenge using the challenge module
    result = generate_challenge()
    
    # Create a unique identifier for this challenge
    challenge_id = str(uuid.uuid4())
    
    # Store the complete challenge data in memory
    challenges[challenge_id] = result
    
    # Return only the ID and challenge text to the client
    return {
        "id": challenge_id,
        "challenge": result["challenge"]
    }


@app.post("/verify")
async def verify_submission(
    audio: UploadFile = File(...),
    challenge_id: str = Form(...),
    latency_ms: int = Form(...)
):
    """
    Verify a voice CAPTCHA submission through three security layers.
    
    Args:
        audio: The uploaded audio file
        challenge_id: The unique challenge identifier
        latency_ms: The response time in milliseconds
    
    Returns:
        dict: Verification result with pass status and relevant details
    """
    # Read the audio file bytes
    audio_bytes = await audio.read()
    
    # LAYER 2: Latency verification (check response timing first)
    # Valid human response time should be between 400ms and 6000ms
    if latency_ms < 400 or latency_ms > 6000:
        return {
            "pass": False,
            "reason": "latency_anomaly",
            "latency_ms": latency_ms
        }
    
    # LAYER 1: Answer correctness verification
    # Transcribe the audio to text
    transcript = transcribe_audio(audio_bytes)
    
    # Retrieve the challenge data from memory
    challenge_data = challenges.get(challenge_id, {})
    
    # Verify if the transcribed answer is correct
    correct = verify_answer(transcript, challenge_data)
    
    if not correct:
        return {
            "pass": False,
            "reason": "wrong_answer",
            "transcript": transcript
        }
    
    # LAYER 3: Voice authenticity verification
    # Check if the voice is synthetic or AI-generated
    synthetic = is_synthetic(audio_bytes)
    
    if synthetic:
        return {
            "pass": False,
            "reason": "synthetic_voice"
        }
    
    # All three layers passed - verification successful
    return {
        "pass": True,
        "transcript": transcript,
        "latency_ms": latency_ms
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
