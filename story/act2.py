# ─────────────────────────────────────────────
#  story/act2.py — The Party Floor
#
#  Free-roam investigation. No scripted choices
#  inside NPC conversations — all free talk.
#  Empty Enter always leaves a conversation.
#
#  Station menu (navigation) stays.
#  Cellar physical inspection choices stay.
#
#  Shared helper: _station_talk() handles the
#  free conversation loop for every station.
# ─────────────────────────────────────────────

import random
from engine import display as D
from engine.game_state import GameState
from engine.npc import NPC

from npcs.fenwick   import CONFIG as FENWICK
from npcs.brienne   import CONFIG as BRIENNE
from npcs.cassian   import CONFIG as CASSIAN
from npcs.ophelia   import CONFIG as OPHELIA
from npcs.demir     import CONFIG as DEMIR
from npcs.kavir     import CONFIG as KAVIR
from npcs.isolde    import CONFIG as ISOLDE
from npcs.duke      import CONFIG as DUKE
from npcs.mrs_alwen import CONFIG as ALWEN

TOAST_CLOCK = 180

STATION_META = {
    "marrow":     ("House Marrow Table",    15),
    "vantrell":   ("House Vantrell Table",  15),
    "delegation": ("Foreign Delegation",    15),
    "isolde":     ("Lady Isolde",           15),
    "duke":       ("Grand Duke Aldric",     20),
    "kitchen":    ("Kitchen & Cellar",      15),
    "balcony":    ("The Balcony",           10),
}


# ═══════════════════════════════════════════════
#  Entry
# ═══════════════════════════════════════════════

def run(gs: GameState):
    _setup(gs)
    _fenwick_opening(gs)

    while gs.game_clock < TOAST_CLOCK:
        _check_timed_events(gs)

        if gs.get_flag("ending_d_triggered"):
            _ending_d(gs)
            return

        choice = _station_menu(gs)

        if choice == "toast":
            break

        if choice in STATION_META:
            _visit_station(choice, gs)
            gs.advance_clock(STATION_META[choice][1])
            gs.record_visit(choice)
            gs.save()

    _transition_to_act3(gs)


# ═══════════════════════════════════════════════
#  Setup
# ═══════════════════════════════════════════════

def _setup(gs: GameState):
    for cfg in [FENWICK, BRIENNE, CASSIAN, OPHELIA,
                DEMIR, KAVIR, ISOLDE, DUKE, ALWEN]:
        gs.init_npc(cfg["id"], cfg["name"])

    if not gs.get_data("vision_window_set"):
        offset = random.randint(30, 60)
        gs.set_data("vision_window_open",  gs.game_clock + offset)
        gs.set_data("vision_window_close", gs.game_clock + offset + 20)
        gs.set_data("vision_window_set",   True)

    if not gs.get_data("passphrase_counter"):
        gs.set_data("passphrase_counter", 0)

    if gs.get_flag("asked_for_duke_act1") or gs.get_flag("reynard_met_warmly"):
        gs.unlock_station("duke")


# ═══════════════════════════════════════════════
#  Shared free conversation helper
# ═══════════════════════════════════════════════

def _station_talk(
    npc: NPC,
    gs: GameState,
    word_limit: int = 200,
    min_exchanges: int = 4,
    partner: NPC = None,
    partner_name_triggers: list = None,
):
    """
    Free conversation loop for any station.

    Empty Enter        → leave
    'log'              → show evidence
    'time'             → show clock
    word_limit +       → NPC wraps up naturally
    min_exchanges

    If partner is set, messages containing partner_name_triggers
    are routed to the partner NPC instead.
    """
    D.system_msg(
        "Press Enter on a blank line to walk away. "
        "Type 'log' to check evidence."
    )

    def _word_count(n: NPC) -> int:
        return sum(
            len(m.get("content", "").split())
            for m in n.state.conversation_history
        )

    while True:
        raw = D.get_free_input()

        if not raw or not raw.strip():
            D.narrate("You step away.")
            break

        cmd = raw.lower().strip()
        if cmd == "log":
            D.show_evidence(gs.evidence_log)
            continue
        if cmd == "time":
            D.system_msg(f"The time is {gs.get_time_str()}.")
            continue

        # Route to partner if named
        active_npc = npc
        if partner and partner_name_triggers:
            if any(t in cmd for t in partner_name_triggers):
                active_npc = partner

        D.player_line(raw)
        response = active_npc.speak(raw)

        if response.startswith("[ERROR"):
            D.error_msg(response)
            hist = active_npc.state.conversation_history
            if hist: hist.pop()
            if hist: hist.pop()
            continue

        D.npc_speak(active_npc.name, response)
        gs.advance_clock(5)

        # Word count gate — primary NPC only
        words     = _word_count(npc)
        exchanges = npc.state.times_spoken
        if words >= word_limit and exchanges >= min_exchanges:
            D.narrate("The conversation reaches a natural pause.")
            break


