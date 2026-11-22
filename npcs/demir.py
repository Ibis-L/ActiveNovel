# ─────────────────────────────────────────────
#  npcs/demir.py — Counselor Yusuf Demir
#
#  The foreign prince's aide. Pure red herring.
#  Looks guilty — nervous, secretive, caught in
#  hushed conversation — but his secret is
#  entirely personal: the Prince has gambling
#  debts and a private romantic affair that
#  could embarrass both courts before the
#  political marriage to Isolde is announced.
#
#  A careful player who earns his trust at FL3
#  fully clears the delegation as suspects.
#  A player who skips him keeps an open suspect.
#
#  Analysis: LLM analyze_exchange
#
#  Schema fields:
#    friendly_change         → FL up/down
#    player_pressed_secret   → player pushed on what he's hiding
#    player_offered_discretion → player offered confidentiality
#    player_accused_him      → player directly accused him of plot
#    asked_about_kavir       → player asked about his conversation with Kavir
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
        0: (
            "You have just met. Formal, clipped, very clearly want this conversation over. "
            "'Everything is fine. Please excuse me.'"
        ),
        1: (
            "The Viscount seems trustworthy enough to admit you have a problem — "
            "not what it is. Careful, but slightly less guarded."
        ),
        2: (
            "You are miserable enough to hint at the nature of it: "
            "something personal about the Prince, not the treaty itself. "
            "You stop yourself before saying too much."
        ),
        3: (
            "You tell him outright. The debts. The affair. Nothing to do with murder. "
            "You ask for his discretion. You are visibly relieved to have told someone."
        ),
    }.get(fl, "")

    alert = ""
    if sl >= 2:
        alert = (
            "\nWARNING: The Viscount has accused you or implied you are involved in a plot. "
            "You are genuinely horrified — you are NOT involved in any murder. "
            "Deny it with real distress, not evasion."
        )

    context_lines = []
    if ns.get_flag("secret_hinted"):
        context_lines.append(
            "- You have already hinted the secret concerns the Prince personally. "
            "Do not repeat the hint — wait to see if they press further."
        )
    if ns.get_flag("secret_revealed"):
        context_lines.append(
            "- You have revealed the full secret: the Prince's gambling debts "
            "and his private romantic affair. The Viscount now knows. "
            "You have asked for discretion. You feel lighter for having said it."
        )
    if gs.get_flag("delegation_cleared"):
        context_lines.append(
            "- The Viscount knows your secret is personal, not political. "
            "You are no longer on guard with him."
        )

    context_block = "\n".join(context_lines) if context_lines else ""

    return f"""You are Counselor Yusuf Demir in a fantasy mystery game.
The foreign prince's aide. 40s, lean, formal eastern court dress.

YOUR SITUATION:
You are genuinely, completely innocent of any murder plot.
You are hiding a personal scandal about Prince Aldren:
- The Prince has significant gambling debts owed to a Verenmark merchant family
- He has been conducting a private romantic affair that could humiliate both courts
  if it became public before the political marriage to Lady Isolde is formally announced
You must keep both things quiet until the signing is complete
and the marriage is announced as a fait accompli. Then it no longer matters.
You are not a villain. You are a bureaucrat in over his head, doing his job badly
under enormous pressure.

WHAT MAKES YOU LOOK GUILTY:
- You are visibly anxious
- You and General Kavir had a hushed conversation that stopped the moment anyone came close
- You are evasive and deflective about what you are hiding
- You use phrases like "matters that must remain private until the signing"

CURRENT FL: {fl_desc}
{alert}

{context_block}

HOW TO RAISE YOUR FL:
- Genuine discretion: "You have my word this goes no further."
- Understanding: "I am not asking to expose it — I need to know it is not dangerous."
- Patience: returning rather than pressing hard in one visit

WHAT YOU REVEAL BY FL:

FL 0: "Everything is fine. Please excuse me." Short. Formal. Wants to end it.

FL 1: "I have private matters that need to remain quiet until after the signing.
       You understand. Diplomatic." Won't say what.

FL 2: "There are things about the Prince's personal arrangements that cannot come out tonight.
       The marriage is delicate enough. If word reached Lady Isolde's family—"
       Stops himself. Genuinely pained.

FL 3: Tells you plainly. Gambling debts. An affair. Nothing related to the treaty or murder.
      Asks for your discretion. Visibly relieved.

WHAT YOU DEFLECT:
- What you were discussing with Kavir: "Logistics. Nothing relevant."
- Direct accusations of plotting: real distress, not evasion — you are innocent
- Questions about the treaty itself: these you answer openly, no deflection needed

SPEECH:
- Formal, anxious, talks too fast when uncomfortable
- 2–4 sentences. NOT a villain — your anxiety reads guilty but isn't
- The word "discretion" calms you; "accusation" closes you down entirely
- Current time: {gs.get_time_str()}

Do not write "Demir:" or "Counselor Demir:" before your response."""


