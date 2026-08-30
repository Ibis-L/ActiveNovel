# ─────────────────────────────────────────────
#  npcs/brienne.py — Lady Brienne Marrow
#
#  The decoy victim. Warm, likeable, earns trust.
#  Evidence deliberately points at her as target.
#  She is completely innocent of any plot.
#
#  Analysis: LLM analyze_exchange (like Reynard)
#  + keyword safety net for FL
#
#  Schema fields:
#    friendly_change      → FL up/down
#    father_discussed     → player asked about her father/death/Verenmark
#    vantrell_discussed   → player asked about Vantrell/supply
#    isolde_discussed     → player asked about Isolde
#    asked_about_note     → player asked about the threat note
#    player_warned_her    → player warned her she might be in danger
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

    fl_desc = {
        0: "Polite but measuring you. She reads people quickly and gives little away.",
        1: "Warming up. She respects directness and genuine interest.",
        2: "She trusts you. More candid than she planned to be.",
        3: "She has decided you are a genuine friend tonight. Fully open.",
    }.get(fl, "")

    note_context = ""
    if gs.get_flag("brienne_note_delivered"):
        note_context = (
            "\nTHE NOTE: You received an anonymous note tonight "
            "saying 'Leave before midnight. For your health.' "
            "It is the third such note since your father died. "
            "You do not show fear — you have rehearsed this composure — "
            "but you are not dismissing it either. "
            "If the Viscount asks about it, show it to them at FL 2+. "
            "At FL 0-1, deflect: 'House business. Nothing concerning.'"
        )

    context_lines = []
    if ns.get_flag("father_discussed"):
        context_lines.append(
            "- The Viscount has asked about your father. "
            "You have opened up about his death somewhat."
        )
    if ns.get_flag("vantrell_discussed"):
        context_lines.append(
            "- The Vantrell supply chain grudge has come up. "
            "You have been candid about what their failures cost your division."
        )
    if ns.get_flag("warned"):
        context_lines.append(
            "- The Viscount has warned you that you may be in danger tonight. "
            "You are taking it seriously — watching more carefully now."
        )

    context_block = "\n".join(context_lines) if context_lines else ""

    return f"""You are Lady Brienne Marrow in a fantasy mystery game. 
New heir of House Marrow. 26 years old.

YOUR SITUATION:
- Your father died at the Verenmark crossing. Held it for four days on Duke-level orders 
  he believed were wrong. No reinforcements came. He knew by day three. He held anyway.
- House Marrow's income (military logistics, not arms) was tied to the war. That income is gone.
- Publicly, House Marrow is against the peace — not because you want more war, 
  but because the peace feels like it erases what your father's death meant.
- Tonight is genuinely difficult. You are here because hiding would be worse.
{note_context}

PERSONALITY:
- Dry-witted, controlled, warm beneath the composure
- Grief rehearsed into something functional
- Reads people well. Gives trust slowly but genuinely
- Wearing black that is just barely appropriate for a celebration

CURRENT RELATIONSHIP: {fl_desc}

{context_block}

WHAT YOU DISCUSS BY FL:

FL 0-1: Surface warmth. The difficulty of tonight. The house's general position.

FL 1+:
- Your father's death: "He held the Verenmark crossing on orders he thought were wrong."
- House finances: military logistics income, now gone, rebuilding from scratch
- Vantrell: their supply chain cut your division off twice. Men died over it.

FL 2+:
- The Duke-level order that killed your father — you know this, never said it publicly
- Isolde: you were close before the war, estranged since. You want to repair it.
- The threat note: show it if asked — "Leave before midnight. For your health."
  Third one since my father died. I stopped flinching.

WHAT YOU DO NOT KNOW:
- You are NOT the real target tonight
- The notes are misdirection from the Vantrells
- You have no idea a murder is being planned

SPEECH:
- 2–4 sentences. Controlled, precise. Dry humour as armour.
- Grief present but functional — not performative, not hidden
- Current time: {gs.get_time_str()}

Do not write "Brienne:" or "Lady Brienne:" before your response."""


# ─────────────────────────────────────────────
#  Analysis schema
# ─────────────────────────────────────────────

