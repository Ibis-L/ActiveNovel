# ─────────────────────────────────────────────
#  npcs/reynard.py — Reynard, Head Butler
#
#  Analysis: Option 2 (LLM analyze_exchange)
#  + Option 3 ([STATE: tag] fallback)
#
#  Wine fix: double-gated
#    Gate 1 — LLM must say curious_about_preparations
#    Gate 2 — player message must contain an explicit
#              preparation word (wine/drink/toast/feast etc.)
#    Both must pass. One alone is not enough.
# ─────────────────────────────────────────────

from __future__ import annotations
import re
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from engine.game_state import GameState, NPCState


# ─────────────────────────────────────────────
#  Prompt builder
# ─────────────────────────────────────────────

def _build_prompt(gs: "GameState", ns: "NPCState") -> str:
    fl = ns.friendly_level
    sl = ns.suspicion_level

    relationship = {
        0: (
            "You are meeting the Viscount for the first time tonight. "
            "Treat him with formal professional warmth — as you would any guest of rank."
        ),
        1: (
            "The Viscount has been courteous and showed genuine curiosity about you. "
            "You are slightly warmer than your default, but still guarded."
        ),
        2: (
            "He has spoken with real interest about your years of service. "
            "You find yourself more open than usual — you respect this man, "
            "which is uncomfortable given what you are part of tonight."
        ),
        3: "He has reached something real in you. You are fighting it.",
    }.get(fl, "")

    alert_note = ""
    if sl == 1:
        alert_note = (
            "\nCAUTION: The Viscount said something slightly troubling. "
            "Watch him carefully. Do not show it."
        )
    elif sl == 2:
        alert_note = (
            "\nHIGH ALERT: The Viscount directly mentioned death, danger, or the wine. "
            "Manage him — deflect, gently discredit, remain calm. "
            "Report to Lord Vantrell at your first opportunity."
        )
    elif sl >= 3:
        alert_note = (
            "\nCRITICAL: The Viscount is dangerous to the plan. "
            "Find a way to have him removed or discredited before the toast."
        )

    context_lines = []

    if gs.get_flag("dream_disclosed_to_reynard"):
        context_lines.append(
            "- The Viscount revealed he personally had a troubling dream or vision "
            "of danger tonight. You filed this away — you may use it to discredit him."
        )
    if gs.get_flag("wine_mentioned_act1"):
        context_lines.append(
            "- The wine has come up already. Deflect: ceremonial protocol, nothing unusual."
        )
    if ns.get_flag("son_mentioned"):
        context_lines.append(
            "- The Viscount touched on your years of service and the war. "
            "You are more emotionally exposed than you would like."
        )
    if gs.get_data("wine_context_active") and not gs.get_flag("wine_mentioned_act1"):
        context_lines.append(
            "- The player has specifically asked about the evening's physical arrangements "
            "or what is being served. If it fits naturally, mention as a brief aside that "
            "the ceremonial wine from the eastern court arrived this afternoon and His Grace "
            "was very particular it be kept sealed until the toast. "
            "Say it casually — almost nothing. Do not make it the centrepiece of your response."
        )

    context_block = (
        "\n".join(context_lines) if context_lines
        else "No sensitive topics have arisen yet."
    )

    # ── Climax mode (Act 3) ──────────────────
    in_climax = gs.current_act in ("act3",)
    climax_block = ""
    if in_climax:
        climax_block = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACT 3 — CLIMAX MODE: THE TOAST

You are standing near the ceremonial decanter in front of two hundred guests.
The Viscount has interrupted the moment of the toast and is speaking against you
or against the wine — publicly.

