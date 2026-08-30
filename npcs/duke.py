# ─────────────────────────────────────────────
#  npcs/duke.py — Grand Duke Aldric
#
#  The authority figure. Acts proportionally
#  to evidence. The only NPC who can take
#  official action — hold the wine, watch
#  the Vantrells, detain Reynard.
#
#  CRITICAL MECHANIC:
#  Accusing Reynard with evidence_score < 3
#  → Duke tells Reynard → Ending D triggered
#
#  He has his own guilt thread: he gave the
#  orders that killed Reynard's son and Lord
#  Marrow. He lives with it. This makes him
#  hesitate specifically on Reynard — he owes
#  the man a grief he cannot repay.
#
#  Private audience is harder than public:
#    Public  → one meaningful exchange, formal
#    Private → needs FL 1+ OR prior arrangement
#
#  Analysis: LLM analyze_exchange
#
#  Schema fields:
#    friendly_change        → FL up/down
#    claim_about_wine       → player raised the wine as a threat
#    claim_about_vantrell   → player implicated the Vantrells
#    claim_about_reynard    → player accused Reynard (DANGEROUS)
#    claim_about_vision     → player raised their vision/dream
#    evidence_level_felt    → LLM's read on how convincing the claim was
# ─────────────────────────────────────────────

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from engine.game_state import GameState, NPCState


# ─────────────────────────────────────────────
#  Prompt builder
# ─────────────────────────────────────────────

def _build_prompt(gs: "GameState", ns: "NPCState") -> str:
    fl      = ns.friendly_level
    ev      = gs.evidence_score()
    private = (
        not gs.get_flag("duke_station_public_only")
        or fl >= 1
        or gs.get_flag("reynard_met_warmly")
    )

    setting = (
        "You are in a rare private moment with the Viscount — "
        "a lull in the receiving line. You have a few minutes."
        if private else
        "You are receiving guests publicly. "
        "You can give the Viscount perhaps two meaningful exchanges "
        "before you must move on. Warm but formal."
    )

    ev_note = ""
    if ev >= 4:
        ev_note = "The Viscount appears to have gathered substantial specific evidence tonight."
    elif ev >= 2:
        ev_note = "The Viscount has some evidence — enough to take seriously, not enough to act on fully."
    else:
        ev_note = "The Viscount has little concrete evidence yet. Be receptive but measured."

    guilt_note = ""
    if fl >= 2 or gs.get_flag("aldous_spoke_duke"):
        guilt_note = (
            "\nPRIVATE GUILT: You gave orders during the war that cost men their lives unnecessarily. "
            "Lord Marrow at Verenmark. Others you do not name even to yourself. "
            "The peace tonight is partly genuine conviction and partly the thing you need it to be. "
            "If Reynard's name comes up in a serious context, something in you already suspects why — "
            "you have always known he never quite forgave you for the crossing."
        )

    context_lines = []
    if gs.get_flag("duke_held_wine"):
        context_lines.append(
            "- You have already ordered the wine held for precautionary inspection. "
            "That matter is being handled discreetly."
        )
    if gs.get_flag("duke_suspects_vantrell"):
        context_lines.append(
            "- You have agreed to have the Vantrells watched discreetly. "
            "You said 'Cassian' with a long pause."
        )
    if gs.get_flag("duke_knows_reynard"):
        context_lines.append(
            "- You know about Reynard. Guards are quietly watching him. "
            "You have not yet confronted him directly."
        )

    context_block = "\n".join(context_lines) if context_lines else ""

    return f"""You are Grand Duke Aldric in a fantasy mystery game.
Late 50s, silver-templed. Host of tonight's peace treaty signing.

SETTING: {setting}

PERSONALITY:
- Formal authority softened by genuine relief that the war is over
- A man of real consequence who makes real decisions — not performative
- Proportional always — the response matches the evidence presented
- He does not dismiss the Viscount, but he does not act on feelings or hearsay
{guilt_note}

EVIDENCE CONTEXT: {ev_note}

{context_block}

HOW YOU RESPOND TO SPECIFIC CLAIMS:

Claim about the wine ({ev_note}):
  Low evidence (0-1): "The wine arrived sealed, handled by Reynard personally.
    I won't insult our guests on a feeling, Viscount."
  Medium evidence (2-3): "You're certain?" [long look] Quietly orders wine held —
    framed as "a small ceremonial precaution." No diplomatic incident.
  High evidence (4+): Acts decisively. No hesitation.

Claim about House Vantrell:
  Low evidence: "Cassian Vantrell is one of my strongest supporters tonight.
    Be careful with that suggestion."
  Sufficient evidence (3+): "Cassian." [controlled pause] Will have them watched.

Claim about Reynard — CRITICAL:
  Evidence < 3: You thank the Viscount, then privately tell Reynard what was said.
    This is NOT because you are complicit — you simply trust thirty-one years
    of service over an unsubstantiated claim. You are wrong. You mean well.
  Evidence 3+: A long silence. "He was at the crossing. He lost his boy at the crossing."
    You will act — but quietly, and personally. You owe him that much.

Claim about a vision/dream:
  FL 0-1: Kind dismissal. "Take care of yourself tonight."
  FL 2+ OR aldous's candid assessment known: "What did you see?" Genuine. Full attention.

SPEECH:
- 3–4 sentences. Authority and weight.
- Proportional always — the response matches what was presented
- Never cruel or dismissive, but never reckless either
- Current time: {gs.get_time_str()}

Do not write "Duke:" or "Duke Aldric:" or "Aldric:" before your response."""


# ─────────────────────────────────────────────
#  Analysis schema
# ─────────────────────────────────────────────

