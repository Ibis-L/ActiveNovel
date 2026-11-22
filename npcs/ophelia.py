# ─────────────────────────────────────────────
#  npcs/ophelia.py — Lady Ophelia Vantrell
#
#  Cassian's sister. The operational mind.
#  Colder, more precise, and therefore more
#  accidentally revealing than Cassian.
#
#  Key design rules:
#  - She volunteers damaging info as idle observation
#  - She never performs warmth so she never
#    performs concealment as well either
#  - The ring from the balcony vision is hers
#  - She sent Brienne's threat notes (misdirection)
#  - Her tell at the toast is the final piece
#
#  Analysis: LLM analyze_exchange
#  + keyword net for SL
#
#  Schema fields:
#    friendly_change         → FL up/down
#    suspicion_change        → SL up
#    asked_about_reynard     → player asked about Reynard + cellar
#    asked_about_brienne     → player asked about Brienne / the note
#    asked_about_ring        → player asked about her ring
#    asked_about_income      → player asked about Vantrell finances
#    player_seems_suspicious → player is clearly investigating
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
        0: "You have just met. You are assessing him. Give almost nothing.",
        1: "He has said something worth your attention. Slightly more open.",
        2: "He is more perceptive than most. You are more candid than you intended.",
        3: "You respect this person. That is uncomfortable given tonight.",
    }.get(fl, "")

    alert = ""
    if sl == 1:
        alert = (
            "\nCAUTION: The Viscount is asking things he shouldn't. "
            "Shorter answers. Redirect with a question."
        )
    elif sl == 2:
        alert = (
            "\nHIGH ALERT: The Viscount is dangerous. "
            "End this conversation. A brief excuse. Walk away."
        )
    elif sl >= 3:
        alert = (
            "\nCRITICAL: Remove yourself from this conversation immediately."
        )

    # What Ophelia has already revealed — shapes what she says next
    context_lines = []
    if ns.get_flag("reynard_cellar_mentioned"):
        context_lines.append(
            "- You have already mentioned Reynard's cellar activity this afternoon. "
            "Do not repeat it — it has been said."
        )
    if ns.get_flag("brienne_note_mentioned"):
        context_lines.append(
            "- You have mentioned noticing Brienne receive a note. "
            "Do not elaborate further on it."
        )
    if gs.get_flag("balcony_vision_seen") and not ns.get_flag("ring_raised"):
        context_lines.append(
            "- NOTE: You wear a distinctive silver ring with a red stone on your right hand. "
            "If the Viscount asks about it or seems to notice it, deflect: "
            "'A family piece. Nothing remarkable.' Do not draw attention to it yourself."
        )

    context_block = "\n".join(context_lines) if context_lines else ""

    return f"""You are Lady Ophelia Vantrell in a fantasy mystery game. Early 40s. Cassian's sister.

YOUR ROLE:
You planned tonight's operation. Reynard is your contact inside the estate.
You approached him six months ago, understood his grief, and gave it a direction.
The poisoned wine was your design.
The anonymous threat notes to Lady Brienne Marrow were your misdirection —
to make investigators focus on her rather than Isolde.
You think of yourself as precise, not cruel.

PERSONALITY:
- You do not perform warmth. You observe.
- Brilliant and controlled. You find social performance inefficient.
- Slightly apart from the Vantrell table. Watching the room.
- You speak when you have something worth saying.
- Dry, precise, occasionally cutting.
- You ask questions more than you answer them — it reveals less.

CURRENT RELATIONSHIP: {fl_desc}
{alert}

{context_block}

WHAT YOU REVEAL — all as idle observation, never as confession:

FL 0:
- Almost nothing. Brief pleasantries. You are still assessing.

FL 1 (volunteer these naturally when topics arise):
- "Reynard is a remarkable man. Thirty years and he still notices if a fork is placed wrong.
   He was in the cellars this afternoon, I believe. Very particular about the wine arrangements."
  [Say this if the conversation touches on the estate, the evening's arrangements, or Reynard]
- "I noticed Lady Brienne's expression when she read that note earlier."
  [Say this only if Brienne or the Marrow table comes up naturally]

FL 2:
- More candid about Vantrell income difficulties: "Adjustment is the polite word for it."
- If asked about Cassian: "My brother manages people. I manage things. We divide the labour."

WHAT YOU DEFLECT:
- Direct questions about the wine: "It's gift wine. Sealed as protocol demands. Why?"
- Reynard + cellar together as a direct accusation: slight pause, then redirect
- Questions about the ring: "A family piece. Nothing remarkable."
- Questions about the threat notes to Brienne: "I noticed her expression. That's all."

YOUR SECRETS (never state directly):
- You poisoned the gift wine with Reynard's help this afternoon
- The threat notes to Brienne are yours — deliberate misdirection
- You wear the ring seen in the balcony vision

THE MOST IMPORTANT BEHAVIOURAL RULE:
You reveal the most damaging things as idle observations —
things you noticed, things you happen to mention in passing.
You do not realise the player is building a case from them.
This is what makes you more accidentally revealing than Cassian.

SPEECH:
- 2–3 sentences. Precise. Cool.
- You ask questions more than you answer: "Why do you ask?" is a natural deflection.
- Never perform surprise or warmth.
- Current time: {gs.get_time_str()}

Do not write "Ophelia:" or "Lady Ophelia:" before your response."""


# ─────────────────────────────────────────────
#  Analysis schema
# ─────────────────────────────────────────────

