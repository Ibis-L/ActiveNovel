# ─────────────────────────────────────────────
#  story/act3.py — The Toast
#
#  FREE-WILL CONFRONTATION SYSTEM
#  ─────────────────────────────
#  The player types what they say and do in
#  natural language. A background GM analyser
#  parses their text to:
#    1. Extract what evidence they are citing
#    2. Cross-check it against evidence_log
#       (cannot win by bluffing undiscovered clues)
#    3. Detect physical actions (intercept / sacrifice)
#    4. Build the Duke's "conviction level"
#
#  NPCs respond live via their LLM prompts.
#
#  Conviction thresholds (Duke):
#    0-1  → toast proceeds (failure)
#    2    → wine held, but Ophelia escapes (Ending B)
#    3+   → full arrest, Ending A or variant
#
#  Isolde FL path still works in parallel:
#    If warned properly in Act 2 she avoids wine
#    regardless of confrontation outcome.
# ─────────────────────────────────────────────

from engine import display as D
from engine import llm
from engine.game_state import GameState
from engine.npc import NPC

from npcs.reynard import CONFIG as REYNARD
from npcs.cassian  import CONFIG as CASSIAN
from npcs.isolde   import CONFIG as ISOLDE
from npcs.duke     import CONFIG as DUKE_CFG


# ─────────────────────────────────────────────
#  Entry
# ─────────────────────────────────────────────

def run(gs: GameState):
    D.clear()
    D.scene_header("ACT 3  —  THE TOAST", gs.get_time_str())

    # Initialise the NPCs for this act
    reynard = NPC(REYNARD,   gs)
    cassian = NPC(CASSIAN,   gs)
    duke    = NPC(DUKE_CFG,  gs)
    isolde  = NPC(ISOLDE,    gs)

    D.narrate(
        "The hall has gone quiet.\n\n"
        "Duke Aldric stands at the front of the room. "
        "Reynard is near the side table — the eastern wine poured into "
        "the ceremonial decanter, several glasses set out.\n\n"
        "Lady Isolde is a few steps behind her father.\n\n"
        "The string quartet has stopped. Two hundred people are watching the Duke."
    )
    D.pause()

    D.npc_speak(
        "Duke Aldric",
        "Friends. Guests. After ten years — tonight we sign. "
        "And then we drink, as people who will not fight each other again."
    )
    D.narrate("Glasses are being lifted. Reynard's hand moves toward the decanter.")
    D.pause()

    # ── Isolde self-save path (from Act 2 trust) ──
    isolde_fl = 0
    try:
        isolde_fl = gs.get_npc("isolde").friendly_level
    except KeyError:
        pass

    if gs.get_flag("isolde_will_avoid_wine") and isolde_fl >= 2:
        D.narrate(
            "From across the room, Lady Isolde meets your eyes.\n\n"
            "She lifts her glass — then quietly sets it down. "
            "She mouths something to a lady beside her. A headache, perhaps.\n\n"
            "She trusted you. She does not know why. She does it anyway."
        )
        D.pause()
        gs.set_flag("isolde_saved_quietly")
        _confrontation_loop(gs, reynard, cassian, duke, isolde, isolde_already_safe=True)
    else:
        _confrontation_loop(gs, reynard, cassian, duke, isolde, isolde_already_safe=False)


# ─────────────────────────────────────────────
#  Main Free-Will Confrontation Loop
# ─────────────────────────────────────────────