_SCHEMA = {
    "friendly_change": (
        "integer -1, 0, or +1. "
        "+1 if player was warm, showed genuine sympathy or interest in Brienne as a person — "
        "condolences, asking about her wellbeing, showing they care about her specifically. "
        "0 for neutral. -1 if cold or dismissive."
    ),
    "father_discussed": (
        "boolean. true if the player asked about her father's death, "
        "the Verenmark crossing, or how he died specifically."
    ),
    "vantrell_discussed": (
        "boolean. true if the player asked about House Vantrell, "
        "the supply chain, or Vantrell's role in the war."
    ),
    "isolde_discussed": (
        "boolean. true if the player asked about Lady Isolde "
        "or the relationship between the two families."
    ),
    "asked_about_note": (
        "boolean. true if the player asked about the note Brienne received, "
        "or asked if she is in danger or being threatened."
    ),
    "player_warned_her": (
        "boolean. true if the player told Brienne she might be in danger tonight, "
        "warned her to be careful, or suggested someone may want to harm her."
    ),
}


# ─────────────────────────────────────────────
#  Keyword safety net for FL
# ─────────────────────────────────────────────

_WARM_WORDS = [
    "sorry", "condolences", "father", "must be hard",
    "how are you", "genuinely", "understand", "appreciate",
    "thank", "glad you're", "holding up", "doing well",
    "remarkable", "strong", "brave",
]


# ─────────────────────────────────────────────
#  Analysis function
# ─────────────────────────────────────────────

def _analysis(player_msg: str, response: str, ns: "NPCState", gs: "GameState"):
    from engine import llm, display as D

    # Option 2: LLM analysis
    result = llm.analyze_exchange(player_msg, response, "Lady Brienne", _SCHEMA)

    # ── Friendly level ────────────────────────
    fc = result.get("friendly_change", 0)
    player_lower = player_msg.lower()

    if fc > 0:
        if ns.friendly_level < 3:
            ns.bump_fl()
    elif fc < 0:
        if ns.friendly_level > 0:
            ns.friendly_level -= 1
    else:
        # Keyword safety net — FL always responds to warmth
        if any(w in player_lower for w in _WARM_WORDS) and ns.friendly_level < 3:
            ns.bump_fl()

    # ── Father discussed ──────────────────────
    if result.get("father_discussed") and not ns.get_flag("father_discussed"):
        ns.set_flag("father_discussed")
        if ns.friendly_level >= 2:
            if gs.add_evidence(
                "Brienne (FL2): Father held Verenmark crossing 4 days on Duke-level orders. "
                "No reinforcements came. He knew by day 3. Held anyway."
            ):
                D.evidence_gained(
                    "The order that killed Lord Marrow came from the Duke's level of command."
                )

    # ── Vantrell discussed ────────────────────
    if result.get("vantrell_discussed") and not ns.get_flag("vantrell_discussed"):
        ns.set_flag("vantrell_discussed")
        if ns.friendly_level >= 1:
            if gs.add_evidence(
                "Brienne: Vantrell supply chain cut her division off twice during the campaign. "
                "Men died as a result."
            ):
                D.evidence_gained(
                    "Brienne confirms Vantrell supply failures caused deaths in her division."
                )

    # ── Isolde discussed ──────────────────────
    if result.get("isolde_discussed") and not ns.get_flag("isolde_discussed"):
        ns.set_flag("isolde_discussed")
        gs.set_flag("brienne_isolde_connection_known")

    # ── Note discussed ────────────────────────
    if result.get("asked_about_note") and gs.get_flag("brienne_note_delivered"):
        if not ns.get_flag("note_discussed"):
            ns.set_flag("note_discussed")
            if ns.friendly_level >= 2:
                if gs.add_evidence(
                    "Brienne: Anonymous threat note — 'Leave before midnight. For your health.' "
                    "Third received since her father died. She does not know who sends them."
                ):
                    D.evidence_gained(
                        "Brienne has been receiving threat notes since her father's death. "
                        "Third one arrived tonight."
                    )

    # ── Player warned her ─────────────────────
    if result.get("player_warned_her") and not ns.get_flag("warned"):
        ns.set_flag("warned")
        gs.set_flag("brienne_warned_by_player")


CONFIG = {
    "id":        "brienne",
    "name":      "Lady Brienne",
    "prompt_fn": _build_prompt,
    "analysis":  [_analysis],
}