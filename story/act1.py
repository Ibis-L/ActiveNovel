# ─────────────────────────────────────────────
#  story/act1.py — Arrival & Reynard
#
#  Free conversation with Reynard.
#  Empty Enter → silence, walk inside.
#  Word count >= 320 AND exchanges >= 6 → Reynard wraps up.
#  SL >= 3 → Reynard has you arrested (dungeon).
#  Passphrase → cold interrogation with credibility meter.
# ─────────────────────────────────────────────

import re
from engine import display as D
from engine import llm
from engine.game_state import GameState
from engine.npc import NPC
from npcs.reynard import CONFIG as REYNARD_CONFIG, check_passphrase

REYNARD_WORD_THRESHOLD = 320
REYNARD_MIN_EXCHANGES  = 6


def run(gs: GameState):
    D.clear()
    D.scene_header("ACT 1  —  THE ESTATE STEPS", gs.get_time_str())

    D.narrate(
        "The carriage door is opened — not by a footman, but by the Head Butler himself.\n\n"
        "REYNARD. Late fifties. Silver-haired. Impeccably composed. "
        "He descends the estate steps personally to meet you.\n\n"
        "A mark of attention. The butler does not greet every guest."
    )

    reynard = NPC(REYNARD_CONFIG, gs)

    D.npc_speak(
        "Reynard",
        "Lord Viscount. His Grace will be glad you've come — "
        "I'll see you through to the hall personally. "
        "Was the road kind to you tonight?"
    )

    D.system_msg(
        "Talk to Reynard freely. "
        "Press Enter on a blank line to fall silent and continue inside."
    )
    D.system_msg("")

    _conversation_loop(reynard, gs)

    if gs.current_act in ("ending_d",):
        return   # already ended

    _enter_hall(gs)

    gs.current_act   = "act2"
    gs.current_scene = "party_floor"
    gs.advance_clock(20)
    gs.save()


# ═══════════════════════════════════════════════
#  Normal conversation loop
# ═══════════════════════════════════════════════

def _conversation_loop(reynard: NPC, gs: GameState):
    while True:
        raw = D.get_free_input()

        if not raw or not raw.strip():
            D.narrate(
                "You say nothing more. "
                "Reynard leads you the rest of the way without another word."
            )
            break

        cmd = raw.lower().strip()

        if cmd == "log":
            D.show_evidence(gs.evidence_log)
            continue
        if cmd == "time":
            D.system_msg(f"The time is {gs.get_time_str()}.")
            continue

        # ── Passphrase ────────────────────────
        if check_passphrase(raw, gs):
            _easter_egg_trigger(gs, reynard)
            return

        # ── LLM response ──────────────────────
        D.player_line(raw)
        response = reynard.speak(raw)

        if response.startswith("[ERROR"):
            D.error_msg(response)
            hist = reynard.state.conversation_history
            if hist: hist.pop()
            if hist: hist.pop()
            continue

        D.npc_speak("Reynard", response)

        # ── Suspicion check ───────────────────
        if reynard.state.suspicion_level >= 3:
            _reynard_arrests_you(gs)
            return

        # ── Word count + exchange gate ─────────
        words     = _word_count(reynard)
        exchanges = reynard.state.times_spoken
        if words >= REYNARD_WORD_THRESHOLD and exchanges >= REYNARD_MIN_EXCHANGES:
            _reynard_wraps_up(reynard, gs)
            break


# ═══════════════════════════════════════════════
#  SL >= 3 — Reynard arrests you
# ═══════════════════════════════════════════════

