# ─────────────────────────────────────────────
#  engine/web_bridge.py
#  Clean JSON bridge connecting the existing
#  Python story/NPC/LLM engine to the 2D Pixel
#  Browser UI without altering terminal mode.
# ─────────────────────────────────────────────

from __future__ import annotations
import random
import threading
from typing import Any, Dict, List
import unittest.mock

from engine import display as D
from engine import llm
from engine.game_state import GameState
from engine.npc import NPC

from npcs.aldous    import CONFIG as ALDOUS_CFG, dynamic_threshold, _count_conversation_words
from npcs.reynard   import CONFIG as REYNARD_CFG, check_passphrase
from npcs.fenwick   import CONFIG as FENWICK_CFG
from npcs.brienne   import CONFIG as BRIENNE_CFG
from npcs.cassian   import CONFIG as CASSIAN_CFG
from npcs.ophelia   import CONFIG as OPHELIA_CFG
from npcs.demir     import CONFIG as DEMIR_CFG
from npcs.kavir     import CONFIG as KAVIR_CFG
from npcs.isolde    import CONFIG as ISOLDE_CFG
from npcs.duke      import CONFIG as DUKE_CFG
from npcs.mrs_alwen import CONFIG as ALWEN_CFG

from story import act0 as act0_mod
from story import act2 as act2_mod

NPC_CONFIGS = {
    "aldous":    ALDOUS_CFG,
    "reynard":   REYNARD_CFG,
    "fenwick":   FENWICK_CFG,
    "brienne":   BRIENNE_CFG,
    "cassian":   CASSIAN_CFG,
    "ophelia":   OPHELIA_CFG,
    "demir":     DEMIR_CFG,
    "kavir":     KAVIR_CFG,
    "isolde":    ISOLDE_CFG,
    "duke":      DUKE_CFG,
    "mrs_alwen": ALWEN_CFG,
}

# Banquet Hall social groups in Act 2
PARTY_GROUPS = {
    "cassian": ["cassian", "ophelia"],
    "ophelia": ["cassian", "ophelia"],
    "demir":   ["demir", "kavir"],
    "kavir":   ["demir", "kavir"],
    "duke":    ["duke", "isolde", "reynard"],
    "isolde":  ["isolde", "duke"],
    "reynard": ["reynard", "duke"],
}

_LOCK = threading.Lock()


class _EventCapture:
    """Captures display calls during a single web turn."""
    def __init__(self):
        self.events: List[Dict[str, str]] = []

    def narrate(self, text: str, delay: bool = False):
        if text and text.strip():
            self.events.append({"type": "narration", "text": text.strip()})

    def vision(self, text: str):
        if text and text.strip():
            self.events.append({"type": "vision", "text": text.strip()})

    def evidence_gained(self, text: str):
        if text and text.strip():
            self.events.append({"type": "evidence", "text": text.strip()})

    def relationship_change(self, npc_name: str, attribute: str, direction: str):
        word = {
            ("friendly", "up"):   f"▲ {npc_name} seems warmer toward you.",
            ("friendly", "down"): f"▼ {npc_name} has grown cooler.",
            ("suspicion", "up"):  f"▲ {npc_name} watches you more carefully now.",
            ("suspicion", "down"):f"▼ {npc_name} seems less guarded.",
        }.get((attribute, direction), f"• Something shifted with {npc_name}.")
        self.events.append({"type": "relationship", "text": word})

    def system_msg(self, text: str):
        if text and text.strip():
            self.events.append({"type": "system", "text": text.strip()})

    def npc_speak(self, name: str, text: str):
        if text and text.strip():
            self.events.append({"type": "npc", "speaker": name, "text": text.strip()})


def _with_capture(fn, *args, **kwargs) -> tuple[Any, List[Dict[str, str]]]:
    cap = _EventCapture()
    with _LOCK:
        with unittest.mock.patch.object(D, "narrate", cap.narrate), \
             unittest.mock.patch.object(D, "vision", cap.vision), \
             unittest.mock.patch.object(D, "evidence_gained", cap.evidence_gained), \
             unittest.mock.patch.object(D, "relationship_change", cap.relationship_change), \
             unittest.mock.patch.object(D, "system_msg", cap.system_msg), \
             unittest.mock.patch.object(D, "npc_speak", cap.npc_speak), \
             unittest.mock.patch.object(D, "pause", lambda *a, **kw: None), \
             unittest.mock.patch.object(D, "clear", lambda: None):
            result = fn(*args, **kwargs)
    return result, cap.events


