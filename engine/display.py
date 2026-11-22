# ─────────────────────────────────────────────
#  engine/display.py
#  All terminal rendering. Nothing else touches
#  the console directly — everything goes here.
# ─────────────────────────────────────────────

import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich.table import Table
from rich import box
from rich.prompt import Prompt

console = Console()

# ── Colour palette ────────────────────────────
C_NARRATION  = "dim white"
C_DIALOGUE   = "white"
C_NPC_NAME   = "gold1"
C_PLAYER     = "cyan"
C_EVIDENCE   = "green"
C_WARNING    = "red"
C_SYSTEM     = "grey50"
C_VISION     = "magenta"
C_TITLE      = "bold gold1"
C_TIME       = "grey70"


# ═══════════════════════════════════════════
#  Core rendering
# ═══════════════════════════════════════════

def clear():
    console.clear()

def pause(prompt: str = "\n  [dim]Press ENTER to continue...[/dim]"):
    console.print(prompt)
    input()

def title_screen():
    console.clear()
    console.print()
    console.print(
        Panel(
            Text("THE VISCOUNT'S VIGIL", justify="center", style="bold gold1"),
            subtitle="[dim]A fantasy mystery — terminal edition[/dim]",
            border_style="gold1",
            padding=(1, 4),
        )
    )
    console.print()


# ── Scene narration ───────────────────────────

def narrate(text: str, delay: bool = True):
    """Atmospheric narration — italicised, dim."""
    console.print()
    for paragraph in text.strip().split("\n\n"):
        console.print(f"  [italic {C_NARRATION}]{paragraph.strip()}[/]")
        console.print()
        if delay:
            time.sleep(0.4)


def vision(text: str):
    """Vision / dream sequences — magenta, framed."""
    console.print()
    console.print(
        Panel(
            f"[italic {C_VISION}]{text.strip()}[/]",
            title="[bold magenta]~ Vision ~[/bold magenta]",
            border_style="magenta",
            padding=(0, 2),
        )
    )
    console.print()


def scene_header(title: str, time_str: str = ""):
    """Divider between scenes."""
    console.print()
    if time_str:
        console.print(Rule(f"[{C_TIME}]{title}  ·  {time_str}[/]", style="grey30"))
    else:
        console.print(Rule(f"[dim]{title}[/dim]", style="grey30"))
    console.print()


# ── Dialogue ──────────────────────────────────

def npc_speak(name: str, text: str):
    """NPC dialogue with coloured name."""
    # Strip any LLM preamble like "Reynard:" or "REYNARD:"
    clean = text.strip()
    for prefix in [f"{name}:", f"{name.upper()}:", f"**{name}**:"]:
        if clean.startswith(prefix):
            clean = clean[len(prefix):].strip()
    console.print()
    console.print(f"  [{C_NPC_NAME}]{name}[/]  [dim]|[/dim]  [{C_DIALOGUE}]{clean}[/]")
    console.print()


def player_line(text: str):
    """Echo the player's spoken line."""
    console.print(f"  [{C_PLAYER}]You[/]  [dim]|[/dim]  [italic]{text}[/italic]")


# ── Choices ───────────────────────────────────

def show_choices(choices: list[tuple[str, str]], allow_free: bool = False):
    """
    Display numbered choices.
    choices: list of (key, label) e.g. [("A", "Ask about the wine"), ...]
    allow_free: if True, show option to talk freely with NPC.
    """
    console.print(f"  [dim]{'─' * 50}[/dim]")
    for i, (_, label) in enumerate(choices, 1):
        console.print(f"  [bold cyan]{i}.[/bold cyan]  {label}")
    if allow_free:
        console.print(f"  [bold cyan]t.[/bold cyan]  [dim]Talk freely...[/dim]")
    console.print(f"  [dim]{'─' * 50}[/dim]")
    console.print()


def get_choice(choices: list[tuple[str, str]], allow_free: bool = False) -> str:
    """
    Show choices and return the chosen key (e.g. "A") or "FREE".
    Loops until valid input.
    """
    show_choices(choices, allow_free)
    valid = [str(i) for i in range(1, len(choices) + 1)]
    if allow_free:
        valid.append("t")
        valid.append("T")

    while True:
        raw = Prompt.ask("  [bold cyan]>[/bold cyan]").strip()
        if raw in valid:
            if raw.lower() == "t":
                return "FREE"
            idx = int(raw) - 1
            return choices[idx][0]
        console.print(f"  [{C_WARNING}]Enter one of: {', '.join(valid)}[/]")


def get_free_input(prompt: str = "") -> str:
    """Get open-ended text input from the player."""
    if prompt:
        console.print(f"  [dim]{prompt}[/dim]")
    return Prompt.ask("  [bold cyan]You[/bold cyan]").strip()


# ── Evidence log ──────────────────────────────

def show_evidence(log: list[str]):
    if not log:
        console.print("  [dim]Nothing recorded yet.[/dim]")
        return
    console.print()
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column(style=f"dim {C_EVIDENCE}", no_wrap=False, max_width=70)
    for i, entry in enumerate(log, 1):
        table.add_row(f"{i}. {entry}")
    console.print(table)
    console.print()


def evidence_gained(text: str):
    """Flash message when new evidence is logged."""
    console.print()
    console.print(
        Panel(
            f"[{C_EVIDENCE}]{text}[/]",
            title="[bold green]Evidence noted[/bold green]",
            border_style="green",
            padding=(0, 2),
        )
    )
    console.print()


def system_msg(text: str):
    """Meta / system messages (commands, hints)."""
    console.print(f"  [{C_SYSTEM}]{text}[/]")


def error_msg(text: str):
    console.print(f"\n  [{C_WARNING}]{text}[/]\n")


# ── Status bar ────────────────────────────────

def status_bar(time_str: str, evidence_count: int, location: str):
    console.print(
        f"  [dim]Time: [white]{time_str}[/white]  ·  "
        f"Evidence: [green]{evidence_count}[/green]  ·  "
        f"Location: [white]{location}[/white][/dim]"
    )


# ── Atmospheric Feedback & Hints ──────────────

def relationship_change(npc_name: str, attribute: str, direction: str):
    """Subtle, atmospheric notification when an NPC's feeling shifts."""
    if direction == "up":
        icon = "▲"
        color = "green"
    elif direction == "down":
        icon = "▼"
        color = "yellow"
    else:
        return

    hints = {
        "friendly": {
            "up": f"  [dim {color}]{icon} {npc_name} seems warmer toward you.[/]",
            "down": f"  [dim {color}]{icon} {npc_name} has grown cooler.[/]",
        },
        "suspicion": {
            "up": f"  [dim red]▲ {npc_name} watches you more carefully now.[/]",
            "down": f"  [dim green]▼ {npc_name} seems less guarded.[/]",
        },
        "trust": {
            "up": f"  [dim {color}]{icon} {npc_name} trusts your discretion.[/]",
            "down": f"  [dim {color}]{icon} {npc_name}'s trust wavers.[/]",
        },
    }
    msg = hints.get(attribute, {}).get(direction, f"  [dim]{icon} Something shifted with {npc_name}.[/]")
    console.print(msg)


def contextual_hint(text: str):
    """Atmospheric, non-intrusive thought or observation."""
    console.print(f"  [dim italic grey62]💭 {text}[/]")

