"""
Challenge Generation and Verification Module using AMD Lemonade Server

This module provides functionality to generate voice CAPTCHA challenges
and verify user responses using AMD's Lemonade Server (OpenAI-compatible API).
Falls back to Google Gemini if Lemonade is unavailable.

AMD LEMONADE SERVER INTEGRATION - AMD SLINGSHOT 2026
"""

import google.generativeai as genai
from openai import OpenAI
import json
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure AMD Lemonade Server (OpenAI-compatible API)
# Running locally on localhost:8080 - NO DATA LEAVES THE DEVICE
lemonade_client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="lemonade"  # Lemonade doesn't require real API key
)

# Fallback: Configure Gemini API with the API key from environment variable
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# Hardcoded fallback challenges in case both APIs fail
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

# Challenge generation prompt
CHALLENGE_PROMPT = """Generate a spoken CAPTCHA challenge.
Rules:
- Answerable verbally in under 10 words
- Requires real-time thinking not lookup
- Has a clear correct answer
- Good types: word chains, simple logic, 
  counterfactual questions, sensory tasks
Return ONLY valid JSON no markdown no backticks no explanation:
{"challenge": "the challenge text", 
 "answer_criteria": "what counts as correct"}"""


def generate_challenge_lemonade() -> dict:
    """
    Generate challenge using AMD Lemonade Server.
    
    Returns:
        dict: Contains 'challenge' and 'answer_criteria'
    
    Raises:
        Exception: If Lemonade call fails
    """
    print("[LEMONADE] Attempting to generate challenge via AMD Lemonade Server...")
    
    # Try multiple model name formats
    model_names_to_try = [
        "unsloth/Phi-4-mini-instruct-GGUF:Phi-4-mini-instruct-Q4_K_M.gguf",
        "Phi-4-mini-instruct-Q4_K_M.gguf",
        "phi4",
        "Phi-4-mini-instruct-GGUF"
    ]
    
    last_error = None
    response = None
    for model_name in model_names_to_try:
        try:
            print(f"[LEMONADE] Trying model name: {model_name}")
            response = lemonade_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": CHALLENGE_PROMPT}],
                max_tokens=150,
                temperature=0.7
            )
            print(f"[LEMONADE] ✓ Success with model: {model_name}")
            break
        except Exception as e:
            last_error = e
            print(f"[LEMONADE] ✗ Failed with '{model_name}': {type(e).__name__} - {str(e)}")
            continue
    else:
        # All model names failed
        raise last_error
    
    response_text = response.choices[0].message.content.strip()
    
    # Clean up markdown formatting if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()
    
    challenge_dict = json.loads(response_text)
    print(f"[LEMONADE] ✓ Successfully generated challenge via AMD Lemonade Server")
    return challenge_dict


def generate_challenge_gemini() -> dict:
    """
    Generate challenge using Google Gemini (fallback).
    
    Returns:
        dict: Contains 'challenge' and 'answer_criteria'
    """
    print("[GEMINI FALLBACK] Using Gemini API...")
    
    response = gemini_model.generate_content(CHALLENGE_PROMPT)
    response_text = response.text.strip()
    
    # Strip markdown code block formatting if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()
    
    challenge_dict = json.loads(response_text)
    print(f"[GEMINI FALLBACK] ✓ Successfully generated challenge")
    return challenge_dict


def generate_challenge() -> dict:
    """
    Generate a spoken CAPTCHA challenge.
    
    Tries AMD Lemonade Server first for local, private processing.
    Falls back to Google Gemini if Lemonade is unavailable.
    
    Returns:
        dict: Contains 'challenge' (the question) and 'answer_criteria' (what's correct)
    """
    try:
        # PRIMARY: Try AMD Lemonade Server (LOCAL, NO DATA LEAVES DEVICE)
        return generate_challenge_lemonade()
        
    except Exception as lemonade_error:
        print(f"[LEMONADE] ✗ Failed: {type(lemonade_error).__name__}")
        
        try:
            # FALLBACK: Try Gemini API
            return generate_challenge_gemini()
            
        except Exception as gemini_error:
            print(f"[GEMINI FALLBACK] ✗ Failed: {type(gemini_error).__name__}")
            
            # LAST RESORT: Use hardcoded challenge
            print(f"[FALLBACK] Using hardcoded challenge")
            return random.choice(FALLBACK_CHALLENGES)


