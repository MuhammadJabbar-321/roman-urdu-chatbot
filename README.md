# Roman Urdu Chatbot (Text + Voice)

Free stack: Groq (LLM + Whisper STT) + edge-tts (free TTS) + FastAPI + plain HTML/JS.

## 1. Get a free Groq API key
Go to https://console.groq.com → sign up → API Keys → create a new key.

## 2. Backend setup
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then paste your Groq key into .env
uvicorn main:app --reload --port 8000
```
Visit http://localhost:8000 — you should see `{"status": "ok", ...}`.

## 3. Frontend
Just open `frontend/index.html` in a browser, or serve it so the microphone
works reliably:
```bash
cd frontend
python -m http.server 5500
```
Then visit http://localhost:5500.

## 4. Use it
- Type in Roman Urdu and hit Send.
- Click the mic button, speak, click again to stop — it transcribes,
  replies, and speaks the reply aloud.

## Notes
- Free Groq limits: roughly 1,000 requests/day and 100K tokens/day on the
  70B model. Fine for personal use and testing.
- edge-tts is free and unofficial (uses Microsoft Edge's cloud voices) —
  reliable for prototyping, not backed by an SLA.
- If mic access fails, make sure you're on `localhost` (not opening the
  HTML file with `file://`) — browsers block microphone access on
  non-secure origins.
