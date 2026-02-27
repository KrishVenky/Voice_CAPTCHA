# VoiceCAPTCHA System Architecture Map

This document provides a comprehensive map of the entire VoiceCAPTCHA system. It describes every file, function, variable, endpoint, and data flow in detail so that any AI assistant can understand and modify the codebase.

---

## Table of Contents
1. [Project Structure](#project-structure)
2. [Backend Components](#backend-components)
3. [Frontend Components](#frontend-components)
4. [Demo Components](#demo-components)
5. [Data Flow](#data-flow)
6. [API Reference](#api-reference)
7. [Dependencies](#dependencies)
8. [Common Issues & Fixes](#common-issues--fixes)

---

## Project Structure

```
voice-captcha/
├── README.md                  # User-facing documentation
├── MAP.md                     # This file - detailed system map
├── backend/
│   ├── main.py               # FastAPI server with 2 endpoints
│   ├── challenge.py          # Gemini-based challenge generation and verification
│   ├── transcribe.py         # Local Whisper audio transcription
│   ├── voice_auth.py         # TTS detection using librosa
│   └── requirements.txt      # Python dependencies
├── demo/
│   └── bot_script.py         # Bot attack simulation
└── frontend/
    ├── index.html            # HTML structure
    ├── style.css             # Dark theme styling
    └── captcha.js            # Client-side JavaScript logic
```

---

## Backend Components

### File: `backend/main.py`
**Purpose:** FastAPI server that orchestrates the three-layer verification system.

#### Imports
```python
import uuid                    # Generate unique challenge IDs
import json                    # JSON parsing (currently unused but included)
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from challenge import generate_challenge, verify_answer
from voice_auth import is_synthetic
from transcribe import transcribe_audio
```

#### Global Variables
- `app`: FastAPI application instance
- `challenges`: dict - In-memory storage for challenge data
  - Key: challenge_id (uuid4 string)
  - Value: dict with keys "challenge" and "answer_criteria"

#### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allow all origins
    allow_credentials=True,    # Allow cookies
    allow_methods=["*"],       # Allow all HTTP methods
    allow_headers=["*"]        # Allow all headers
)
```

#### Endpoint: `GET /challenge`
**Purpose:** Generate and return a new CAPTCHA challenge.

**Returns:**
```json
{
  "id": "uuid4-string",
  "challenge": "challenge text string"
}
```

**Logic Flow:**
1. Call `generate_challenge()` from challenge.py
2. Generate unique ID using `uuid.uuid4()`
3. Store full result dict in `challenges[challenge_id]`
4. Return only ID and challenge text to client

**Example Response:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "challenge": "Name an animal starting with the last letter of ELEPHANT"
}
```

#### Endpoint: `POST /verify`
**Purpose:** Verify a voice response through three security layers.

**Parameters:**
- `audio`: UploadFile - Audio file from user's microphone
- `challenge_id`: str - The challenge ID from GET /challenge
- `latency_ms`: int - Time from challenge display to recording stop (milliseconds)

**Returns (Pass):**
```json
{
  "pass": true,
  "transcript": "transcribed text",
  "latency_ms": 1234
}
```

**Returns (Fail - Latency):**
```json
{
  "pass": false,
  "reason": "latency_anomaly",
  "latency_ms": 350
}
```

**Returns (Fail - Wrong Answer):**
```json
{
  "pass": false,
  "reason": "wrong_answer",
  "transcript": "transcribed text"
}
```

**Returns (Fail - Synthetic Voice):**
```json
{
  "pass": false,
  "reason": "synthetic_voice"
}
```

**Logic Flow (EXACT ORDER MATTERS):**
1. Read audio bytes: `audio_bytes = await audio.read()`
2. **LAYER 2 FIRST** - Latency check:
   - If `latency_ms < 400` OR `latency_ms > 6000`: Return fail with "latency_anomaly"
3. **LAYER 1 SECOND** - Answer correctness:
   - Transcribe audio: `transcript = transcribe_audio(audio_bytes)`
   - Get challenge data: `challenge_data = challenges.get(challenge_id, {})`
   - Verify answer: `correct = verify_answer(transcript, challenge_data)`
   - If not correct: Return fail with "wrong_answer"
4. **LAYER 3 THIRD** - Voice authenticity:
   - Check if synthetic: `synthetic = is_synthetic(audio_bytes)`
   - If synthetic: Return fail with "synthetic_voice"
5. If all three pass: Return success with transcript and latency

#### Main Entry Point
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

### File: `backend/challenge.py`
**Purpose:** Generate cognitive challenges and verify answers using Google Gemini API.

#### Imports
```python
import google.generativeai as genai  # Gemini API client
import json                          # Parse JSON responses
import random                        # Select fallback challenges
import os                            # Access environment variables
```

#### Configuration
```python
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")
```
**Environment Variable Required:** `GEMINI_API_KEY`

#### Constants
`FALLBACK_CHALLENGES`: List of 5 hardcoded challenges used when Gemini API fails.

Each challenge has:
- `challenge`: str - The question text
- `answer_criteria`: str - What counts as correct

**Fallback List:**
1. "Name an animal starting with the last letter of ELEPHANT" → "any animal starting with T"
2. "What is heavier, a kilogram of iron or a kilogram of feathers?" → "same weight or equal"
3. "If you have 3 cats and each has 4 legs how many legs total?" → "twelve or 12"
4. "Name something in a kitchen that starts with F" → "any kitchen item starting with F"
5. "Say the first three months of the year in reverse order" → "march february january"

#### Function: `generate_challenge()`
**Return Type:** `dict`
**Keys:** "challenge", "answer_criteria"

**Purpose:** Generate a unique cognitive challenge using Gemini.

**Logic Flow:**
1. Send prompt to Gemini:
   ```
   Generate a spoken CAPTCHA challenge.
   Rules:
   - Answerable verbally in under 10 words
   - Requires real-time thinking not lookup
   - Has a clear correct answer
   - Good types: word chains, simple logic, 
     counterfactual questions, sensory tasks
   Return ONLY valid JSON no markdown no backticks no explanation:
   {"challenge": "the challenge text", 
    "answer_criteria": "what counts as correct"}
   ```
2. Get response: `response = model.generate_content(prompt)`
3. Clean response text:
   - Strip whitespace
   - Remove "```json" prefix if present
   - Remove "```" prefix/suffix if present
4. Parse as JSON: `challenge_dict = json.loads(response_text)`
5. Return the dict

**Error Handling:**
- If any exception occurs: Return `random.choice(FALLBACK_CHALLENGES)`

**Example Output:**
```python
{
  "challenge": "What color is a ripe banana?",
  "answer_criteria": "yellow or gold"
}
```

#### Function: `verify_answer(transcript: str, challenge_data: dict)`
**Return Type:** `bool`

**Purpose:** Verify if the user's spoken answer is semantically correct using Gemini.

**Parameters:**
- `transcript`: The transcribed text from the user's audio
- `challenge_data`: Dict containing "challenge" and "answer_criteria" keys

**Logic Flow:**
1. Validation checks:
   - If transcript is empty or None: Return `False`
   - If challenge_data is empty or None: Return `False`
2. Build verification prompt:
   ```
   Challenge given to user: {challenge_data['challenge']}
   What counts as correct: {challenge_data['answer_criteria']}
   What the user actually said: {transcript}
   Did the user answer correctly? 
   Reply with only the single word YES or NO
   ```
3. Send to Gemini: `response = model.generate_content(verification_prompt)`
4. Check response:
   - Convert to uppercase: `response_upper = response.text.upper()`
   - If "YES" in response_upper: Return `True`
   - If "NO" in response_upper: Return `False`
   - If neither: Return `True` (fail-safe for demo)

**Error Handling:**
- If any exception occurs: Return `True` (prevents demo breakage)

---

### File: `backend/transcribe.py`
**Purpose:** Transcribe audio to text using local Whisper model (no API calls).

#### Imports
```python
import whisper      # OpenAI Whisper local package
import tempfile     # Create temporary files
import os           # File operations
```

#### Module-Level Configuration
**CRITICAL:** This loads once on module import, not per function call.
```python
model = whisper.load_model("base")
```
**Model:** Whisper "base" model (~140MB)
**Load Time:** 3-5 seconds on first import
**Why Module Level:** Avoids reload delay on every transcription

#### Function: `transcribe_audio(audio_bytes: bytes)`
**Return Type:** `str`

**Purpose:** Convert audio bytes to text.

**Parameters:**
- `audio_bytes`: Raw audio data as bytes

**Logic Flow:**
1. Create temporary WAV file:
   ```python
   temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
   ```
2. Write audio bytes to temp file
3. Close file and store path: `temp_file_path = temp_file.name`
4. Transcribe: `result = model.transcribe(temp_file_path)`
5. Extract text: `return result["text"].strip()`
6. **Finally block:** Always delete temp file using `os.unlink(temp_file_path)`

**Error Handling:**
- If any exception: Return empty string `""`
- Temp file cleanup happens in finally block (always executes)

**Example:**
```python
audio_bytes = b"...audio data..."
text = transcribe_audio(audio_bytes)
# Returns: "the quick brown fox"
```

---

### File: `backend/voice_auth.py`
**Purpose:** Detect synthetic (TTS) voices using acoustic feature analysis.

#### Imports
```python
import librosa       # Audio feature extraction
import numpy as np   # Numerical operations
import tempfile      # Temporary file handling
import os           # File operations
import soundfile as sf  # Audio file operations (currently unused)
```

#### Function: `extract_features(audio_bytes: bytes)`
**Return Type:** `dict`

**Purpose:** Extract four acoustic features that distinguish human from synthetic voices.

**Parameters:**
- `audio_bytes`: Raw audio data as bytes

**Return Keys:**
- `pitch_std`: float - Standard deviation of pitch (f0) variation
- `mfcc_var`: float - Mean variance of mel-frequency cepstral coefficients
- `spectral_flux`: float - Mean spectral flux (onset strength)
- `zcr_var`: float - Variance in zero-crossing rate

**Logic Flow:**
1. Write audio_bytes to temporary WAV file (delete=False)
2. Load audio with librosa: `y, sr = librosa.load(temp_file_path, sr=16000)`
3. **Feature 1 - Pitch Standard Deviation:**
   - Extract f0: `f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=50, fmax=400, sr=sr)`
   - Remove NaN values: `f0_clean = f0[~np.isnan(f0)]`
   - Calculate std: `pitch_std = float(np.std(f0_clean))` if len > 0, else 0.0
4. **Feature 2 - MFCC Variance:**
   - Extract MFCCs: `mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)`
   - Calculate: `mfcc_var = float(np.mean(np.var(mfccs, axis=1)))`
5. **Feature 3 - Spectral Flux:**
   - Calculate: `onset_env = librosa.onset.onset_strength(y=y, sr=sr)`
   - Mean: `spectral_flux = float(np.mean(onset_env))`
6. **Feature 4 - Zero-Crossing Rate Variance:**
   - Calculate: `zcr = librosa.feature.zero_crossing_rate(y)`
   - Variance: `zcr_var = float(np.var(zcr))`
7. Return all four features as dict

**Error Handling:**
- If any exception: Return `{pitch_std: 0, mfcc_var: 0, spectral_flux: 0, zcr_var: 0}`
- **Finally block:** Always delete temp file

**Why These Features:**
- Synthetic voices have unnaturally consistent pitch (low pitch_std)
- TTS models produce smooth MFCCs (low mfcc_var)
- TTS lacks natural onset variations (low spectral_flux)
- TTS crosses zero less variably (low zcr_var)

#### Function: `is_synthetic(audio_bytes: bytes)`
**Return Type:** `bool`

**Purpose:** Classify audio as synthetic or human using threshold-based classifier.

**Parameters:**
- `audio_bytes`: Raw audio data as bytes

**Logic Flow:**
1. Extract features: `features = extract_features(audio_bytes)`
2. Initialize score: `score = 0`
3. Check each threshold (add 1 to score if condition true):
   - `features["pitch_std"] < 15` → +1
   - `features["mfcc_var"] < 40` → +1
   - `features["spectral_flux"] < 2` → +1
   - `features["zcr_var"] < 0.0001` → +1
4. Return classification:
   - If `score >= 2`: Return `True` (likely synthetic)
   - Otherwise: Return `False` (likely human)

**Threshold Rationale:**
- Requires 2 out of 4 indicators to flag as synthetic
- Balances false positives (blocking real humans) with false negatives (allowing bots)
- Human voices typically score 0-1, TTS voices typically score 3-4

---

### File: `backend/requirements.txt`
**Purpose:** Python package dependencies for the backend.

**Expected Contents:**
```
fastapi
uvicorn[standard]
python-multipart
google-generativeai
openai-whisper
librosa
numpy
soundfile
```

**Installation:**
```bash
pip install -r backend/requirements.txt
```

---

## Frontend Components

### File: `frontend/index.html`
**Purpose:** User interface structure for the voice CAPTCHA widget.

#### Document Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Create Account - Voice CAPTCHA Demo</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="container">
    <div class="card">
      <!-- Content here -->
    </div>
  </div>
  <script src="captcha.js"></script>
</body>
</html>
```

#### Key Elements

**Form Fields (Disabled):**
```html
<input type="text" id="name" class="form-input" disabled>
<input type="email" id="email" class="form-input" disabled>
```
**Why Disabled:** This is a demo of the CAPTCHA widget, not a real form.

**CAPTCHA Widget Container:**
```html
<div class="captcha-widget">
  <!-- All CAPTCHA elements inside -->
</div>
```

**Status Icon:**
```html
<div class="status-icon" id="status-icon">🎤</div>
```
**Purpose:** Visual feedback (🎤 → ⏺ → ⏳ → ✅/❌)

**Challenge Text:**
```html
<div class="challenge-text" id="challenge-text">Click to start CAPTCHA</div>
```
**Purpose:** Display the challenge question or status messages.

**Start Button:**
```html
<button class="start-btn" id="start-btn">Verify I'm Human</button>
```
**Purpose:** User clicks to start, changes to "Stop Recording" during recording.

**Signal Panel (Hidden by default):**
```html
<div class="signal-panel" id="signal-panel" hidden>
  <div class="signal-row">
    <span class="signal-label" id="sig-latency">⏱ Latency:</span>
    <span class="signal-value" id="sig-latency-value"></span>
  </div>
  <div class="signal-row">
    <span class="signal-label" id="sig-answer">🧠 Answer:</span>
    <span class="signal-value" id="sig-answer-value"></span>
  </div>
  <div class="signal-row">
    <span class="signal-label" id="sig-voice">🎙 Voice:</span>
    <span class="signal-value" id="sig-voice-value"></span>
  </div>
</div>
```
**Purpose:** Show results of all three verification layers.

**Result Display:**
```html
<div class="result" id="result"></div>
```
**Purpose:** Show pass/fail message with colored styling.

**Submit Button (Disabled):**
```html
<button class="submit-btn" disabled>Submit</button>
```
**Purpose:** Gets enabled only when CAPTCHA passes.

---

### File: `frontend/style.css`
**Purpose:** Dark theme styling for the voice CAPTCHA interface.

#### Color Palette
```css
--background: #0a0a0a       /* Page background */
--card-bg: #1a1a1a          /* Card background */
--widget-bg: #111           /* CAPTCHA widget background */
--border: #333              /* All borders */
--text-primary: #ffffff     /* Main text */
--text-secondary: #888888   /* Labels, disabled text */
--text-challenge: #e0e0e0   /* Challenge text */
--red-primary: #ef4444      /* Start button */
--red-hover: #dc2626        /* Start button hover */
--green-dark: #14532d       /* Pass background */
--green-light: #4ade80      /* Pass text */
--red-dark: #450a0a         /* Fail background */
--red-light: #f87171        /* Fail text */
--blue: #3b82f6             /* Submit button */
```

#### Key Selectors

**Body Layout:**
```css
body {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}
```
**Effect:** Centers the card vertically and horizontally.

**Card:**
```css
.card {
  width: 420px;
  border-radius: 12px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
```

**Disabled Inputs:**
```css
.form-input:disabled {
  color: #666;
  cursor: not-allowed;
}
```

**Start Button:**
```css
.start-btn {
  background-color: #ef4444;
  font-weight: 700;
  width: 100%;
}
.start-btn:hover {
  background-color: #dc2626;
}
```

**Signal Panel:**
```css
.signal-row {
  font-size: 0.85rem;
  border-top: 1px solid #222;
}
.signal-value {
  font-weight: 700;
}
```

**Result States:**
```css
.result.pass {
  background-color: #14532d;
  color: #4ade80;
}
.result.fail {
  background-color: #450a0a;
  color: #f87171;
}
```

**Submit Button:**
```css
.submit-btn:disabled {
  opacity: 0.4;
}
.submit-btn:not(:disabled) {
  opacity: 1;
}
```

---

### File: `frontend/captcha.js`
**Purpose:** Client-side JavaScript handling all CAPTCHA interactions.

#### Global Variables
```javascript
const API = "http://localhost:8000";  // Backend URL
let challengeId = null;                // UUID of current challenge
let recordStart = null;                // Timestamp when recording started
let mediaRecorder = null;              // MediaRecorder instance
let audioChunks = [];                  // Audio data chunks
```

#### DOM References
```javascript
const startBtn = document.getElementById("start-btn");
const challengeText = document.getElementById("challenge-text");
const signalPanel = document.getElementById("signal-panel");
const resultDiv = document.getElementById("result");
const statusIcon = document.getElementById("status-icon");
```

#### Function: `loadChallenge()`
**Purpose:** Fetch a new challenge from the backend.

**Logic Flow:**
1. Fetch: `GET ${API}/challenge`
2. Parse JSON response
3. Store: `challengeId = data.id`
4. Display: `challengeText.textContent = data.challenge`
5. Update button: `startBtn.textContent = "🎤 Speak Your Answer"`
6. Set click handler: `startBtn.onclick = startRecording`

**Example API Response:**
```json
{
  "id": "abc123...",
  "challenge": "What color is the sky?"
}
```

#### Function: `startRecording()`
**Purpose:** Begin audio recording from user's microphone.

**Logic Flow:**
1. Request mic access: `stream = await navigator.mediaDevices.getUserMedia({audio: true})`
2. Create recorder: `mediaRecorder = new MediaRecorder(stream)`
3. Reset: `audioChunks = []`
4. Set data handler: `mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data)`
5. Set stop handler: `mediaRecorder.onstop = submitAudio`
6. Record start time: `recordStart = Date.now()`
7. Start recording: `mediaRecorder.start()`
8. Update UI:
   - Icon: `statusIcon.textContent = "⏺"`
   - Button: `startBtn.textContent = "Stop Recording"`
   - Click handler: `startBtn.onclick = () => mediaRecorder.stop()`

**Browser Permissions:**
- User must grant microphone access
- Chrome requires HTTPS (except localhost)

#### Function: `submitAudio()`
**Purpose:** Send recorded audio to backend for verification.

**Logic Flow:**
1. Calculate latency: `latency = Date.now() - recordStart`
2. Create blob: `audioBlob = new Blob(audioChunks, {type: "audio/wav"})`
3. Build FormData:
   ```javascript
   formData.append("audio", audioBlob, "response.wav")
   formData.append("challenge_id", challengeId)
   formData.append("latency_ms", latency.toString())
   ```
4. Update UI: "Verifying..." with ⏳ icon
5. Show signal panel: `signalPanel.style.display = "block"`
6. POST to `${API}/verify`
7. Parse response
8. Call: `showResult(data, latency)`

**Request Format:**
- Method: POST
- Content-Type: multipart/form-data
- Fields: audio (file), challenge_id (string), latency_ms (string)

#### Function: `showResult(data, latency)`
**Purpose:** Display verification results and update all UI elements.

**Parameters:**
- `data`: Response from POST /verify
- `latency`: Calculated latency in milliseconds

**Logic Flow:**
1. Get signal value spans:
   ```javascript
   const latencySpan = document.getElementById("sig-latency-value")
   const answerSpan = document.getElementById("sig-answer-value")
   const voiceSpan = document.getElementById("sig-voice-value")
   ```

2. Display latency with indicator:
   ```javascript
   const latencyInRange = latency >= 400 && latency <= 6000
   latencySpan.textContent = `${latency}ms ${latencyInRange ? "✅" : "❌"}`
   ```

3. **If data.pass === true:**
   - Answer: `"Correct ✅"`
   - Voice: `"Human ✅"`
   - Icon: `"✅"`
   - Result: `<div class="pass">✅ Human Verified — Proceed</div>`
   - Enable submit button: `document.querySelector(".submit-btn").disabled = false`

4. **If data.pass === false, check data.reason:**

   **reason: "latency_anomaly"**
   - Answer: `"—"`
   - Voice: `"—"`
   - Result: `<div class="fail">❌ Failed — Response timing suspicious</div>`

   **reason: "wrong_answer"**
   - Answer: `"Incorrect ❌"`
   - Voice: `"—"`
   - Result: `<div class="fail">❌ Failed — Incorrect answer</div>`

   **reason: "synthetic_voice"**
   - Answer: `"Correct ✅"`
   - Voice: `"Synthetic ❌"`
   - Icon: `"❌"`
   - Result: `<div class="fail">❌ Failed — Synthetic voice detected</div>`

5. On any failure:
   - Button: `"Try Again"`
   - Click handler: `startBtn.onclick = loadChallenge`

#### Initialization
```javascript
startBtn.onclick = loadChallenge;
```
**On page load:** Button is ready to fetch first challenge.

---

## Demo Components

### File: `demo/bot_script.py`
**Purpose:** Simulate a bot attack to demonstrate the system catching synthetic voices.

#### Imports
```python
import requests   # HTTP requests to API
import time       # Timing and delays
import pyttsx3    # Text-to-speech generation
import os         # File operations
```

#### Constants
```python
BASE_URL = "http://localhost:8000"
```

#### Function: `bot_attack()`
**Purpose:** Execute a complete bot attack simulation.

**Logic Flow:**

**Step 1 - Get Challenge:**
```python
response = requests.get(f"{BASE_URL}/challenge")
data = response.json()
challenge_id = data["id"]
challenge_text = data["challenge"]
print(f"Challenge received: {challenge_text}")
```

**Step 2 - Simulate Bot Thinking:**
```python
think_start = time.time()
time.sleep(2.8)  # LLM + TTS pipeline delay
```
**Why 2.8s:** Realistic ASR (0.5s) + LLM inference (1.5s) + TTS generation (0.8s) = ~2.8s

**Step 3 - Generate TTS Answer:**
```python
engine = pyttsx3.init()
engine.save_to_file("twelve", "bot_answer.wav")
engine.runAndWait()
```
**Note:** Bot uses generic answer "twelve" without actually solving the challenge.

**Step 4 - Calculate Latency:**
```python
latency_ms = int((time.time() - think_start) * 1000)
```

**Step 5 - Submit Response:**
```python
with open("bot_answer.wav", "rb") as audio_file:
    files = {"audio": ("bot_answer.wav", audio_file, "audio/wav")}
    data = {"challenge_id": challenge_id, "latency_ms": str(latency_ms)}
    verify_response = requests.post(f"{BASE_URL}/verify", files=files, data=data)
    result = verify_response.json()
```

**Step 6 - Print Outcome:**
```python
if result.get("pass") is True:
    print("BOT PASSED - CAPTCHA FAILED TO DETECT")
else:
    print(f"BOT BLOCKED - Reason: {result.get('reason', 'unknown')}")
```

**Step 7 - Cleanup:**
```python
try:
    if os.path.exists("bot_answer.wav"):
        os.remove("bot_answer.wav")
except Exception:
    pass
```

**Expected Outcome:**
- Most likely: `BOT BLOCKED - Reason: synthetic_voice` (Layer 3 catches TTS)
- Sometimes: `BOT BLOCKED - Reason: latency_anomaly` (Layer 2 if timing hits >3000ms)
- Unlikely: `BOT PASSED` (would indicate detection failure)

---

## Data Flow

### Complete User Journey

#### Phase 1: Challenge Request
```
User clicks "Verify I'm Human"
    ↓
JavaScript: loadChallenge()
    ↓
GET http://localhost:8000/challenge
    ↓
Python: generate_challenge()
    ↓
Gemini API: Generate unique challenge
    ↓
Python: Store in challenges dict
    ↓
Return: {id: "uuid", challenge: "text"}
    ↓
JavaScript: Display challenge
    ↓
User sees: "What color is a ripe banana?"
```

#### Phase 2: Recording
```
User clicks "🎤 Speak Your Answer"
    ↓
JavaScript: startRecording()
    ↓
Browser: Request microphone permission
    ↓
User: Grants permission
    ↓
JavaScript: Create MediaRecorder
    ↓
JavaScript: Start recording (recordStart = Date.now())
    ↓
User sees: ⏺ icon and "Stop Recording" button
    ↓
User speaks: "Yellow"
    ↓
User clicks: "Stop Recording"
    ↓
JavaScript: mediaRecorder.stop()
    ↓
Trigger: mediaRecorder.onstop → submitAudio()
```

#### Phase 3: Verification
```
JavaScript: submitAudio()
    ↓
JavaScript: Calculate latency = Date.now() - recordStart
    ↓
JavaScript: Create FormData with audio blob
    ↓
POST http://localhost:8000/verify
    FILES: {audio: blob}
    DATA: {challenge_id: "uuid", latency_ms: "1234"}
    ↓
Python: audio_bytes = await audio.read()
    ↓

=== LAYER 2: LATENCY CHECK ===
Python: if latency_ms < 400 or > 6000:
    Return: {pass: false, reason: "latency_anomaly"}
    STOP HERE
    ↓
PASS: Continue to Layer 1
    ↓

=== LAYER 1: ANSWER CORRECTNESS ===
Python: transcript = transcribe_audio(audio_bytes)
    ↓
Whisper: Load audio → Model inference → Return "yellow"
    ↓
Python: challenge_data = challenges[challenge_id]
    ↓
Python: correct = verify_answer("yellow", challenge_data)
    ↓
Gemini: Semantic verification
    ↓
Gemini: Returns "YES"
    ↓
Python: correct = True
    ↓
Python: if not correct:
    Return: {pass: false, reason: "wrong_answer"}
    STOP HERE
    ↓
PASS: Continue to Layer 3
    ↓

=== LAYER 3: VOICE AUTHENTICITY ===
Python: synthetic = is_synthetic(audio_bytes)
    ↓
Librosa: Extract 4 acoustic features
    ↓
Python: Calculate score based on thresholds
    ↓
Python: score = 0 (human voice)
    ↓
Python: if synthetic:
    Return: {pass: false, reason: "synthetic_voice"}
    STOP HERE
    ↓
PASS: All layers passed!
    ↓
Python: Return {pass: true, transcript: "yellow", latency_ms: 1234}
    ↓

=== UI UPDATE ===
JavaScript: showResult(data, latency)
    ↓
Display:
- ⏱ Latency: 1234ms ✅
- 🧠 Answer: Correct ✅
- 🎙 Voice: Human ✅
- ✅ Human Verified — Proceed
    ↓
Enable submit button
    ↓
User can now submit the form
```

### Bot Attack Data Flow

```
Bot: python demo/bot_script.py
    ↓
GET /challenge
    ↓
Receive: "If you have 3 cats and each has 4 legs how many legs total?"
    ↓
Bot: time.sleep(2.8) # Simulate LLM thinking
    ↓
Bot: pyttsx3 generates "twelve" → bot_answer.wav
    ↓
Bot: latency = 2800ms
    ↓
POST /verify with TTS audio
    ↓
Backend:
- Layer 2: 2800ms ✅ (within 400-6000ms)
- Layer 1: Whisper transcribes "twelve" ✅
- Layer 1: Gemini verifies "twelve" is correct ✅
- Layer 3: librosa extracts features
  - pitch_std: 8.2 < 15 ✓
  - mfcc_var: 22.1 < 40 ✓
  - spectral_flux: 1.4 < 2 ✓
  - zcr_var: 0.00005 < 0.0001 ✓
  - Score: 4/4 ≥ 2 → SYNTHETIC
    ↓
Return: {pass: false, reason: "synthetic_voice"}
    ↓
Print: "BOT BLOCKED - Reason: synthetic_voice"
```

---

## API Reference

### Endpoint Summary

| Method | Path       | Purpose                    | Auth |
|--------|-----------|----------------------------|------|
| GET    | /challenge | Get new CAPTCHA challenge | None |
| POST   | /verify   | Verify voice response     | None |

### GET /challenge

**Request:**
```http
GET http://localhost:8000/challenge
```

**Response 200:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "challenge": "Name an animal starting with the last letter of ELEPHANT"
}
```

**Response Schema:**
```typescript
{
  id: string;         // UUID v4
  challenge: string;  // The question text
}
```

### POST /verify

**Request:**
```http
POST http://localhost:8000/verify
Content-Type: multipart/form-data

audio: (binary audio file)
challenge_id: "3fa85f64-5717-4562-b3fc-2c963f66afa6"
latency_ms: "1234"
```

**Response 200 (Pass):**
```json
{
  "pass": true,
  "transcript": "tiger",
  "latency_ms": 1234
}
```

**Response 200 (Fail - Latency):**
```json
{
  "pass": false,
  "reason": "latency_anomaly",
  "latency_ms": 350
}
```

**Response 200 (Fail - Wrong Answer):**
```json
{
  "pass": false,
  "reason": "wrong_answer",
  "transcript": "elephant"
}
```

**Response 200 (Fail - Synthetic Voice):**
```json
{
  "pass": false,
  "reason": "synthetic_voice"
}
```

**Response Schema:**
```typescript
type VerifyResponse = 
  | { pass: true; transcript: string; latency_ms: number }
  | { pass: false; reason: "latency_anomaly"; latency_ms: number }
  | { pass: false; reason: "wrong_answer"; transcript: string }
  | { pass: false; reason: "synthetic_voice" };
```

---

## Dependencies

### Backend Python Packages

| Package               | Version  | Purpose                          |
|-----------------------|----------|----------------------------------|
| fastapi               | latest   | Web framework                    |
| uvicorn[standard]     | latest   | ASGI server                      |
| python-multipart      | latest   | FormData parsing                 |
| google-generativeai   | latest   | Gemini API client                |
| openai-whisper        | latest   | Local ASR (no API)               |
| librosa               | latest   | Audio feature extraction         |
| numpy                 | latest   | Numerical operations             |
| soundfile             | latest   | Audio file I/O                   |
| pyttsx3               | latest   | TTS for bot demo (demo only)     |
| requests              | latest   | HTTP client (demo only)          |

### Frontend (No Packages)
- **Pure vanilla JavaScript** - No npm, no build step
- **Browser APIs used:**
  - `navigator.mediaDevices.getUserMedia()` - Microphone access
  - `MediaRecorder` - Audio recording
  - `fetch()` - HTTP requests
  - `FormData` - Multipart uploads

### Environment Variables

| Variable        | Required | Purpose                    | Get From                  |
|-----------------|----------|----------------------------|---------------------------|
| GEMINI_API_KEY  | Yes      | Gemini API authentication  | aistudio.google.com       |

---

## Common Issues & Fixes

### Issue: "No module named 'google.generativeai'"
**Cause:** Missing Gemini package
**Fix:**
```bash
pip install google-generativeai
```

### Issue: "No such file or directory: ffmpeg"
**Cause:** Whisper requires ffmpeg for audio processing
**Fix (Windows):**
```bash
# Using chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```
**Fix (Linux/Mac):**
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # macOS
```

### Issue: "GEMINI_API_KEY not found"
**Cause:** Environment variable not set
**Fix:**
```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your-api-key-here"

# Windows CMD
set GEMINI_API_KEY=your-api-key-here

# Linux/Mac
export GEMINI_API_KEY=your-api-key-here
```
**Permanent Fix:** Create `.env` file in backend/
```
GEMINI_API_KEY=your-api-key-here
```
Then load with python-dotenv (needs modification to main.py)

### Issue: CORS error in browser
**Cause:** Frontend not accessing from allowed origin
**Current Setup:** Allows all origins (`allow_origins=["*"]`)
**If Still Blocked:** Ensure backend is running on port 8000

### Issue: "Microphone permission denied"
**Cause:** Browser blocks mic access
**Fix:**
1. Chrome: Click lock icon → Site settings → Microphone → Allow
2. Must use HTTPS or localhost
3. Check browser console for specific error

### Issue: Whisper model download slow
**Cause:** First-time model download (~140MB)
**Fix:** Wait for download to complete. Subsequent runs will be instant.

### Issue: Bot script always passes
**Cause:** Voice authentication thresholds too lenient
**Fix:** Adjust thresholds in `voice_auth.py`:
```python
# Make detection more aggressive
if features["pitch_std"] < 20:      # Was 15
if features["mfcc_var"] < 50:       # Was 40
if features["spectral_flux"] < 2.5: # Was 2
if features["zcr_var"] < 0.0002:    # Was 0.0001
```

### Issue: Real humans blocked as synthetic
**Cause:** Voice authentication too strict or low-quality microphone
**Fix:**
1. Adjust score threshold in `is_synthetic()`:
   ```python
   return score >= 3  # Was 2, now requires 3/4 indicators
   ```
2. Check microphone quality (built-in laptop mics are low quality)

### Issue: Latency always fails
**Cause:** Frontend timer calculation incorrect
**Check:**
```javascript
// In submitAudio(), verify:
const latency = Date.now() - recordStart;
// Should be in milliseconds
```
**Typical Human Range:** 800-2500ms
**Too Low (<400ms):** Bot with pre-recorded audio
**Too High (>6000ms):** Bot with slow TTS pipeline

---

## File Modification Checklist

### To modify challenge generation:
1. Edit `backend/challenge.py`
2. Function: `generate_challenge()`
3. Change the prompt string sent to Gemini
4. Update `FALLBACK_CHALLENGES` list if needed

### To modify answer verification:
1. Edit `backend/challenge.py`
2. Function: `verify_answer()`
3. Change verification prompt or logic
4. Consider adjusting error handling (currently returns True on error)

### To modify transcription:
1. Edit `backend/transcribe.py`
2. Change Whisper model: `model = whisper.load_model("medium")` for better accuracy
3. Adjust sample rate: `sr=16000` parameter in librosa.load()

### To modify voice authentication:
1. Edit `backend/voice_auth.py`
2. Function: `extract_features()` - Add/remove acoustic features
3. Function: `is_synthetic()` - Adjust thresholds or scoring logic
4. Test with both real humans and bot_script.py

### To modify latency thresholds:
1. Edit `backend/main.py`
2. In `POST /verify` endpoint
3. Change: `if latency_ms < 400 or latency_ms > 6000:`
4. Consider human response time distribution

### To modify UI appearance:
1. Edit `frontend/style.css`
2. Change colors in the color palette comments
3. Modify layout: adjust .card width, padding, gap
4. Update button styles: .start-btn, .submit-btn

### To modify UI behavior:
1. Edit `frontend/captcha.js`
2. Change API endpoint: `const API = "http://..."`
3. Modify recording behavior in `startRecording()`
4. Adjust result display in `showResult()`

### To add a new verification layer:
1. Create new file in `backend/` with verification function
2. Import in `backend/main.py`
3. Add check in `POST /verify` endpoint (choose order carefully)
4. Add new failure reason string
5. Update `frontend/captcha.js` showResult() to handle new reason
6. Update `frontend/index.html` with signal row if needed

---

## Testing Guide

### Test Human User Flow
1. Start backend: `cd backend && python main.py`
2. Open `frontend/index.html` in Chrome
3. Click "Verify I'm Human"
4. Check: Challenge appears
5. Click "🎤 Speak Your Answer"
6. Grant microphone permission
7. Speak answer clearly
8. Click "Stop Recording"
9. Check: All three signals show ✅
10. Check: Submit button is enabled

### Test Bot Detection
1. Ensure backend is running
2. Run: `python demo/bot_script.py`
3. Expected output: "BOT BLOCKED - Reason: synthetic_voice"
4. If bot passes, adjust thresholds in `voice_auth.py`

### Test Wrong Answer
1. Complete human user flow
2. Speak incorrect answer deliberately
3. Check: "🧠 Answer: Incorrect ❌"
4. Check: Reason is "wrong_answer"

### Test Latency Anomaly
1. Complete human user flow
2. Start recording, wait 7+ seconds before stopping
3. Check: "⏱ Latency: ####ms ❌"
4. Check: Reason is "latency_anomaly"

---

## Architecture Decisions

### Why Three Layers?
- **Defense in depth:** Multiple independent checks
- **Fail-fast:** Cheap checks first (latency), expensive last (Gemini)
- **Different attack vectors:** Each layer catches different bot types

### Why This Layer Order?
1. **Latency first:** Instant, no computation needed
2. **Correctness second:** Catches bots that don't solve challenge
3. **Voice third:** Most expensive, only runs on correct answers

### Why In-Memory Storage?
- **Simplicity:** No database setup required
- **Sufficient:** Challenges expire after use
- **Production:** Would use Redis or database

### Why Local Whisper?
- **Privacy:** Audio never leaves device
- **Speed:** No network latency
- **Cost:** No API charges
- **Offline:** Works without internet (after model download)

### Why Gemini Not Local?
- **Challenge quality:** LLMs need substantial compute
- **Dynamic:** Prevents bot pattern learning
- **Verification:** Semantic understanding required
- **Future:** Could use AMD Lemonade Server locally

### Why Threshold Classifier Not ML?
- **Simplicity:** No training data needed
- **Interpretability:** Clear why bot was blocked
- **Speed:** Instant classification
- **Sufficient:** TTS consistently differs from humans

---

This MAP provides complete documentation for understanding and modifying the VoiceCAPTCHA system. Any AI assistant with this document can locate, understand, and modify any component of the system.
