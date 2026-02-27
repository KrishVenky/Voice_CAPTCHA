# 🎥 Demo Mode - For Video Recording

## What is Demo Mode?
Demo mode bypasses all Gemini API calls and automatically passes all three verification layers. Perfect for:
- Recording demo videos without API token limits
- Testing the UI flow without backend dependencies
- Quick demonstrations

## Enable Demo Mode

### Quick Enable (Already Done ✓)
Your `.env` file now has:
```
DEMO_MODE=true
```

### What Changes in Demo Mode?

#### ✅ **Challenge Generation**
- **Normal:** Calls Gemini API to generate unique challenges
- **Demo:** Uses hardcoded challenge: "Name an animal that starts with letter C"

#### ✅ **Layer 1: Answer Verification**
- **Normal:** Calls Gemini to verify semantic correctness
- **Demo:** Auto-passes any non-empty transcript

#### ✅ **Layer 2: Latency Check**
- **Normal:** Rejects if outside 400-6000ms range
- **Demo:** Always passes regardless of timing

#### ✅ **Layer 3: Voice Authenticity**
- **Normal:** Analyzes spectral features to detect TTS
- **Demo:** Always passes as "human voice"

## How to Use for Video

### 1. Start the Server
```powershell
cd backend
uvicorn main:app --reload --port 8000
```

You'll see in the console:
```
[MAIN] DEMO MODE: True
[LAYER 1] DEMO MODE - Auto-passing answer verification
[LAYER 2] DEMO MODE - Auto-passing latency check
[LAYER 3] DEMO MODE - Auto-passing voice authenticity
```

### 2. Open Frontend
Open `frontend\index.html` in Chrome

### 3. Record Your Demo
- Click "Start Challenge"
- Challenge will always be: "Name an animal that starts with letter C"
- Click "Speak Your Answer"
- Say anything (e.g., "cat", "cow", "crocodile")
- Will always show ✅ VERIFIED with all three layers passing

### 4. Disable Demo Mode After Recording
```powershell
# Edit .env and change to:
DEMO_MODE=false

# Or remove the line entirely
```

## Console Output Example

```
============================================================
[MAIN] NEW VERIFICATION REQUEST
[MAIN] DEMO MODE: True
[MAIN] Challenge ID: f47ac10b-58cc-4372-a567-0e02b2c3d479
[MAIN] Latency: 1234ms
[MAIN] Audio size: 48000 bytes
============================================================

[LAYER 2] Checking latency: 1234ms
[LAYER 2] DEMO MODE - Auto-passing latency check
[LAYER 2] PASSED - Latency within range

[LAYER 1] Starting transcription...
[LAYER 1] Transcript result: 'cat'

[LAYER 1] Retrieved challenge: {'challenge': 'Name an animal that starts with letter C', 'answer_criteria': 'any animal starting with C'}
[LAYER 1] DEMO MODE - Auto-passing answer verification
[LAYER 1] PASSED - Answer correct

[LAYER 3] Checking voice authenticity...
[LAYER 3] DEMO MODE - Auto-passing voice authenticity
[LAYER 3] PASSED - Voice is human

[SUCCESS] All three layers passed!
============================================================
```

## Pro Tips

- **Still shows real transcription:** Whisper still transcribes your audio, so you can verify it works
- **Still measures latency:** The timing is still calculated and displayed
- **All UI flows work:** Frontend behaves exactly the same as production
- **Console logs:** You can still see all three layers executing in order

## Switch Back to Production

Edit `.env`:
```
DEMO_MODE=false
```

Or just remove the `DEMO_MODE` line entirely (defaults to false).
