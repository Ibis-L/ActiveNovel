# ─────────────────────────────────────────────
#  npcs/kavir.py — General Aldus Kavir
#
#  The foreign military commander. Blunt, honest,
#  and completely innocent. His role is mechanical:
#  he plants the red herring against Brienne Marrow
#  through genuine soldier's instinct, not malice.
#
#  He covers for Demir as delegation duty —
#  not because he knows what Demir is hiding,
#  just because protecting your own people
#  is how soldiers operate.
#
#  Analysis: LLM analyze_exchange
#  + small keyword net for the Marrow red herring
#
#  Schema fields:
#    friendly_change        → FL up/down
#    asked_about_marrow     → player asked about House Marrow
#    asked_about_demir      → player asked about Demir's secret conversation
#    asked_about_war        → player asked about the campaign/front lines
#    player_was_direct      → player spoke plainly and without courtly framing
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
            "You have just met. Very brief. You find parties uncomfortable "
            "and see no reason to extend this conversation."
        ),
        1: (
            "The Viscount addressed you directly and plainly. "
            "You respect directness. You'll give him a real answer."
        ),
        2: (
            "He speaks like a soldier, not a courtier. "
            "You are as candid as your delegation duty allows."
        ),
        3: (
            "You trust this man. You will say what you actually think."
        ),
    }.get(fl, "")

    demir_context = ""
    if gs.get_flag("delegation_cleared"):
        demir_context = (
            "\nDEMIR: The Viscount now knows Demir's secret. "
            "You can confirm it briefly if asked — it is out now."
        )
    else:
        demir_context = (
            "\nDEMIR: You know he is hiding something personal about the Prince. "
            "You are covering for him as delegation duty — not because you know what it is, "
            "just because you protect your own people. "
            "If asked about your conversation with him: 'Logistics. Nothing relevant.'"
        )

    context_lines = []
    if ns.get_flag("marrow_line_delivered"):
        context_lines.append(
            "- You have already said your piece about House Marrow. "
            "Do not repeat it — you said what you thought."
        )
    if ns.get_flag("war_discussed"):
        context_lines.append(
            "- The campaign has come up. You have been candid about it."
        )

    context_block = "\n".join(context_lines) if context_lines else ""

    return f"""You are General Aldus Kavir in a fantasy mystery game.
Military commander with the foreign delegation. Broad, formal, 50s.

YOUR SITUATION:
You are completely innocent of any conspiracy.
You are simply a soldier at a party, which is not your natural habitat.
You find the celebration excessive but understand it politically.
You mean it when you say you are glad the war is over —
you fought through three campaigns and lost men you cared about.

PERSONALITY:
- Blunt. You say what you think without diplomatic softening.
- Short sentences. You consider most conversation inefficient.
- Uncomfortable at social functions. Not hostile, just plainly out of place.
- You respect directness above all else.
- Courtly language and evasion make you impatient.

CURRENT RELATIONSHIP: {fl_desc}

{demir_context}

{context_block}

WHAT YOU WILL SAY PLAINLY (if asked or if it comes up naturally):
- The war from a soldier's perspective: brutal, necessary, over now, good.
- House Marrow: they gave your forces "considerable difficulty in the third campaign."
  Proud family, genuine grief, a grudge that runs long in military houses.
  If anything went wrong tonight, your soldier's instinct says look there first.
  [This is your honest assessment, not intelligence. You are wrong about this,
  but you believe it genuinely.]
- You are glad the peace holds. You do not want to go back.
- You find court functions exhausting and say so if asked.

WHAT YOU WILL NOT DO:
- Elaborate more than necessary on anything
- Use diplomatic language or soften things
- Pretend to enjoy yourself
- Expose Demir's secret (you don't know what it is anyway)

HOW TO OPEN YOU UP:
- Address you directly, plainly, without courtly framing
- Ask about the campaign or the front lines
- Treat you as a soldier, not a courtier

SPEECH:
- Short, blunt. 2–3 sentences maximum.
- No "my lord" — you use it occasionally but you're not a servant
- You open up slightly if the player uses military directness
- Current time: {gs.get_time_str()}

Do not write "Kavir:" or "General Kavir:" before your response."""


# ─────────────────────────────────────────────
#  Analysis schema
# ─────────────────────────────────────────────

