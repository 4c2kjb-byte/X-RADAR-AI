import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .ai import ask_ai
from .collector import collector_loop
from .database import (
    get_recent_posts,
    init_db,
    save_chat_message,
)
from .telegram_bot import telegram_loop


# =========================
# PATHS
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"


# =========================
# REQUEST MODEL
# =========================

class AskRequest(BaseModel):

    question: str


# =========================
# BACKGROUND TASKS
# =========================

collector_task = None

telegram_task = None


# =========================
# STARTUP / SHUTDOWN
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):

    global collector_task
    global telegram_task


    # -------------------------
    # Initialize database
    # -------------------------

    init_db()


    # -------------------------
    # Start X collector
    # -------------------------

    collector_task = asyncio.create_task(
        collector_loop()
    )


    # -------------------------
    # Start Telegram bot
    # -------------------------

    telegram_task = asyncio.create_task(
        telegram_loop()
    )


    print()
    print("=" * 60)
    print("X RADAR AI")
    print("=" * 60)
    print("Server started.")
    print("Collector started.")
    print("Telegram bot started.")
    print("=" * 60)
    print()


    yield


    # -------------------------
    # Shutdown
    # -------------------------

    tasks = [
        collector_task,
        telegram_task,
    ]


    for task in tasks:

        if task:

            task.cancel()


    await asyncio.gather(
        *[
            task
            for task in tasks
            if task
        ],
        return_exceptions=True
    )


# =========================
# FASTAPI APP
# =========================

app = FastAPI(
    title="X Radar AI",
    description=(
        "AI assistant for analyzing "
        "the user's X For You feed."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# =========================
# HEALTH
# =========================

@app.get("/api/health")
async def health():

    return {
        "status": "ok",
        "service": "x-radar-ai"
    }


# =========================
# POSTS
# =========================

@app.get("/api/posts")
async def posts():

    data = get_recent_posts(
        limit=150
    )

    return {
        "count": len(data),
        "posts": data
    }


# =========================
# ASK AI
# =========================

@app.post("/api/ask")
async def ask(request: AskRequest):

    question = request.question.strip()


    if not question:

        return {
            "answer": "اكتب سؤالك أولًا."
        }


    # -------------------------
    # Get posts
    # -------------------------

    posts = get_recent_posts(
        limit=150
    )


    # -------------------------
    # Save question
    # -------------------------

    from datetime import datetime, timezone

    now = datetime.now(
        timezone.utc
    ).isoformat()


    save_chat_message(
        role="user",
        content=question,
        created_at=now
    )


    # -------------------------
    # Ask AI
    # -------------------------

    answer = await ask_ai(
        question=question,
        posts=posts
    )


    # -------------------------
    # Save answer
    # -------------------------

    save_chat_message(
        role="assistant",
        content=answer,
        created_at=datetime.now(
            timezone.utc
        ).isoformat()
    )


    return {
        "answer": answer
    }


# =========================
# FRONTEND
# =========================

@app.get("/")
async def frontend():

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


@app.get("/style.css")
async def stylesheet():

    return FileResponse(
        FRONTEND_DIR / "style.css"
    )


@app.get("/script.js")
async def javascript():

    return FileResponse(
        FRONTEND_DIR / "script.js"
    )