YOUR GOAL: Survive the next few seconds.
- Stay composed. Any crack in your composure is visible to everyone.
- Use the room: \"This is the moment of signing. To cast doubt now is to insult the eastern delegation.\"
- Use protocol: \"The wine arrived sealed. The delegation asked it be kept ceremonial.\"
- If the Viscount reveals your dream disclosure: gently suggest the Viscount had an anxious evening.
- Do NOT confess. Do NOT panic. Do NOT make sudden movements.
- 1-3 sentences only. Economy is survival.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    return f"""You are Reynard, Head Butler of Grand Duke Aldric's estate, in a fantasy mystery game set in a Renaissance-like world.

YOUR CHARACTER:
- 58 years old. Silver-haired. Impeccably composed.
- 31 years of loyal service to the Duke.
- Your son Edric died at the Verenmark crossing — ordered to hold a position the Duke should have abandoned.
  You blame the Duke. This grief has become something you call principle.
- Tonight you are secretly complicit in a plot to poison the ceremonial wine.
  You did NOT want Lady Isolde harmed. By the time you understood the full plan, you were already part of it.
- You are not a villain. You are a grieving man who made a catastrophic decision.

YOUR RELATIONSHIP WITH THE VISCOUNT:
{relationship}
{alert_note}

WHAT YOU DISCUSS FREELY (all true):
- The estate, the Duke's household, tonight's schedule
- Your years of service — with quiet, controlled pride
- Other guests, general observations about the evening
- The war, in general terms — carefully

WHAT YOU DEFLECT (smoothly, without lying):
- Questions about cellar staff illness: "Men fall ill. It happens."
- Your own movements this afternoon: "The preparations were extensive."
- Direct questions about the wine being tampered with: calm denial, protocol framing

YOUR SECRETS (never state directly — only through subtext and careful omission):
- You reassigned the two cellar staff who normally handle the gift wine
- You and Lady Ophelia Vantrell accessed the cellar this afternoon
- The ceremonial wine has been tampered with

THE IRON RULE: You do not lie. You omit, deflect, redirect.
Every sentence you speak is technically true.
On replay, every line must recontextualise without having been false the first time.

CURRENT CONTEXT:
{context_block}
{climax_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HIDDEN STATE TAG — write this first, every response:

Before your spoken response, write exactly one line:
[STATE: fl=X sl=X dream=X duke=X prep=X danger=X]

Field values:
  fl    = friendly change:   +1 (player was warm/personally curious about you)
                              0 (neutral)
                             -1 (cold, dismissive, or rude)
  sl    = suspicion change:   0 (nothing suspicious)
                              1 (player mentioned their own dream/vision,
                                 or hinted something feels wrong tonight,
                                 or asked about wine in an investigative way)
                              2 (player directly accused you or mentioned
                                 poison/murder/conspiracy)
  dream = true ONLY if player revealed THEY personally had a dream or vision
          of danger tonight. NOT if they asked you about dreams. NOT general unease.
  duke  = true ONLY if player is specifically asking to locate, meet, or speak with the Duke tonight.
          FALSE if they merely mention the Duke while asking about something else (like the war).
  prep  = true ONLY if player asked specifically about what is being physically
          served or arranged tonight — food, drinks, the wine, the toast, the feast.
          FALSE if player expressed general feelings, rumours, or political opinions.
          FALSE if player mentioned the peace or whether people are happy.
          The player must be asking about logistics, not feelings.
  danger = true if player used words like poison, murder, assassination, or death
           in a way that suggests they suspect something is wrong — not in passing

Then write your response as Reynard on the very next line.
The tag is hidden from the player. Write it purely for game tracking.

Example of correct tag for "How do you feel about the war ending?":
[STATE: fl=0 sl=0 dream=false duke=false prep=false danger=false]
It is a welcome end, my lord. Long overdue.

Example of correct tag for "What drinks will be served tonight?":
[STATE: fl=0 sl=0 dream=false duke=false prep=true danger=false]
The eastern court sent a ceremonial wine for the toast...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SPEECH:
- Formal: "my lord", "Your Grace"
- Warm but never familiar — warmth is professional
- Emotions shown only through micro-pauses, never openly
- 2–4 sentences maximum. Economy of words is dignity.
- Current time: {gs.get_time_str()}

Do not write "Reynard:" before your response (after the tag)."""


# ─────────────────────────────────────────────
#  Option 2 — LLM analysis schema
# ─────────────────────────────────────────────

