"""
FastAPI Voice CAPTCHA Verification System

This module implements a three-layer voice CAPTCHA verification system:
- Layer 1: Answer correctness verification
- Layer 2: Response latency verification
- Layer 3: Voice authenticity verification
"""

import uuid
import json
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from challenge import generate_challenge, verify_answer
from voice_auth import is_synthetic
from transcribe import transcribe_audio

# Demo mode: bypasses Gemini API and auto-passes verification
# Set DEMO_MODE=true in .env or environment to enable
DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"

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
    if DEMO_MODE:
        # Use hardcoded challenge for demo
        result = {
            "challenge": "Name an animal that starts with letter C",
            "answer_criteria": "any animal starting with C"
        }
        print("[DEMO MODE] Using hardcoded challenge")
    else:
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
    
    print(f"\n{'='*60}")
    print(f"[MAIN] NEW VERIFICATION REQUEST")
    print(f"[MAIN] DEMO MODE: {DEMO_MODE}")
    print(f"[MAIN] Challenge ID: {challenge_id}")
    print(f"[MAIN] Latency: {latency_ms}ms")
    print(f"[MAIN] Audio size: {len(audio_bytes)} bytes")
    print(f"{'='*60}\n")
    
    # LAYER 2: Latency verification (check response timing first)
    # Valid human response time should be between 400ms and 6000ms
    print(f"[LAYER 2] Checking latency: {latency_ms}ms")
    if DEMO_MODE:
        print(f"[LAYER 2] DEMO MODE - Auto-passing latency check")
    elif latency_ms < 400 or latency_ms > 6000:
        print(f"[LAYER 2] FAILED - Latency out of range (400-6000ms)")
        return {
            "pass": False,
            "reason": "latency_anomaly",
            "latency_ms": latency_ms
        }
    print(f"[LAYER 2] PASSED - Latency within range\n")
    
    # LAYER 1: Answer correctness verification
    # Transcribe the audio to text
    print(f"[LAYER 1] Starting transcription...")
    transcript = transcribe_audio(audio_bytes)
    print(f"[LAYER 1] Transcript result: '{transcript}'\n")
    
    # Retrieve the challenge data from memory
    challenge_data = challenges.get(challenge_id, {})
    print(f"[LAYER 1] Retrieved challenge: {challenge_data}")
    
    # Verify if the transcribed answer is correct
    if DEMO_MODE:
        print(f"[LAYER 1] DEMO MODE - Auto-passing answer verification")
        correct = len(transcript.strip()) > 0  # Just check non-empty
    else:
        print(f"[LAYER 1] Verifying answer with Gemini...")
        correct = verify_answer(transcript, challenge_data)
    
    if not correct:
        print(f"[LAYER 1] FAILED - Answer incorrect")
        print(f"{'='*60}\n")
        return {
            "pass": False,
            "reason": "wrong_answer",
            "transcript": transcript
        }
    print(f"[LAYER 1] PASSED - Answer correct\n")
    
    # LAYER 3: Voice authenticity verification
    # Check if the voice is synthetic or AI-generated
    print(f"[LAYER 3] Checking voice authenticity...")
    if DEMO_MODE:
        print(f"[LAYER 3] DEMO MODE - Auto-passing voice authenticity")
        synthetic = False
    else:
        synthetic = is_synthetic(audio_bytes)
    
    if synthetic:
        print(f"[LAYER 3] FAILED - Voice is synthetic")
        print(f"{'='*60}\n")
        return {
            "pass": False,
            "reason": "synthetic_voice"
        }
    print(f"[LAYER 3] PASSED - Voice is human\n")
    
    # All three layers passed - verification successful
    print(f"[SUCCESS] All three layers passed!")
    print(f"{'='*60}\n")
    return {
        "pass": True,
        "transcript": transcript,
        "latency_ms": latency_ms
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