# ═══════════════════════════════════════════════
#  Fenwick Opening
# ═══════════════════════════════════════════════

def _fenwick_opening(gs: GameState):
    D.clear()
    D.scene_header("ACT 2  —  THE PARTY FLOOR", gs.get_time_str())

    D.narrate(
        "The hall is enormous, loud, and bright. "
        "Guests cluster near the fireplace, along the tables, "
        "at the windows looking out over the dark garden. "
        "Servants move with trays. A string quartet plays something festive.\n\n"
        "Two hundred people who believe tonight is only a celebration."
    )
    D.narrate(
        "A minor lord materialises at your elbow almost immediately — "
        "LORD FENWICK, mid-fifties, wine glass already in hand, "
        "genuinely pleased to see you."
    )

    fenwick = NPC(FENWICK, gs)
    D.npc_speak(
        "Lord Fenwick",
        "Viscount! Splendid — you made it. "
        "Dreadful journey? You look like a man with something on his mind. Wine?"
    )

    D.system_msg(
        "Talk to Fenwick freely — ask about the room, the guests, the evening. "
        "Press Enter on a blank line when you're ready to explore."
    )

    _station_talk(fenwick, gs, word_limit=220, min_exchanges=3)
    D.pause()


# ═══════════════════════════════════════════════
#  Station Menu
# ═══════════════════════════════════════════════

def _station_menu(gs: GameState) -> str:
    D.clear()
    remaining = gs.minutes_to_toast()
    D.scene_header("THE PARTY FLOOR", gs.get_time_str())

    if remaining > 60:
        D.system_msg(
            f"~{remaining} minutes until the toast.  "
            f"Evidence: {len(gs.evidence_log)} items."
        )
    elif remaining > 30:
        D.narrate(
            "The servants are beginning to move with more purpose. "
            "Someone is setting out glasses near the far table."
        )
        D.system_msg(f"~{remaining} minutes until the toast.")
    else:
        D.narrate(
            "A footman has placed the ceremonial decanter on the side table. "
            "The toast is close."
        )
        D.system_msg(f"~{remaining} minutes remaining.")

    D.system_msg("")

    available = []
    for sid in gs.unlocked_stations:
        if sid not in STATION_META:
            continue
        name, cost = STATION_META[sid]
        visits     = gs.station_visits(sid)
        label      = name
        if visits > 0:
            label += f"  [visited ×{visits}]"
        label += f"  (~{cost} min)"
        available.append((sid, label))

    available.append(("toast", "Head to the hall — I have gathered what I can."))

    return D.get_choice(available)


# ═══════════════════════════════════════════════
#  Station dispatcher
# ═══════════════════════════════════════════════

def _visit_station(sid: str, gs: GameState):
    {
        "marrow":     _visit_marrow,
        "vantrell":   _visit_vantrell,
        "delegation": _visit_delegation,
        "isolde":     _visit_isolde,
        "duke":       _visit_duke,
        "kitchen":    _visit_kitchen,
        "balcony":    _visit_balcony,
    }.get(sid, lambda g: None)(gs)


# ═══════════════════════════════════════════════
#  STATION: House Marrow
# ═══════════════════════════════════════════════

