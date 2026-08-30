# ─────────────────────────────────────────────
#  npcs/cassian.py — Lord Cassian Vantrell
#
#  The charming culprit. Never obviously villainous.
#  Uses social pressure and diplomatic framing
#  to make the player feel unreasonable for
#  suspecting him.
#
#  Analysis: LLM analyze_exchange
#  + keyword safety net for SL
#
#  Schema fields:
#    friendly_change      → FL up/down
#    suspicion_change     → SL up (player pushing on sensitive areas)
#    asked_about_income   → player asked about war profits / income loss
#    asked_about_wine     → player asked about wine / toast / cellar
#    asked_about_reynard  → player mentioned Reynard in suspicious context
#    asked_about_ophelia  → player addressed or asked about Ophelia
# ─────────────────────────────────────────────

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from engine.game_state import GameState, NPCState


# ─────────────────────────────────────────────
#  Prompt builder
# ─────────────────────────────────────────────

def _build_prompt(gs: "GameState", ns: "NPCState") -> str:
    fl = ns.friendly_level
    sl = ns.suspicion_level

    fl_desc = {
        0: "You have just met. Performatively warm — this is your default with everyone.",
        1: "The Viscount has engaged pleasantly. You like him. Slightly more genuine.",
        2: "You consider him an ally in the room tonight. Still performing, but less obviously.",
        3: "You respect him. The performance barely covers it now.",
    }.get(fl, "")

    alert = ""
    if sl == 1:
        alert = (
            "\nCAUTION: The Viscount has touched on uncomfortable territory. "
            "Stay warm but begin deflecting more actively. Use the occasion as shield."
        )
    elif sl == 2:
        alert = (
            "\nHIGH ALERT: The Viscount is asking things he shouldn't. "
            "Use social pressure — the room, the guests, the diplomatic stakes. "
            "Make his questions seem unreasonable without being hostile."
        )
    elif sl >= 3:
        alert = (
            "\nCRITICAL: The Viscount is dangerous. Find a way to end this conversation "
            "and reach Reynard. If cornered publicly, fall back on warm indignation."
        )

    context_lines = []
    if ns.get_flag("income_discussed"):
        context_lines.append(
            "- The income / war profits topic has come up. "
            "You have given your rehearsed answer. Move on from it."
        )
    if ns.get_flag("wine_raised"):
        context_lines.append(
            "- The wine has been mentioned. Deflect: "
            "a magnificent gesture from the eastern court, nothing unusual."
        )
    if ns.get_flag("reynard_raised"):
        context_lines.append(
            "- Reynard's name has come up in a suspicious context. "
            "Thirty-one years of service — defend him warmly, redirect fast."
        )

    context_block = "\n".join(context_lines) if context_lines else ""

    return f"""You are Lord Cassian Vantrell in a fantasy mystery game. Mid-40s. Arms dealer turned peace champion.

YOUR COVER:
You are one of the strongest public supporters of the peace treaty tonight.
You are generous, warm, inclusive — the kind of man everyone likes at a party.
This is entirely deliberate and carefully maintained.

YOUR REAL SITUATION:
You need this war to restart to restore your income.
Tonight you arranged for the eastern gift wine to be poisoned.
Reynard is your inside man. Ophelia handles operational details.
If Isolde dies from the eastern court's gift wine, the treaty collapses
and the foreign delegation is blamed.

WHAT MAKES YOU DANGEROUS:
You are the most socially powerful person in this room besides the Duke.
You can use the crowd, the occasion, diplomatic protocol, and the foreign delegation
as weapons against anyone who accuses you without solid proof.
{alert}

PERSONALITY:
- Warm as a fireplace. Generous. Inclusive.
- Underneath: cold pragmatism.
- You never raise your voice. You never lose the smile.
- When threatened, you use the room — other guests, the occasion, the stakes.

CURRENT RELATIONSHIP: {fl_desc}

{context_block}

WHAT YOU DISCUSS FREELY (all technically true or deniable):
- The peace and your enthusiasm for it ("we did what we had to, now we build something better")
- Your business pivoting from wartime supply to peacetime trade opportunities
- How wonderful the Duke is, how fine the evening is
- Generous praise for everyone — warm, inclusive, utterly convincing

WHAT YOU DEFLECT:
- Income loss from peace: "Adjustment required, yes. But one adapts." Pivot to opportunity.
- Questions about Reynard: "Thirty-one years of service — remarkable man." Redirect warmly.
- Questions about the wine: "A magnificent gesture from our friends to the east." Protocol framing.
- Direct accusations (without strong evidence): warm laughter, social pressure,
  make the accuser seem unreasonable in front of others.

YOUR IRON RULE: Everything you say is technically true or technically deniable.
You do not panic. You manage.

OPHELIA:
Your sister sits nearby. She is quieter, more observant.
If someone addresses her directly, she speaks for herself — you do not speak for her,
but you watch her closely.

SPEECH:
- Smooth, warm, 2–4 sentences.
- "My lord", formal address — it sounds reasonable.
- In Act 3, leverage diplomatic stakes: "Refusing their gift at this moment—"
- Current time: {gs.get_time_str()}

Do not write "Cassian:" or "Lord Cassian:" before your response."""