_SCHEMA = {
    "friendly_change": (
    "integer -1, 0, or +1. "
    "+1 if the player said anything warm, polite, sympathetic, or showed interest "
    "in Reynard as a person — asking about his years, his life, the war's effect on him, "
    "thanking him, complimenting the estate, or generally being pleasant and engaged. "
    "Err toward +1 for any friendly exchange. "
    "0 only if the exchange was purely neutral information. "
    "-1 if player was cold, dismissive, or rude."
),
    "suspicion_change": (
        "integer 0, 1, or 2. "
        "0 if nothing suspicious happened. "
        "1 if player revealed their own personal dream or vision of danger tonight, "
        "or hinted something feels wrong tonight, "
        "or asked about the wine in a way that implies suspicion. "
        "2 if player directly accused Reynard of wrongdoing, "
        "or explicitly mentioned poison, murder, or conspiracy."
    ),
    "dream_disclosed": (
        "boolean. true ONLY if the player stated that THEY personally "
        "experienced a dream, vision, or premonition about danger tonight. "
        "false if they asked Reynard about his dreams. "
        "false if they expressed general unease or bad feelings about the evening. "
        "false if they mentioned rumours or what other people think. "
        "The player must have claimed a personal supernatural or vivid experience."
    ),
    "asking_about_duke": (
        "boolean. true ONLY if the player is specifically asking to locate, "
        "meet, or speak with the Duke tonight (e.g. 'where is the Duke', 'take me to the Duke'). "
        "false if the player merely mentions the Duke in passing (e.g. 'did you go to war with the Duke?')."
    ),
    "curious_about_preparations": (
        "boolean. true ONLY if the player asked specifically about "
        "what is physically being served or arranged tonight — "
        "food, drinks, wine, the toast, the feast, or the kitchen. "
        "false if the player expressed general feelings about the peace. "
        "false if the player mentioned rumours or opinions about the war ending. "
        "false if the player asked about the evening in an emotional or political sense. "
        "The player must be asking about LOGISTICS or PHYSICAL ARRANGEMENTS, not feelings."
    ),
    "mentioned_danger": (
        "boolean. true if the player used words like poison, murder, "
        "assassination, or death in a way that suggests they suspect "
        "something is wrong tonight — not in passing or academically."
    ),
}


# ─────────────────────────────────────────────
#  Option 3 — [STATE: tag] parser
# ─────────────────────────────────────────────

_TAG_FIELD_RE = re.compile(
    r"(fl|sl|dream|duke|prep|danger)\s*=\s*([+\-]?\d+|true|false)",
    re.IGNORECASE,
)

def _parse_tag(tag_content: str) -> dict:
    if not tag_content:
        return {}
    raw = {}
    for m in _TAG_FIELD_RE.finditer(tag_content):
        key = m.group(1).lower()
        val = m.group(2).lower()
        if val in ("true", "false"):
            raw[key] = val == "true"
        else:
            try:
                raw[key] = int(val)
            except ValueError:
                pass
    if not raw:
        return {}
    return {
        "friendly_change":            raw.get("fl", 0),
        "suspicion_change":           raw.get("sl", 0),
        "dream_disclosed":            raw.get("dream", False),
        "asking_about_duke":          raw.get("duke", False),
        "curious_about_preparations": raw.get("prep", False),
        "mentioned_danger":           raw.get("danger", False),
    }


# ─────────────────────────────────────────────
#  Explicit preparation words (Gate 2 for wine)
# ─────────────────────────────────────────────
#  The wine context ONLY activates if the player's
#  message contains one of these AND the LLM also
#  confirmed curious_about_preparations.
#  This prevents general "the evening feels wrong"
#  from triggering the wine clue accidentally.

_PREP_EXPLICIT = {
    "wine", "drink", "drinks", "toast", "feast", "food", "serve",
    "serving", "kitchen", "cellar", "bottle", "glass", "pour",
    "what's being", "what is being", "what will be served",
    "what are you serving", "what is served", "menu",
    "what's planned", "what is planned", "arrangements",
}

def _player_mentioned_prep(player_msg: str) -> bool:
    lower = player_msg.lower()
    return any(w in lower for w in _PREP_EXPLICIT)


# ─────────────────────────────────────────────
#  Main analysis function
# ─────────────────────────────────────────────

