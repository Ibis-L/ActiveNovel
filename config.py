# ─────────────────────────────────────────────
#  THE VISCOUNT'S VIGIL — Configuration
# ─────────────────────────────────────────────

import os

# Load .env file if present
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.isfile(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip("'\""))

# LLM PROVIDER — choose one:
#   "ollama"  → free, local, needs `ollama serve` running
#   "groq"    → free tier (needs API key at https://console.groq.com)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq")

# Ollama settings
OLLAMA_URL   = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")          # or "mistral", "phi3", "gemma2:2b"

# Groq settings (only used if LLM_PROVIDER = "groq")
# Set your API key in .env or as an environment variable GROQ_API_KEY
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

# Paths
SAVE_FILE    = "data/saves/game_state.json"

# Display
TYPING_DELAY = True                # False = instant text (faster for testing)

# Debug: prints raw LLM prompts/responses
DEBUG_MODE   = True