def _confrontation_loop(
    gs: GameState,
    reynard: NPC, cassian: NPC, duke: NPC, isolde: NPC,
    isolde_already_safe: bool
):
    """
    The player types freely. Every message is analysed by the GM.
    Conviction accumulates. The Duke acts when convinced enough.
    After MAX_TURNS or when player runs out of things to say, the toast proceeds.
    """

    MAX_TURNS = 6   # exchanges before the Duke loses patience
    conviction = 0  # Duke's running total (needs ≥ 2 to stop toast, ≥ 3 for full Ending A)
    all_verified = set()  # accumulate all verified evidence across turns

    # Track if Reynard has been directly accused
    reynard_accused   = False
    vantrell_accused  = False
    warned_dream_used = gs.get_flag("dream_disclosed_to_reynard")

    D.system_msg(
        "The moment is now. Speak freely — say what you must, do what you must.\n"
        "  Type your words or actions in plain language.\n"
        "  ('log' = check evidence  |  blank Enter = say nothing, let the toast happen)"
    )
    D.system_msg("")

    for turn in range(1, MAX_TURNS + 1):

        remaining = MAX_TURNS - turn + 1
        if remaining <= 2:
            D.narrate(
                f"{'One last chance.' if remaining == 1 else 'The Duke is growing impatient.'} "
                "Reynard reaches for the decanter."
            )

        raw = D.get_free_input()

        # ── Special commands ──────────────────────
        if not raw or not raw.strip():
            D.narrate("You say nothing. The Duke raises his glass.")
            D.pause()
            break

        cmd = raw.lower().strip()
        if cmd == "log":
            D.show_evidence(gs.evidence_log)
            continue

        # ── GM Analysis ───────────────────────────
        D.player_line(raw)
        analysis = llm.analyze_confrontation(raw, gs.evidence_log)

        verified   = analysis.get("verified_evidence",   [])
        phantom    = analysis.get("phantom_evidence",    [])
        action     = analysis.get("action")
        strength   = analysis.get("persuasion_strength", 0)
        acc_rey    = analysis.get("targets_reynard",     False)
        acc_van    = analysis.get("targets_vantrell",    False)

        all_verified.update(verified)

        # ── Physical action — short circuit ───────
        if action == "drink_sacrifice":
            _confront_sacrifice(gs, isolde)
            return

        if action == "physical_intercept":
            result = _confront_physical(gs, isolde, reynard)
            if result == "saved":
                conviction = max(conviction, 2)
                _resolve_aftermath(gs, conviction, all_verified, reynard, cassian,
                                   reynard_accused, vantrell_accused, isolde_already_safe)
                return
            elif result == "arrested":
                _ending_d(gs)
                return
            else:  # "brienne_saved" — Brienne intervened, one more turn
                conviction += 1
                continue

        # ── Bluffing with unfound evidence ────────
        if phantom and not verified:
            D.narrate(
                "You make your claim — but the words ring hollow. "
                "You don't actually know that. Not for certain."
            )
            # Cassian pounces
            resp = cassian.speak(
                "The Viscount has made a claim they clearly cannot back up. "
                "Deflect warmly but decisively for the room. One or two sentences."
            )
            D.npc_speak("Lord Cassian", resp)
            continue

        # ── Accusing Reynard ──────────────────────
        if acc_rey and not reynard_accused:
            reynard_accused = True
            ev = gs.evidence_score()
            if ev < 3:
                # Duke tells Reynard — Ending D
                D.narrate(
                    "The Duke's face shifts — not belief, but discomfort. "
                    "He looks at Reynard. Then back at you."
                )
                D.npc_speak(
                    "Duke Aldric",
                    "Viscount, Reynard has served me thirty-one years. "
                    "I will not hear this without proof. "
                    "I will need you to... step aside. For now."
                )
                D.narrate(
                    "He says it quietly. But Reynard heard every word.\n\n"
                    "And Reynard is already moving."
                )
                D.pause()
                _ending_d(gs)
                return
            else:
                # Duke takes it seriously
                D.narrate("A silence falls over the Duke's face that is different from anything tonight.")
                resp = duke.speak(
                    "The Viscount has accused Reynard with serious evidence. "
                    "React with quiet, controlled gravity — not anger, but something deep. "
                    "One to two sentences. You are remembering the Verenmark crossing."
                )
                D.npc_speak("Duke Aldric", resp)
                conviction += 2

        # ── Accusing Vantrells ────────────────────
        if acc_van and not vantrell_accused:
            vantrell_accused = True
            ev = gs.evidence_score()
            if ev < 2:
                resp = cassian.speak(
                    "The Viscount has just accused you publicly with no evidence. "
                    "Handle it with warm, devastating grace. One or two sentences."
                )
                D.npc_speak("Lord Cassian", resp)
            else:
                cassian_resp = cassian.speak(
                    "The Viscount has accused you with real evidence. "
                    "Your warmth cracks for just a moment — then you recover. One sentence."
                )
                D.npc_speak("Lord Cassian", cassian_resp)
                D.narrate("Cassian's recovery is one half-second too slow. The Duke has already seen it.")
                conviction += 1

        # ── Reynard's counter-move (if not accused) ──
        if not acc_rey and verified and "reynard" not in raw.lower():
            # Reynard pre-empts
            if warned_dream_used and "vision" in verified:
                rey_resp = reynard.speak(
                    "The Viscount is using a vision or dream as evidence. "
                    "You know they told you about their dream on arrival — use it gently to discredit. "
                    "One or two sentences, completely calm."
                )
                D.npc_speak("Reynard", rey_resp)
            else:
                rey_resp = reynard.speak(
                    "The Viscount has raised evidence against the wine. Deflect — one calm sentence."
                )
                D.npc_speak("Reynard", rey_resp)

        # ── Score the evidence presented ──────────
        ev_score  = len(verified)
        ev_total  = gs.evidence_score()

        # Conviction per turn based on evidence quality
        turn_conviction = 0
        if ev_score >= 3:
            turn_conviction = 2
        elif ev_score == 2:
            turn_conviction = 1
        elif ev_score == 1 and strength >= 2:
            turn_conviction = 1
        elif strength >= 3 and ev_total >= 4:
            # Very compelling argument even with one piece
            turn_conviction = 1

        conviction += turn_conviction

        # ── Duke's running reaction ───────────────
        _duke_running_reaction(gs, duke, conviction, verified, strength, turn)

        # ── Early win: conviction threshold met ───
        if conviction >= 3:
            D.narrate("The Duke raises one hand. The room stills.")
            D.npc_speak("Duke Aldric", "Hold the wine. Now. All of it.")
            D.narrate(
                "He does not explain himself to the room.\n\n"
                "He doesn't need to. He is the Duke."
            )
            D.pause()
            gs.set_flag("wine_stopped")
            gs.set_flag("duke_held_wine")
            _resolve_aftermath(gs, conviction, all_verified, reynard, cassian,
                               reynard_accused, vantrell_accused, isolde_already_safe)
            return

        elif conviction == 2:
            # Partial — Duke pauses but doesn't fully commit yet
            D.npc_speak(
                "Duke Aldric",
                "Reynard. Hold the wine one moment — a precautionary tradition. "
                "We will speak shortly."
            )
            D.narrate(
                "It is not an arrest. It is not an accusation. "
                "But the decanter stays where it is."
            )
            D.pause()
            gs.set_flag("wine_stopped")
            # Continue the loop — player can push further for full ending

    # ── Loop exhausted — determine outcome ───────
    if gs.get_flag("wine_stopped") or isolde_already_safe:
        _resolve_aftermath(gs, conviction, all_verified, reynard, cassian,
                           reynard_accused, vantrell_accused, isolde_already_safe)
    else:
        D.narrate("You have said what you can. The Duke's patience has run its course.")
        _toast_proceeds(gs)


