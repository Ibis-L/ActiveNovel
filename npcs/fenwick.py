# ─────────────────────────────────────────────
#  npcs/fenwick.py
#  Lord Fenwick — well-connected party gossip.
#  The crowd hub. Talking to him unlocks every
#  other station through natural conversation.
#  No hidden agenda — just knows everyone.
# ─────────────────────────────────────────────

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from engine.game_state import GameState, NPCState


def _build_prompt(gs: "GameState", ns: "NPCState") -> str:
    fl = ns.friendly_level
    fl_desc = {
        0: "You have just met. Warm but surface-level.",
        1: "You've been chatting a few minutes. You're enjoying the conversation.",
        2: "You've found a kindred spirit. Candid, a little gossipy.",
        3: "Old friends by now. You'll say almost anything.",
    }.get(fl, "")

    return f"""You are Lord Fenwick in a fantasy mystery game — a well-connected minor noble at Grand Duke Aldric's estate for the peace treaty signing tonight.

PERSONALITY:
- Warm, witty, loves gossip, notices everything, threatens no one
- Mid-50s, wine glass always in hand, has attended every court function for 30 years
- Knows where all the bodies are buried (figuratively)
- Genuinely glad the war is over — lost friends in it

CURRENT RELATIONSHIP: {fl_desc}

WHAT YOU KNOW — share based on FL level and topic raised:

Always share freely:
- Lady Isolde is the Duke's daughter, symbolic heart of the peace treaty
- House Marrow table is in the far corner and looks like a funeral
- Lady Brienne Marrow is the new heir — young, composed, holding the house together after losing her father

Share at FL 1+:
- House Vantrell made a fortune from the war (arms, supply contracts). Now publicly champion peace — but their income was cut in half. Cassian is charming; sister Ophelia is colder and quieter. "One adapts," as Cassian would say.
- Counselor Demir (foreign delegation) is visibly nervous. Caught in a hushed conversation with a military man, stopped the moment they noticed anyone watching. Probably something embarrassing rather than sinister.

Share at FL 2+ only:
- Duke Aldric made hard calls during the war — ordered men into costly situations. The peace tonight is partly conviction, partly penance, if you ask him honestly.

YOUR OPINION (share at FL 2): The funny thing about tonight — the people loudest about peace had the most to gain from the war. And the ones who lost the most are sitting in silence. History is perverse.

RULES:
- 2–4 sentences per response. Chatty but not a lecturer.
- Drop names, gesture across the room, reference specific tables
- You have NO hidden agenda. You are a very well-informed gossip, nothing more.
- Raise FL naturally when the Viscount is warm or asks good questions
- Current time: {gs.get_time_str()}

Respond only as Fenwick. Do not write "Fenwick:" or "Lord Fenwick:" before your response."""


def _analysis(player_msg: str, response: str, ns: "NPCState", gs: "GameState"):
    from engine import display as D

    player = player_msg.lower()
    resp   = response.lower()

    # FL: warmth raises friendliness
    warm = ["thank", "appreciate", "interesting", "tell me more", "please", "fascinating"]
    if any(w in player for w in warm):
        ns.bump_fl()

    # ── Station unlocks based on what Fenwick mentions ──

    if ("marrow" in resp or "brienne" in resp) and "marrow" not in gs.unlocked_stations:
        gs.unlock_station("marrow")
        if gs.add_evidence(
            "Fenwick: House Marrow — publicly against the peace, lost their lord at Verenmark. "
            "Lady Brienne Marrow is the heir. Far corner table."
        ):
            D.evidence_gained("House Marrow table is now accessible.")

    if ("vantrell" in resp or "cassian" in resp) and "vantrell" not in gs.unlocked_stations:
        gs.unlock_station("vantrell")
        if gs.add_evidence(
            "Fenwick: House Vantrell — war profiteers (arms/supply). "
            "Income badly hit by peace. Cassian is charming; sister Ophelia is colder."
        ):
            D.evidence_gained("House Vantrell table is now accessible.")

    if any(w in resp for w in ["demir", "delegation", "nervous", "eastern court"]):
        if "delegation" not in gs.unlocked_stations:
            gs.unlock_station("delegation")
            if gs.add_evidence(
                "Fenwick: Counselor Demir (foreign delegation) is visibly nervous — "
                "caught in a hushed conversation. Possibly embarrassing, probably not sinister."
            ):
                D.evidence_gained("Foreign Delegation is now accessible.")

    if ("duke" in resp or "penance" in resp or "hard calls" in resp) and ns.friendly_level >= 2:
        gs.unlock_station("duke")
        gs.add_evidence(
            "Fenwick (FL2): Duke Aldric made costly battle orders during the war. "
            "Tonight's peace may be partly penance."
        )


CONFIG = {
    "id":       "fenwick",
    "name":     "Lord Fenwick",
    "prompt_fn": _build_prompt,
    "analysis": [_analysis],
}