# ─────────────────────────────────────────────
#  story/prologue.py
#  The opening dream. Entirely scripted —
#  no choices, no LLM. Pure atmosphere.
# ─────────────────────────────────────────────

import time
from engine import display as D
from engine.game_state import GameState


def run(gs: GameState):
    """Run the prologue dream sequence."""

    D.clear()
    D.title_screen()
    D.pause("  [dim]Press ENTER to begin...[/dim]")
    D.clear()

    # ── The Dream ─────────────────────────────

    D.vision(
        "Black. Silence.\n\n"
        "Then — fragments. Like looking through broken glass at candlelight."
    )
    D.pause()

    D.vision(
        "A hall full of people. Laughter. Music.\n\n"
        "A glass of deep red wine, held up in toast."
    )
    D.pause()

    D.vision(
        "A hand — gloved in black — passing behind a table.\n\n"
        "Too quick. Too careful."
    )
    D.pause()

    D.vision(
        "A woman's face. Half-turned. Smiling at someone you cannot see.\n\n"
        "The glass rising to her lips."
    )
    D.pause()

    D.vision(
        "And then—\n\n"
        "Nothing.\n\n"
        "Just the sound of something shattering.\n\n"
        "And her gasp."
    )
    D.pause()

    # ── Waking ────────────────────────────────

    D.clear()
    time.sleep(0.5)

    D.narrate(
        "You wake.\n\n"
        "Your room. Pre-dawn. The kind of dark that sits on your chest.\n\n"
        "You sit up slowly, pressing two fingers to your temples.\n\n"
        "The visions have come before. Your grandmother called it the Sight — said the bloodline "
        "carried it like a scar. They are never clear. They are never wrong."
    )

    D.narrate(
        "You dress without speaking to your valet.\n\n"
        "Today you are expected at Grand Duke Aldric's estate. Tonight, the peace treaty "
        "will be signed. They say it ends ten years of war. Two hundred nobles celebrating.\n\n"
        "You say nothing about what you saw.\n\n"
        "But you don't stop seeing it."
    )

    D.pause()

    # Update state
    gs.current_act = "act0"
    gs.current_scene = "carriage"
    gs.set_flag("prologue_done", True)
    gs.save()
