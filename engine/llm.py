# ─────────────────────────────────────────────
#  engine/llm.py
#  Two functions:
#    chat()             → NPC dialogue, natural prose
#    analyze_exchange() → intent analysis, returns JSON dict
# ─────────────────────────────────────────────

from __future__ import annotations
import json
import requests
import config


def chat(system_prompt: str, messages: list, temperature: float = 0.75) -> str:
    if config.LLM_PROVIDER == "ollama":
        return _ollama(system_prompt, messages, temperature)
    elif config.LLM_PROVIDER == "groq":
        return _groq(system_prompt, messages, temperature)
    return f"[ERROR: Unknown provider '{config.LLM_PROVIDER}']"


_ANALYSIS_SYSTEM = """You are a game state analyser for a text-based mystery game.
Read a single conversation exchange and return a JSON object describing
the player's intent and any state changes that should result.

Rules:
- Return ONLY valid JSON. No explanation, no markdown, no extra text.
- Judge INTENT, not surface keywords.
  "what is your dream?" → the player is asking about the NPC, NOT revealing their own dream.
  "I had a vision of someone dying" → the player IS disclosing a personal vision.
  "how long have you served?" → warm, rapport-building.
  "tell me about the wine" → curious, but not yet suspicious unless context suggests it.
- When genuinely unsure, use 0 or false rather than guessing."""


def analyze_exchange(
    player_msg: str,
    npc_response: str,
    npc_name: str,
    schema: dict,
) -> dict:
    """
    Analyse a conversation exchange and return structured state updates.

    schema: {field_name: plain-English description of what this field means}
    Returns: dict matching schema keys, or {} on any failure.
    Callers must handle {} as "no state change this turn".
    """
    schema_lines = "\n".join(f'  "{k}": {v}' for k, v in schema.items())
    prompt = (
        f"NPC: {npc_name}\n"
        f'Player said: "{player_msg}"\n'
        f'{npc_name} replied: "{npc_response}"\n\n'
        f"Return JSON with exactly these fields:\n"
        f"{{\n{schema_lines}\n}}"
    )

    raw = chat(
        system_prompt=_ANALYSIS_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )

    if raw.startswith("[ERROR"):
        return {}

    try:
        clean = raw.strip()
        if "```" in clean:
            parts = clean.split("```")
            clean = parts[1] if len(parts) > 1 else parts[0]
            if clean.startswith("json"):
                clean = clean[4:]
        return json.loads(clean.strip())
    except (json.JSONDecodeError, IndexError, ValueError):
        return {}


def _ollama(system: str, messages: list, temperature: float) -> str:
    payload = {
        "model": config.OLLAMA_MODEL,
        "messages": [{"role": "system", "content": system}] + messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": 300},
    }
    try:
        r = requests.post(f"{config.OLLAMA_URL}/api/chat", json=payload, timeout=90)
        r.raise_for_status()
        return r.json()["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        return f"[ERROR: Cannot reach Ollama. Run: ollama serve && ollama pull {config.OLLAMA_MODEL}]"
    except requests.exceptions.Timeout:
        return "[ERROR: Ollama timed out.]"
    except Exception as e:
        return f"[ERROR: Ollama — {e}]"


def _groq(system: str, messages: list, temperature: float) -> str:
    if not config.GROQ_API_KEY:
        return "[ERROR: GROQ_API_KEY not set.]"
    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.GROQ_MODEL,
        "messages": [{"role": "system", "content": system}] + messages,
        "temperature": temperature,
        "max_tokens": 300,
    }
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=payload, timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError:
        if r.status_code == 401: return "[ERROR: Groq API key invalid.]"
        if r.status_code == 429: return "[ERROR: Groq rate limit — wait a moment.]"
        return f"[ERROR: Groq HTTP {r.status_code}]"
    except Exception as e:
        return f"[ERROR: Groq — {e}]"