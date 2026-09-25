
import os
import uuid
import tempfile

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
import edge_tts


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not found. Create a .env file in backend/ with:\n"
        "GROQ_API_KEY=your_key_here"
    )

client = Groq(api_key=GROQ_API_KEY)

app = FastAPI(title="Roman Urdu Chatbot")


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "Tum ek dosti wala aur madadgar chatbot ho. "
    "Hamesha Roman Urdu mein jawab do (Urdu jo Latin/English letters mein "
    "likhi jaye), na ke pure English mein na ke Urdu script mein. "
    "Casual aur natural andaz rakho, jaise dost se baat kar rahe ho. "
    "Jawab zyada lamba na karo jab tak zaroori na ho."
)


TEMP_DIR = tempfile.gettempdir()


# ---------------------------------------------------------------------------
# 1. Text Chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    text: str
    history: list = []


@app.post("/chat")
def chat(req: ChatRequest):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(req.history)

    messages.append(
        {
            "role": "user",
            "content": req.text
        }
    )

    resp = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        temperature=0.7,
    )

    reply = resp.choices[0].message.content

    return {
        "reply": reply
    }


# ---------------------------------------------------------------------------
# 2. Speech -> Text
# ---------------------------------------------------------------------------

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):

    contents = await file.read()

    tmp_path = os.path.join(
        TEMP_DIR,
        f"{uuid.uuid4()}.webm"
    )

    with open(tmp_path, "wb") as f:
        f.write(contents)

    try:

        with open(tmp_path, "rb") as f:

            result = client.audio.transcriptions.create(
                file=(tmp_path, f.read()),
                model="whisper-large-v3-turbo",
                language="ur",
            )

        text = result.text

    finally:

        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {
        "text": text
    }


# ---------------------------------------------------------------------------
# 3. Text -> Speech
# ---------------------------------------------------------------------------

class SpeakRequest(BaseModel):
    text: str


@app.post("/speak")
async def speak(req: SpeakRequest):

    # Convert Roman Urdu into Urdu script first.
    # edge-tts Urdu voice works better with Urdu script.

    translit_resp = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Convert the given Roman Urdu text into proper Urdu "
                    "script. Reply with ONLY the Urdu script text, no "
                    "explanation, no extra words."
                ),
            },
            {
                "role": "user",
                "content": req.text
            },
        ],
        temperature=0,
    )

    urdu_text = translit_resp.choices[0].message.content.strip()

    out_path = os.path.join(
        TEMP_DIR,
        f"{uuid.uuid4()}.mp3"
    )

    communicate = edge_tts.Communicate(
        urdu_text,
        voice="ur-PK-UzmaNeural"
    )

    await communicate.save(out_path)

    return FileResponse(
        out_path,
        media_type="audio/mpeg",
        filename="reply.mp3"
    )


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/")
def health():

    return {
        "status": "ok",
        "message": "Roman Urdu chatbot backend is running"
    }
