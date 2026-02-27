/**
 * Voice CAPTCHA Frontend JavaScript
 * Handles challenge loading, audio recording, and verification
 */

// API configuration and global state variables
const API = "http://localhost:8000";
let challengeId = null;
let recordStart = null;
let mediaRecorder = null;
let audioChunks = [];

// Get DOM elements
const startBtn = document.getElementById("start-btn");
const challengeText = document.getElementById("challenge-text");
const signalPanel = document.getElementById("signal-panel");
const resultDiv = document.getElementById("result");
const statusIcon = document.getElementById("status-icon");

// Debug: Verify DOM elements are found
console.log("DOM Elements loaded:", {
    startBtn: !!startBtn,
    challengeText: !!challengeText,
    signalPanel: !!signalPanel,
    resultDiv: !!resultDiv,
    statusIcon: !!statusIcon
});

/**
 * Load a new CAPTCHA challenge from the backend
 */
async function loadChallenge() {
    try {
        // Fetch challenge from backend API
        const response = await fetch(`${API}/challenge`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        console.log("Challenge loaded:", data);
        
        // Store the challenge ID for later verification
        challengeId = data.id;
        
        // Display the challenge text to the user
        challengeText.textContent = data.challenge;
        
        // Update button to allow user to speak their answer
        startBtn.textContent = "🎤 Speak Your Answer";
        startBtn.onclick = startRecording;
    } catch (error) {
        console.error("Error loading challenge:", error);
        challengeText.textContent = "Error loading challenge. Check console.";
        alert("Error: " + error.message);
    }
}

/**
 * Start recording audio from the user's microphone
 */
async function startRecording() {
    try {
        // Request microphone access from the browser
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        console.log("Microphone access granted");
        
        // Create a MediaRecorder to capture audio
        mediaRecorder = new MediaRecorder(stream);
        
        // Reset audio chunks array for new recording
        audioChunks = [];
        
        // Collect audio data as it becomes available
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        // Submit audio when recording stops
        mediaRecorder.onstop = submitAudio;
        
        // Record the start time for latency calculation
        recordStart = Date.now();
        
        // Start the recording
        mediaRecorder.start();
        
        // Update UI to show recording in progress
        statusIcon.textContent = "⏺";
        startBtn.textContent = "Stop Recording";
        startBtn.onclick = () => mediaRecorder.stop();
    } catch (error) {
        console.error("Error starting recording:", error);
        alert("Microphone access denied or error: " + error.message);
        challengeText.textContent = "Please allow microphone access";
    }
}

/**
 * Submit recorded audio to backend for verification
 */
async function submitAudio() {
    try {
        // Calculate response latency in milliseconds
        const latency = Date.now() - recordStart;
        
        // Create audio blob from recorded chunks
        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
        
        console.log("Submitting audio, latency:", latency, "ms");
        
        // Prepare form data for multipart upload
        const formData = new FormData();
        formData.append("audio", audioBlob, "response.wav");
        formData.append("challenge_id", challengeId);
        formData.append("latency_ms", latency.toString());
        
        // Update UI to show verification in progress
        challengeText.textContent = "Verifying...";
        statusIcon.textContent = "⏳";
        signalPanel.style.display = "block";
        
        // Submit to backend verification endpoint
        const response = await fetch(`${API}/verify`, {
            method: "POST",
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Parse verification result
        const data = await response.json();
        
        console.log("Verification result:", data);
        
        // Display the verification results
        showResult(data, latency);
    } catch (error) {
        console.error("Error submitting audio:", error);
        challengeText.textContent = "Error verifying. Check console.";
        alert("Error during verification: " + error.message);
    }
}

/**
 * Display verification results and update UI accordingly
 * @param {Object} data - Verification result from backend
 * @param {number} latency - Response time in milliseconds
 */
function showResult(data, latency) {
    // Get signal value span elements by ID
    const latencySpan = document.getElementById("sig-latency-value");
    const answerSpan = document.getElementById("sig-answer-value");
    const voiceSpan = document.getElementById("sig-voice-value");
    
    // Display latency with checkmark if in valid range, X if anomalous
    const latencyInRange = latency >= 400 && latency <= 6000;
    latencySpan.textContent = `${latency}ms ${latencyInRange ? "✅" : "❌"}`;
    
    if (data.pass) {
        // All three verification layers passed
        answerSpan.textContent = "Correct ✅";
        voiceSpan.textContent = "Human ✅";
        statusIcon.textContent = "✅";
        resultDiv.innerHTML = '<div class="pass">✅ Human Verified — Proceed</div>';
        
        // Enable submit button to allow form submission
        document.querySelector(".submit-btn").disabled = false;
    } else {
        // Handle different failure reasons
        if (data.reason === "latency_anomaly") {
            // Failed Layer 2: Response timing suspicious
            answerSpan.textContent = "—";
            voiceSpan.textContent = "—";
            resultDiv.innerHTML = '<div class="fail">❌ Failed — Response timing suspicious</div>';
        } else if (data.reason === "wrong_answer") {
            // Failed Layer 1: Incorrect answer
            answerSpan.textContent = "Incorrect ❌";
            voiceSpan.textContent = "—";
            resultDiv.innerHTML = '<div class="fail">❌ Failed — Incorrect answer</div>';
        } else if (data.reason === "synthetic_voice") {
            // Failed Layer 3: Synthetic voice detected
            answerSpan.textContent = "Correct ✅";
            voiceSpan.textContent = "Synthetic ❌";
            statusIcon.textContent = "❌";
            resultDiv.innerHTML = '<div class="fail">❌ Failed — Synthetic voice detected</div>';
        }
        
        // Allow user to try again
        startBtn.textContent = "Try Again";
        startBtn.onclick = loadChallenge;
    }
}

// Initialize the CAPTCHA widget on page load
startBtn.onclick = loadChallenge;

console.log("Voice CAPTCHA initialized. Click 'Verify I'm Human' to start.");
