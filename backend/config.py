import os
from pathlib import Path

from dotenv import load_dotenv


# =========================
# PROJECT PATHS
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================
# ENVIRONMENT
# =========================

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# =========================
# DATABASE
# =========================

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    str(DATA_DIR / "x_radar.db")
)


# =========================
# X COLLECTOR
# =========================

X_HOME_URL = "https://x.com/home"

COLLECT_INTERVAL_SECONDS = int(
    os.getenv(
        "COLLECT_INTERVAL_SECONDS",
        "120"
    )
)

COLLECT_SCROLLS = int(
    os.getenv(
        "COLLECT_SCROLLS",
        "8"
    )
)


# =========================
# OPENAI
# =========================

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    ""
)

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna"
)


# =========================
# TELEGRAM
# =========================

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    ""
)

TELEGRAM_ALLOWED_USER_ID = os.getenv(
    "TELEGRAM_ALLOWED_USER_ID",
    ""
)


# =========================
# SERVER
# =========================

HOST = os.getenv(
    "HOST",
    "0.0.0.0"
)

PORT = int(
    os.getenv(
        "PORT",
        "8000"
    )
)
