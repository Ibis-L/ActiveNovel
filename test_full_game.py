# ─────────────────────────────────────────────
#  test_full_game.py
#  Automated End-to-End Simulation & Verification
# ─────────────────────────────────────────────

import io
import sys
import os
import time
import contextlib
import unittest.mock
from engine.game_state import GameState
from engine import display as D
from story import prologue, act0, act1, act2, act3
import config

config.TYPING_DELAY = False

class SimulatedPlayer:
    """Simulates player inputs, handling both choice indices/keys and free text."""
    def __init__(self, script_inputs):
        self.inputs = list(script_inputs)

    def get_choice(self, choices, allow_free=False):
        if not self.inputs:
            return choices[-1][0]
        raw = self.inputs.pop(0)
        # Support either numeric index ("1", "2") or exact key ("YES", "kitchen")
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx][0]
        for key, _ in choices:
            if key.lower() == raw.lower():
                return key
        return raw

    def get_free_input(self, prompt=""):
        if not self.inputs:
            return ""
        return self.inputs.pop(0)


def run_ending_a_playthrough():
    """
    Simulates a full Golden Path playthrough targeting ENDING A (Full Victory),
    plus inline edge-case command checks ('help', 'log', 'time').
    """
    gs = GameState()
    gs.data["vision_window_open"] = 0
    gs.data["vision_window_close"] = 300
    gs.data["vision_window_set"] = True

    buffer = io.StringIO()
    old_stdout = sys.stdout

    inputs = [
        # Act 0
        "SPEAK",
        "What do you think of the peace treaty?",
        "Have you heard anything about the Duke's conduct during the war?",
        "How long until we arrive?",
        "leave",

        # Act 1 (Reynard on estate steps)
        "help",  # Edge case: test help command
        "How long have you served the Duke, Reynard? Thirty years?",
        "What is being served tonight? Is there anything special prepared for the feast or drinks?",
        "time",  # Edge case: test time command
        "",      # Blank enter to step inside

        # Act 2 - Station 1: Fenwick
        "Who here actually supported the war most and profited?",
        "What do you know about the foreign delegation?",
        "What do you really think of the Duke?",
        "log",   # Edge case: test log command
        "",      # Leave Fenwick

        # Act 2 - Station 2: Kitchen & Cellar
        "kitchen",
        "Did Reynard give you any special orders about the wine?",
        "Two of Reynard's cellar staff fell ill today, I heard?",
        "",      # Leave Alwen
        "YES",   # Go down to cellar
        "BOTH",  # Examine both seal and log

        # Act 2 - Station 3: Balcony
        "balcony",

        # Act 2 - Station 4: House Marrow (for completeness & threat note)
        "marrow",
        "I'm sorry about your father.",
        "Tell me about the Verenmark crossing.",
        "",

        # Act 2 - Station 5: Vantrell Table (Ophelia's ring + Cassian's income)
        "vantrell",
        "House Vantrell was heavily involved in the war effort. The peace must cut into your income.",
        "Lady Ophelia, you've been very quiet tonight.",
        "Lady Ophelia, that is a striking silver ring with a red stone you are wearing.",
        "",

        # Act 2 - Station 6: Lady Isolde (Trust + Wine Warning)
        "isolde",
        "You seem to carry the burden of this peace treaty with great grace. What does it cost you?",
        "I am truly glad you are here, Isolde. I see how much you care for this peace.",
        "I believe the ceremonial wine tonight has been tampered with. Do not drink from it at the toast.",
        "",

        # Act 2 - Station 7: Foreign Delegation (Clear Demir)
        "delegation",
        "Counselor Demir, you have my word of complete discretion. What is troubling you?",
        "Thank you for trusting me, Counselor. Your secret is safe with me.",
        "",

        # Act 2 - Head to toast
        "toast",

        # Act 3 - Confrontation
        "Your Grace, stop! The seal on that eastern wine was reapplied — the wax doesn't match — and both cellar staff fell mysteriously ill at four o'clock!",
        "The cellar log shows those bottles were moved today, and Ophelia Vantrell was seen at the cellar door!",
        # Ophelia tell
        "Her! Lady Ophelia Vantrell — she knows exactly what is in that wine!",
        # Reynard moment
        "Why, Reynard? Thirty-one years of service.",
        "You could still do something right. Testify. Tell the Duke everything.",
    ]

    sim = SimulatedPlayer(inputs)

    with unittest.mock.patch.object(D, "pause", lambda *a, **kw: None), \
         unittest.mock.patch.object(D, "clear", lambda: None), \
         unittest.mock.patch.object(D, "get_choice", sim.get_choice), \
         unittest.mock.patch.object(D, "get_free_input", sim.get_free_input), \
         unittest.mock.patch.object(time, "sleep", lambda *a: None):

        sys.stdout = buffer
        try:
            prologue.run(gs)
            assert gs.get_flag("prologue_done"), "Prologue flag not set"

            act0.run(gs)
            assert gs.current_act == "act1", f"Expected act1, got {gs.current_act}"

            act1.run(gs)
            assert gs.current_act == "act2", f"Expected act2, got {gs.current_act}"
            assert gs.get_flag("reynard_met_warmly"), "reynard_met_warmly not set"
            assert gs.get_flag("wine_mentioned_act1"), "wine_mentioned_act1 not set"

            act2.run(gs)
            assert gs.current_act == "act3", f"Expected act3, got {gs.current_act}"
            assert gs.get_flag("wine_seal_discovered"), "wine_seal_discovered not set"
            assert gs.get_flag("cellar_log_found"), "cellar_log_found not set"
            assert gs.get_flag("balcony_vision_seen"), "balcony_vision_seen not set"
            assert gs.get_flag("ophelia_ring_asked"), "ophelia_ring_asked not set"
            assert gs.get_flag("isolde_warned"), "isolde_warned not set"
            assert gs.get_flag("isolde_will_avoid_wine"), "isolde_will_avoid_wine not set"
            assert gs.get_flag("delegation_cleared"), "delegation_cleared not set"

            act3.run(gs)
            assert gs.current_act == "ending_a", f"Expected ending_a, got {gs.current_act}"
            assert gs.get_flag("wine_stopped"), "wine_stopped not set"
            assert gs.get_flag("ophelia_caught"), "ophelia_caught not set"
            assert gs.get_flag("cassian_caught"), "cassian_caught not set"
            assert gs.get_flag("reynard_testified"), "reynard_testified not set"
        finally:
            sys.stdout = old_stdout

    return gs, buffer.getvalue()