def _visit_marrow(gs: GameState):
    D.clear()
    D.scene_header("HOUSE MARROW TABLE", gs.get_time_str())

    brienne = NPC(BRIENNE, gs)
    first   = gs.station_visits("marrow") == 0

    if first:
        D.narrate(
            "Far corner of the hall — quieter, darker, "
            "as if the festivity stops at the edge of their table. "
            "LADY BRIENNE MARROW sits at the centre. Composed. "
            "Black dress that is just barely appropriate for a celebration. "
            "Two older retainers flank her.\n\n"
            "She looks up as you approach — not hostile, but measuring."
        )
        D.npc_speak(
            "Lady Brienne",
            "Viscount. I wondered if anyone would bother with our corner tonight. "
            "Sit, if you like. You\'re not obliged to be cheerful."
        )
    else:
        D.narrate("Brienne looks up as you return to her table.")
        resp = brienne.speak("You have come back.")
        D.npc_speak("Lady Brienne", resp)

    # Threat note — fires after Vantrell station visited
    # Delivers mid-conversation so player can react naturally
    if gs.station_visits("vantrell") >= 1 and not gs.get_flag("brienne_note_delivered"):
        _deliver_brienne_note(gs, brienne)

    # One of the retainers mutters on first visit — plants the red herring
    if first and not brienne.state.get_flag("retainer_line_heard"):
        brienne.state.set_flag("retainer_line_heard")
        D.narrate(
            "One of the older retainers at the table mutters something "
            "to the other — not quietly enough:"
        )
        D.npc_speak(
            "Retainer",
            "...can\'t believe they put her within twenty feet of Vantrell "
            "after what his supply chain cost our..."
        )
        D.narrate("He stops when he notices you listening.")

    _station_talk(brienne, gs, word_limit=220, min_exchanges=4)
    _increment_passphrase_counter(gs, "marrow")


def _deliver_brienne_note(gs: GameState, brienne: NPC):
    D.narrate(
        "A servant approaches quietly and places a folded note "
        "beside Brienne\'s glass. She reads it without expression. "
        "A moment. Then she folds it and puts it away."
    )
    gs.set_flag("brienne_note_delivered")
    D.narrate(
        "Her expression doesn\'t change. "
        "But something in her posture does — a stillness "
        "that wasn\'t there a moment ago."
    )

    # Evidence logged automatically — player can ask about it in free conversation
    # brienne.py analysis will add detailed evidence if player asks + FL 2+
    if gs.add_evidence(
        "Brienne received an anonymous note tonight — "
        "read it, folded it, showed no public reaction. "
        "Something in her posture changed."
    ):
        D.evidence_gained(
            "Brienne received a note tonight. "
            "She didn\'t react publicly — but she noticed."
        )


# ═══════════════════════════════════════════════
#  STATION: House Vantrell
# ═══════════════════════════════════════════════

def _visit_vantrell(gs: GameState):
    D.clear()
    D.scene_header("HOUSE VANTRELL TABLE", gs.get_time_str())

    cassian = NPC(CASSIAN, gs)
    ophelia = NPC(OPHELIA, gs)
    first   = gs.station_visits("vantrell") == 0

    if first:
        D.narrate(
            "Centre-left of the hall — well-lit, animated, "
            "the most comfortable table in the room. "
            "LORD CASSIAN VANTRELL holds court; mid-forties, warm face. "
            "His sister LADY OPHELIA sits a little apart, "
            "elegant and still, watching the room.\n\n"
            "Cassian sees you and opens his arms."
        )
    else:
        D.narrate("You return to the Vantrell table.")

    D.npc_speak(
        "Lord Cassian",
        "Viscount! Come — we were just celebrating. "
        "The war is over. Can you believe it?"
    )

    D.system_msg(
        "Address Cassian or Ophelia by name to direct your words. "
        "Press Enter on a blank line to walk away."
    )

    _station_talk(
        cassian, gs,
        word_limit=180, min_exchanges=3,
        partner=ophelia,
        partner_name_triggers=["ophelia", "lady ophelia", "sister"],
    )
    _increment_passphrase_counter(gs, "vantrell")