def _reynard_arrests_you(gs: GameState):
    D.pause()
    D.narrate(
        "Reynard stops walking.\n\n"
        "Not dramatically. He simply stops, and turns, "
        "and looks at you with an expression that has no warmth in it at all."
    )
    D.npc_speak(
        "Reynard",
        "You know rather too much for a guest who has only just arrived, my lord."
    )
    D.narrate("He says it quietly. Almost kindly.")
    D.npc_speak(
        "Reynard",
        "I'm afraid I can't allow you to continue into the hall tonight."
    )
    D.narrate(
        "Two guards appear from a side corridor. "
        "You have exactly enough time to understand "
        "that they were already positioned there.\n\n"
        "Reynard has been a butler for thirty-one years. "
        "He anticipated this before you said the second wrong thing."
    )
    D.pause()
    D.clear()
    D.scene_header("ENDING D  —  THE DUNGEON")
    D.narrate(
        "The room they put you in is not uncomfortable. "
        "That is almost worse — it means this was planned for.\n\n"
        "You can hear the party through the floor above. "
        "Music. Laughter. Then, much later, the sound of a toast.\n\n"
        "Then silence where there should not be silence.\n\n"
        "Then footsteps. Running."
    )
    D.pause()
    D.narrate(
        "In the dark, you put your head in your hands.\n\n"
        "You said too much, too soon, to exactly the wrong person.\n\n"
        "The vision was real. You just couldn't stop it from here."
    )
    D.pause()
    gs.set_flag("ending_d_triggered", True)
    gs.current_act = "ending_d"
    gs.save()


# ═══════════════════════════════════════════════
#  Passphrase — full interrogation path
# ═══════════════════════════════════════════════

_INTERROGATION_SCHEMA = {
    "credibility_change": (
        "integer from -2 to +2. "
        "How much does this answer increase or decrease Reynard's belief "
        "that the player is a genuine operative who knows the plan? "
        "+2: specific, calm, shows insider knowledge. "
        "+1: plausible and composed. "
        "0: vague, neither convincing nor alarming. "
        "-1: evasive, confused, or inconsistent. "
        "-2: directly contradicts what a genuine operative would know, "
        "or player admitted overhearing the phrase, or seems frightened."
    ),
    "seems_investigator": (
        "boolean. true if the answer suggests the player is investigating a plot "
        "rather than part of one — e.g. admitting curiosity, asking questions "
        "instead of answering, or seeming confused about why the phrase matters."
    ),
    "contradicted_themselves": (
        "boolean. true if this answer directly contradicts something "
        "the player said in an earlier answer this interrogation."
    ),
}


def _build_interrogation_prompt(gs: GameState, credibility: int, exchange_num: int) -> str:
    if credibility >= 4:
        stance = (
            "You are beginning to think this person may be genuine. "
            "Still cold and careful, but fractionally less guarded."
        )
    elif credibility <= 1:
        stance = (
            "You are almost certain this person is a threat or a fool. "
            "You are deciding whether to end this now."
        )
    else:
        stance = (
            "You are not convinced either way. "
            "You are methodical. Every answer is being weighed."
        )

    questions = [
        "Your first question: 'Who sent you? I was not told to expect anyone.'",
        "Your second question: 'What do you know about tonight specifically? Not the phrase — the plan.'",
        "Your third question: 'If you are who you claim, you will know what happens after the toast. Tell me.'",
        "Fourth exchange. You have heard enough to form a view. Press them on any inconsistency.",
    ]
    q_hint = questions[min(exchange_num, len(questions) - 1)]

    return f"""You are Reynard, Head Butler of Grand Duke Aldric's estate.

Someone has just spoken the conspiracy passphrase. You are in a private corridor.
You are NOT the warm professional butler right now.
You are an operative assessing a potential threat or unexpected asset.

YOUR MANNER:
- Cold. Efficient. Not threatening yet, but capable of it.
- No pleasantries. No "my lord." Short, direct questions.
- You confirm nothing about the plan until you are satisfied.
- You are running an assessment. Every word they say is evidence.

CURRENT ASSESSMENT: {stance}

WHAT A GENUINE OPERATIVE WOULD KNOW:
- The passphrase and its countersign
- That House Vantrell is involved
- That the plan concerns the ceremonial wine tonight
- That the goal is to implicate the foreign delegation
You do not volunteer this. You are asking, not telling.

SUSPICION SIGNALS YOU ARE WATCHING FOR:
- Vague non-answers ("I just know things")
- Admitting they overheard the phrase by accident
- Asking you questions instead of answering yours
- Fear, confusion, or contradiction

{q_hint}

2-3 sentences maximum. Cold, direct, no warmth.
Do not write "Reynard:" before your response."""


