# ─────────────────────────────────────────────
#  story/act3.py — The Toast
# ─────────────────────────────────────────────

from engine import display as D
from engine import llm
from engine.game_state import GameState
from engine.npc import NPC

from npcs.reynard import CONFIG as REYNARD
from npcs.cassian import CONFIG as CASSIAN
from npcs.isolde  import CONFIG as ISOLDE


def run(gs: GameState):
    D.clear()
    D.scene_header("ACT 3  —  THE TOAST", gs.get_time_str())
    D.narrate(
        "The hall has gone quiet.\n\n"
        "Duke Aldric stands at the front of the room. "
        "Reynard is near the side table — the eastern wine poured into "
        "the ceremonial decanter, several glasses set out.\n\n"
        "Lady Isolde is a few steps behind her father."
    )
    D.pause()
    D.npc_speak(
        "Duke Aldric",
        "Friends. Guests. After ten years — tonight we sign. "
        "And then we drink, as people who will not fight each other again."
    )
    D.narrate("Glasses are being lifted. You have one moment.")
    D.pause()
    _run_confrontation(gs)


def _run_confrontation(gs: GameState):
    ev = gs.evidence_score()
    options = []

    if ev >= 3 and gs.get_flag("illness_discovered"):
        options.append(("STAFF",
            '"Stop. That wine was tampered with — Reynard cleared the cellar staff who would have handled it."'))
    if ev >= 2 and gs.get_flag("wine_seal_discovered"):
        options.append(("SEAL",
            '"Your Grace — the seal on that wine was reapplied. It was opened before tonight."'))
    if ev >= 2 and gs.get_flag("cellar_log_found"):
        options.append(("LOG",
            '"Reynard moved those bottles to the serving rack this afternoon. His own handwriting."'))
    if ev >= 2 and gs.get_flag("balcony_vision_seen"):
        options.append(("VISION",
            '"Your Grace — please. Don\'t drink yet. I have seen what happens if you do."'))
    if ev >= 4 and gs.get_flag("ophelia_alerted"):
        options.append(("OPHELIA",
            '"Ophelia Vantrell and Reynard. Together at the cellar, this afternoon."'))

    options.append(("PHYSICAL", "Move — step between Isolde and her glass."))
    options.append(("PLEA",     '"Please. Something is wrong with that wine."'))
    options.append(("SACRIFICE","Reach across and drink from Isolde\'s glass yourself."))

    D.narrate("What do you do?")
    choice = D.get_choice(options)

    {
        "STAFF":    _confront_staff,
        "SEAL":     _confront_seal,
        "LOG":      _confront_log,
        "VISION":   _confront_vision,
        "OPHELIA":  _confront_ophelia,
        "PHYSICAL": _confront_physical,
        "PLEA":     _confront_plea,
        "SACRIFICE":_confront_sacrifice,
    }[choice](gs)


def _confront_staff(gs: GameState):
    reynard = NPC(REYNARD, gs)
    cassian = NPC(CASSIAN, gs)

    D.player_line(
        "Stop. That wine was tampered with. "
        "Reynard cleared the cellar staff who would normally handle it — "
        "both fell suddenly ill this afternoon."
    )
    D.narrate("The hall goes quiet differently now.")

    resp = reynard.speak(
        "The Viscount has publicly accused you of clearing the cellar staff "
        "to tamper with the wine. Respond calmly in front of two hundred guests. "
        "One to two sentences."
    )
    D.npc_speak("Reynard", resp)
    D.narrate("He is perfectly calm. Two hundred people are watching.")

    follow = []
    if gs.get_flag("illness_discovered"):
        follow.append(("PUSH_ILL",
            '"Convenient illness — both men incapacitated by four o\'clock, the same afternoon."'))
    if gs.get_flag("cellar_log_found"):
        follow.append(("PUSH_LOG",
            '"Your own cellar log shows you moved those bottles. In your handwriting."'))
    follow.append(("HOLD", "Say nothing more — let it land."))

    c2 = D.get_choice(follow)

    if c2 == "PUSH_ILL":
        D.player_line("Convenient illness — both men incapacitated by four o'clock this afternoon.")
        resp2 = cassian.speak(
            "Step forward warmly and make the accusation seem unreasonable. One to two sentences."
        )
        D.npc_speak("Lord Cassian", resp2)
    elif c2 == "PUSH_LOG":
        D.player_line("Your own cellar log shows you moved those bottles. In your handwriting.")
        D.narrate("A pause longer than any pause tonight. The Duke looks at Reynard. Reynard does not look back.")

    _duke_decision(gs, gs.evidence_score())