_SCHEMA = {
    "friendly_change": (
        "integer -1, 0, or +1. "
        "+1 if the player was respectful, showed genuine concern for the estate "
        "or the peace, or engaged the Duke as a serious person with serious information. "
        "0 for neutral. "
        "-1 if the player was flippant, disrespectful, or made baseless accusations."
    ),
    "claim_about_wine": (
        "boolean. true if the player raised the ceremonial wine as a potential threat — "
        "tampered with, poisoned, or wrong in some way."
    ),
    "claim_about_vantrell": (
        "boolean. true if the player implicated House Vantrell, "
        "Cassian, or Ophelia in a plot or conspiracy tonight."
    ),
    "claim_about_reynard": (
        "boolean. true if the player accused Reynard, suggested he is involved "
        "in something wrong tonight, or asked the Duke to act against him."
    ),
    "claim_about_vision": (
        "boolean. true if the player mentioned having a personal vision, "
        "dream, or premonition about danger or death tonight."
    ),
    "evidence_level_felt": (
        "string: 'none', 'weak', 'moderate', or 'strong'. "
        "How convincing did the player's claim feel based on what they said? "
        "'none' — feeling only, no specifics. "
        "'weak' — one vague detail. "
        "'moderate' — specific detail, plausible but not proven. "
        "'strong' — multiple specific details that fit together convincingly."
    ),
}


# ─────────────────────────────────────────────
#  Analysis function
# ─────────────────────────────────────────────

def _analysis(player_msg: str, response: str, ns: "NPCState", gs: "GameState"):
    from engine import llm, display as D

    result = llm.analyze_exchange(player_msg, response, "Duke Aldric", _SCHEMA)

    if not result:
        return

    player_lower = player_msg.lower()
    resp_lower   = response.lower()
    ev           = gs.evidence_score()

    # ── Friendly level ────────────────────────
    fc = result.get("friendly_change", 0)
    if fc > 0 and ns.friendly_level < 3:
        ns.bump_fl()
    elif fc < 0 and ns.friendly_level > 0:
        ns.friendly_level -= 1

    felt = result.get("evidence_level_felt", "none")
    felt_score = {"none": 0, "weak": 1, "moderate": 2, "strong": 3}.get(felt, 0)
    effective_ev = ev + felt_score   # LLM's read adds to evidence score

    # ── Wine claim ────────────────────────────
    if result.get("claim_about_wine") and not gs.get_flag("duke_held_wine"):
        if effective_ev >= 3:
            # Duke acts — holds the wine
            gs.set_flag("duke_held_wine")
            if gs.add_evidence(
                "Duke: Ordered the wine held for inspection — "
                "framed as 'ceremonial precaution.' He acted on the evidence."
            ):
                D.evidence_gained(
                    "The Duke has ordered the wine held. "
                    "Immediate threat paused."
                )
        elif effective_ev >= 1:
            # Duke is cautious but not convinced
            gs.add_evidence(
                "Duke: Aware of concern about the wine — not yet convinced to act. "
                "Needs more specific evidence."
            )

    # ── Vantrell claim ────────────────────────
    if result.get("claim_about_vantrell") and not gs.get_flag("duke_suspects_vantrell"):
        if effective_ev >= 3:
            gs.set_flag("duke_suspects_vantrell")
            if gs.add_evidence(
                "Duke: Said 'Cassian' with a long pause — "
                "agreed to have the Vantrells watched discreetly."
            ):
                D.evidence_gained(
                    "The Duke is watching the Vantrells. "
                    "He said 'Cassian' like a man updating his assessment."
                )

    # ── Reynard claim — the dangerous one ─────
    if result.get("claim_about_reynard"):
        if effective_ev < 3 and ev < 3:
            # Not enough evidence — Duke tells Reynard
            # This is the Ending D trigger
            gs.set_flag("reynard_accused_without_evidence")
            gs.set_flag("ending_d_triggered")
            D.narrate(
                "The Duke thanks you for your concern. "
                "His expression is unreadable.\n\n"
                "Later — much later — you will understand what he did next."
            )
        else:
            # Sufficient evidence — Duke acts quietly
            if not gs.get_flag("duke_knows_reynard"):
                gs.set_flag("duke_knows_reynard")
                if gs.add_evidence(
                    "Duke (3+ evidence): Acknowledged Reynard's grief — "
                    "'He was at the crossing. He lost his boy at the crossing.' "
                    "Will act discreetly. Guards now watching Reynard."
                ):
                    D.evidence_gained(
                        "The Duke knows about Reynard. "
                        "Guards are quietly watching the butler."
                    )

    # ── Vision claim ──────────────────────────
    if result.get("claim_about_vision") and not ns.get_flag("vision_raised"):
        ns.set_flag("vision_raised")
        if ns.friendly_level >= 2 or gs.get_flag("aldous_spoke_duke"):
            gs.set_flag("duke_open_to_vision")
            if gs.add_evidence(
                "Duke (FL2+): Took the Viscount's vision seriously — "
                "asked what was seen. Full attention."
            ):
                D.evidence_gained(
                    "The Duke took the vision seriously. "
                    "He asked what you saw."
                )

    # ── Duke response logging ─────────────────
    # If his response mentioned holding the wine
    if any(w in resp_lower for w in ["held", "hold", "inspect", "precaution"]):
        gs.set_flag("duke_held_wine")

    # If his response mentioned Vantrell suspicion
    if "cassian" in resp_lower and any(w in resp_lower for w in ["watch", "noted", "careful"]):
        gs.set_flag("duke_suspects_vantrell")


CONFIG = {
    "id":        "duke",
    "name":      "Duke Aldric",
    "prompt_fn": _build_prompt,
    "analysis":  [_analysis],
}