# ─────────────────────────────────────────────
#  Duke Running Reaction
# ─────────────────────────────────────────────

def _duke_running_reaction(gs: GameState, duke: NPC, conviction: int,
                           verified: list, strength: int, turn: int):
    """
    The Duke reacts each turn based on what's being presented.
    His response is always live LLM — no scripted lines.
    """
    if not verified and strength < 2:
        # Nothing convincing — Duke is polite but doesn't act
        resp = duke.speak(
            f"The Viscount has made a vague or unsubstantiated claim (turn {turn} of {6}). "
            "Respond with measured courtesy — you are not convinced, but you are not dismissive. "
            "One sentence. The room is watching."
        )
        D.npc_speak("Duke Aldric", resp)
        return

    clue_summary = ", ".join(verified) if verified else "general concern"
    conviction_note = (
        "You are not yet convinced enough to act."
        if conviction < 2 else
        "You are beginning to believe this. Something is wrong tonight."
    )

    resp = duke.speak(
        f"The Viscount has just presented evidence: [{clue_summary}]. "
        f"Persuasion strength: {strength}/3. {conviction_note} "
        "Respond proportionally — one to two sentences. You are a man of weight."
    )
    D.npc_speak("Duke Aldric", resp)


# ─────────────────────────────────────────────
#  Physical Intercept
# ─────────────────────────────────────────────

