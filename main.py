#!/usr/bin/env python3
# ─────────────────────────────────────────────
#  THE VISCOUNT'S VIGIL
#  main.py — entry point
#
#  Run:  python main.py
#        python main.py --new      (force new game)
#        python main.py --debug    (show LLM prompts)
# ─────────────────────────────────────────────

import sys
import os
import argparse

# ── CLI args ──────────────────────────────────
parser = argparse.ArgumentParser(description="The Viscount's Vigil")
parser.add_argument("--new",   action="store_true", help="Start a new game")
parser.add_argument("--debug", action="store_true", help="Show LLM debug output")
parser.add_argument("--act",   type=str, default=None,
                    help="Jump to act: prologue / act0 / act1 (dev use)")
args = parser.parse_args()

if args.debug:
    import config
    config.DEBUG_MODE = True

# ── Imports (after potential debug flag set) ──
from engine import display as D
from engine.game_state import GameState
import config


# ═══════════════════════════════════════════════
#  SAVE / LOAD
# ═══════════════════════════════════════════════

def load_or_new() -> GameState:
    """Load existing save or create fresh state."""
    if args.new:
        return GameState()

    if os.path.exists(config.SAVE_FILE):
        D.clear()
        D.system_msg("A save file was found.")
        choices = [
            ("LOAD", "Continue from your last save"),
            ("NEW",  "Start a new game"),
        ]
        c = D.get_choice(choices)
        if c == "LOAD":
            try:
                return GameState.load(config.SAVE_FILE)
            except Exception as e:
                D.error_msg(f"Could not load save: {e}")
                D.system_msg("Starting a new game.")

    return GameState()


# ═══════════════════════════════════════════════
#  LLM HEALTH CHECK
# ═══════════════════════════════════════════════

def check_llm():
    """Quick connectivity test before we start."""
    D.system_msg(f"Checking LLM connection ({config.LLM_PROVIDER})...")
    from engine import llm
    test = llm.chat("You are a test.", [{"role": "user", "content": "Say OK."}])
    if test.startswith("[ERROR"):
        D.error_msg(test)
        D.narrate(
            "The game can still run, but NPC conversations will show errors "
            "until the LLM is available.\n\n"
            "Quick setup:\n"
            "  Ollama:  https://ollama.com  →  ollama serve  →  ollama pull llama3.2\n"
            "  Groq:    https://console.groq.com  →  set GROQ_API_KEY in config.py"
        )
        choices = [("CONTINUE", "Continue anyway"), ("QUIT", "Quit and fix the LLM first")]
        c = D.get_choice(choices)
        if c == "QUIT":
            sys.exit(0)
    else:
        D.system_msg(f"LLM connected. ✓")


# ═══════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════

def run_game(gs: GameState):
    """
    Main game loop. Runs the current act and advances.
    When more acts are implemented, add them here.
    """
    from story import prologue, act0, act1, act2, act3

    # Developer jump-to-act
    if args.act:
        gs.current_act = args.act

    while True:
        act = gs.current_act

        if act == "prologue":
            prologue.run(gs)

        elif act == "act0":
            act0.run(gs)

        elif act == "act1":
            act1.run(gs)

        elif act == "act2":
            act2.run(gs)

        elif act == "act3":
            act3.run(gs)    

        else:
            D.error_msg(f"Unknown act: '{act}'. Check game_state.current_act.")
            break


def _show_summary(gs: GameState):
    """End-of-build summary for development."""
    from rich.table import Table
    from rich import box
    from engine.display import console

    console.print()
    console.print("  [dim]── State Summary ──────────────────[/dim]")
    console.print(f"  Time:      {gs.get_time_str()}")
    console.print(f"  Evidence:  {len(gs.evidence_log)} items")
    console.print()
    console.print("  [dim]Notable flags:[/dim]")

    important_flags = [
        ("dream_disclosed_to_reynard", "⚠ Dream disclosed to Reynard — he'll use this"),
        ("reynard_alerted",            "⚠ Reynard is on high alert"),
        ("reynard_met_warmly",         "✓ Reynard met with warmth — backstory thread open"),
        ("wine_mentioned_act1",        "✓ Wine clue in play"),
        ("asked_for_duke_act1",        "  Asked for Duke early — public meeting only"),
        ("easter_egg_activated",       "★ Easter Egg path activated"),
    ]
    for flag, label in important_flags:
        if gs.get_flag(flag):
            console.print(f"    {label}")

    # Reynard FL and SL
    try:
        r = gs.get_npc("reynard")
        console.print(f"\n  Reynard — FL: {r.friendly_level}/3  SL: {r.suspicion_level}/3")
    except KeyError:
        pass
    console.print()


# ═══════════════════════════════════════════════
#  ENTRY
# ═══════════════════════════════════════════════

def main():
    D.title_screen()

    # LLM check
    check_llm()
    D.pause()

    # Load or create game
    gs = load_or_new()

    # Run
    try:
        run_game(gs)
    except KeyboardInterrupt:
        D.narrate("\n\nThe evening is paused. Your save is kept.")
        gs.save()
    except Exception as e:
        D.error_msg(f"Unexpected error: {e}")
        if config.DEBUG_MODE:
            import traceback
            traceback.print_exc()
        gs.save()
        D.system_msg("Game saved before crash.")

    D.system_msg("Goodbye, my lord.")


if __name__ == "__main__":
    main()
