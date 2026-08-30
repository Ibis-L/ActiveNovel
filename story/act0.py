# ─────────────────────────────────────────────
#  story/act0.py — The Carriage
#
#  Free conversation with Aldous.
#  No scripted topics. No evidence logging.
#  This is atmosphere — investigation starts Act 1.
#
#  Naturalness system:
#    - Starts at 3 (neutral)
#    - Natural questions (+1), blunt ones (-1/-2)
#    - Controls how long the conversation runs
#      and whether Aldous cuts it short with concern
#    - Score injected into gs.data so Aldous's
#      prompt adapts each exchange
#
#  Conversation ends when:
#    A) Word count exceeds dynamic_threshold(naturalness)
#       → Aldous notices the estate and wraps up
#    B) Naturalness drops to 0
#       → Aldous asks "Are you alright, my lord?"
#          and falls quiet — arrived anyway
#    C) Player types 'leave' / 'done' / 'silent'
# ─────────────────────────────────────────────

import random
from engine import display as D
from engine.game_state import GameState
from engine.npc import NPC
from npcs.aldous import CONFIG as ALDOUS_CONFIG, dynamic_threshold, _count_conversation_words


def run(gs: GameState):
    D.clear()
    D.scene_header("ACT 0  —  THE CARRIAGE", gs.get_time_str())

    D.narrate(
        "The carriage sways on the road. Outside the window, farmland "
        "gives way to forest. The last light of afternoon cuts long through the trees.\n\n"
        "Your coachman Aldous has been quiet since you left. "
        "He knows, as all your staff know, not to speak first "
        "when you've had one of your mornings."
    )
    D.narrate(
        "The vision is still with you. A hall. Red wine. A woman. "
        "The sound of something shattering.\n\n"
        "In a few hours you will be at Grand Duke Aldric's estate. "
        "The peace treaty will be signed tonight. "
        "Two hundred nobles celebrating the end of ten years of war.\n\n"
        "Someone in that room is going to die."
    )
    D.pause()

    D.narrate("The road stretches ahead. Aldous sits steady on the box.")

    choice = D.get_choice([
        ("SPEAK",  "Knock on the roof panel and speak to Aldous."),
        ("SILENT", "Ride in silence — keep your thoughts."),
    ])

    if choice == "SILENT":
        _ride_silent(gs)
    else:
        _ride_talking(gs)

    _arrival(gs)

    gs.game_clock   = 0
    gs.current_act  = "act1"
    gs.current_scene = "arrival"
    gs.save()


# ═══════════════════════════════════════════════
#  Silent path
# ═══════════════════════════════════════════════

def _ride_silent(gs: GameState):
    D.narrate(
        "You pull the curtain and watch the trees pass.\n\n"
        "The vision plays again, uninvited. "
        "The gloved hand. The glass. The gasp.\n\n"
        "You arrive knowing only what you brought with you."
    )
    gs.log_choice("act0_silent")
    D.pause()


# ═══════════════════════════════════════════════
#  Talking path
# ═══════════════════════════════════════════════

def _ride_talking(gs: GameState):
    aldous = NPC(ALDOUS_CONFIG, gs)

    D.narrate("You knock twice on the roof panel. The small window slides open.")
    D.npc_speak("Aldous", "My lord?")

    gs.log_choice("act0_speaking")
    gs.set_data("aldous_naturalness", 3)   # start neutral

    D.system_msg(
        "Talk to Aldous. He is a coachman — "
        "ask naturally and he will talk freely. "
        "Type 'leave' or 'done' to ride in silence."
    )
    D.system_msg("")

    _conversation_loop(aldous, gs)


# ═══════════════════════════════════════════════
#  Naturalness scoring
# ═══════════════════════════════════════════════

# Patterns that feel blunt, suspicious, or unnatural
# for a casual conversation with a coachman
_BLUNT = [
    "tell me about",
    "tell me everything",
    "where are we going",
    "what is our destination",
    "what is the duke",
    "who is the duke",
    "why are we going",
    "what do you know about",
    "who will be there",
    "who is going to be",
    "who else is",
    "what house",
    "is there any danger",
    "do you know of any plot",
    "what can you tell me",
]

# Patterns that feel natural and conversational
_NATURAL = [
    "how do you feel",
    "how do you think",
    "what do you think",
    "do you think",
    "i heard",
    "i imagine",
    "i was wondering",
    "how long",
    "how far",
    "are we nearly",
    "almost there",
    "have you been",
    "have you ever",
    "have you heard",
    "what is it like",
    "what's it like",
    "must be",
    "seems like",
    "do you ever",
    "what was the",
    "how was the",
    "cold tonight",
    "good road",
    "long journey",
    "been a long",
]