def _confront_physical(gs: GameState, isolde: NPC, reynard: NPC) -> str:
    """
    Player physically moves. Returns: 'saved', 'arrested', 'brienne_saved'.
    """
    D.narrate("You don't speak. You move.")

    isolde_fl = 0
    try:
        isolde_fl = gs.get_npc("isolde").friendly_level
    except KeyError:
        pass

    if isolde_fl >= 2 or gs.get_flag("isolde_will_avoid_wine"):
        D.narrate(
            "Isolde sees you coming across the room.\n\n"
            "Something in her face — she has been watching you all evening. "
            "She sets her glass down. Takes one step back."
        )
        D.npc_speak("Lady Isolde", "All right. Talk.")
        D.pause()
        gs.set_flag("wine_stopped")
        gs.set_flag("isolde_saved_physical")
        return "saved"
    else:
        D.narrate("A guard catches your arm. The room erupts in confused noise.")

        brienne_fl = 0
        try:
            brienne_fl = gs.get_npc("brienne").friendly_level
        except KeyError:
            pass

        if brienne_fl >= 2:
            D.narrate("From across the hall, Lady Brienne Marrow stands up.")
            D.npc_speak("Lady Brienne", "Let him speak.")
            D.narrate(
                "The guard hesitates. The room waits.\n\n"
                "Brienne's voice has the quiet authority of a woman "
                "who has been composing herself all evening."
            )
            D.pause()
            gs.set_flag("wine_stopped")
            gs.set_flag("brienne_intervened")
            return "brienne_saved"
        else:
            return "arrested"


# ─────────────────────────────────────────────
#  Sacrifice
# ─────────────────────────────────────────────

def _confront_sacrifice(gs: GameState, isolde: NPC):
    D.narrate(
        "You can't prove anything.\n\n"
        "The Duke is speaking. Glasses are lifting. "
        "You are standing next to Lady Isolde's glass and you make "
        "the only calculation you have left."
    )
    D.narrate("You reach across. You lift her glass. You drink it.")
    D.npc_speak("Lady Isolde", "What — what are you—")
    D.narrate("You say nothing. You set the glass down. You wait.")
    D.pause()
    D.narrate(
        "The poison is slow — designed to look natural, to strike hours later. "
        "You do not know tonight whether you have killed yourself "
        "or simply made a very theatrical point."
    )
    D.pause()
    _ending_g(gs)


# ─────────────────────────────────────────────
#  Aftermath — Ophelia's Tell & Reynard's Moment
# ─────────────────────────────────────────────

