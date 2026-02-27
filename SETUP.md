# Quick Setup Guide

## For Your Friend

### Step 1: Create `.env` file
In the root folder (`voice-captcha`), create a file named `.env` (no extension) with:
```
GEMINI_API_KEY=paste_the_key_here
```

### Step 2: Install dependencies
```powershell
# Activate virtual environment (if not already active)
.venv\Scripts\Activate.ps1

# Install/update dependencies
pip install -r backend\requirements.txt
```

### Step 3: Run the server
```powershell
cd backend
uvicorn main:app --reload --port 8000
```

### Step 4: Open the frontend
Open `frontend\index.html` in Chrome

---

## Troubleshooting

### "No module named dotenv"
Run: `pip install python-dotenv`

### "GEMINI_API_KEY not set"
- Check `.env` file exists in the root folder (same level as README.md)
- Check there are no spaces around the `=` sign
- Restart the server after creating `.env`

### "Cannot find .env file"
The `.env` file must be in the project root:
```
voice-captcha/
├── .env          ← HERE
├── README.md
├── backend/
└── frontend/
```