def _easter_egg_trigger(gs: GameState, reynard: NPC):
    D.player_line("The harvest was good this year.")
    D.narrate("A pause. Longer than any pause tonight.")
    D.npc_speak("Reynard", "...Better than the war years.")

    D.narrate(
        "Something happens to his face. "
        "The professional warmth leaves it completely — "
        "replaced not by hostility but by nothing. A blank efficiency.\n\n"
        "He glances down the corridor both ways. Steps closer."
    )
    D.npc_speak("Reynard", "Walk with me. Now. Do not speak until I tell you to.")
    D.narrate(
        "He leads you down a servants' corridor. "
        "The party noise fades. A door closes.\n\n"
        "He turns and looks at you the way a man looks at something "
        "he is deciding whether to step on."
    )
    D.npc_speak(
        "Reynard",
        "I was not told to expect anyone tonight. "
        "So either you are very well connected, "
        "or you are very stupid. I am going to find out which."
    )
    D.pause()

    credibility = _interrogation_loop(gs, reynard)

    if credibility >= 5:
        _interrogation_passed(gs)
    else:
        _interrogation_failed(gs)


def _interrogation_loop(gs: GameState, reynard: NPC) -> int:
    credibility       = 3   # neutral start, out of 6
    MAX_EXCHANGES     = 4
    TAG_RE            = re.compile(r"^\[STATE:\s*([^\]]+)\]\s*", re.IGNORECASE)
    interrogation_history = []

    for i in range(MAX_EXCHANGES):
        system = _build_interrogation_prompt(gs, credibility, i)

        # First turn: inject the trigger context so Reynard opens with his question
        if i == 0:
            interrogation_history.append({
                "role": "user",
                "content": "[The player has just spoken the passphrase. You are alone in the corridor. Begin your interrogation.]"
            })

        raw   = llm.chat(system, interrogation_history, temperature=0.6)
        m     = TAG_RE.match(raw.strip())
        clean = raw.strip()[m.end():].strip() if m else raw.strip()

        interrogation_history.append({"role": "assistant", "content": clean})
        D.npc_speak("Reynard", clean)

        if credibility <= 0:
            D.narrate("He has heard enough.")
            break

        # Player answers
        D.system_msg(
            "Answer Reynard. Empty Enter = silence (counts against you)."
        )
        answer = D.get_free_input()

        if not answer or not answer.strip():
            D.narrate("You say nothing.")
            D.npc_speak("Reynard", "Silence. Interesting.")
            credibility -= 1
            interrogation_history.append({"role": "user",      "content": "[The player said nothing.]"})
            interrogation_history.append({"role": "assistant",  "content": "Silence. Interesting."})
        else:
            D.player_line(answer)
            interrogation_history.append({"role": "user", "content": answer})

            result = llm.analyze_exchange(answer, clean, "Reynard", _INTERROGATION_SCHEMA)
            change = result.get("credibility_change", 0)
            credibility = max(0, min(6, credibility + change))

            if result.get("seems_investigator") or result.get("contradicted_themselves"):
                credibility = 0

            # Subtle feedback
            if change >= 2:
                D.narrate("Something in his expression shifts — fractionally.")
            elif change <= -2:
                D.narrate("His eyes go flat.")
            elif change == -1:
                D.narrate("A small pause. He files it away.")

        if credibility <= 0 or credibility >= 5:
            break

    return credibility