def _resolve_aftermath(
    gs: GameState, conviction: int, all_verified: set,
    reynard: NPC, cassian: NPC,
    reynard_accused: bool, vantrell_accused: bool,
    isolde_already_safe: bool
):
    """
    After the wine is stopped (or Isolde is safe),
    play out the Ophelia tell, Reynard's confession moment,
    and route to the correct ending.
    """

    # ── Ophelia's tell ─────────────────────────
    if not gs.get_flag("ophelia_confronted"):
        D.narrate(
            "With the immediate crisis paused, the room redistributes its attention. "
            "Cassian is talking — managing the crowd, perfectly composed as always. "
            "You look past him.\n\n"
            "Lady Ophelia Vantrell has taken one half-step toward the corridor. "
            "Her hand moves — without her seeming to notice — toward a servant "
            "about to lift one of the wine glasses. She just barely stops herself."
        )
        D.pause()
        D.narrate("You notice Lady Ophelia's hand reach. Then freeze.")
        D.pause()

        D.system_msg("What do you do?")

        # Free text choice at this moment
        raw = D.get_free_input()
        raw_lower = raw.lower() if raw else ""

        names_ophelia = any(w in raw_lower for w in [
            "ophelia", "her", "lady vantrell", "vantrell", "point", "stop", "name", "she"
        ])

        if names_ophelia and raw:
            D.player_line(raw)
            D.narrate("Cassian's warmth finally cracks. Just for a moment. The Duke has seen it.")
            resp = cassian.speak(
                "Your sister has just been publicly named in her tell. "
                "Begin to defend her but let your composure crack for one instant. One sentence."
            )
            D.npc_speak("Lord Cassian", resp)
            D.npc_speak("Duke Aldric", "Guards. Both of them. Now.")
            gs.set_flag("ophelia_caught")
            gs.set_flag("cassian_caught")
            _reynard_moment(gs, reynard)
            if gs.get_flag("easter_egg_activated"):
                _ending_e(gs)
            else:
                _ending_a(gs)
        else:
            D.narrate(
                "You say nothing. Ophelia moves toward the corridor — not quite fleeing, "
                "but leaving.\n\n"
                "By the time anyone notices, she is gone.\n\n"
                "Cassian is arrested an hour later on Reynard's testimony."
            )
            gs.set_flag("cassian_caught")
            _reynard_moment(gs, reynard)
            _ending_b(gs)
    else:
        # Ophelia was already confronted during the confrontation loop
        _reynard_moment(gs, reynard)
        if gs.get_flag("ophelia_caught"):
            _ending_a(gs)
        else:
            _ending_b(gs)


# ─────────────────────────────────────────────
#  Reynard's Final Moment
# ─────────────────────────────────────────────

def _reynard_moment(gs: GameState, reynard: NPC):
    D.narrate("Before the guards reach Reynard, you cross to him. He is standing very still.")

    D.system_msg("Say something to him — or say nothing.")
    raw = D.get_free_input()

    asks_why = any(w in (raw.lower() if raw else "") for w in [
        "why", "thirty", "reason", "years", "son", "edric",
        "crossing", "tell me", "what happened", "how"
    ])

    if not raw or not raw.strip():
        D.narrate("He submits without a word. His face gives nothing.")
        return

    D.player_line(raw)

    if asks_why:
        D.narrate("The composure goes. Not dramatically. It just stops.")
        D.npc_speak(
            "Reynard",
            "My son held the Verenmark crossing for four days. "
            "Command said reinforcements were coming. They weren't. "
            "He knew by the third day. He held anyway — because those were his orders."
        )
        D.pause()
        D.npc_speak(
            "Reynard",
            "His Grace gave that order. "
            "And tonight he stands at a signing table and calls it peace."
        )
        D.pause()
        D.npc_speak(
            "Reynard",
            "I didn't want the girl hurt. I told them — not her. "
            "But by the time I understood what Vantrell actually wanted, "
            "I was already part of it."
        )
        D.pause()

        reynard_fl = 0
        try:
            reynard_fl = gs.get_npc("reynard").friendly_level
        except KeyError:
            pass

        if reynard_fl >= 1 and gs.get_flag("reynard_met_warmly"):
            D.system_msg("Ask him to testify, acknowledge his grief, or condemn him.")
            raw2 = D.get_free_input()
            raw2_lower = raw2.lower() if raw2 else ""

            wants_testimony = any(w in raw2_lower for w in [
                "testify", "tell", "speak", "right", "still", "chance", "come forward"
            ])
            acknowledges_grief = any(w in raw2_lower for w in [
                "understand", "know why", "his grief", "his son", "your son",
                "he'll live", "duke must", "penance"
            ])

            if wants_testimony or acknowledges_grief:
                D.player_line(raw2 if raw2 else "Testify. Tell the Duke everything.")
                D.npc_speak("Reynard", "He'll never forgive me.")
                D.player_line("He'll have to try.")
                D.narrate(
                    "Reynard turns — not toward the guards, toward the Duke — "
                    "and begins to speak.\n\n"
                    "His testimony takes twenty minutes. Thorough. "
                    "Every meeting, every instruction, every name.\n\n"
                    "Cassian's legal defence collapses before it begins."
                )
                gs.set_flag("reynard_testified")
            else:
                D.player_line(raw2 if raw2 else "You'll answer for this.")
                D.npc_speak("Reynard", "Yes. I will.")
                D.narrate("He submits to arrest. Nothing more is said.")
        else:
            D.narrate("There is nothing left to say. The guards take him.")
    else:
        # Player said something else
        D.npc_speak("Reynard", "Yes, my lord.")
        D.narrate("He submits to arrest without resistance.")

    D.pause()


