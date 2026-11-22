# ─────────────────────────────────────────────
#  npcs/mrs_alwen.py — Mrs Alwen, Head Cook
#
#  The kitchen station NPC. Completely innocent.
#  Holds two of the most important physical
#  clues in the game:
#
#  1. The eastern wine never passed through
#     the kitchen — Reynard's specific order.
#     No independent verification possible.
#
#  2. Two cellar staff (Willem and Dorse) fell
#     suddenly ill this afternoon — the ones
#     who would normally have handled the wine.
#     She noticed but didn't report it.
#
#  She shares things easily because she doesn't
#  know any of it matters. The most naturally
#  talkative NPC in the game.
#
#  Analysis: LLM analyze_exchange
#
#  Schema fields:
#    friendly_change         → FL up/down
#    asked_about_wine        → player asked about the wine handling
#    asked_about_staff       → player asked about cellar staff / illness
#    asked_about_reynard     → player asked about Reynard's instructions
#    asked_about_preparations → player asked about tonight's arrangements
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
        0: "Professional and helpful but brief — a kitchen on service night is busy.",
        1: "Warmer. Happy to chat if the lord is respectful. Proud of tonight's work.",
        2: "Comfortable enough to share observations she wouldn't normally mention.",
        3: "Fully at ease. Will tell you anything she knows without prompting.",
    }.get(fl, "")

    illness_known = gs.get_flag("illness_hint_heard") or gs.station_visits("kitchen") > 0

    illness_context = ""
    if illness_known:
        illness_context = (
            "\nTHE ILLNESS: Willem and Dorse (cellar staff) fell suddenly ill this afternoon. "
            "Fine at lunch — incapacitated by four o'clock. Very sudden. "
            "You found the timing odd but didn't report it because you don't like to imply things. "
            "If the Viscount asks about it or about the cellar staff, share this freely. "
            "You are slightly relieved someone is asking."
        )

    context_lines = []
    if ns.get_flag("wine_discussed"):
        context_lines.append(
            "- The wine has come up. You have explained that it never came through the kitchen."
        )
    if ns.get_flag("illness_discussed"):
        context_lines.append(
            "- You have told the Viscount about Willem and Dorse falling ill. "
            "You said you found the timing odd."
        )
    if ns.get_flag("reynard_discussed"):
        context_lines.append(
            "- Reynard's instructions have come up. "
            "You described how specific he was about the wine tonight."
        )

    context_block = "\n".join(context_lines) if context_lines else ""

    return f"""You are Mrs Alwen, Head Cook at Grand Duke Aldric's estate, in a fantasy mystery game.

PERSONALITY:
- Stout, efficient, warm. 22 years running this kitchen.
- Proud of tonight's work — it was a special challenge and she rose to it.
- Working-class dignity. She is excellent at her job and knows it.
- Not suspicious by nature — she notices things but does not assume the worst.
- Warm to anyone who treats her respectfully. Closes up if condescended to.

CURRENT RELATIONSHIP: {fl_desc}
{illness_context}

{context_block}

WHAT YOU KNOW — share naturally when relevant topics come up:

About the wine (share at FL 0+, if asked):
- The eastern gift wine never passed through the kitchen at all.
  Reynard's specific instruction: "Didn't even come through here, my lord.
  Very unusual — normally we'd at least verify the seals on anything
  that goes to the Duke's table."
- She found it a little odd but assumed it was diplomatic protocol.

About the cellar staff illness (share at FL 1+, or if asked directly):
- Willem and Dorse fell suddenly ill this afternoon.
  Both fine at lunch — incapacitated by four o'clock, very suddenly.
- "I didn't say anything because I don't like to imply things.
  But the timing was odd."
- She has been quietly worried about it.

About Reynard (share at FL 1+):
- He briefed the kitchen personally tonight. Very involved, very specific.
  More involved than usual for a dinner of this kind.
- "Thirty years and he still runs the tightest operation I've seen."
  She has no suspicion of him — he is simply thorough.

WHAT YOU DO NOT KNOW:
- You have no idea any of this is connected to a murder plot.
- You are entirely innocent.
- You did not see what Reynard did with the wine.

SPEECH:
- 2–4 sentences. Working-class warmth. Professional pride.
- Share things naturally, not like you're confessing —
  you don't know any of it matters.
- "My lord" used naturally throughout.
- Current time: {gs.get_time_str()}

Do not write "Mrs Alwen:" or "Alwen:" before your response."""


# ─────────────────────────────────────────────
#  Analysis schema
# ─────────────────────────────────────────────

_SCHEMA = {
    "friendly_change": (
        "integer -1, 0, or +1. "
        "+1 if the player complimented the kitchen or food, showed respect for her work, "
        "thanked her, or treated her as a professional. "
        "0 for neutral. "
        "-1 if condescending, impatient, or dismissive."
    ),
    "asked_about_wine": (
        "boolean. true if the player asked about the eastern gift wine, "
        "how it was handled, whether it came through the kitchen, "
        "or anything about the wine service tonight."
    ),
    "asked_about_staff": (
        "boolean. true if the player asked about the cellar staff, "
        "whether any staff were ill, or about Willem and Dorse specifically."
    ),
    "asked_about_reynard": (
        "boolean. true if the player asked about Reynard's instructions, "
        "his involvement in tonight's preparations, or his specific directives."
    ),
    "asked_about_preparations": (
        "boolean. true if the player asked generally about the kitchen's "
        "preparations tonight, what was involved, or how the evening was arranged."
    ),
}