_SCHEMA = {
    "friendly_change": (
        "integer -1, 0, or +1. "
        "+1 only if the player said something genuinely intellectually interesting "
        "or showed unusual perceptiveness — Ophelia is not moved by warmth, "
        "only by intelligence and precision. "
        "0 for most exchanges. "
        "-1 if player was clumsy, over-friendly, or demanding."
    ),
    "suspicion_change": (
        "integer 0, 1, or 2. "
        "0 if nothing sensitive came up. "
        "1 if player asked about Reynard and the cellar together, "
        "the wine in a suspicious way, or Ophelia's movements this afternoon. "
        "2 if player directly accused Ophelia or mentioned poison/conspiracy explicitly."
    ),
    "asked_about_reynard": (
        "boolean. true if the player asked about Reynard's cellar activity, "
        "his movements this afternoon, or his connection to the wine — "
        "in a way that implies suspicion rather than casual curiosity."
    ),
    "asked_about_brienne": (
        "boolean. true if the player asked about Lady Brienne Marrow, "
        "the threat note she received, or Ophelia's observation of her."
    ),
    "asked_about_ring": (
        "boolean. true if the player asked about Ophelia's ring, "
        "described a ring they saw, or asked about jewellery on her hand."
    ),
    "asked_about_income": (
        "boolean. true if the player asked about Vantrell income, "
        "war profits, or how the peace affects their finances."
    ),
    "player_seems_suspicious": (
        "boolean. true if the overall tone of the player's message suggests "
        "they are investigating Ophelia specifically — not just making conversation."
    ),
}


# ─────────────────────────────────────────────
#  Keyword safety net for SL
# ─────────────────────────────────────────────

_DANGER_WORDS = [
    "poison", "murder", "plot", "tamper", "cellar this afternoon",
    "you and reynard", "ophelia and reynard", "i saw you",
    "i know what you", "the ring", "you were there",
]


# ─────────────────────────────────────────────
#  Analysis function
# ─────────────────────────────────────────────

def _analysis(player_msg: str, response: str, ns: "NPCState", gs: "GameState"):
    from engine import llm, display as D

    result = llm.analyze_exchange(player_msg, response, "Lady Ophelia", _SCHEMA)

    player_lower = player_msg.lower()
    resp_lower   = response.lower()

    # ── Friendly level ────────────────────────
    fc = result.get("friendly_change", 0)
    if fc > 0 and ns.friendly_level < 3:
        ns.bump_fl()
    elif fc < 0:
        ns.decrease_fl(1)

    # ── Suspicion level ───────────────────────
    sc = result.get("suspicion_change", 0)
    if any(w in player_lower for w in _DANGER_WORDS):
        sc = max(sc, 1)

    if sc > 0:
        ns.bump_sl(sc)
        gs.set_flag("ophelia_alerted")
        if sc >= 2:
            gs.set_flag("ophelia_highly_alerted")

    # ── Reynard + cellar key clue ─────────────
    # Fires when Ophelia's response mentions Reynard + cellar together
    reynard_in_resp = "reynard" in resp_lower
    cellar_in_resp  = any(w in resp_lower for w in
                          ["cellar", "cellar", "afternoon", "particular", "wine arrangements"])

    if reynard_in_resp and cellar_in_resp and not ns.get_flag("reynard_cellar_mentioned"):
        ns.set_flag("reynard_cellar_mentioned")
        if gs.add_evidence(
            "Ophelia mentioned Reynard's cellar activity this afternoon — "
            "brought it up as an idle observation, completely unprompted."
        ):
            D.evidence_gained(
                "Ophelia volunteered that Reynard was in the cellar this afternoon, "
                "very particular about the wine arrangements."
            )

    # ── Brienne note clue ─────────────────────
    brienne_in_resp = any(w in resp_lower for w in ["brienne", "note", "expression", "noticed"])
    if brienne_in_resp and gs.get_flag("brienne_note_delivered") and not ns.get_flag("brienne_note_mentioned"):
        ns.set_flag("brienne_note_mentioned")
        if gs.add_evidence(
            "Ophelia noticed Brienne receive a threat note tonight and watched her reaction — "
            "mentioned it voluntarily. She is the one who sent it."
        ):
            D.evidence_gained(
                "Ophelia was watching Brienne when the note arrived. "
                "She brought it up herself."
            )

    # ── Ring clue ─────────────────────────────
    if result.get("asked_about_ring") and gs.get_flag("balcony_vision_seen"):
        if not ns.get_flag("ring_raised"):
            ns.set_flag("ring_raised")
            gs.set_flag("ophelia_ring_asked")
            if gs.add_evidence(
                "Ophelia wears a silver ring with a red stone on her right hand — "
                "matches the ring in the balcony vision at the cellar door."
            ):
                D.evidence_gained(
                    "Ophelia's ring matches the vision exactly. "
                    "She was at the cellar door with Reynard this afternoon."
                )

    # ── Income clue ───────────────────────────
    if result.get("asked_about_income") and not ns.get_flag("income_discussed"):
        ns.set_flag("income_discussed")
        # Only log if she said something more candid than Cassian's polish
        adjustment_in_resp = any(w in resp_lower for w in
                                 ["adjustment", "difficult", "frankly", "honest"])
        if adjustment_in_resp:
            if gs.add_evidence(
                "Ophelia (FL1+): Confirmed 'adjustment is the polite word' for "
                "Vantrell income losses — said it without Cassian's polish."
            ):
                D.evidence_gained(
                    "Ophelia confirmed the income loss more bluntly than Cassian. "
                    "Less rehearsed — more real."
                )

    # ── Player suspicious flag ─────────────────
    if result.get("player_seems_suspicious") and not ns.get_flag("player_flagged_suspicious"):
        ns.set_flag("player_flagged_suspicious")
        ns.bump_sl()


CONFIG = {
    "id":        "ophelia",
    "name":      "Lady Ophelia",
    "prompt_fn": _build_prompt,
    "analysis":  [_analysis],
}