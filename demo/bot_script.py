"""
Bot Attack Simulation Script

This script simulates an automated bot attempting to defeat the voice CAPTCHA
system. Used for demonstration purposes to show the multi-layer defense system
catching synthetic voice attacks.
"""

import requests
import time
import pyttsx3
import os

BASE_URL = "http://localhost:8000"


def bot_attack():
    """
    Simulate a bot attempting to bypass the voice CAPTCHA system.
    
    The bot follows a realistic attack pattern:
    1. Fetch challenge
    2. Process with simulated LLM thinking delay
    3. Generate synthetic TTS audio response
    4. Submit with calculated latency
    5. Display verification result
    """
    
    # Step 1: Get the challenge from the API
    print("=" * 40)
    print("BOT ATTACK STARTING")
    print("=" * 40)
    
    response = requests.get(f"{BASE_URL}/challenge")
    data = response.json()
    
    challenge_id = data["id"]
    challenge_text = data["challenge"]
    
    print(f"Challenge received: {challenge_text}")
    
    # Step 2: Simulate bot thinking delay (ASR + LLM + TTS pipeline)
    print("Bot processing challenge...")
    think_start = time.time()
    
    # Realistic delay for LLM inference (2-4 seconds typical)
    time.sleep(2.8)
    
    # Step 3: Generate TTS answer using synthetic voice
    print("Generating TTS response...")
    engine = pyttsx3.init()
    
    # Generate a generic answer (bot doesn't actually solve the challenge)
    engine.save_to_file("twelve", "bot_answer.wav")
    engine.runAndWait()
    
    # Step 4: Calculate total latency from start to submission
    latency_ms = int((time.time() - think_start) * 1000)
    print(f"Bot latency: {latency_ms}ms")
    
    # Step 5: Submit the bot-generated response to the verification endpoint
    print("Submitting bot response...")
    
    with open("bot_answer.wav", "rb") as audio_file:
        files = {
            "audio": ("bot_answer.wav", audio_file, "audio/wav")
        }
        data = {
            "challenge_id": challenge_id,
            "latency_ms": str(latency_ms)
        }
        
        verify_response = requests.post(f"{BASE_URL}/verify", files=files, data=data)
        result = verify_response.json()
    
    # Step 6: Print the outcome of the bot attack
    print("=" * 40)
    print(f"RESULT: {result}")
    
    if result.get("pass") is True:
        print("BOT PASSED - CAPTCHA FAILED TO DETECT")
    else:
        print(f"BOT BLOCKED - Reason: {result.get('reason', 'unknown')}")
    
    print("=" * 40)
    
    # Step 7: Cleanup temporary audio file
    try:
        if os.path.exists("bot_answer.wav"):
            os.remove("bot_answer.wav")
    except Exception:
        pass


if __name__ == "__main__":
    bot_attack()
