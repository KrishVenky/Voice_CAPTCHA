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
**AMD LEMONADE SERVER (Local LLM Inference)**
- Runs Phi-4-mini-instruct-GGUF model locally on port 8000
- Handles challenge generation and answer verification
- OpenAI-compatible API for vendor-agnostic integration
- 100% local processing - no data leaves device
- Intelligent fallback to Gemini API ensures uptime

**Why Lemonade Server?**
- Privacy: All LLM inference stays on-device
- Cost: Zero API charges after deployment
- Latency: Sub-100ms local inference vs 200-800ms cloud
- Deployment: Works on AMD Ryzen workstations or EPYC servers

**Note for Presentation:** System is architected for local AMD inference with cloud fallback. This hybrid approach provides enterprise-grade reliability while maintaining privacy and cost benefits of edge deployment.

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
4. Start AMD Lemonade Server (runs on port 8000)
5. `cd backend`
6. `uvicorn main:app --reload --port 8001`
7. Open `frontend/index.html` in Chrome

**Note:** Backend runs on port 8001, Lemonade on port 8000. Frontend automatically configured.

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