# ═══════════════════════════════════════════════
#  STATION: Foreign Delegation
# ═══════════════════════════════════════════════

def _visit_delegation(gs: GameState):
    D.clear()
    D.scene_header("FOREIGN DELEGATION", gs.get_time_str())

    demir = NPC(DEMIR, gs)
    kavir = NPC(KAVIR, gs)
    first = gs.station_visits("delegation") == 0

    if first:
        D.narrate(
            "Near the east corridor. COUNSELOR YUSUF DEMIR stands beside "
            "GENERAL ALDUS KAVIR — broad, formal, saying little. "
            "Demir stops talking the moment you approach."
        )
    else:
        D.narrate("You return to the foreign delegation.")

    D.npc_speak("Counselor Demir", "Lord Viscount. A wonderful evening.")

    D.system_msg(
        "Address Demir or Kavir by name to direct your words. "
        "Press Enter on a blank line to leave."
    )

    _station_talk(
        demir, gs,
        word_limit=180, min_exchanges=3,
        partner=kavir,
        partner_name_triggers=["kavir", "general", "commander"],
    )


# ═══════════════════════════════════════════════
#  STATION: Lady Isolde
# ═══════════════════════════════════════════════

def _visit_isolde(gs: GameState):
    D.clear()
    D.scene_header("LADY ISOLDE", gs.get_time_str())

    isolde = NPC(ISOLDE, gs)
    first  = gs.station_visits("isolde") == 0

    if first:
        D.narrate(
            "Southeast end of the hall, near a group of young courtiers. "
            "She is laughing at something when you arrive — genuinely. "
            "She turns to you with easy warmth."
        )
        D.npc_speak(
            "Lady Isolde",
            "Viscount! I was hoping to meet you properly tonight. "
            "They say you have been on your own little investigation of the room. "
            "What have you concluded?"
        )
    else:
        D.narrate("Isolde smiles as you approach again.")
        resp = isolde.speak("You've returned.")
        D.npc_speak("Lady Isolde", resp)

    _station_talk(isolde, gs, word_limit=200, min_exchanges=4)


# ═══════════════════════════════════════════════
#  STATION: The Duke
# ═══════════════════════════════════════════════

def _visit_duke(gs: GameState):
    D.clear()
    D.scene_header("GRAND DUKE ALDRIC", gs.get_time_str())

    duke    = NPC(DUKE, gs)
    private = (
        not gs.get_flag("duke_station_public_only")
        or duke.state.friendly_level >= 1
        or gs.get_flag("reynard_met_warmly")
    )

    if private:
        D.narrate(
            "You find the Duke during a lull in the receiving line. "
            "An aide steps away. You have a few private words."
        )
        D.npc_speak(
            "Duke Aldric",
            "I don't get many moments tonight. "
            "What's on your mind, Viscount? "
            "You look like a man with something to say."
        )
    else:
        D.narrate(
            "The Duke is working the receiving line. "
            "You join it and wait. When you reach him "
            "you have perhaps two exchanges — publicly."
        )
        D.npc_speak("Duke Aldric", "Viscount. Glad you came. A night to remember.")

    _station_talk(duke, gs, word_limit=200, min_exchanges=3)

    if gs.get_flag("ending_d_triggered"):
        _ending_d(gs)


# ═══════════════════════════════════════════════
#  STATION: Kitchen & Cellar
# ═══════════════════════════════════════════════

def _visit_kitchen(gs: GameState):
    D.clear()
    D.scene_header("KITCHEN & CELLAR", gs.get_time_str())

    alwen = NPC(ALWEN, gs)
    first = gs.station_visits("kitchen") == 0

    if first:
        D.narrate(
            "A servants' corridor off the east end leads down to the kitchens — "
            "warm, busy, smelling of roasted meat and beeswax. "
            "MRS ALWEN, the head cook, looks up from a tray of pastries."
        )
    else:
        D.narrate("Mrs Alwen looks up as you enter the kitchen again.")

    D.npc_speak(
        "Mrs Alwen",
        "My lord! Is something wrong — has a dish not come up right?"
    )

    _station_talk(alwen, gs, word_limit=160, min_exchanges=3)

    # Offer cellar after kitchen conversation
    D.narrate("The cellar stairs are visible through a door at the back of the kitchen.")
    go_down = D.get_choice([
        ("YES", "Go down to the cellar and have a look."),
        ("NO",  "Leave the kitchen."),
    ])
    if go_down == "YES":
        _inspect_cellar(gs)

    _increment_passphrase_counter(gs, "kitchen")