# ─────────────────────────────────────────────
#  Toast Proceeds (Failure paths)
# ─────────────────────────────────────────────

def _toast_proceeds(gs: GameState):
    """Called when the player fails to stop the toast."""

    # Last chance — if Isolde warned and trusted player
    isolde_fl = 0
    try:
        isolde_fl = gs.get_npc("isolde").friendly_level
    except KeyError:
        pass

    if gs.get_flag("isolde_will_avoid_wine") and isolde_fl >= 2:
        D.narrate(
            "The Duke raises his glass. The room follows.\n\n"
            "You watch Isolde across the room. She lifts her glass. "
            "Then quietly sets it down — a small, private decision.\n\n"
            "She claims a headache. No one notices except you."
        )
        D.pause()
        gs.set_flag("isolde_saved_quietly")
        gs.set_flag("wine_stopped")
        _resolve_aftermath(gs, 1, set(), NPC(REYNARD, gs), NPC(CASSIAN, gs),
                           False, False, True)
        return

    D.narrate("The Duke raises his glass. The room follows.")
    D.pause()
    D.narrate("The wine is drunk. The toast is made.")
    D.pause()
    D.narrate(
        "Twenty minutes later, a physician is running.\n\n"
        "Lady Isolde collapses near the east corridor."
    )
    D.pause()

    ev = gs.evidence_score()
    if ev == 0:
        _ending_f(gs)
    else:
        _ending_c(gs)


# ─────────────────────────────────────────────
#  Endings
# ─────────────────────────────────────────────

def _ending_a(gs: GameState):
    D.clear()
    D.scene_header("ENDING A  —  FULL VICTORY")
    D.narrate(
        "No toast. The wine confirmed poisoned before dawn. "
        "Treaty signed anyway — an hour late, everyone shaken. But signed.\n\n"
        "Cassian Vantrell in custody by morning. Ophelia with him.\n\n"
        "Reynard arrested. The Duke speaks to him alone a long time before the guards are called."
    )
    D.pause()
    if gs.get_flag("reynard_testified"):
        D.narrate(
            "Reynard's testimony seals the case. "
            "His fate left to the Duke's discretion. "
            "The Duke does not look like a man who will be lenient — "
            "but he does not look entirely clean either."
        )
        D.pause()
    D.npc_speak(
        "Lady Isolde",
        "I didn't know who you were, when you warned me. I almost didn't listen."
    )
    D.pause()
    D.narrate("The Sight doesn't show you death that night. First time in weeks.")
    D.pause()
    gs.current_act = "ending_a"
    gs.save()
    _credits(gs)


def _ending_b(gs: GameState):
    D.clear()
    D.scene_header("ENDING B  —  PYRRHIC VICTORY")
    D.narrate(
        "The treaty is signed. Isolde is safe.\n\n"
        "Cassian maintains his innocence through an expensive legal defence. "
        "Without Ophelia's testimony the evidence is circumstantial. "
        "He may never face full justice.\n\n"
        "Somewhere, Ophelia Vantrell is on a road out of the country."
    )
    D.pause()
    D.narrate(
        "You watch the Duke sign the treaty and think: this is a victory.\n\n"
        "Partial. Enough.\n\nEnough for now."
    )
    D.pause()
    gs.current_act = "ending_b"
    gs.save()
    _credits(gs)