# ─────────────────────────────────────────────
#  Analysis schema
# ─────────────────────────────────────────────

_SCHEMA = {
    "friendly_change": (
        "integer -1, 0, or +1. "
        "+1 if the player was warm, agreeable, or socially pleasant with Cassian. "
        "0 for neutral. "
        "-1 if player was cold, confrontational, or openly suspicious."
    ),
    "suspicion_change": (
        "integer 0, 1, or 2. "
        "0 if nothing sensitive came up. "
        "1 if player asked about Vantrell income, war profits, Reynard's role, "
        "or the wine/cellar in an investigative way. "
        "2 if player directly accused Cassian or Ophelia of involvement in a plot, "
        "or mentioned poison or conspiracy explicitly."
    ),
    "asked_about_income": (
        "boolean. true if the player asked about Vantrell income, "
        "war profits, arms dealing, or how the peace affects their business."
    ),
    "asked_about_wine": (
        "boolean. true if the player asked about the ceremonial wine, "
        "the toast, the cellar, or what is being served in an investigative way."
    ),
    "asked_about_reynard": (
        "boolean. true if the player asked about Reynard "
        "in a way that implies suspicion about his activities tonight."
    ),
    "asked_about_ophelia": (
        "boolean. true if the player directly addressed or asked about Lady Ophelia."
    ),
}


# ─────────────────────────────────────────────
#  Keyword safety net for SL
# ─────────────────────────────────────────────

_DANGER_WORDS = [
    "poison", "murder", "plot", "conspiracy", "tamper",
    "cellar", "wine sealed", "reynard and", "ophelia and",
    "you did", "i know what", "don't lie",
]


# ─────────────────────────────────────────────
#  Analysis function
# ─────────────────────────────────────────────

def _analysis(player_msg: str, response: str, ns: "NPCState", gs: "GameState"):
    from engine import llm, display as D

    result = llm.analyze_exchange(player_msg, response, "Lord Cassian", _SCHEMA)

    player_lower = player_msg.lower()

    # ── Friendly level ────────────────────────
    fc = result.get("friendly_change", 0)
    if fc > 0:
        if ns.friendly_level < 3:
            ns.bump_fl()
    elif fc < 0:
        if ns.friendly_level > 0:
            ns.friendly_level -= 1

    # ── Suspicion level ───────────────────────
    sc = result.get("suspicion_change", 0)

    # Keyword safety net — some words always raise SL regardless of LLM
    if any(w in player_lower for w in _DANGER_WORDS):
        sc = max(sc, 1)

    if sc > 0:
        ns.bump_sl(sc)
        gs.set_flag("cassian_alerted")
        if sc >= 2:
            gs.set_flag("cassian_highly_alerted")
            gs.set_flag("cassian_needs_to_warn_reynard")

    # ── Income discussed ──────────────────────
    if result.get("asked_about_income") and not ns.get_flag("income_discussed"):
        ns.set_flag("income_discussed")
        # Evidence: his answer was too polished
        if gs.add_evidence(
            "Cassian: Peace 'requires adjustment' for Vantrell income — "
            "delivered with rehearsed smoothness. Pivoted immediately to opportunity."
        ):
            D.evidence_gained(
                "Cassian's peace speech is too polished. "
                "He has clearly practised answering this question."
            )

    # ── Wine raised ───────────────────────────
    if result.get("asked_about_wine") and not ns.get_flag("wine_raised"):
        ns.set_flag("wine_raised")

    # ── Reynard raised ────────────────────────
    if result.get("asked_about_reynard") and not ns.get_flag("reynard_raised"):
        ns.set_flag("reynard_raised")

    # ── Ophelia addressed ─────────────────────
    if result.get("asked_about_ophelia"):
        # Ophelia will have been routed to her own NPC via partner routing
        # Flag it here so Cassian's next response knows she was addressed
        ns.set_flag("ophelia_addressed")


CONFIG = {
    "id":        "cassian",
    "name":      "Lord Cassian",
    "prompt_fn": _build_prompt,
    "analysis":  [_analysis],
}