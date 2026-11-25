"""
Full Game End-to-End Test and Validation Harness
Simulates complete gameplay from Prologue through Act 3 to Ending A,
testing edge cases, state transitions, relationship shifts, and NPC dialogue.
"""

import sys
import os
import unittest.mock

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from engine.game_state import GameState
from engine.npc import NPC
from engine import display as D
from engine import llm
import config

# Turn off delays for testing speed
config.TYPING_DELAY = False

transcript_log = []

def record(speaker, text):
    transcript_log.append(f"[{speaker}] {text.strip()}")

# Wrap display methods to capture the transcript
orig_narrate = D.narrate
orig_npc_speak = D.npc_speak
orig_player_line = D.player_line
orig_vision = D.vision
orig_evidence_gained = D.evidence_gained
orig_relationship_change = D.relationship_change

def mock_narrate(text, delay=False):
    record("NARRATION", text)

def mock_npc_speak(name, text):
    record(name, text)

def mock_player_line(text):
    record("YOU", text)

def mock_vision(text):
    record("VISION", text)

def mock_evidence_gained(text):
    record("EVIDENCE NOTED", text)

def mock_relationship_change(npc_name, attr, direction):
    record("SYSTEM", f"{npc_name} {attr} -> {direction}")

def run_full_test():
    with unittest.mock.patch.object(D, "narrate", mock_narrate), \
         unittest.mock.patch.object(D, "npc_speak", mock_npc_speak), \
         unittest.mock.patch.object(D, "player_line", mock_player_line), \
         unittest.mock.patch.object(D, "vision", mock_vision), \
         unittest.mock.patch.object(D, "evidence_gained", mock_evidence_gained), \
         unittest.mock.patch.object(D, "relationship_change", mock_relationship_change), \
         unittest.mock.patch.object(D, "pause", lambda *a, **kw: None):

        print("=================================================================")
        print("STARTING END-TO-END PLAYTHROUGH TEST: THE VISCOUNT'S VIGIL")
        print("=================================================================\n")

        gs = GameState()

        # -------------------------------------------------------------
        # PROLOGUE
        # -------------------------------------------------------------
        from story import prologue
        prologue.run(gs)
        assert gs.current_act == "act0"
        assert gs.get_flag("prologue_done")
        print("✓ Prologue completed successfully.")

        # -------------------------------------------------------------
        # ACT 0 — THE CARRIAGE (Talking with Aldous)
        # -------------------------------------------------------------
        from story import act0
        # Mock choice: SPEAK to Aldous
        with unittest.mock.patch.object(D, "get_choice", return_value="SPEAK"):
            # Mock conversation inputs to Aldous, then finish
            aldous_inputs = [
                "What do you think of the peace treaty?",
                "Have you heard anything about the Duke's conduct during the war?",
                "How long until we arrive?",
                "done"
            ]
            with unittest.mock.patch.object(D, "get_free_input", side_effect=aldous_inputs):
                act0.run(gs)

        assert gs.current_act == "act1"
        assert gs.game_clock == 0
        print("✓ Act 0 (The Carriage) completed successfully.")

        # -------------------------------------------------------------
        # ACT 1 — THE ESTATE STEPS (Reynard)
        # -------------------------------------------------------------
        from story import act1
        # Conversing with Reynard: build trust, ask about arrangements, then enter
        reynard_inputs = [
            "How long have you served the Duke, Reynard? Thirty-one years?",
            "What's being served tonight? Is there anything special prepared for the signing?",
            ""  # blank enter to step inside
        ]
        with unittest.mock.patch.object(D, "get_free_input", side_effect=reynard_inputs):
            act1.run(gs)

        assert gs.current_act == "act2"
        assert gs.get_flag("reynard_met_warmly")
        assert gs.get_flag("wine_mentioned_act1")
        assert len(gs.evidence_log) >= 1
        print("✓ Act 1 (The Estate Steps) completed successfully. Clue: Wine mentioned logged.")

        # -------------------------------------------------------------
        # ACT 2 — THE PARTY FLOOR (Exploration & Investigation)
        # -------------------------------------------------------------
        from story import act2
        
        # 1. Fenwick opening
        fenwick_inputs = [
            "Who here actually supported the war most? Who profited?",
            "What do you know about the foreign delegation?",
            "What do you think of the Duke?",
            "" # walk away
        ]
        with unittest.mock.patch.object(D, "get_free_input", side_effect=fenwick_inputs):
            act2._setup(gs)
            act2._fenwick_opening(gs)

        assert "vantrell" in gs.unlocked_stations
        assert "delegation" in gs.unlocked_stations
        print("✓ Act 2: Fenwick station completed. Unlocked Vantrell & Delegation.")

        # 2. Kitchen & Cellar
        kitchen_inputs = [
            "Two of Reynard's cellar staff fell ill today, I heard?",
            "Did Reynard give you any special orders about the wine?",
            "" # walk away from Mrs. Alwen
        ]
        with unittest.mock.patch.object(D, "get_free_input", side_effect=kitchen_inputs), \
             unittest.mock.patch.object(D, "get_choice", side_effect=["YES", "BOTH"]):
            act2._visit_kitchen(gs)

        assert gs.get_flag("wine_seal_discovered")
        assert gs.get_flag("cellar_log_found")
        assert gs.get_flag("illness_discovered")
        print("✓ Act 2: Kitchen & Cellar completed. Clues: Seal reapplied, Cellar log found, Staff illness.")

        # 3. The Balcony (Vision)
        # Set clock inside window
        gs.set_data("vision_window_open", gs.game_clock - 5)
        gs.set_data("vision_window_close", gs.game_clock + 20)
        act2._visit_balcony(gs)
        assert gs.get_flag("balcony_vision_seen")
        print("✓ Act 2: Balcony Vision triggered. Clue: Reynard and woman with ruby ring.")

        # 4. House Marrow (Lady Brienne)
        marrow_inputs = [
            "I'm sorry about your father.",
            "Tell me about the Verenmark crossing — if you want to.",
            "What did you mean about Vantrell's supply chain?",
            "I saw you receive that note. Leave before midnight? You might be in danger.",
            "" # step away
        ]
        # Ensure Vantrell was visited or simulate visit count so note is delivered
        gs.record_visit("vantrell")
        with unittest.mock.patch.object(D, "get_free_input", side_effect=marrow_inputs):
            act2._visit_marrow(gs)
        assert gs.get_flag("brienne_note_delivered")
        print("✓ Act 2: House Marrow completed. Threat note delivered and analyzed.")

        # 5. House Vantrell (Cassian & Ophelia)
        vantrell_inputs = [
            "Lord Cassian, the peace must cut into your arms income significantly.",
            "Lady Ophelia, you've been remarkably quiet tonight.",
            "Lady Ophelia, that is a striking silver ring with a red stone on your hand.",
            "" # step away
        ]
        with unittest.mock.patch.object(D, "get_free_input", side_effect=vantrell_inputs):
            act2._visit_vantrell(gs)
        assert gs.get_flag("ophelia_ring_asked")
        print("✓ Act 2: House Vantrell completed. Clues: Ophelia ring matched, cellar activity noted.")

        # 6. Lady Isolde (Building trust & warning about wine)
        isolde_inputs = [
            "Lady Isolde, you seem to be the only person genuinely enjoying the evening.",
            "What does tonight cost you personally, if I may ask?",
            "Lady Isolde, please listen to me. I believe the ceremonial wine tonight has been tampered with. Do not drink it.",
            "" # step away
        ]
        with unittest.mock.patch.object(D, "get_free_input", side_effect=isolde_inputs):
            act2._visit_isolde(gs)
        assert gs.get_flag("isolde_will_avoid_wine")
        print("✓ Act 2: Lady Isolde completed. Trust built, Isolde self-save armed.")

        # 7. Foreign Delegation (Demir & Kavir)
        delegation_inputs = [
            "Counselor Demir, you have my complete word of discretion. What is troubling you?",
            "General Kavir, how does a soldier feel about this peace tonight?",
            "" # step away
        ]
        with unittest.mock.patch.object(D, "get_free_input", side_effect=delegation_inputs):
            act2._visit_delegation(gs)
        assert gs.get_flag("delegation_cleared")
        print("✓ Act 2: Foreign Delegation completed. Delegation cleared of conspiracy.")

        # 8. Grand Duke Aldric
        duke_inputs = [
            "Your Grace, the ceremonial wine from the eastern court has been tampered with. The seal was reapplied.",
            "" # step away
        ]
        with unittest.mock.patch.object(D, "get_free_input", side_effect=duke_inputs):
            act2._visit_duke(gs)
        print("✓ Act 2: Duke audience completed.")

        print(f"Total evidence gathered before Act 3: {len(gs.evidence_log)} items.")
        assert gs.evidence_score() >= 4

        # Transition to Act 3
        act2._transition_to_act3(gs)
        assert gs.current_act == "act3"
        print("✓ Act 2 concluded, transitioned to Act 3.")

        # -------------------------------------------------------------
        # ACT 3 — THE TOAST (Confrontation & Ending A)
        # -------------------------------------------------------------
        from story import act3

        # Climax confrontation speech citing real evidence
        confrontation_inputs = [
            # Turn 1: Lead with the altered seal and cellar log
            "Your Grace, stop! The wine seal was reapplied with wrong wax, and Reynard moved those bottles in his cellar log!",
            # Turn 2: Name the illness and Ophelia at the cellar door with the ruby ring
            "Mrs. Alwen confirmed both cellar staff fell suddenly ill at four o'clock, and Ophelia Vantrell was at the cellar door with Reynard wearing that ruby ring!",
        ]
        # In aftermath: Name Ophelia when she reaches
        ophelia_tell_input = ["Her! Lady Ophelia Vantrell knows exactly what is in that wine!"]
        # In Reynard moment: ask why, then urge testimony
        reynard_moment_inputs = [
            "Why, Reynard? Thirty-one years of service.",
            "You could still do something right. Testify. Tell the Duke everything."
        ]

        all_act3_inputs = confrontation_inputs + ophelia_tell_input + reynard_moment_inputs + [""]

        with unittest.mock.patch.object(D, "get_free_input", side_effect=all_act3_inputs):
            act3.run(gs)

        assert gs.current_act == "ending_a"
        assert gs.get_flag("ophelia_caught")
        assert gs.get_flag("reynard_testified")
        print("✓ Act 3 completed! ENDING A (FULL VICTORY) ACHIEVED!")
        print("=================================================================\n")

        return gs

if __name__ == "__main__":
    state = run_full_test()
    # Save test transcript
    with open("test_run_transcript.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(transcript_log))
    print(f"Complete test transcript written to test_run_transcript.txt ({len(transcript_log)} events).")