def _ending_c(gs: GameState):
    D.clear()
    D.scene_header("ENDING C  —  THE WRONG TARGET")
    D.narrate(
        "You spent the night close to Lady Brienne — warned her, stayed near. "
        "She is alive and grateful.\n\n"
        "At midnight, a glass shatters on the far side of the hall.\n\nIsolde."
    )
    D.pause()
    D.narrate(
        "The poison worked slowly — she survives, barely. "
        "The treaty postponed indefinitely. No one is caught. The peace is on ice."
    )
    D.pause()
    D.npc_speak("Lady Brienne", "You protected me all night. I didn't know what from.")
    D.narrate("You didn't either. Not the right thing.")
    D.pause()
    gs.current_act = "ending_c"
    gs.save()
    _credits(gs)


def _ending_d(gs: GameState):
    D.clear()
    D.scene_header("ENDING D  —  THE DUNGEON")
    D.narrate(
        "Reynard moves efficiently. You are removed from the hall.\n\n"
        "Not violently. Not publicly. You are accused of attempting to disrupt "
        "the peace treaty signing. The Duke is regretful but firm.\n\n"
        "You are held in a cellar room for six hours."
    )
    D.pause()
    D.narrate(
        "You hear the toast from below.\n\n"
        "Then a physician's footsteps, running, overhead.\n\n"
        "In the dark, you put your head in your hands.\n\n"
        "The vision was real. You just couldn't stop it alone."
    )
    D.pause()
    gs.current_act = "ending_d"
    gs.save()
    _credits(gs)


def _ending_e(gs: GameState):
    D.clear()
    D.scene_header("ENDING E  —  THE CONSPIRACY CODA")
    D.narrate(
        "Because you walked into Reynard's corridor with the harvest passphrase, "
        "you dismantled the plot from the inside out.\n\n"
        "Every courier, every ledger, and every contingency House Vantrell prepared "
        "is in the Duke's hands before sunrise. Isolde is safe, the treaty is signed, "
        "and the conspiracy's shadow network collapses overnight."
    )
    D.pause()
    D.npc_speak(
        "Duke Aldric",
        "I do not know how you learned their countersign, Viscount — "
        "and perhaps it is wiser for both of us if I never ask."
    )
    D.pause()
    gs.current_act = "ending_e"
    gs.save()
    _credits(gs)


def _ending_f(gs: GameState):
    D.clear()
    D.scene_header("ENDING F  —  TOTAL FAILURE")
    D.narrate(
        "Isolde dies — not tonight, but three days later.\n\n"
        "The foreign delegation is blamed. The treaty is shredded. "
        "Demir is arrested for a crime he did not commit.\n\n"
        "House Vantrell announces its support for justice "
        "and re-establishes its supply contracts within the month.\n\n"
        "The peace lasted eight days."
    )
    D.pause()
    D.narrate(
        "You leave the estate before dawn.\n\n"
        "The Sight doesn't give you another vision for a long time.\n\nIt doesn't need to."
    )
    D.pause()
    gs.current_act = "ending_f"
    gs.save()
    _credits(gs)


def _ending_g(gs: GameState):
    D.clear()
    D.scene_header("ENDING G  —  SELF-SACRIFICE")
    D.narrate(
        "The physician keeps you confined for three days. "
        "The poison was slow by design. You survive — barely.\n\n"
        "The disruption rattles the Vantrells. Ophelia tries to retrieve the original wine "
        "from the cellar the following morning and is found by two servants who report it.\n\n"
        "The case is made by others, in your absence."
    )
    D.pause()
    D.npc_speak("Lady Isolde", "You didn't even know if it would work.")
    D.player_line("No.")
    D.npc_speak("Lady Isolde", "That was either very brave or very stupid.")
    D.pause()
    D.narrate(
        "You consider this for a moment.\n\n"
        "You have been told you're not always the best at telling the difference."
    )
    D.pause()
    gs.current_act = "ending_g"
    gs.save()
    _credits(gs)


# ─────────────────────────────────────────────
#  Ending D path from Act 2 (unused SL path)
# ─────────────────────────────────────────────

def _ending_d_act2(gs: GameState):
    """Called from act2 when Reynard detains the player early."""
    _ending_d(gs)


# ─────────────────────────────────────────────
#  Credits
# ─────────────────────────────────────────────