def _inspect_cellar(gs: GameState):
    D.clear()
    D.scene_header("THE CELLAR", gs.get_time_str())
    D.narrate(
        "Stone steps, cool air, racks of bottles. "
        "In the far corner: a specific rack, separated from the others — "
        "the eastern wine."
    )

    # These are physical inspection choices, not dialogue — keep them
    choices = [
        ("SEAL",  "Examine the wine seal closely."),
        ("LOG",   "Look for a cellar handling log or record."),
        ("BOTH",  "Examine both carefully."),
        ("LEAVE", "Leave the cellar."),
    ]
    c = D.get_choice(choices)

    if c == "LEAVE":
        return

    if c in ("SEAL", "BOTH"):
        D.narrate(
            "The wax seal has been reapplied — "
            "a fractionally different colour from the eastern court "
            "description on the accompanying provenance letter. "
            "Not obviously wrong. Wrong enough, if you are looking."
        )
        if gs.add_evidence(
            "Cellar: Eastern wine seal has been reapplied — "
            "colour doesn't match the official provenance letter."
        ):
            D.evidence_gained(
                "The gift wine's seal was broken and resealed. Someone tampered with it."
            )
            gs.set_flag("wine_seal_discovered")

    if c in ("LOG", "BOTH"):
        D.narrate(
            "A cellar log tucked beside the rack. "
            "Two bottles moved from a different section to the serving rack — "
            "this afternoon. The handwriting is precise and familiar.\n\n"
            "Reynard's."
        )
        if gs.add_evidence(
            "Cellar log: Reynard personally moved specific bottles "
            "to the serving rack this afternoon — his own handwriting."
        ):
            D.evidence_gained(
                "Reynard's handwriting in the cellar log. "
                "He moved the wine to the serving rack himself today."
            )
            gs.set_flag("cellar_log_found")

    D.pause()


# ═══════════════════════════════════════════════
#  STATION: The Balcony
# ═══════════════════════════════════════════════

def _visit_balcony(gs: GameState):
    D.clear()
    D.scene_header("THE BALCONY", gs.get_time_str())

    D.narrate(
        "Tall windows open onto a stone balcony overlooking the garden. "
        "Lanterns in the hedgerows below. Quiet."
    )

    clock_now    = gs.game_clock
    window_open  = gs.get_data("vision_window_open",  9999)
    window_close = gs.get_data("vision_window_close", 9999)

    if window_open <= clock_now <= window_close and not gs.get_flag("balcony_vision_seen"):
        _balcony_vision(gs)
    else:
        D.narrate(
            "You look out over the garden. The lanterns blur into the dark. "
            "You think of the dream. Nothing new comes."
        )
        if gs.get_flag("balcony_vision_seen"):
            D.narrate(
                "The vision is still with you: Reynard, the cellar, "
                "the woman with the ring. You know what you saw."
            )

    D.pause()


def _balcony_vision(gs: GameState):
    D.narrate("The lanterns blur. For a moment the garden is lit differently — afternoon light.")

    D.vision(
        "The cellar door, seen from the garden side.\n\n"
        "Reynard — carrying something wrapped in cloth, moving quickly, not looking up.\n\n"
        "Behind him the door is held open by a gloved hand. "
        "A woman's hand. A ring catches the light — silver, red stone.\n\n"
        "Then it is night again."
    )

    gs.set_flag("balcony_vision_seen")
    if gs.add_evidence(
        "VISION (balcony): Reynard at the cellar door this afternoon — "
        "carrying something, moving fast. A woman held the door: "
        "silver ring with red stone."
    ):
        D.evidence_gained(
            "Second vision — Reynard and a woman at the cellar this afternoon. "
            "The ring is identifiable."
        )

    D.narrate(
        "You look down at your hands. The stone balustrade. The garden.\n\n"
        "Find the ring."
    )