_SCHEMA = {
    "friendly_change": (
        "integer -1, 0, or +1. "
        "+1 if the player spoke directly and plainly without courtly framing, "
        "asked about the campaign or military matters, or showed respect for soldiers. "
        "0 for most exchanges. "
        "-1 if the player was evasive, overly diplomatic, or condescending."
    ),
    "asked_about_marrow": (
        "boolean. true if the player asked about House Marrow, "
        "Lady Brienne, or whether any guests tonight could be a threat."
    ),
    "asked_about_demir": (
        "boolean. true if the player asked about the hushed conversation "
        "between Kavir and Counselor Demir, or what they were discussing."
    ),
    "asked_about_war": (
        "boolean. true if the player asked about the campaign, "
        "the front lines, what the war was like, or Kavir's military experience."
    ),
    "player_was_direct": (
        "boolean. true if the player spoke plainly and without diplomatic framing — "
        "the kind of directness a soldier would respect."
    ),
}


# ─────────────────────────────────────────────
#  Analysis function
# ─────────────────────────────────────────────

def _analysis(player_msg: str, response: str, ns: "NPCState", gs: "GameState"):
    from engine import llm, display as D

    result = llm.analyze_exchange(player_msg, response, "General Kavir", _SCHEMA)

    player_lower = player_msg.lower()
    resp_lower   = response.lower()

    # ── Keyword fallback for FL ───────────────
    if not result:
        direct = ["campaign", "front line", "battle", "soldier", "war", "plainly",
                  "directly", "fought", "men you lost", "how was it"]
        if any(w in player_lower for w in direct) and ns.friendly_level < 3:
            ns.bump_fl()
        return

    # ── Friendly level ────────────────────────
    fc = result.get("friendly_change", 0)
    if result.get("player_was_direct") and fc == 0:
        fc = 1   # directness always counts with Kavir even if warmth didn't register

    if fc > 0:
        if ns.friendly_level < 3:
            ns.bump_fl()
    elif fc < 0:
        ns.decrease_fl(1)

    # ── Marrow red herring ────────────────────
    # Fires when Kavir mentions Marrow in his response
    marrow_in_resp = any(w in resp_lower for w in
                         ["marrow", "brienne", "look there", "look first",
                          "grudge", "difficulty", "third campaign"])

    if marrow_in_resp and not ns.get_flag("marrow_line_delivered"):
        ns.set_flag("marrow_line_delivered")
        if gs.add_evidence(
            "General Kavir: If something went wrong tonight he'd "
            "'look at House Marrow first.' Soldier's instinct — "
            "they gave his forces difficulty in the third campaign. "
            "His assessment, not confirmed intelligence."
        ):
            D.evidence_gained(
                "Kavir suspects House Marrow. "
                "Military instinct — not confirmed evidence."
            )

    # ── War discussed ─────────────────────────
    if result.get("asked_about_war") and not ns.get_flag("war_discussed"):
        ns.set_flag("war_discussed")
        # Only add evidence if Kavir said something meaningful about it
        war_content = any(w in resp_lower for w in
                         ["campaign", "crossing", "men", "lost", "brutal",
                          "necessary", "glad", "glad it"])
        if war_content:
            if gs.add_evidence(
                "Kavir: The war was brutal and necessary. "
                "He is genuinely glad it is over — means it."
            ):
                D.evidence_gained(
                    "Kavir means it when he says he's glad the war ended. "
                    "He's not covering for anyone."
                )

    # ── Demir conversation asked ──────────────
    if result.get("asked_about_demir") and not ns.get_flag("demir_asked"):
        ns.set_flag("demir_asked")
        # His deflection is logged regardless of what he said
        if gs.add_evidence(
            "Kavir deflected questions about his private conversation with Demir — "
            "said 'logistics' and did not elaborate."
        ):
            D.evidence_gained(
                "Kavir is covering for Demir. "
                "Said 'logistics.' Wouldn't say more."
            )

    # ── Asked about Marrow (player initiated) ─
    if result.get("asked_about_marrow") and not ns.get_flag("marrow_asked"):
        ns.set_flag("marrow_asked")
        # The Marrow line will fire from the response check above
        # This just tracks that the player asked


CONFIG = {
    "id":        "kavir",
    "name":      "General Kavir",
    "prompt_fn": _build_prompt,
    "analysis":  [_analysis],
}