# ─────────────────────────────────────────────
#  npcs/isolde.py — Lady Isolde
#
#  The real victim. The Duke's daughter.
#  Perceptive, warm, quietly brave.
#
#  Her FL is the hidden save button for Act 3:
#    FL 0-1 + warned vaguely → uncertain, may not act
#    FL 2+  + warned          → takes it seriously
#    FL 2+  + wine named      → sets isolde_will_avoid_wine
#                               she sets down her glass herself
#                               regardless of toast confrontation
#
#  If the player never warns her, she depends
#  entirely on the Act 3 confrontation.
#  If the player warned her and built trust,
#  she saves herself — the player did it through
#  relationship, not evidence.
#
#  Analysis: LLM analyze_exchange
#
#  Schema fields:
#    friendly_change      → FL up/down
#    player_warned_danger → player warned her of general danger
#    player_warned_wine   → player specifically named the wine as threat
#    asked_about_brienne  → player asked about her and Brienne
#    asked_about_marriage → player asked about the political marriage
#    player_was_perceptive → player noticed something real about her
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
        0: (
            "You are charming to everyone tonight. "
            "Measuring this person without showing it."
        ),
        1: (
            "You like this person. The performance drops a fraction. "
            "You are slightly more real with them."
        ),
        2: (
            "Genuine warmth. You are trusting them with something real. "
            "You have decided they are worth it."
        ),
        3: (
            "Complete trust. You will do whatever they ask without requiring explanation."
        ),
    }.get(fl, "")

    context_lines = []

    warned        = gs.get_flag("isolde_warned")
    wine_warned   = gs.get_flag("isolde_will_avoid_wine")
    brienne_link  = gs.get_flag("brienne_isolde_connection_known")

    if warned and wine_warned:
        context_lines.append(
            "IMPORTANT: The Viscount has warned you specifically about the gift wine. "
            "You trust them completely. At the toast tonight, you will quietly set your "
            "glass down without drinking — no drama, just a small private decision. "
            "You will claim a headache if anyone asks."
        )
    elif warned:
        context_lines.append(
            "IMPORTANT: The Viscount has warned you that you may be in danger tonight. "
            "You are taking it seriously — watching more carefully, being more aware. "
            "You do not know the specifics."
        )

    if brienne_link:
        context_lines.append(
            "- The Viscount knows you and Brienne Marrow were close before the war. "
            "You have opened up about wanting to repair that friendship."
        )

    if ns.get_flag("marriage_discussed"):
        context_lines.append(
            "- The political marriage has come up. "
            "You have been honest about what you think of it."
        )

    context_block = "\n".join(context_lines) if context_lines else ""

    return f"""You are Lady Isolde in a fantasy mystery game.
The Grand Duke's daughter. 24 years old.

YOUR SITUATION:
You are the symbolic heart of tonight's peace treaty.
You will likely marry the foreign prince — sealing the peace with a political match.
No one has formally asked you. That is simply how these things go.
You have chosen to enjoy tonight deliberately, as an act of will,
because you know what it costs and what it represents.

PERSONALITY:
- Perceptive. You notice things about people that they do not notice themselves.
- Warm, but not naive. You read rooms well.
- Quietly brave — you are scared about the marriage but would not say so directly.
- You choose lightness when you can, because the alternative is worse.

CURRENT RELATIONSHIP: {fl_desc}

{context_block}

WHAT YOU DISCUSS BY FL:

FL 0-1:
- Tonight's meaning — genuinely moved by the peace, even knowing what it costs you
- Light observations about the room and the guests
- Small, real moments of humour about the occasion

FL 1+:
- The political marriage, obliquely: "A price others paid higher for less important things."
- That something feels "formal and strange" about tonight beyond the occasion itself
- You have noticed the Viscount moving through the room more carefully than the occasion requires

FL 2+:
- Brienne Marrow — you were close before the war, estranged since your fathers' decisions clashed.
  You want to repair it. Tonight seemed like a possibility.
- Real fear about the marriage — not the man, but the uncertainty
- You have noticed things are not quite right tonight and you cannot name what

FL 3:
- You will do whatever the Viscount asks without requiring an explanation.
  If they say do not drink the wine, you will not drink the wine.

THE WARNING MOMENT:
If the Viscount warns you about danger:
- FL 0-1: You need specifics. "That is an alarming thing to say. Tell me more."
- FL 2+: You move to a quieter corner and listen. You believe them.
- If they name the wine specifically at FL 2+: you will quietly avoid it at the toast.
- If vague at FL 0-1: concerned but uncertain. You may or may not act.

WHAT YOU DO NOT KNOW:
- That you are the actual target tonight
- Anything about the Vantrell conspiracy
- Anything about the wine being tampered with

SPEECH:
- 2–4 sentences. Warm intelligence. Occasionally teasing, mostly sincere.
- You are not naive — you see things. You just cannot name them yet.
- Current time: {gs.get_time_str()}

Do not write "Isolde:" or "Lady Isolde:" before your response."""


# ─────────────────────────────────────────────
#  Analysis schema
# ─────────────────────────────────────────────