def _interrogation_passed(gs: GameState):
    D.narrate(
        "A long moment. He looks at you the way you'd look at a lock "
        "you've just realised is more complex than you thought."
    )
    D.npc_speak(
        "Reynard",
        "All right. Either you're genuine or you're the best liar I've met tonight. "
        "Either way — you've earned five minutes."
    )
    D.narrate("He sits down on a crate and clasps his hands.\n\nFor the first time tonight, he looks tired.")
    D.npc_speak(
        "Reynard",
        "Ask what you need to ask. But understand — if I decide I've made a mistake, "
        "this conversation ends in a way you won't enjoy."
    )
    D.pause()

    gs.set_flag("easter_egg_activated",            True)
    gs.set_flag("easter_egg_interrogation_passed", True)
    gs.log_choice("act1_easter_egg_passed")

    D.system_msg(
        "Easter Egg path open. Reynard will answer questions about the plan. "
        "This route continues in Act 2. Press ENTER to continue."
    )
    D.pause()


def _interrogation_failed(gs: GameState):
    D.narrate("He stands up straight.\n\nThe decision has been made.")
    D.npc_speak(
        "Reynard",
        "You're not one of us. I don't know how you got that phrase — "
        "but you are not leaving this corridor as a problem I have to worry about."
    )
    D.narrate(
        "The door at the end of the corridor opens. "
        "Two guards. They were already there.\n\n"
        "Of course they were."
    )
    D.pause()
    D.clear()
    D.scene_header("ENDING D  —  THE DUNGEON")
    D.narrate(
        "The room is not uncomfortable. That is almost worse.\n\n"
        "You can hear the party through the ceiling. "
        "Music. Laughter. Then, much later, a toast.\n\n"
        "Then silence where there should not be silence.\n\n"
        "Then footsteps. Running."
    )
    D.pause()
    D.narrate(
        "You knew the right words.\n\n"
        "You just didn't know enough of the right answers.\n\n"
        "The vision was real. You just couldn't stop it from here."
    )
    D.pause()
    gs.set_flag("ending_d_triggered", True)
    gs.current_act = "ending_d"
    gs.save()


# ═══════════════════════════════════════════════
#  Natural wrap-up
# ═══════════════════════════════════════════════

def _reynard_wraps_up(reynard: NPC, gs: GameState):
    D.narrate("The corridor opens. The sound of the party swells ahead.")
    closing = reynard.speak(
        "You have reached the entrance to the main hall. "
        "End the walk in one short sentence — you have other guests to attend to. "
        "Stay in character. One sentence only."
    )
    if closing.startswith("[ERROR") or len(closing.strip()) < 5 or len(closing) > 200:
        closing = "The hall is just ahead, my lord — if you'll excuse me, I have others to attend to."
    D.npc_speak("Reynard", closing)
    D.narrate("He steps aside. The doors are open.")


# ═══════════════════════════════════════════════
#  Enter the hall
# ═══════════════════════════════════════════════

def _enter_hall(gs: GameState):
    D.clear()
    D.scene_header("THE MAIN HALL", gs.get_time_str())
    D.narrate(
        "The doors open.\n\n"
        "The hall is enormous. Candlelit. Loud. Guests cluster near the fireplace, "
        "along the tables, at the windows. Servants move with trays. "
        "The string quartet plays something bright.\n\n"
        "Two hundred people who believe tonight is only a celebration."
    )
    if gs.evidence_log:
        D.narrate("You carry what you've gathered — fragments, but a beginning.")
        D.system_msg("Type 'log' during conversations to check your evidence.")
    D.narrate(
        "Somewhere in this room: the culprit. The method. The victim.\n\n"
        "The toast is in three hours."
    )
    D.pause()


# ── Helpers ───────────────────────────────────

def _word_count(reynard: NPC) -> int:
    return sum(
        len(msg.get("content", "").split())
        for msg in reynard.state.conversation_history
    )