# ═══════════════════════════════════════════════
#  Timed Events
# ═══════════════════════════════════════════════

def _check_timed_events(gs: GameState):
    # Passphrase overheard
    counter = gs.get_data("passphrase_counter", 0)
    if counter >= 2 and not gs.get_flag("passphrase_overheard"):
        _overhear_passphrase(gs)

    # Reynard reports to Vantrells
    if not gs.get_flag("reynard_reported_to_vantrell"):
        try:
            r = gs.get_npc("reynard")
            if r.suspicion_level >= 2 and gs.station_visits("vantrell") >= 1:
                D.narrate(
                    "Out of the corner of your eye — Reynard, near the Vantrell table, "
                    "leaning briefly toward Lord Cassian before straightening and moving on."
                )
                gs.set_flag("reynard_reported_to_vantrell")
                try:
                    gs.get_npc("cassian").bump_sl()
                except KeyError:
                    pass
        except KeyError:
            pass

    # Final bell
    if gs.minutes_to_toast() <= 30 and not gs.get_flag("final_bell_rung"):
        gs.set_flag("final_bell_rung")
        D.narrate(
            "\nSomewhere in the hall, a bell rings once. "
            "A servant begins placing glasses near the wine service."
        )
        D.system_msg("The toast is approaching. Use your remaining time carefully.")


def _increment_passphrase_counter(gs: GameState, station: str):
    conspiracy = {"vantrell", "kitchen", "marrow"}
    if station in conspiracy:
        c = gs.get_data("passphrase_counter", 0)
        gs.set_data("passphrase_counter", c + 1)


def _overhear_passphrase(gs: GameState):
    D.narrate(
        "You are moving between guests when you catch it — "
        "two voices, low, somewhere just behind you:\n\n"
        "  '...the harvest was good this year...'\n\n"
        "  '...better than the war years...'\n\n"
        "You turn. Just the noise of the party. "
        "You couldn't say who spoke, or to whom."
    )
    gs.set_flag("passphrase_overheard")
    D.system_msg(
        "Passphrase overheard. You can try speaking it "
        "if you think you know who might respond."
    )


# ═══════════════════════════════════════════════
#  Transitions
# ═══════════════════════════════════════════════

def _transition_to_act3(gs: GameState):
    D.clear()
    D.narrate(
        "The string quartet finishes mid-phrase.\n\n"
        "A footman strikes a bell — once, twice, three times. "
        "The hall grows quiet in that particular way.\n\n"
        "Duke Aldric moves to the front of the room. "
        "Reynard stands near the side table — "
        "the eastern wine poured into the ceremonial decanter, "
        "several glasses already set out.\n\n"
        "Lady Isolde is a few steps behind her father."
    )
    D.pause()

    ev = gs.evidence_score()
    if ev == 0:
        D.narrate("You carry nothing concrete. Whatever happens now will depend on instinct and trust.")
    elif ev <= 2:
        D.narrate("You have pieces — not enough for certainty, but enough to act on.")
    else:
        D.narrate("You know what you know. The question is whether anyone will listen in time.")

    D.pause()
    gs.current_act = "act3"
    gs.save()


def _ending_d(gs: GameState):
    D.clear()
    D.scene_header("ENDING D  —  THE DUNGEON")
    D.narrate(
        "Reynard moves efficiently and without drama.\n\n"
        "You are escorted to a room in the lower estate. "
        "The door is locked.\n\n"
        "You hear the toast from below.\n\n"
        "Then a physician's footsteps, running, overhead.\n\n"
        "In the dark, you put your head in your hands.\n\n"
        "The vision was real. You just couldn't stop it alone."
    )
    D.pause()
    gs.current_act = "ending_d"
    gs.save()