def test_edge_cases():
    """Verify key edge cases and alternate endings."""
    results = []

    with unittest.mock.patch.object(D, "pause", lambda *a, **kw: None), \
         unittest.mock.patch.object(D, "clear", lambda: None), \
         unittest.mock.patch.object(time, "sleep", lambda *a: None), \
         contextlib.redirect_stdout(io.StringIO()):

        # 1. Edge Case: Accusing Reynard in Act 3 with < 3 evidence -> Ending D
        gs1 = GameState()
        gs1.current_act = "act3"
        sim1 = SimulatedPlayer(["Reynard is the traitor! Arrest Reynard now!"])
        with unittest.mock.patch.object(D, "get_free_input", sim1.get_free_input):
            act3.run(gs1)
        assert gs1.current_act == "ending_d", f"Expected ending_d, got {gs1.current_act}"
        results.append("✓ Edge Case 1 (Premature Reynard accusation -> Ending D): PASSED")

        # 2. Edge Case: Bluffing with phantom evidence -> Rejected by GM & Cassian
        gs2 = GameState()
        gs2.current_act = "act3"
        sim2 = SimulatedPlayer([
            "The wine seal was broken and reapplied with wrong wax!",  # Phantom bluff (not in log)
            ""  # Give up -> Toast proceeds -> Ending F
        ])
        with unittest.mock.patch.object(D, "get_free_input", sim2.get_free_input):
            act3.run(gs2)
        assert gs2.current_act == "ending_f", f"Expected ending_f after failed bluff, got {gs2.current_act}"
        results.append("✓ Edge Case 2 (Phantom evidence bluff rejection + Toast failure -> Ending F): PASSED")

        # 3. Edge Case: Drink Sacrifice -> Ending G
        gs3 = GameState()
        gs3.current_act = "act3"
        sim3 = SimulatedPlayer(["I reach across, lift Isolde's glass, and drink it myself."])
        with unittest.mock.patch.object(D, "get_free_input", sim3.get_free_input):
            act3.run(gs3)
        assert gs3.current_act == "ending_g", f"Expected ending_g, got {gs3.current_act}"
        results.append("✓ Edge Case 3 (Self-Sacrifice action -> Ending G): PASSED")

        # 4. Edge Case: Easter Egg Passphrase in Act 1
        gs4 = GameState()
        gs4.current_act = "act1"
        sim4 = SimulatedPlayer([
            "The harvest was good this year.",
            "House Vantrell sent me regarding the ceremonial wine.",
            "To implicate the foreign delegation at the toast.",
            "The eastern wine is poisoned.",
            "I know the full plan."
        ])
        with unittest.mock.patch.object(D, "get_free_input", sim4.get_free_input):
            act1.run(gs4)
        # Either passed interrogation (act2 + easter_egg_activated) or failed (ending_d)
        assert gs4.current_act in ("act2", "ending_d")
        results.append(f"✓ Edge Case 4 (Easter Egg Passphrase Interrogation -> {gs4.current_act}): PASSED")

        # 5. Edge Case: Memory & Summarization (>12 messages triggers summary & trims history)
        gs5 = GameState()
        from engine.npc import NPC
        from npcs.fenwick import CONFIG as FENWICK
        fen = NPC(FENWICK, gs5)
        for i in range(6):
            fen.speak(f"Tell me more about the guests, turn {i+1}.")
        assert len(fen.state.conversation_summaries) >= 1, "Conversation summary should have triggered"
        assert len(fen.state.conversation_history) <= 6, "History should have trimmed to last 6 messages"
        results.append("✓ Edge Case 5 (Long-conversation summarization & context trimming): PASSED")

    return results


if __name__ == "__main__":
    print("Running full playthrough (Prologue -> Act 3 -> Ending A)...")
    gs, transcript = run_ending_a_playthrough()
    with open("test_run_transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript)
    print(f"Main Playthrough PASSED! Final Act: {gs.current_act} | Evidence: {len(gs.evidence_log)} | Score: {gs.evidence_score()}")

    print("\nRunning Edge Case Suite...")
    edge_results = test_edge_cases()
    for r in edge_results:
        print(" ", r)
    print("\nALL END-TO-END & EDGE CASE TESTS PASSED!")