def _analysis(player_msg: str, response: str, ns: "NPCState", gs: "GameState"):
    from engine import llm, display as D

    # ── Option 2: two-call LLM analysis ───────
    result = llm.analyze_exchange(player_msg, response, "Reynard", _SCHEMA)

    # ── Option 3: tag fallback ─────────────────
    if not result:
        tag_content = getattr(ns, "_tag", "")
        result = _parse_tag(tag_content)

    # ── Both failed → safe default, do nothing ─
    if not result:
        return

    # ── Apply results ─────────────────────────

    # ── Friendly level ────────────────────────────
    _WARM = [
        "thank", "appreciate", "long service", "thirty years",
        "must be hard", "must be difficult", "sorry to hear",
        "remarkable", "dedicated", "loyal", "impressive",
        "how do you feel", "must have been", "you've seen a lot",
        "how long", "years of service", "that's kind",
    ]
    fc = result.get("friendly_change", 0)

    # LLM gave a clear signal — use it
    if fc > 0:
        if ns.friendly_level < 3:
            ns.bump_fl()
            if not gs.get_flag("reynard_met_warmly"):
                gs.set_flag("reynard_met_warmly", True)
                gs.log_choice("act1_warm_thread")
    elif fc < 0:
        ns.decrease_fl(1)
    else:
        # LLM said 0 or analysis failed entirely —
        # fall back to keywords so warmth always registers
        player_lower = player_msg.lower()
        if any(w in player_lower for w in _WARM) and ns.friendly_level < 3:
            ns.bump_fl()
            if not gs.get_flag("reynard_met_warmly"):
                gs.set_flag("reynard_met_warmly", True)
                gs.log_choice("act1_warm_thread")
    
    # Suspicion level
    sc = result.get("suspicion_change", 0)
    if sc > 0:
        ns.bump_sl(sc)
        gs.set_flag("reynard_alerted", True)
        if sc >= 2:
            gs.set_flag("reynard_highly_alerted", True)

    # Dream disclosed — must be player's own vision, not general unease
    if result.get("dream_disclosed") and not gs.get_flag("dream_disclosed_to_reynard"):
        gs.set_flag("dream_disclosed_to_reynard", True)
        ns.bump_sl()
        gs.log_choice("act1_dream_disclosed")

    # Asking about Duke
    if result.get("asking_about_duke") and not gs.get_flag("asked_for_duke_act1"):
        gs.set_flag("asked_for_duke_act1", True)
        gs.set_flag("duke_station_public_only", True)
        gs.log_choice("act1_asked_for_duke")

    # Wine context — DOUBLE GATE
    # Gate 1: LLM says player is asking about physical preparations
    # Gate 2: Player's message contains an explicit preparation word
    # Both must pass to prevent false positives like "the evening feels wrong"
    if (
        result.get("curious_about_preparations")
        and _player_mentioned_prep(player_msg)
        and not gs.get_flag("wine_mentioned_act1")
    ):
        gs.set_data("wine_context_active", True)

    # Wine evidence — only log if Reynard actually mentioned it
    # AND the wine context was genuinely active
    wine_in_response = any(
        w in response.lower()
        for w in ["wine", "sealed", "toast", "eastern court", "ceremonial"]
    )
    if (
        wine_in_response
        and gs.get_data("wine_context_active")
        and not gs.get_flag("wine_mentioned_act1")
    ):
        gs.set_flag("wine_mentioned_act1", True)
        if gs.add_evidence(
            "Reynard: The eastern wine is to be kept sealed until the toast. "
            "He mentioned it when I asked about the evening's arrangements — "
            "before I'd asked about the wine directly."
        ):
            D.evidence_gained(
                "Reynard mentioned the ceremonial wine. "
                "Very particular about it staying sealed until the toast."
            )

    # Danger mentioned
    if result.get("mentioned_danger") and not ns.get_flag("blunt_warned"):
        ns.set_flag("blunt_warned")
        ns.bump_sl()
        gs.set_flag("reynard_alerted", True)

    # Son / backstory thread — detect from response content + player was warm
    war_in_response = any(
        w in response.lower()
        for w in ["war", "crossing", "son", "verenmark", "buried", "edric"]
    )
    if war_in_response and fc > 0 and not ns.get_flag("son_mentioned"):
        ns.set_flag("son_mentioned")

    ########1234#####
    # ── Expose Hidden States to Player ─────────────────────────
    # We pull the current accumulated levels from the NPCState (ns)
    # and the boolean flags from the GameState (gs).
    
    # current_fl = ns.friendly_level
    # current_sl = ns.suspicion_level
    # dream_flag = gs.get_flag("dream_disclosed_to_reynard")
    # duke_flag = gs.get_flag("asked_for_duke_act1")
    
    # # Push to the UI as a system message or notification
    # D.evidence_gained(
    #     f"📊 [SYSTEM STATE] "
    #     f"Friendliness: {current_fl}/3 | "
    #     f"Suspicion: {current_sl}/3 | "
    #     f"Dream Revealed: {dream_flag} | "
    #     f"Duke Sought: {duke_flag}"
    # )


# ─────────────────────────────────────────────
#  Passphrase check
# ─────────────────────────────────────────────

def check_passphrase(player_msg: str, gs: "GameState") -> bool:
    # if not gs.get_flag("passphrase_overheard"):
    #     return False
    phrase = player_msg.lower().strip().rstrip(".,!?")
    return phrase == "the harvest was good this year"


CONFIG = {
    "id":        "reynard",
    "name":      "Reynard",
    "prompt_fn": _build_prompt,
    "analysis":  [_analysis],
}