def _confront_seal(gs: GameState):
    cassian = NPC(CASSIAN, gs)
    D.player_line(
        "Your Grace — the seal on that wine was reapplied. "
        "It was opened before tonight. The colour doesn't match the provenance letter."
    )
    D.npc_speak("Reynard",
        "A resealed bottle could have occurred in transit, my lord. These things happen.")
    resp = cassian.speak(
        "Make the accusation seem reckless at a peace signing. One to two sentences."
    )
    D.npc_speak("Lord Cassian", resp)
    _duke_decision(gs, gs.evidence_score())


def _confront_log(gs: GameState):
    reynard = NPC(REYNARD, gs)
    D.player_line(
        "Reynard personally moved those bottles to the serving rack this afternoon. "
        "It's in the cellar log. His own handwriting."
    )
    D.narrate("He doesn't answer immediately. The Duke notices the pause.")
    D.npc_speak("Duke Aldric", "Reynard. Is this true?")
    resp = reynard.speak(
        "Answer honestly but evasively — you did move them, frame it as routine. One sentence."
    )
    D.npc_speak("Reynard", resp)
    D.narrate("The Duke watches him a moment longer than is comfortable.")
    _duke_decision(gs, gs.evidence_score() + 1)


def _confront_vision(gs: GameState):
    reynard = NPC(REYNARD, gs)
    D.player_line("Your Grace — please. Don't drink yet. I have seen what happens if you do.")
    D.narrate("The room goes uncertain.")
    D.npc_speak("Duke Aldric", "Reynard?")

    if gs.get_flag("dream_disclosed_to_reynard"):
        resp = reynard.speak(
            "Use the fact that the Viscount told you about his dream on arrival "
            "to gently discredit him. One to two sentences."
        )
        D.npc_speak("Reynard", resp)
        D.narrate("The room shifts. You told Reynard about your vision on arrival. He is using it against you now.")
        _duke_decision(gs, gs.evidence_score() - 1)
    else:
        resp = reynard.speak(
            "Try to suggest the Viscount has been anxious this evening. One sentence."
        )
        D.npc_speak("Reynard", resp)
        D.npc_speak("Duke Aldric", "He said nothing of anxiety to me, Reynard.")
        D.narrate("A small thing. The Duke noticed.")
        _duke_decision(gs, gs.evidence_score())


def _confront_ophelia(gs: GameState):
    D.player_line("Ophelia Vantrell and Reynard. Together at the cellar door this afternoon. I have seen it.")
    D.narrate("The room goes very still.")
    D.narrate(
        "Lady Ophelia Vantrell takes one half-step toward the corridor.\n\n"
        "Her hand moves — without her noticing — toward a servant about to lift a glass. "
        "She just barely stops herself."
    )
    cassian = NPC(CASSIAN, gs)
    resp = cassian.speak(
        "Begin to defend your sister but let your warmth crack for just a moment. One sentence."
    )
    D.npc_speak("Lord Cassian", resp)
    D.narrate("Cassian's recovery is a half-second too slow. The Duke has already seen it.")
    D.npc_speak("Duke Aldric", "Reynard. Hold the wine.")
    gs.set_flag("wine_stopped")
    gs.set_flag("ophelia_confronted")
    _ophelia_aftermath(gs)


def _confront_physical(gs: GameState):
    D.player_line("...")
    D.narrate("You don't speak. You move.")

    isolde_fl = 0
    try: isolde_fl = gs.get_npc("isolde").friendly_level
    except KeyError: pass

    if isolde_fl >= 2 or gs.get_flag("isolde_will_avoid_wine"):
        D.narrate("Isolde sees you. She sets her glass down and takes a half-step back.")
        D.npc_speak("Lady Isolde", "All right. Talk.")
        gs.set_flag("wine_stopped")
        gs.set_flag("isolde_saved_physical")
        _post_wine_stopped(gs)
    else:
        D.narrate("A guard catches your arm. The room erupts in confused noise.")
        brienne_fl = 0
        try: brienne_fl = gs.get_npc("brienne").friendly_level
        except KeyError: pass

        if brienne_fl >= 2:
            D.narrate("From across the hall, Lady Brienne Marrow stands up.")
            D.npc_speak("Lady Brienne", "Let him speak.")
            D.narrate("The room waits.")
            gs.set_flag("wine_stopped")
            gs.set_flag("brienne_intervened")
            _post_wine_stopped(gs)
        else:
            _ending_d_toast(gs)