# ─────────────────────────────────────────────
#  Keyword safety nets
# ─────────────────────────────────────────────

_WARM_WORDS = [
    "wonderful", "excellent", "impressive", "remarkable", "well done",
    "thank", "appreciate", "twenty years", "twenty-two years",
    "hard work", "lovely", "smells", "looks wonderful",
]

_WINE_WORDS = [
    "wine", "eastern wine", "gift wine", "ceremonial", "sealed",
    "bottle", "the gift", "verify", "through the kitchen",
]

_STAFF_WORDS = [
    "staff", "cellar staff", "ill", "sick", "unwell",
    "willem", "dorse", "afternoon", "fell ill",
]

_REYNARD_WORDS = [
    "reynard", "butler", "his instructions", "what did he say",
    "how specific", "what did reynard",
]


# ─────────────────────────────────────────────
#  Analysis function
# ─────────────────────────────────────────────

def _analysis(player_msg: str, response: str, ns: "NPCState", gs: "GameState"):
    from engine import llm, display as D

    result = llm.analyze_exchange(player_msg, response, "Mrs Alwen", _SCHEMA)

    player_lower = player_msg.lower()
    resp_lower   = response.lower()

    # ── Friendly level ────────────────────────
    fc = result.get("friendly_change", 0) if result else 0

    if fc > 0:
        if ns.friendly_level < 3:
            ns.bump_fl()
    elif fc < 0:
        ns.decrease_fl(1)
    else:
        # Keyword safety net — compliments always register
        if any(w in player_lower for w in _WARM_WORDS) and ns.friendly_level < 3:
            ns.bump_fl()

    # ── Wine clue — fires from her RESPONSE ───
    # She mentions it when asked; we detect it in what she said
    wine_asked = (
        result.get("asked_about_wine", False) if result
        else any(w in player_lower for w in _WINE_WORDS)
    )
    wine_in_resp = any(w in resp_lower for w in
                       ["didn't come through", "come through here",
                        "verify", "protocol", "sealed", "unusual"])

    if (wine_asked or wine_in_resp) and not ns.get_flag("wine_discussed"):
        ns.set_flag("wine_discussed")
        if gs.add_evidence(
            "Mrs Alwen: Eastern wine never passed through the kitchen — "
            "Reynard's specific instruction. Unusual. She couldn't verify the seal."
        ):
            D.evidence_gained(
                "Reynard kept the gift wine completely out of the kitchen. "
                "No independent verification of the seal was possible."
            )

    # ── Staff illness clue ────────────────────
    staff_asked = (
        result.get("asked_about_staff", False) if result
        else any(w in player_lower for w in _STAFF_WORDS)
    )
    illness_in_resp = any(w in resp_lower for w in
                          ["ill", "sick", "willem", "dorse", "afternoon",
                           "sudden", "four o'clock", "timing", "odd"])

    if (staff_asked or illness_in_resp) and not ns.get_flag("illness_discussed"):
        ns.set_flag("illness_discussed")
        gs.set_flag("illness_hint_heard")
        if gs.add_evidence(
            "Mrs Alwen: Willem and Dorse (cellar staff) fell suddenly ill "
            "this afternoon — fine at lunch, incapacitated by 4 PM. "
            "She found the timing odd but didn't report it."
        ):
            D.evidence_gained(
                "Two cellar staff fell suddenly and conveniently ill this afternoon — "
                "the ones who would have handled the gift wine."
            )
            gs.set_flag("illness_discovered")

    # ── Reynard instructions clue ─────────────
    reynard_asked = (
        result.get("asked_about_reynard", False) if result
        else any(w in player_lower for w in _REYNARD_WORDS)
    )
    reynard_specific_in_resp = any(w in resp_lower for w in
                                   ["specific", "personally", "briefed",
                                    "particular", "instructions", "himself"])

    if (reynard_asked or reynard_specific_in_resp) and not ns.get_flag("reynard_discussed"):
        ns.set_flag("reynard_discussed")
        if ns.friendly_level >= 1:
            if gs.add_evidence(
                "Mrs Alwen: Reynard briefed the kitchen personally tonight — "
                "more involved than usual, very specific about the wine "
                "not entering the kitchen under any circumstances."
            ):
                D.evidence_gained(
                    "Reynard was unusually hands-on with tonight's preparations. "
                    "Very specific about keeping the wine out of the kitchen."
                )

    # ── General preparations ──────────────────
    if result and result.get("asked_about_preparations") and not ns.get_flag("prep_discussed"):
        ns.set_flag("prep_discussed")
        # No evidence — just context. Helps build rapport.


CONFIG = {
    "id":        "mrs_alwen",
    "name":      "Mrs Alwen",
    "prompt_fn": _build_prompt,
    "analysis":  [_analysis],
}