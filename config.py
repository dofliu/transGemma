"""
Centralized configuration management.
Loads from environment variables and .env file with sensible defaults.
"""

import os
from pathlib import Path

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ── Paths ──
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = Path(os.getenv("TG_TEMP_DIR", str(BASE_DIR / "temp")))
DB_PATH = Path(os.getenv("TG_DB_PATH", str(BASE_DIR / "history.db")))
LOG_DIR = Path(os.getenv("TG_LOG_DIR", str(BASE_DIR / "logs")))

TEMP_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── Ollama / Model ──
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("TG_OLLAMA_MODEL", "translategemma")
OLLAMA_MEETING_MODEL = os.getenv("TG_OLLAMA_MEETING_MODEL", "qwen3:4b")

# ── Gemini (optional cloud backend) ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Server ──
API_HOST = os.getenv("TG_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("TG_API_PORT", "8000"))
GRADIO_HOST = os.getenv("TG_GRADIO_HOST", "0.0.0.0")
GRADIO_PORT = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

# ── Logging ──
LOG_LEVEL = os.getenv("TG_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv(
    "TG_LOG_FORMAT",
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
LOG_TO_FILE = os.getenv("TG_LOG_TO_FILE", "true").lower() in ("true", "1", "yes")
LOG_FILE = LOG_DIR / "transgemma.log"

# ── Feature Flags ──
ENABLE_TTS = os.getenv("TG_ENABLE_TTS", "true").lower() in ("true", "1", "yes")
ENABLE_VIDEO = os.getenv("TG_ENABLE_VIDEO", "true").lower() in ("true", "1", "yes")
ENABLE_MEETING = os.getenv("TG_ENABLE_MEETING", "true").lower() in ("true", "1", "yes")

# ── Limits ──
MAX_TEXT_LENGTH = int(os.getenv("TG_MAX_TEXT_LENGTH", "50000"))
MAX_UPLOAD_MB = int(os.getenv("TG_MAX_UPLOAD_MB", "150"))
MAX_BATCH_SIZE = int(os.getenv("TG_MAX_BATCH_SIZE", "50"))