def _confront_plea(gs: GameState):
    cassian = NPC(CASSIAN, gs)
    D.player_line("Please. Something is wrong with that wine. Don't drink it.")
    resp = cassian.speak(
        "Handle the plea graciously for the room — warm, sympathetic, devastating. One to two sentences."
    )
    D.npc_speak("Lord Cassian", resp)
    D.narrate("The Duke looks at you. You have nothing concrete. He shakes his head slightly.")

    isolde_fl = 0
    try: isolde_fl = gs.get_npc("isolde").friendly_level
    except KeyError: pass

    if isolde_fl >= 2 or gs.get_flag("isolde_will_avoid_wine"):
        D.narrate(
            "From across the room, Isolde meets your eyes.\n\n"
            "She sets down her glass without drinking. Claims a headache.\n\n"
            "She doesn't know why you warned her. She trusts you anyway."
        )
        gs.set_flag("wine_stopped")
        gs.set_flag("isolde_saved_by_trust")
        _post_wine_stopped(gs)
    else:
        _toast_proceeds(gs, "no_evidence")


def _confront_sacrifice(gs: GameState):
    D.player_line("...")
    D.narrate(
        "You reach across, lift Isolde's glass, and drink from it."
    )
    D.npc_speak("Lady Isolde", "What — what are you—")
    D.narrate("You say nothing. You set the glass down. You wait.")
    D.pause()
    D.narrate(
        "The poison is slow by design. You don't know tonight "
        "whether you have killed yourself or made a very dramatic point."
    )
    _ending_g(gs)


def _duke_decision(gs: GameState, effective_ev: int):
    if gs.get_flag("duke_held_wine") or effective_ev >= 3:
        D.npc_speak("Duke Aldric", "You're certain.")
        D.narrate("He looks at you. Then at the wine. Then at Reynard.\n\nA long moment.")
        D.npc_speak("Duke Aldric", "Hold the wine. Pending a precautionary inspection.")
        D.narrate("He frames it as tradition. The foreign delegation exchanges glances.")
        D.npc_speak("Duke Aldric", "Reynard.")
        gs.set_flag("wine_stopped")
        gs.set_flag("duke_held_wine")
        _post_wine_stopped(gs)
    elif effective_ev >= 2:
        D.npc_speak("Duke Aldric", "Viscount. I will take your concern under advisement. One moment.")
        D.narrate("He gestures for the wine to be held — awkwardly, apologetically. Not a full stop, but a pause.")
        gs.set_flag("wine_stopped")
        _post_wine_stopped(gs)
    else:
        D.npc_speak("Duke Aldric",
            "Viscount, I appreciate your concern. But I will not insult our guests on a feeling.")
        _toast_proceeds(gs, "duke_not_convinced")


def _post_wine_stopped(gs: GameState):
    if gs.get_flag("ophelia_confronted"):
        _ophelia_aftermath(gs)
        return

    D.narrate(
        "With the crisis paused the room redistributes its attention. "
        "Cassian is talking — managing, perfect as always. You look past him."
    )
    D.narrate(
        "Lady Ophelia Vantrell has taken one half-step toward the corridor. "
        "Her hand moves toward a servant about to lift a glass — "
        "and she just barely stops herself."
    )
    D.narrate("You notice Lady Ophelia's hand reach toward the tray. Then freeze.")
    D.pause()

    choice = D.get_choice([
        ("NAME",  '"Her. Lady Ophelia Vantrell — she knows exactly what is in that wine."'),
        ("WATCH", "Say nothing. Watch what she does next."),
    ])

    if choice == "NAME":
        D.player_line("Her. Lady Ophelia Vantrell — she knows exactly what is in that wine.")
        D.narrate("Cassian's warmth finally cracks. Just for a moment.")
        D.npc_speak("Duke Aldric", "Guards. Both of them. Now.")
        gs.set_flag("ophelia_caught")
        gs.set_flag("cassian_caught")
        _reynard_moment(gs)
        _ending_a(gs)
    else:
        D.narrate(
            "Ophelia moves toward the corridor — not quite fleeing, but leaving. "
            "By the time anyone notices, she is gone.\n\n"
            "Cassian is arrested an hour later on Reynard's testimony."
        )
        gs.set_flag("cassian_caught")
        _reynard_moment(gs)
        _ending_b(gs)


def _ophelia_aftermath(gs: GameState):
    D.narrate("Ophelia does not run. She stands very still — every exit calculated and closed.")
    D.npc_speak("Duke Aldric", "Guards — Lady Ophelia. Lord Cassian. No one leaves this hall.")
    gs.set_flag("ophelia_caught")
    gs.set_flag("cassian_caught")
    _reynard_moment(gs)
    _ending_a(gs)