def _credits(gs: GameState):
    D.pause()
    D.clear()
    ending   = gs.current_act.replace("ending_", "").upper()
    evidence = len(gs.evidence_log)
    ev_score = gs.evidence_score()
    choices  = len(gs.player_choices)

    ending_titles = {
        "A": "ENDING A  —  FULL VICTORY",
        "B": "ENDING B  —  PYRRHIC VICTORY",
        "C": "ENDING C  —  THE WRONG TARGET",
        "D": "ENDING D  —  THE DUNGEON",
        "E": "ENDING E  —  THE CONSPIRACY CODA",
        "F": "ENDING F  —  TOTAL FAILURE",
        "G": "ENDING G  —  THE SACRIFICIAL RECKONING",
    }

    D.scene_header(ending_titles.get(ending, f"ENDING {ending}"))
    D.narrate(
        f"Investigation Records:\n"
        f"  • Clues Discovered: {evidence} recorded ({ev_score}/7 vital conspiracy links)\n"
        f"  • Crossroads Logged: {choices} player decisions\n"
        f"  • Final Chronometer: {gs.get_time_str()}"
    )

    # ── Character Bonds Summary ──
    D.narrate("── Cast Relationships & Impression ──")
    notable_npcs = [
        "reynard", "isolde", "cassian", "ophelia", "duke",
        "brienne", "demir", "kavir", "mrs_alwen", "fenwick"
    ]
    for nid in notable_npcs:
        try:
            n = gs.get_npc(nid)
            fl_bar = "●" * n.friendly_level + "○" * (3 - n.friendly_level)
            sl_bar = "▲" * n.suspicion_level + "△" * (3 - n.suspicion_level)
            mem_count = len(n.memories)
            mem_note = f" · {mem_count} key memories" if mem_count else ""
            if n.times_spoken > 0:
                D.system_msg(f"  {n.name:18s} | Rapport: {fl_bar} | Suspicion: {sl_bar} | {n.times_spoken} exchanges{mem_note}")
        except KeyError:
            pass

    # ── Major Divergence Flags ──
    D.narrate("\n── Notable Choices & Realizations ──")
    milestones = [
        ("reynard_met_warmly",         "✓ Connected with Reynard's grief — unsealed his testimony path"),
        ("dream_disclosed_to_reynard", "⚠ Revealed your vision to Reynard — provided him leverage to doubt you"),
        ("isolde_will_avoid_wine",     "✓ Earned Lady Isolde's profound trust — she protected herself"),
        ("isolde_warned",              "✓ Alerted Isolde to danger"),
        ("wine_seal_discovered",       "✓ Detected the altered wax seal in the cellar"),
        ("cellar_log_found",           "✓ Discovered Reynard's entry in the cellar log"),
        ("balcony_vision_seen",        "✓ Experienced the balcony vision at twilight"),
        ("ophelia_ring_asked",         "✓ Corroborated Ophelia's silver and ruby ring"),
        ("delegation_cleared",         "✓ Unravelled Demir's private dilemma — cleared the eastern delegation"),
        ("reynard_testified",          "★ Reynard stepped forward with complete public confession"),
        ("ophelia_caught",             "✓ Apprehended Ophelia before she could slip away"),
        ("brienne_warned_by_player",   "✓ Sheltered Lady Brienne from the threat notes"),
        ("duke_held_wine",             "✓ Persuaded Duke Aldric to order precautionary inspection"),
        ("easter_egg_activated",       "★ Infiltrated the conspiracy via the secret harvest passphrase"),
    ]
    logged_any = False
    for flag, desc in milestones:
        if gs.get_flag(flag):
            D.system_msg(f"  {desc}")
            logged_any = True
    if not logged_any:
        D.system_msg("  A cautious evening — minimal overt interventions.")

    D.narrate(
        "\n── Narrative Paths & Secrets ──\n"
        "The Viscount's Vigil possesses extensive branching outcomes.\n"
        "Hidden paths include: the balcony vision window, the secret countersign,\n"
        "Isolde's self-preservation route, and turning the Butler before the toast.\n"
        "Replay with different dialogues, tone, and investigative targets to uncover every secret."
    )
    D.pause("  [dim]Press ENTER to conclude your vigil.[/dim]")