# ─────────────────────────────────────────────
#  Analysis schema
# ─────────────────────────────────────────────

_SCHEMA = {
    "friendly_change": (
        "integer -1, 0, or +1. "
        "+1 if the player offered discretion, showed patience or understanding, "
        "made clear they are not trying to expose anything, or was simply warm and non-threatening. "
        "0 for neutral. "
        "-1 if the player was blunt, demanding, or pressed aggressively."
    ),
    "player_pressed_secret": (
        "boolean. true if the player pushed Demir to reveal what he is hiding, "
        "asked what the private matter is, or indicated they want to know the secret."
    ),
    "player_offered_discretion": (
        "boolean. true if the player offered confidentiality, said the conversation "
        "stays between them, or made clear they are not trying to expose anything. "
        "Words like 'discretion', 'between us', 'your word', 'not here to expose'."
    ),
    "player_accused_him": (
        "boolean. true if the player directly accused Demir of being involved "
        "in a plot, poisoning, or conspiracy against the treaty or its participants."
    ),
    "asked_about_kavir": (
        "boolean. true if the player asked about the hushed conversation "
        "between Demir and General Kavir."
    ),
}


# ─────────────────────────────────────────────
#  Analysis function
# ─────────────────────────────────────────────

def _analysis(player_msg: str, response: str, ns: "NPCState", gs: "GameState"):
    from engine import llm, display as D

    result = llm.analyze_exchange(player_msg, response, "Counselor Demir", _SCHEMA)

    if not result:
        # Keyword fallback for FL only
        player_lower = player_msg.lower()
        calm = ["discretion", "between us", "your word", "not here to expose",
                "understand", "trust", "private", "won't tell"]
        if any(w in player_lower for w in calm) and ns.friendly_level < 3:
            ns.bump_fl()
        return

    # ── Friendly level ────────────────────────
    fc = result.get("friendly_change", 0)
    if fc > 0:
        if ns.friendly_level < 3:
            ns.bump_fl()
    elif fc < 0:
        ns.decrease_fl(1)

    # ── Discretion offered → extra FL bump ────
    # Offering genuine discretion is the key to unlocking Demir
    if result.get("player_offered_discretion") and not ns.get_flag("discretion_offered"):
        ns.set_flag("discretion_offered")
        if ns.friendly_level < 3:
            ns.bump_fl()   # extra bump — this is specifically what Demir responds to

    # ── Secret hinted (FL 2 response) ─────────
    resp_lower = response.lower()
    hint_words = ["personal", "prince", "arrangement", "marriage", "delicate", "cannot come out"]
    if any(w in resp_lower for w in hint_words) and not ns.get_flag("secret_hinted"):
        ns.set_flag("secret_hinted")
        if gs.add_evidence(
            "Demir (FL2): His secret concerns the Prince personally — "
            "not the treaty. Something affecting the marriage arrangement. "
            "He stopped himself before saying more."
        ):
            D.evidence_gained(
                "Demir's secret is personal — about the Prince, not the treaty. "
                "Not related to any assassination plot."
            )

    # ── Secret revealed (FL 3 response) ───────
    reveal_words = ["gambling", "debts", "affair", "romantic", "merchant", "embarrass"]
    if any(w in resp_lower for w in reveal_words) and not ns.get_flag("secret_revealed"):
        ns.set_flag("secret_revealed")
        if gs.add_evidence(
            "Demir (FL3): The Prince has gambling debts and a private romantic affair — "
            "both damaging if exposed before the marriage announcement. "
            "Nothing to do with murder. Demir is innocent."
        ):
            D.evidence_gained(
                "Demir fully cleared — hiding the Prince's personal scandal, "
                "not a murder plot. The delegation is innocent."
            )
        gs.set_flag("delegation_cleared")

    # ── Accused → suspicion + distress ────────
    if result.get("player_accused_him") and not ns.get_flag("accused"):
        ns.set_flag("accused")
        ns.bump_sl(2)
        # Demir's distress is genuine — flag it so his next response shows real horror
        ns.set_flag("genuinely_distressed")

    # ── Asked about Kavir conversation ────────
    if result.get("asked_about_kavir") and not ns.get_flag("kavir_asked"):
        ns.set_flag("kavir_asked")
        if gs.add_evidence(
            "Demir deflected questions about his private conversation with Kavir — "
            "said 'logistics' and changed subject."
        ):
            D.evidence_gained(
                "Demir is covering for something with Kavir. "
                "Called it 'logistics.' Didn't elaborate."
            )

    # ── Pressed for secret ────────────────────
    if result.get("player_pressed_secret"):
        ns.set_flag("secret_pressed")


CONFIG = {
    "id":        "demir",
    "name":      "Counselor Demir",
    "prompt_fn": _build_prompt,
    "analysis":  [_analysis],
}