def _reynard_moment(gs: GameState):
    D.narrate("Before the guards reach Reynard, you cross to him. He is standing very still.")

    choice = D.get_choice([
        ("WHY",     '"Why, Reynard? Thirty-one years."'),
        ("NOTHING", "Say nothing. Let the guards take him."),
    ])

    if choice == "NOTHING":
        D.narrate("He submits without a word. His face gives nothing.")
        return

    D.player_line("Why, Reynard? Thirty-one years.")
    D.narrate("The composure goes. Not dramatically. It just stops.")

    reynard = NPC(REYNARD, gs)
    D.npc_speak("Reynard",
        "My son held the Verenmark crossing for four days. "
        "Command said reinforcements were coming. They weren't. "
        "He knew by the third day. He held anyway — because those were his orders.")
    D.pause()
    D.npc_speak("Reynard",
        "His Grace gave that order. "
        "And tonight he stands at a signing table and calls it peace.")
    D.pause()
    D.npc_speak("Reynard",
        "I didn't want the girl hurt. I told them — not her. "
        "But by the time I understood what Vantrell actually wanted, "
        "I was already part of it.")
    D.pause()

    reynard_fl = 0
    try: reynard_fl = gs.get_npc("reynard").friendly_level
    except KeyError: pass

    if reynard_fl >= 1 and gs.get_flag("reynard_met_warmly"):
        c2 = D.get_choice([
            ("REACH",   '"You could still do something right. Testify. Tell the Duke everything."'),
            ("GRIEF",   '"He\'ll have to live with what he ordered too. You know that."'),
            ("CONDEMN", '"You\'ll answer for what you nearly did."'),
        ])
        if c2 in ("REACH", "GRIEF"):
            D.player_line(
                "You could still do something right. Testify." if c2 == "REACH"
                else "He'll have to live with what he ordered too. Maybe that's the point."
            )
            D.npc_speak("Reynard", "He'll never forgive me.")
            D.player_line("He'll have to try.")
            D.narrate(
                "Reynard turns — not toward the guards, toward the Duke — and begins to speak.\n\n"
                "His testimony takes twenty minutes. Thorough. "
                "Names every meeting, every instruction, everything.\n\n"
                "Cassian's legal defence collapses before it begins."
            )
            gs.set_flag("reynard_testified")
        else:
            D.player_line("You'll answer for what you nearly did.")
            D.npc_speak("Reynard", "Yes. I will.")
            D.narrate("He submits to arrest. Nothing more is said.")
    else:
        D.narrate("There is nothing left to say. The guards take him.")
    D.pause()


def _toast_proceeds(gs: GameState, reason: str):
    D.narrate("The Duke raises his glass. The room follows.")
    D.pause()

    if gs.get_flag("isolde_will_avoid_wine"):
        isolde_fl = 0
        try: isolde_fl = gs.get_npc("isolde").friendly_level
        except KeyError: pass
        if isolde_fl >= 2:
            D.narrate(
                "Isolde lifts her glass — and sets it down again without drinking. "
                "A quiet headache, she tells her father. No one notices except you."
            )
            gs.set_flag("isolde_saved_quietly")
            _post_wine_stopped(gs)
            return

    D.narrate("The wine is drunk. The toast is made.")
    D.pause()
    D.narrate(
        "Twenty minutes later, a physician is running.\n\n"
        "Lady Isolde collapses near the east corridor."
    )
    D.pause()
    _ending_f(gs) if reason == "no_evidence" else _ending_c(gs)


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
    D.npc_speak("Lady Isolde",
        "I didn't know who you were, when you warned me. I almost didn't listen.")
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
    D.narrate("You watch the Duke sign the treaty and think: this is a victory.\n\nPartial. Enough.\n\nEnough for now.")
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
        "At midnight, a glass shatters on the far side of the hall.\n\nIsodle."
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


def _ending_d_toast(gs: GameState):
    D.clear()
    D.scene_header("ENDING D  —  THE DUNGEON")
    D.narrate(
        "Reynard moves efficiently. You are removed from the hall.\n\n"
        "You hear the toast from below.\n\n"
        "Then a physician's footsteps, running, overhead.\n\n"
        "In the dark, you put your head in your hands.\n\n"
        "The vision was real. You just couldn't stop it alone."
    )
    D.pause()
    gs.current_act = "ending_d"
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
    D.narrate("You consider this for a moment.\n\nYou have been told you're not always the best at telling the difference.")
    D.pause()
    gs.current_act = "ending_g"
    gs.save()
    _credits(gs)


def _credits(gs: GameState):
    D.pause()
    D.clear()
    ending   = gs.current_act.replace("ending_", "").upper()
    evidence = len(gs.evidence_log)
    ev_score = gs.evidence_score()
    choices  = len(gs.player_choices)
    D.scene_header("THE END")
    D.narrate(
        f"Ending:    {ending}\n"
        f"Evidence:  {evidence} items  ({ev_score} key conspiracy clues)\n"
        f"Choices:   {choices} recorded"
    )
    D.narrate(
        "The game can be replayed — different evidence paths lead to different options. "
        "The vision window, the passphrase, Reynard's trust — "
        "some things only reveal themselves on a second pass."
    )
    D.pause("  [dim]Press ENTER to exit.[/dim]")