class WebSession:
    def __init__(self):
        self.gs = GameState()
        self.gs.current_act = "prologue"
        self.gs.current_scene = "dream"
        self.act3_phase = "confrontation"  # confrontation | ophelia_tell | reynard_why | reynard_testify | done
        self.act3_turns = 0
        self.act3_conviction = 0
        self.act3_verified: set = set()
        self.reynard_accused = False
        self.vantrell_accused = False
        self.isolde_already_safe = False
        self.easter_egg_mode = False
        self.interrogation_cred = 3
        self.interrogation_turn = 0
        self.interrogation_history: List[Dict[str, str]] = []

    def snapshot(self) -> Dict[str, Any]:
        npcs = {}
        for nid, cfg in NPC_CONFIGS.items():
            try:
                ns = self.gs.get_npc(nid)
                npcs[nid] = {
                    "id": nid,
                    "name": ns.name,
                    "friendly_level": ns.friendly_level,
                    "suspicion_level": ns.suspicion_level,
                    "times_spoken": ns.times_spoken,
                    "memories": list(ns.memories),
                }
            except KeyError:
                npcs[nid] = {
                    "id": nid,
                    "name": cfg["name"],
                    "friendly_level": 0,
                    "suspicion_level": 0,
                    "times_spoken": 0,
                    "memories": [],
                }
        return {
            "current_act": self.gs.current_act,
            "current_scene": self.gs.current_scene,
            "game_clock": self.gs.game_clock,
            "time_str": self.gs.get_time_str(),
            "minutes_to_toast": self.gs.minutes_to_toast(),
            "evidence_log": list(self.gs.evidence_log),
            "evidence_score": self.gs.evidence_score(),
            "unlocked_stations": list(self.gs.unlocked_stations),
            "flags": dict(self.gs.flags),
            "npcs": npcs,
            "act3_phase": self.act3_phase,
            "act3_turns": self.act3_turns,
            "act3_conviction": self.act3_conviction,
        }

    def advance_prologue(self) -> Dict[str, Any]:
        self.gs.set_flag("prologue_done", True)
        self.gs.current_act = "act0"
        self.gs.current_scene = "carriage"
        self.gs.init_npc("aldous", "Aldous")
        self.gs.set_data("aldous_naturalness", 3)
        return {
            "events": [
                {"type": "narration", "text": "You knock twice on the carriage roof panel. The small wooden hatch slides open."},
                {"type": "npc", "speaker": "Aldous", "text": "My lord? The road's clear tonight. Care for a word before we reach the gates?"}
            ],
            "state": self.snapshot(),
        }

    def finish_act0(self) -> Dict[str, Any]:
        self.gs.game_clock = 0
        self.gs.current_act = "act1"
        self.gs.current_scene = "arrival"
        self.gs.init_npc("reynard", "Reynard")
        return {
            "events": [
                {"type": "vision", "text": "A glass at her lips. Red wine on white silk. The sound of shattering."},
                {"type": "narration", "text": "7:00 PM — The carriage stops at the estate steps. Head Butler REYNARD descends personally to greet you."},
                {"type": "npc", "speaker": "Reynard", "text": "Lord Viscount. His Grace will be glad you've come — I'll see you through to the hall personally. Was the road kind to you tonight?"}
            ],
            "state": self.snapshot(),
        }

    def enter_hall_act2(self) -> Dict[str, Any]:
        def _do():
            act2_mod._setup(self.gs)
            self.gs.current_act = "act2"
            self.gs.current_scene = "party_floor"
            self.gs.advance_clock(20)
        _, events = _with_capture(_do)
        events.insert(0, {
            "type": "narration",
            "text": "The grand doors open onto a candlelit hall of two hundred nobles celebrating the end of a ten-year war. The toast is in three hours. Somewhere in this room: the culprit, the method, and the victim."
        })
        events.append({
            "type": "npc",
            "speaker": "Lord Fenwick",
            "text": "Viscount! Splendid — you made it. Dreadful journey? You look like a man with something on his mind. Wine?"
        })
        return {"events": events, "state": self.snapshot()}

    def visit_station(self, station_id: str) -> Dict[str, Any]:
        if station_id not in act2_mod.STATION_META and station_id != "fenwick":
            return {"events": [{"type": "system", "text": f"Unknown location: {station_id}"}], "state": self.snapshot()}
        if station_id != "fenwick" and station_id not in self.gs.unlocked_stations:
            return {"events": [{"type": "system", "text": f"You haven't located or unlocked {act2_mod.STATION_META[station_id][0]} yet. Speak with Lord Fenwick first."}], "state": self.snapshot()}

        def _do():
            if station_id == "fenwick":
                self.gs.current_scene = "fenwick"
                return
            act2_mod._check_timed_events(self.gs)
            if self.gs.get_flag("ending_d_triggered"):
                self.gs.current_act = "ending_d"
                return

            self.gs.current_scene = station_id
            cost = act2_mod.STATION_META[station_id][1]
            self.gs.advance_clock(cost)
            self.gs.record_visit(station_id)
            act2_mod._increment_passphrase_counter(self.gs, station_id)

            if station_id == "balcony":
                clock_now = self.gs.game_clock
                w_open = self.gs.get_data("vision_window_open", 9999)
                w_close = self.gs.get_data("vision_window_close", 9999)
                if w_open <= clock_now <= w_close and not self.gs.get_flag("balcony_vision_seen"):
                    act2_mod._balcony_vision(self.gs)
                else:
                    D.narrate("You look out over the dark garden. Lanterns sway in the cool night air.")
            elif station_id == "marrow":
                brienne = NPC(BRIENNE_CFG, self.gs)
                if self.gs.station_visits("vantrell") >= 1 and not self.gs.get_flag("brienne_note_delivered"):
                    act2_mod._deliver_brienne_note(self.gs, brienne)

            # Check again if clock passed threshold
            act2_mod._check_timed_events(self.gs)

        _, events = _with_capture(_do)
        if self.gs.current_act == "act2" and self.gs.game_clock >= 180:
            toast_data = self.start_act3()
            events.extend(toast_data["events"])
        return {"events": events, "state": self.snapshot()}

    def inspect_cellar(self, choice: str) -> Dict[str, Any]:
        choice = choice.upper()
        def _do():
            if choice in ("SEAL", "BOTH"):
                if self.gs.game_clock >= 135:
                    D.narrate(
                        "The eastern rack is already empty — only faint slivers of dark wax "
                        "linger in the wooden cradle. The bottles have already been carried "
                        "upstairs to the dais sideboard for the toast."
                    )
                    self.gs.add_evidence(
                        "Cellar (9:15 PM+): Eastern wine already moved upstairs for service."
                    )
                else:
                    D.narrate(
                        "The wax seal has been reapplied — a fractionally different colour from the "
                        "eastern court description on the provenance letter."
                    )
                    if self.gs.add_evidence(
                        "Cellar: Eastern wine seal has been reapplied — colour doesn't match the official provenance letter."
                    ):
                        D.evidence_gained("The gift wine's seal was broken and resealed. Someone tampered with it.")
                        self.gs.set_flag("wine_seal_discovered")
            if choice in ("LOG", "BOTH"):
                D.narrate(
                    "A cellar log tucked beside the rack. Two bottles moved from a different "
                    "section to the serving rack this afternoon. The handwriting is Reynard's."
                )
                if self.gs.add_evidence(
                    "Cellar log: Reynard personally moved specific bottles to the serving rack this afternoon — his own handwriting."
                ):
                    D.evidence_gained("Reynard's handwriting in the cellar log. He moved the wine himself today.")
                    self.gs.set_flag("cellar_log_found")

        _, events = _with_capture(_do)
        return {"events": events, "state": self.snapshot()}

    def talk(self, npc_id: str, message: str) -> Dict[str, Any]:
        if npc_id not in NPC_CONFIGS:
            return {"reply": "", "events": [{"type": "system", "text": "Unknown character."}], "state": self.snapshot()}

        # Handle Act 1 Easter egg passphrase
        if self.gs.current_act == "act1" and npc_id == "reynard":
            if self.easter_egg_mode:
                return self._handle_interrogation(message)
            if check_passphrase(message, self.gs):
                self.easter_egg_mode = True
                self.gs.current_scene = "dungeon"
                self.interrogation_cred = 3
                self.interrogation_turn = 0
                self.interrogation_history = [{
                    "role": "user",
                    "content": "[The player has just spoken the passphrase. Begin your interrogation.]"
                }]
                return {
                    "reply": "...Better than the war years. Walk with me. Now. Who sent you? I was not told to expect anyone.",
                    "events": [{"type": "narration", "text": "The professional warmth leaves Reynard's face completely. He pulls you down a dark stone corridor into the lower dungeon cells."}],
                    "state": self.snapshot(),
                }

        def _pick_group_speakers(group: List[str], preferred: str, msg: str) -> List[str]:
            """Decide who speaks first and optionally who chimes in next (capped at 2 beats)."""
            low = msg.lower()
            first = preferred
            for member in group:
                name_key = NPC_CONFIGS[member]["name"].lower().split()[-1]
                if name_key in low:
                    first = member
                    break

            others = [m for m in group if m != first]
            if not others:
                return [first]

            # Ask LLM director if a second NPC at the table should chime in
            prompt = (
                f"Group present: {', '.join(group)}. Primary responder: {first}.\n"
                f'Player said: "{msg}"\n'
                f"Should another person in the group add a brief reaction after {first}? "
                f"Reply ONLY with one id from [{', '.join(others)}] or NONE."
            )
            decision = llm.chat(
                "You are a conversation director. Reply with ONLY an NPC id or NONE.",
                [{"role": "user", "content": prompt}],
                temperature=0.2,
            ).strip().lower()

            for cand in others:
                if cand in decision:
                    return [first, cand]
            return [first]

        def _do():
            if self.gs.current_act == "act0" and npc_id == "aldous":
                score = act0_mod._score_question(message)
                nat = max(0, min(5, self.gs.get_data("aldous_naturalness", 3) + score))
                self.gs.set_data("aldous_naturalness", nat)

            turns: List[Dict[str, str]] = []

            if self.gs.current_act == "act2" and npc_id in PARTY_GROUPS and len(PARTY_GROUPS[npc_id]) > 1:
                speakers = _pick_group_speakers(PARTY_GROUPS[npc_id], npc_id, message)
                primary_id = speakers[0]
                primary_npc = NPC(NPC_CONFIGS[primary_id], self.gs)
                primary_reply = primary_npc.speak(message)
                turns.append({
                    "speaker_id": primary_id,
                    "speaker_name": primary_npc.name,
                    "text": primary_reply,
                })

                # Optional second beat (max 2 beats total so group never loops)
                if len(speakers) > 1:
                    sec_id = speakers[1]
                    sec_npc = NPC(NPC_CONFIGS[sec_id], self.gs)
                    sec_prompt = (
                        f"[Group context: The Viscount just said '{message}' and {primary_npc.name} replied '{primary_reply}'. "
                        f"Add a brief, natural 1-sentence reaction or aside in character.]"
                    )
                    sec_reply = sec_npc.speak(sec_prompt)
                    turns.append({
                        "speaker_id": sec_id,
                        "speaker_name": sec_npc.name,
                        "text": sec_reply,
                    })
                reply = primary_reply
            else:
                npc = NPC(NPC_CONFIGS[npc_id], self.gs)
                reply = npc.speak(message)
                if not reply.strip():
                    reply = f".....({npc.name} chooses to be silent)"
                turns.append({
                    "speaker_id": npc_id,
                    "speaker_name": npc.name,
                    "text": reply,
                })

            if self.gs.current_act == "act2":
                self.gs.advance_clock(5)
                act2_mod._check_timed_events(self.gs)

            # Check Reynard arrest in Act 1
            if self.gs.current_act == "act1" and npc_id == "reynard" and self.gs.get_npc("reynard").suspicion_level >= 3:
                self.gs.set_flag("ending_d_triggered", True)
                self.gs.current_act = "ending_d"
                self.gs.current_scene = "dungeon"
                D.narrate("Reynard stops walking. Two guards appear from the side corridor. You said too much, too soon.")

            if self.gs.get_flag("ending_d_triggered"):
                self.gs.current_act = "ending_d"
                self.gs.current_scene = "dungeon"

            return reply, turns

        (reply, turns), events = _with_capture(_do)
        if self.gs.current_act == "act2" and self.gs.game_clock >= 180:
            toast_data = self.start_act3()
            events.extend(toast_data["events"])
        return {"reply": reply, "turns": turns, "events": events, "state": self.snapshot()}

    def _handle_interrogation(self, answer: str) -> Dict[str, Any]:
        from story.act1 import _INTERROGATION_SCHEMA, _build_interrogation_prompt
        from engine.npc import _extract_tag
        self.interrogation_history.append({"role": "user", "content": answer})
        result = llm.analyze_exchange(answer, "", "Reynard", _INTERROGATION_SCHEMA)
        change = result.get("credibility_change", 0)
        self.interrogation_cred = max(0, min(6, self.interrogation_cred + change))
        if result.get("seems_investigator") or result.get("contradicted_themselves"):
            self.interrogation_cred = 0
        self.interrogation_turn += 1

        if self.interrogation_cred <= 0 or (self.interrogation_turn >= 4 and self.interrogation_cred < 5):
            self.easter_egg_mode = False
            self.gs.set_flag("ending_d_triggered", True)
            self.gs.current_act = "ending_d"
            self.gs.current_scene = "dungeon"
            return {
                "reply": "You're not one of us. Guards.",
                "events": [{"type": "narration", "text": "Two guards step into the dungeon corridor and seize you in irons. Ending D — The Dungeon."}],
                "state": self.snapshot(),
            }
        if self.interrogation_cred >= 5:
            self.easter_egg_mode = False
            self.gs.set_flag("easter_egg_activated", True)
            self.gs.set_flag("easter_egg_interrogation_passed", True)
            hall_data = self.enter_hall_act2()
            hall_events = [{"type": "evidence", "text": "Easter Egg path unlocked! Reynard leads you back up into the Main Hall."}] + hall_data["events"]
            return {
                "reply": "All right. Either you're genuine or you're the best liar I've met tonight. Come inside.",
                "events": hall_events,
                "state": self.snapshot(),
            }
        sys_p = _build_interrogation_prompt(self.gs, self.interrogation_cred, self.interrogation_turn)
        raw_reply = llm.chat(sys_p, self.interrogation_history, temperature=0.6)
        reply, _ = _extract_tag(raw_reply)
        if not reply.strip():
            reply = ".....(Reynard watches you in cold silence)"
        self.interrogation_history.append({"role": "assistant", "content": reply})
        events = []
        if change >= 2:
            events.append({"type": "narration", "text": "Something in his expression shifts — fractionally."})
        elif change <= -2:
            events.append({"type": "narration", "text": "His eyes go flat."})
        elif change == -1:
            events.append({"type": "narration", "text": "A small pause. He files it away."})
        return {"reply": reply, "events": events, "state": self.snapshot()}

    def start_act3(self) -> Dict[str, Any]:
        self.gs.current_act = "act3"
        self.gs.current_scene = "toast"
        self.gs.game_clock = 180
        self.act3_phase = "confrontation"
        self.act3_turns = 0
        self.act3_conviction = 0
        self.act3_verified = set()

        events = [{
            "type": "narration",
            "text": "10:00 PM — The string quartet stops. Duke Aldric rises to lead the ceremonial toast. Reynard reaches for the eastern decanter."
        }]
        isolde_fl = self.gs.get_npc("isolde").friendly_level if "isolde" in self.gs.npc_states else 0
        if self.gs.get_flag("isolde_will_avoid_wine") and isolde_fl >= 2:
            self.isolde_already_safe = True
            self.gs.set_flag("isolde_saved_quietly", True)
            events.append({
                "type": "narration",
                "text": "Across the hall, Lady Isolde meets your eyes and quietly sets her glass down. She trusted your warning."
            })
        events.append({
            "type": "npc",
            "speaker": "Duke Aldric",
            "text": "Friends. Guests. After ten years — tonight we sign. And then we drink, as people who will not fight each other again."
        })
        return {"events": events, "state": self.snapshot()}

    def _act3_ophelia_tell(self, message: str, cassian: NPC) -> str:
        names_ophelia = any(w in message.lower() for w in ["ophelia", "her", "lady vantrell", "vantrell", "point", "stop", "name", "she"])
        if names_ophelia and message.strip():
            D.narrate("Cassian's warmth cracks for a single instant. The Duke sees it.")
            D.npc_speak("Lord Cassian", cassian.speak("Your sister has just been publicly named. Defend her but crack for one instant."))
            D.npc_speak("Duke Aldric", "Guards. Both of them. Now.")
            self.gs.set_flag("ophelia_caught", True)
            self.gs.set_flag("cassian_caught", True)
        else:
            D.narrate("You say nothing. Ophelia slips out into the night. Cassian is arrested an hour later.")
            self.gs.set_flag("cassian_caught", True)
        self.act3_phase = "reynard_why"
        D.narrate("Before the guards reach Reynard, you cross to him. He is standing very still.")
        return "Before the guards reach Reynard, you cross to him. Say something—or leave him to his silence."

    def _act3_reynard_why(self, message: str) -> str:
        asks_why = any(w in message.lower() for w in ["why", "thirty", "reason", "years", "son", "edric", "crossing", "tell me", "what happened"])
        if asks_why:
            D.narrate("The composure leaves him completely.")
            D.npc_speak("Reynard", "My son held the Verenmark crossing for four days. Command said reinforcements were coming. His Grace gave that order. I didn't want the girl hurt.")
            r_fl = self.gs.get_npc("reynard").friendly_level
            if r_fl >= 1 and self.gs.get_flag("reynard_met_warmly"):
                self.act3_phase = "reynard_testify"
                return "Ask him to testify, acknowledge his grief, or condemn him."
        self._finalize_ending()
        return ""

    def _act3_reynard_testify(self, message: str) -> str:
        low = message.lower()
        if any(w in low for w in ["testify", "tell", "speak", "right", "chance", "understand", "son", "grief"]):
            D.npc_speak("Reynard", "He'll never forgive me.")
            D.narrate("Reynard turns toward the Duke and gives a twenty-minute confession. Cassian's legal defense collapses.")
            self.gs.set_flag("reynard_testified", True)
        else:
            D.npc_speak("Reynard", "Yes. I will answer for this.")
        self._finalize_ending()
        return ""

    def act3_action(self, message: str) -> Dict[str, Any]:
        def _do():
            reynard = NPC(REYNARD_CFG, self.gs)
            cassian = NPC(CASSIAN_CFG, self.gs)
            duke    = NPC(DUKE_CFG, self.gs)
            isolde  = NPC(ISOLDE_CFG, self.gs)

            if self.act3_phase == "ophelia_tell":
                return self._act3_ophelia_tell(message, cassian)
            if self.act3_phase == "reynard_why":
                return self._act3_reynard_why(message)
            if self.act3_phase == "reynard_testify":
                return self._act3_reynard_testify(message)

            # Phase: Main confrontation
            self.act3_turns += 1
            if not message.strip():
                return self._resolve_toast_failure()

            analysis = llm.analyze_confrontation(message, self.gs.evidence_log)
            verified = analysis.get("verified_evidence", [])
            phantom  = analysis.get("phantom_evidence", [])
            action   = analysis.get("action")
            strength = analysis.get("persuasion_strength", 0)
            acc_rey  = analysis.get("targets_reynard", False)
            acc_van  = analysis.get("targets_vantrell", False)
            self.act3_verified.update(verified)

            if action == "drink_sacrifice":
                D.narrate("You reach across, lift Isolde's glass, and drink it yourself. The slow poison rattles the Vantrells into exposing themselves.")
                self.gs.current_act = "ending_g"
                self.act3_phase = "done"
                return "Ending G — Self-Sacrifice."

            if action == "physical_intercept":
                i_fl = isolde.state.friendly_level
                b_fl = self.gs.get_npc("brienne").friendly_level if "brienne" in self.gs.npc_states else 0
                if i_fl >= 2 or self.gs.get_flag("isolde_will_avoid_wine"):
                    D.narrate("Isolde sees you coming and sets her glass down.")
                    self.gs.set_flag("wine_stopped", True)
                    self.act3_conviction = max(self.act3_conviction, 2)
                    self.act3_phase = "ophelia_tell"
                    D.narrate("Lady Ophelia's hand freezes over a servant's glass. What do you do?")
                    return "Wine stopped! Lady Ophelia's hand reaches toward a glass and freezes. What do you do?"
                elif b_fl >= 2:
                    D.narrate("A guard grabs your arm, but Lady Brienne stands: 'Let him speak.'")
                    self.act3_conviction += 1
                    return "Brienne bought you a moment."
                else:
                    self.gs.current_act = "ending_d"
                    self.act3_phase = "done"
                    return "Guards seize you. Ending D — The Dungeon."

            if phantom and not verified:
                D.narrate("Your claim rings hollow — you have no proof of that.")
                D.npc_speak("Lord Cassian", cassian.speak("The Viscount made an unsubstantiated claim. Deflect warmly."))
                return "Cassian smoothly deflects your bluff."

            if acc_rey and not self.reynard_accused:
                self.reynard_accused = True
                if self.gs.evidence_score() < 3:
                    D.npc_speak("Duke Aldric", "Reynard has served me thirty-one years. I will not hear this without proof.")
                    self.gs.current_act = "ending_d"
                    self.act3_phase = "done"
                    return "Ending D — The Dungeon."
                self.act3_conviction += 2
                D.npc_speak("Duke Aldric", duke.speak("The Viscount accused Reynard with serious evidence. React with quiet gravity."))

            if acc_van and not self.vantrell_accused:
                self.vantrell_accused = True
                if self.gs.evidence_score() >= 2:
                    D.npc_speak("Lord Cassian", cassian.speak("Accused with real evidence. Crack for one moment."))
                    D.narrate("Cassian's recovery is one half-second too slow. The Duke saw it.")
                    self.act3_conviction += 1

            ev_score = len(verified)
            if ev_score >= 3:
                self.act3_conviction += 2
            elif ev_score == 2 or (ev_score == 1 and strength >= 2):
                self.act3_conviction += 1

            if self.act3_conviction >= 3:
                self.gs.set_flag("wine_stopped", True)
                self.gs.set_flag("duke_held_wine", True)
                D.npc_speak("Duke Aldric", "Hold the wine. Now. All of it.")
                D.narrate("With the crisis paused, you notice Lady Ophelia's hand move toward a servant's glass—then freeze.")
                self.act3_phase = "ophelia_tell"
                return "The Duke halted the wine! Lady Ophelia's hand freezes near a glass. What do you do?"

            if self.act3_turns >= 6:
                if self.gs.get_flag("wine_stopped") or self.isolde_already_safe:
                    self.act3_phase = "ophelia_tell"
                    D.narrate("Lady Ophelia's hand freezes near a servant's glass. What do you do?")
                    return "Lady Ophelia's hand freezes near a glass. What do you do?"
                return self._resolve_toast_failure()

            resp = duke.speak(f"The Viscount presented [{', '.join(verified)}]. Respond proportionally in 1-2 sentences.")
            D.npc_speak("Duke Aldric", resp)
            return resp

        reply, events = _with_capture(_do)
        return {"reply": reply, "events": events, "state": self.snapshot()}

    def _resolve_toast_failure(self) -> str:
        if self.isolde_already_safe:
            self.gs.set_flag("wine_stopped", True)
            self.act3_phase = "ophelia_tell"
            D.narrate("Isolde quietly sets her glass down. Across the room, Ophelia's hand freezes.")
            return "Isolde saved herself! Ophelia's hand freezes near a glass. What do you do?"
        D.narrate("The toast is made. Twenty minutes later, Lady Isolde collapses near the east corridor.")
        self.gs.current_act = "ending_f" if self.gs.evidence_score() == 0 else "ending_c"
        self.act3_phase = "done"
        return f"The toast proceeded. {self.gs.current_act.upper()} reached."

    def _finalize_ending(self):
        if self.gs.get_flag("ophelia_caught"):
            self.gs.current_act = "ending_e" if self.gs.get_flag("easter_egg_activated") else "ending_a"
        else:
            self.gs.current_act = "ending_b"
        self.act3_phase = "done"
        self.gs.save()