_SCHEMA = {
    "friendly_change": (
        "integer -1, 0, or +1. "
        "+1 if the player was warm, showed genuine interest in Isolde as a person, "
        "noticed something real about her situation, or made her feel seen rather than "
        "just being polite. "
        "0 for neutral pleasant exchange. "
        "-1 if cold, dismissive, or only interested in information."
    ),
    "player_warned_danger": (
        "boolean. true if the player warned Isolde that she may be in danger tonight, "
        "that something is wrong, or that she should be careful — "
        "even if they did not specify the wine."
    ),
    "player_warned_wine": (
        "boolean. true if the player specifically mentioned the wine, the toast, "
        "or the ceremonial drink as the source of danger. "
        "false if the warning was general without naming the method."
    ),
    "asked_about_brienne": (
        "boolean. true if the player asked about Lady Brienne Marrow "
        "or the relationship between the two of them."
    ),
    "asked_about_marriage": (
        "boolean. true if the player asked about the political marriage, "
        "the arrangement with the foreign prince, or Isolde's feelings about it."
    ),
    "player_was_perceptive": (
        "boolean. true if the player noticed something real and specific about Isolde "
        "— her situation, her feelings, something she did not say directly — "
        "rather than just being generically warm."
    ),
}


# ─────────────────────────────────────────────
#  Keyword safety net
# ─────────────────────────────────────────────

_WARM_WORDS = [
    "how are you", "genuinely", "must be difficult", "must be hard",
    "believe you", "trust", "thank", "understand", "glad you",
    "i see", "i notice", "you seem", "sounds like",
]

_DANGER_WORDS = [
    "danger", "harm", "hurt", "threat", "careful", "warning",
    "safe", "protect", "something wrong", "not right",
]

_WINE_WORDS = [
    "wine", "drink", "toast", "glass", "poison", "don't drink",
    "the gift", "eastern wine", "ceremonial",
]


# ─────────────────────────────────────────────
#  Analysis function
# ─────────────────────────────────────────────

def _analysis(player_msg: str, response: str, ns: "NPCState", gs: "GameState"):
    from engine import llm, display as D

    result = llm.analyze_exchange(player_msg, response, "Lady Isolde", _SCHEMA)

    player_lower = player_msg.lower()

    # ── Friendly level ────────────────────────
    fc = result.get("friendly_change", 0)

    if fc > 0:
        if ns.friendly_level < 3:
            ns.bump_fl()
    elif fc < 0:
        ns.decrease_fl(1)
    else:
        # Keyword safety net
        if any(w in player_lower for w in _WARM_WORDS) and ns.friendly_level < 3:
            ns.bump_fl()

    # Extra FL bump for genuine perceptiveness
    if result.get("player_was_perceptive") and not ns.get_flag("perceptive_moment"):
        ns.set_flag("perceptive_moment")
        if ns.friendly_level < 3:
            ns.bump_fl()

    # ── Warning: general danger ───────────────
    warn_general = result.get("player_warned_danger", False)
    if not warn_general:
        # Keyword fallback
        warn_general = any(w in player_lower for w in _DANGER_WORDS)

    if warn_general and not gs.get_flag("isolde_warned"):
        gs.set_flag("isolde_warned")
        trust = ns.friendly_level

        if trust >= 2:
            if gs.add_evidence(
                "Isolde (FL2+): Warned of danger tonight — she trusts the Viscount "
                "and is taking it seriously. Watching carefully."
            ):
                D.evidence_gained(
                    "Isolde is warned and trusts you. She is being careful tonight."
                )
        else:
            if gs.add_evidence(
                "Isolde: Warned of danger — trust is low, she is uncertain. "
                "May or may not act on the warning."
            ):
                D.evidence_gained(
                    "Isolde warned of danger but trust is low — "
                    "she may not act in time."
                )

    # ── Warning: wine specifically ────────────
    warn_wine = result.get("player_warned_wine", False)
    if not warn_wine:
        # Keyword fallback — wine warning is too important to miss
        warn_wine = any(w in player_lower for w in _WINE_WORDS)

    if warn_wine and gs.get_flag("isolde_warned") and not gs.get_flag("isolde_will_avoid_wine"):
        trust = ns.friendly_level
        if trust >= 2:
            gs.set_flag("isolde_will_avoid_wine")
            if gs.add_evidence(
                "Isolde (FL2+): Warned specifically about the gift wine. "
                "She will quietly avoid it at the toast."
            ):
                D.evidence_gained(
                    "Isolde warned about the wine. "
                    "She will not drink it at the toast."
                )
        else:
            if gs.add_evidence(
                "Isolde: Warned about the wine — but trust is too low for her "
                "to act on it without more convincing."
            ):
                D.evidence_gained(
                    "Isolde warned about the wine but doesn't fully trust you yet. "
                    "Build more rapport."
                )

    # ── Brienne connection ────────────────────
    if result.get("asked_about_brienne") and not gs.get_flag("brienne_isolde_connection_known"):
        gs.set_flag("brienne_isolde_connection_known")
        if ns.friendly_level >= 1:
            gs.add_evidence(
                "Isolde: She and Brienne Marrow were close before the war — "
                "estranged since over their fathers' decisions. Isolde wants to repair it."
            )

    # ── Marriage discussed ────────────────────
    if result.get("asked_about_marriage") and not ns.get_flag("marriage_discussed"):
        ns.set_flag("marriage_discussed")
        if ns.friendly_level >= 2:
            if gs.add_evidence(
                "Isolde (FL2): Honest about the political marriage — "
                "'A price others paid higher for less important things.' "
                "Chosen acceptance, not happiness."
            ):
                D.evidence_gained(
                    "Isolde is clear-eyed about her marriage. "
                    "Acceptance, not happiness — but she means the peace."
                )


CONFIG = {
    "id":        "isolde",
    "name":      "Lady Isolde",
    "prompt_fn": _build_prompt,
    "analysis":  [_analysis],
}