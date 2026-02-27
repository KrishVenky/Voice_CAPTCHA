# VoiceCAPTCHA
A privacy-first drop-in CAPTCHA replacement using spoken cognitive 
challenges verified through three simultaneous layers. No audio ever 
leaves the user's device.

## The Problem
- Image CAPTCHAs are being solved by bots at over 95% accuracy
- Audio CAPTCHAs exclude non-English speakers and people with accents
- reCAPTCHA sends all behavioral data to Google servers
- Existing solutions are cloud-dependent and privacy-invasive

## How It Works
Three verification layers run simultaneously on every response:

**Layer 1 - Cognitive Correctness:**
Gemini generates a unique dynamic challenge for every session.
Cannot be pre-computed or looked up. 
Gemini verifies whether the spoken answer is semantically correct.

**Layer 2 - Response Latency Profiling:**
Humans begin speaking within 0.8 to 2.5 seconds of hearing a challenge.
Bots using LLM plus TTS pipelines take 2.5 to 6 seconds before 
audio begins due to inference lag.
Responses outside the 400ms to 6000ms human window are rejected.

**Layer 3 - Voice Authenticity:**
Spectral analysis via librosa detects TTS-generated audio.
Four features extracted: pitch standard deviation, MFCC variance,
spectral flux, zero crossing rate variance.
TTS voices score abnormally low on all four because they are 
too consistent compared to natural human speech.

## AMD Integration
- Whisper ASR runs on Ryzen AI NPU via ONNX Runtime and VitisAI 
  execution provider for sub-3W continuous transcription
- Challenge generation and answer verification run via AMD Lemonade 
  Server on localhost, OpenAI-compatible API, zero external calls
- Voice authenticity classifier validated on AMD Developer Cloud MI300X
- In local NPU mode no audio ever leaves the user device

## Attacks Prevented
- Standard selenium and puppeteer bots: cannot interact with microphone
- reCAPTCHA solver services: cannot speak into remote microphone
- Vision model bots: no image to attack
- Pre-recorded playback: caught by latency layer
- Basic TTS bots: caught by voice authenticity layer
- Credential stuffing at scale: real-time voice makes bulk attempts 
  economically unviable

## Run Locally
1. `pip install -r backend/requirements.txt`
2. Get free Gemini API key from aistudio.google.com
3. Create .env file with `GEMINI_API_KEY=your_key_here`
4. `cd backend`
5. `uvicorn main:app --reload --port 8000`
6. Open `frontend/index.html` in Chrome

## Demo the Bot Attack
```bash
python demo/bot_script.py
```
Expected output: `BOT BLOCKED - Reason: latency_anomaly or synthetic_voice`

## Tech Stack
- **Backend:** FastAPI Python
- **LLM:** Google Gemini 2.0 Flash
- **ASR:** OpenAI Whisper local offline
- **Voice Analysis:** librosa numpy
- **Frontend:** Vanilla HTML CSS JavaScript
- **AMD:** Ryzen AI NPU, Lemonade Server, AMD Developer Cloud

## Team
Built for AMD Slingshot Hackathon 2026