def _score_question(text: str) -> int:
    """
    Returns:
        +1  natural, conversational
         0  neutral
        -1  blunt or suspiciously direct
        -2  very blunt / demanding (short commanding questions)
    """
    lower = text.lower().strip()
    words = lower.split()

    # Very short commanding questions are suspicious
    # e.g. "Where are we?" "Who is there?" "Tell me."
    if len(words) <= 3 and any(lower.startswith(w) for w in
                                ["who", "tell", "what is", "where are", "why are"]):
        return -2

    # Blunt patterns
    if any(p in lower for p in _BLUNT):
        return -1

    # Natural patterns
    if any(p in lower for p in _NATURAL):
        return 1

    return 0


# ═══════════════════════════════════════════════
#  Conversation loop
# ═══════════════════════════════════════════════

def _conversation_loop(aldous: NPC, gs: GameState):
    naturalness = gs.get_data("aldous_naturalness", 3)
    
    turn = 0
    max_turn = 7
    while True:
        raw = D.get_free_input()
        if not raw:
            D.narrate("You say nothing more. The road passes in silence.")
            break

        cmd = raw.lower().strip()

        if cmd in ("leave", "done", "silent", "enough", "quiet", "stop",""):
            D.narrate("You slide the panel closed. The road passes in silence.")
            break

        if cmd == "log":
            D.show_evidence(gs.evidence_log)
            continue
        turn+=1
        # Score the question BEFORE sending to LLM
        score      = _score_question(raw)
        naturalness = max(0, min(5, naturalness + score))
        gs.set_data("aldous_naturalness", naturalness)

        # Naturalness hit zero — Aldous is concerned, conversation ends
        if naturalness == 0:
            _aldous_concerned(aldous, gs)
            break

        # Send to LLM (prompt already adapts via gs.data["aldous_naturalness"])
        D.player_line(raw)
        response = aldous.speak(raw)

        if response.startswith("[ERROR"):
            D.error_msg(response)
            hist = aldous.state.conversation_history
            if hist: hist.pop()
            if hist: hist.pop()
            continue

        D.npc_speak("Aldous", response)

        # Word count check AFTER showing response
        words     = _count_conversation_words(aldous.state)
        threshold = dynamic_threshold(naturalness)

        if words >= threshold or turn >= max_turn:
            _aldous_arrival_wrap(aldous, gs, naturalness)
            break


# ═══════════════════════════════════════════════
#  Conversation endings
# ═══════════════════════════════════════════════

def _aldous_concerned(aldous: NPC, gs: GameState):
    """
    Player asked too many blunt/suspicious questions.
    Aldous gently checks in and the conversation trails off.
    """
    lines = [
        "Are you quite alright, my lord? You've been asking some... odd things.",
        "My lord — are you well? You seem unlike yourself tonight.",
        "Forgive me, my lord, but — is something the matter?",
    ]
    D.npc_speak("Aldous", random.choice(lines))
    D.narrate(
        "He falls quiet after that, eyes back on the road.\n\n"
        "The estate is visible through the trees ahead — "
        "you'll be there soon enough."
    )
    gs.log_choice("act0_aldous_concerned")


def _aldous_arrival_wrap(aldous: NPC, gs: GameState, naturalness: int):
    """
    Natural end — enough has been said, the estate is in sight.
    Aldous wraps up and points you toward the lights.
    """
    D.narrate("A change in the road. Smoother gravel. The trees begin to thin.")

    # Ask LLM for a natural closing line
    closing = aldous.speak(
        "You have just noticed the estate lights through the trees ahead. "
        "Wrap up the conversation naturally in one short sentence — "
        "let the lord know you've arrived. Stay in character."
    )

    # Fallback if LLM produces something unhelpful
    if closing.startswith("[ERROR") or len(closing.strip()) < 5 or len(closing) > 200:
        if naturalness >= 3:
            closing = "There she is, my lord. We've made good time."
        else:
            closing = "My lord — the estate. We're here."

    D.npc_speak("Aldous", closing)
    D.narrate("The panel slides closed. The carriage begins to slow.")


# ═══════════════════════════════════════════════
#  Arrival cutscene — always plays
# ═══════════════════════════════════════════════

def _arrival(gs: GameState):
    D.clear()
    D.scene_header("THE ESTATE GATES", "6:58 PM")

    D.narrate(
        "The carriage slows on the gravel drive.\n\n"
        "Through the window: an estate lit from every window. "
        "Other carriages still arriving. Music drifts from inside — "
        "a string quartet, something festive.\n\n"
        "Two hundred people celebrating the end of a war."
    )

    D.narrate("You close your eyes for just a moment.")

    D.vision(
        "A glass at her lips.\n\n"
        "Red wine on white silk.\n\n"
        "The sound of shattering."
    )

    D.narrate(
        "You open your eyes. The gate. The lanterns. A footman coming forward.\n\n"
        "You are here."
    )

    D.pause()