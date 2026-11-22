# ─────────────────────────────────────────────
#  engine/llm.py
#  Three functions:
#    chat()                  → NPC dialogue, natural prose
#    analyze_exchange()      → intent analysis, returns JSON dict
#    analyze_confrontation() → Act 3 Game Master analyzer
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


# ─────────────────────────────────────────────
#  Act 3 "Game Master" Confrontation Analyzer
#  Reads player's free-text during the climax
#  and extracts what evidence they are citing
#  and what actions they are attempting.
# ─────────────────────────────────────────────

_CONFRONTATION_SYSTEM = """You are a game-master analyser for a text-based mystery game called "The Viscount's Vigil".
The player is in the climax — a public confrontation at a peace treaty signing where they must stop a poisoned toast.
Read the player's message and return a JSON object.

EVIDENCE MAP (these are the real clues that can exist in the game):
  "wine_seal"      — player mentions the wine seal was tampered with / resealed
  "cellar_staff"   — player mentions the cellar staff being made ill / removed
  "cellar_log"     — player mentions the cellar log / bottles were moved by Reynard
  "ophelia_cellar" — player names Ophelia Vantrell + Reynard + cellar together
  "vision"         — player cites their personal prophetic vision/dream as reason
  "illness"        — player mentions cellar staff fell mysteriously ill
  "vantrell_income"— player accuses Vantrells of needing the war / income motive
  "kitchen_orders" — player mentions Reynard ordered wine kept from the kitchen

ACTIONS:
  "physical_intercept" — player physically moves to block Isolde from drinking (e.g. "I step between", "I grab the glass", "I move to her")
  "drink_sacrifice"    — player drinks the wine themselves to save Isolde

Rules:
- Return ONLY valid JSON. No explanation, no markdown.
- evidence_cited: array of strings from the EVIDENCE MAP above (only clues explicitly mentioned or clearly implied)
- action: one of "physical_intercept", "drink_sacrifice", or null
- persuasion_strength: integer 0-3 (0=rambling/vague, 1=weak/general, 2=clear argument, 3=compelling/specific)
- targets_reynard: boolean — player is directly naming/accusing Reynard by name
- targets_vantrell: boolean — player is directly naming/accusing the Vantrells by name"""

_CONFRONTATION_SCHEMA = """{
  "evidence_cited": ["array of clue keys from evidence map, empty if none"],
  "action": "physical_intercept | drink_sacrifice | null",
  "persuasion_strength": "integer 0-3",
  "targets_reynard": "boolean",
  "targets_vantrell": "boolean"
}"""


def analyze_confrontation(player_msg: str, evidence_log: list) -> dict:
    """
    Act 3 Game Master analysis.

    Reads the player's free-text confrontation message.
    Cross-references evidence_cited against the actual evidence_log
    to verify the player legitimately discovered those clues.

    Returns:
        verified_evidence  : list[str] — clues cited AND confirmed in log
        phantom_evidence   : list[str] — clues cited but NOT in log (bluffing)
        action             : str | None
        persuasion_strength: int 0-3
        targets_reynard    : bool
        targets_vantrell   : bool
    """
    prompt = (
        f'Player said during the climax confrontation: "{player_msg}"\n\n'
        f"Return JSON:\n{_CONFRONTATION_SCHEMA}"
    )

    raw = chat(
        system_prompt=_CONFRONTATION_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )

    parsed: dict = {}
    if not raw.startswith("[ERROR"):
        try:
            clean = raw.strip()
            if "```" in clean:
                parts = clean.split("```")
                clean = parts[1] if len(parts) > 1 else parts[0]
                if clean.startswith("json"):
                    clean = clean[4:]
            parsed = json.loads(clean.strip())
        except (json.JSONDecodeError, IndexError, ValueError):
            parsed = {}

    cited    = parsed.get("evidence_cited", [])
    ev_text  = "\n".join(evidence_log).lower()

    # Cross-reference: which cited clues are actually in the player's log?
    # Each key has a set of terms that must appear in the evidence log.
    _VERIFY = {
        "wine_seal":       ["wine seal", "resealed", "reapplied"],
        "cellar_staff":    ["cellar staff", "fell ill", "suddenly ill", "incapacitated"],
        "cellar_log":      ["cellar log", "repositioned", "moved those bottles", "moved wine"],
        "ophelia_cellar":  ["ophelia"],
        "vision":          ["vision", "balcony"],
        "illness":         ["ill", "incapacitated", "sick"],
        "vantrell_income": ["vantrell", "income", "war profit", "supply"],
        "kitchen_orders":  ["kitchen", "sealed", "kept away"],
    }

    verified = []
    phantom  = []
    for clue in cited:
        terms = _VERIFY.get(clue, [])
        if any(t in ev_text for t in terms):
            verified.append(clue)
        else:
            phantom.append(clue)

    return {
        "verified_evidence":   verified,
        "phantom_evidence":    phantom,
        "action":              parsed.get("action"),
        "persuasion_strength": parsed.get("persuasion_strength", 0),
        "targets_reynard":     parsed.get("targets_reynard", False),
        "targets_vantrell":    parsed.get("targets_vantrell", False),
    }


def _ollama(system: str, messages: list, temperature: float) -> str:
    payload = {
        "model": config.OLLAMA_MODEL,
        "messages": [{"role": "system", "content": system}] + messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": 500},
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
        "max_tokens": 500,
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