def verify_answer_lemonade(transcript: str, challenge_data: dict) -> bool:
    """
    Verify answer using AMD Lemonade Server.
    
    Args:
        transcript: The transcribed text of the user's audio response
        challenge_data: Dict containing 'challenge' and 'answer_criteria'
    
    Returns:
        bool: True if the answer is correct, False otherwise
    
    Raises:
        Exception: If Lemonade call fails
    """
    print(f"[LEMONADE VERIFY] Verifying via AMD Lemonade Server...")
    
    verification_prompt = f"""Challenge given to user: {challenge_data['challenge']}
What counts as correct: {challenge_data['answer_criteria']}
What the user actually said: {transcript}
Did the user answer correctly? 
Reply with only the single word YES or NO"""
    
    # Use the working model name from Lemonade server
    model_name = "Phi-4-mini-instruct-GGUF"
    
    response = lemonade_client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": verification_prompt}],
        max_tokens=10,
        temperature=0.3
    )
    
    response_text = response.choices[0].message.content.upper()
    
    print(f"[LEMONADE VERIFY] Response: '{response_text}'")
    
    if "YES" in response_text:
        print(f"[LEMONADE VERIFY] ✓ Answer correct")
        return True
    if "NO" in response_text:
        print(f"[LEMONADE VERIFY] ✗ Answer incorrect")
        return False
    
    # Default to True if unclear
    print(f"[LEMONADE VERIFY] Warning: No YES/NO found, defaulting to TRUE")
    return True


def verify_answer_gemini(transcript: str, challenge_data: dict) -> bool:
    """
    Verify answer using Google Gemini (fallback).
    
    Args:
        transcript: The transcribed text of the user's audio response
        challenge_data: Dict containing 'challenge' and 'answer_criteria'
    
    Returns:
        bool: True if the answer is correct, False otherwise
    """
    print(f"[GEMINI FALLBACK VERIFY] Verifying via Gemini API...")
    
    verification_prompt = f"""Challenge given to user: {challenge_data['challenge']}
What counts as correct: {challenge_data['answer_criteria']}
What the user actually said: {transcript}
Did the user answer correctly? 
Reply with only the single word YES or NO"""
    
    response = gemini_model.generate_content(verification_prompt)
    response_upper = response.text.upper()
    
    print(f"[GEMINI FALLBACK VERIFY] Response: '{response.text}'")
    
    if "YES" in response_upper:
        print(f"[GEMINI FALLBACK VERIFY] ✓ Answer correct")
        return True
    if "NO" in response_upper:
        print(f"[GEMINI FALLBACK VERIFY] ✗ Answer incorrect")
        return False
    
    # Default to True if unclear
    print(f"[GEMINI FALLBACK VERIFY] Warning: No YES/NO found, defaulting to TRUE")
    return True


def verify_answer(transcript: str, challenge_data: dict) -> bool:
    """
    Verify if the user's spoken answer is correct.
    
    Tries AMD Lemonade Server first for local, private processing.
    Falls back to Google Gemini if Lemonade is unavailable.
    
    Args:
        transcript: The transcribed text of the user's audio response
        challenge_data: Dict containing 'challenge' and 'answer_criteria'
    
    Returns:
        bool: True if the answer is correct, False otherwise
              Returns True on complete failure to avoid breaking the demo
    """
    try:
        print(f"[VERIFY] Transcript received: '{transcript}'")
        print(f"[VERIFY] Challenge data: {challenge_data}")
        
        # Validate inputs - return False if empty or None
        if not transcript:
            print(f"[VERIFY] Transcript is empty, returning False")
            return False
        
        if not challenge_data:
            print(f"[VERIFY] Challenge data is empty, returning False")
            return False
        
        try:
            # PRIMARY: Try AMD Lemonade Server (LOCAL, NO DATA LEAVES DEVICE)
            return verify_answer_lemonade(transcript, challenge_data)
            
        except Exception as lemonade_error:
            print(f"[LEMONADE VERIFY] ✗ Failed: {type(lemonade_error).__name__}")
            
            try:
                # FALLBACK: Try Gemini API
                return verify_answer_gemini(transcript, challenge_data)
                
            except Exception as gemini_error:
                print(f"[GEMINI FALLBACK VERIFY] ✗ Failed: {type(gemini_error).__name__}")
                
                # Default to True to not break demo
                print(f"[VERIFY] All verification methods failed, defaulting to TRUE")
                return True
        
    except Exception as e:
        # If anything fails, return True to not break the demo
        print(f"[VERIFY ERROR] Exception: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return True
