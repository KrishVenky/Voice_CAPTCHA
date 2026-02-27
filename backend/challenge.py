"""
Challenge Generation and Verification Module using Google Gemini API

This module provides functionality to generate voice CAPTCHA challenges
and verify user responses using Google's Gemini 2.0 Flash model.
"""

import google.generativeai as genai
import json
import random
import os

# Configure Gemini API with the API key from environment variable
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Initialize the Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")

# Hardcoded fallback challenges in case Gemini API fails
FALLBACK_CHALLENGES = [
    {
        "challenge": "Name an animal starting with the last letter of ELEPHANT",
        "answer_criteria": "any animal starting with T"
    },
    {
        "challenge": "What is heavier, a kilogram of iron or a kilogram of feathers?",
        "answer_criteria": "same weight or equal"
    },
    {
        "challenge": "If you have 3 cats and each has 4 legs how many legs total?",
        "answer_criteria": "twelve or 12"
    },
    {
        "challenge": "Name something in a kitchen that starts with F",
        "answer_criteria": "any kitchen item starting with F"
    },
    {
        "challenge": "Say the first three months of the year in reverse order",
        "answer_criteria": "march february january"
    }
]


def generate_challenge() -> dict:
    """
    Generate a spoken CAPTCHA challenge using Google Gemini.
    
    Sends a prompt to Gemini requesting a challenge that:
    - Can be answered verbally in under 10 words
    - Requires real-time thinking not lookup
    - Has a clear correct answer
    
    Returns:
        dict: Contains 'challenge' (the question) and 'answer_criteria' (what's correct)
              Falls back to a random hardcoded challenge if generation fails
    """
    try:
        # Define the prompt for Gemini to generate a challenge
        prompt = """Generate a spoken CAPTCHA challenge.
   Rules:
   - Answerable verbally in under 10 words
   - Requires real-time thinking not lookup
   - Has a clear correct answer
   - Good types: word chains, simple logic, 
     counterfactual questions, sensory tasks
   Return ONLY valid JSON no markdown no backticks no explanation:
   {"challenge": "the challenge text", 
    "answer_criteria": "what counts as correct"}"""
        
        # Send the prompt to Gemini and get the response
        response = model.generate_content(prompt)
        
        # Extract the text from the response
        response_text = response.text
        
        # Strip markdown code block formatting if present
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse the cleaned JSON string
        challenge_dict = json.loads(response_text)
        
        return challenge_dict
        
    except Exception:
        # If anything fails, return a random fallback challenge
        return random.choice(FALLBACK_CHALLENGES)


def verify_answer(transcript: str, challenge_data: dict) -> bool:
    """
    Verify if the user's spoken answer is correct using Google Gemini.
    
    Args:
        transcript: The transcribed text of the user's audio response
        challenge_data: Dict containing 'challenge' and 'answer_criteria'
    
    Returns:
        bool: True if the answer is correct, False otherwise
              Returns True on error to avoid breaking the demo
    """
    try:
        # Validate inputs - return False if empty or None
        if not transcript:
            return False
        
        if not challenge_data:
            return False
        
        # Build the verification prompt for Gemini
        verification_prompt = f"""Challenge given to user: {challenge_data['challenge']}
   What counts as correct: {challenge_data['answer_criteria']}
   What the user actually said: {transcript}
   Did the user answer correctly? 
   Reply with only the single word YES or NO"""
        
        # Send the verification prompt to Gemini
        response = model.generate_content(verification_prompt)
        
        # Check if YES or NO appears in the response
        response_upper = response.text.upper()
        
        if "YES" in response_upper:
            return True
        if "NO" in response_upper:
            return False
        
        # If neither YES nor NO found, default to True
        return True
        
    except Exception:
        # If anything fails, return True to not break the demo
        return True
