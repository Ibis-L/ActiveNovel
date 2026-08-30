# ─────────────────────────────────────────────
#  engine/npc.py
#  Base NPC class.
#
#  speak() flow:
#    1. Build system prompt (state-injected)
#    2. Call LLM → raw response
#    3. Strip [STATE: ...] tag if present
#       → tag stored on ns._tag for analysis fallback
#       → clean response stored in history & returned
#    4. Run analysis rules (Option 2 + Option 3 fallback)
# ─────────────────────────────────────────────

from __future__ import annotations
import re
from typing import TYPE_CHECKING
from engine import llm
from engine import display as D

if TYPE_CHECKING:
    from engine.game_state import GameState, NPCState


# Regex for the optional [STATE: ...] tag Reynard emits
_TAG_RE = re.compile(r"^\[STATE:\s*([^\]]+)\]\s*", re.IGNORECASE)


def _extract_tag(raw: str) -> tuple[str, str]:
    """
    Split a [STATE: ...] prefix from the response.
    Returns (clean_response, tag_content).
    If no tag, tag_content is "".
    """
    m = _TAG_RE.match(raw.strip())
    if m:
        tag_content = m.group(1).strip()
        clean = raw.strip()[m.end():].strip()
        return clean, tag_content
    return raw.strip(), ""


class NPC:
    """
    A living NPC.

    Config dict keys:
      id          : str
      name        : str
      prompt_fn   : Callable[[GameState, NPCState], str]
      analysis    : list[Callable[[str, str, NPCState, GameState], None]]
    """

    def __init__(self, config: dict, game_state: "GameState"):
        self.id: str   = config["id"]
        self.name: str = config["name"]
        self._prompt_fn   = config["prompt_fn"]
        self._analysis    = config.get("analysis", [])
        self.gs = game_state
        self.gs.init_npc(self.id, self.name)

    @property
    def state(self) -> "NPCState":
        return self.gs.get_npc(self.id)

    def speak(self, player_message: str, temperature: float = 0.75) -> str:
        """
        Send a message and get the NPC's response.
        Handles tag extraction, history, and analysis.
        Returns the clean response text (no tag).
        """
        ns     = self.state
        system = self._prompt_fn(self.gs, ns)

        # Build history with player's new message
        ns.conversation_history.append({
            "role": "user",
            "content": player_message,
        })

        # Call LLM
        raw = llm.chat(
            system_prompt=system,
            messages=ns.conversation_history,
            temperature=temperature,
        )

        # Extract [STATE: ...] tag (Option 3 data)
        clean, tag = _extract_tag(raw)

        # Store tag on state object for analysis fallback
        # (not persisted to JSON — just lives during this session)
        ns._tag = tag  # type: ignore[attr-defined]

        # Store CLEAN response in history (no tag pollution for future turns)
        ns.conversation_history.append({
            "role": "assistant",
            "content": clean,
        })
        ns.times_spoken += 1

        # Run analysis rules
        for rule in self._analysis:
            rule(player_message, clean, ns, self.gs)

        return clean

    def free_conversation(self, intro_text: str = ""):
        """
        Open conversation loop.
        Empty input (just Enter) → exit the conversation.
        'log' → show evidence. 'time' → show clock.
        """
        if intro_text:
            D.narrate(intro_text)

        D.system_msg(
            f"Talking with {self.name}. "
            "Press Enter on a blank line to walk away. "
            "Type 'log' to check evidence."
        )

        while True:
            raw = D.get_free_input()

            # Empty Enter → leave
            if not raw or not raw.strip():
                D.narrate(f"You say nothing more and step away from {self.name}.")
                break

            cmd = raw.lower().strip()

            if cmd == "log":
                D.show_evidence(self.gs.evidence_log)
                continue
            if cmd == "time":
                D.system_msg(f"The time is {self.gs.get_time_str()}.")
                continue

            D.player_line(raw)
            response = self.speak(raw)

            if response.startswith("[ERROR"):
                D.error_msg(response)
                hist = self.state.conversation_history
                if hist: hist.pop()
                if hist: hist.pop()
                continue

            D.npc_speak(self.name, response)
            self.gs.advance_clock(5)