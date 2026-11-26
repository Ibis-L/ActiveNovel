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


def _summarize_conversation(ns: "NPCState", npc_name: str):
    """
    Summarize older conversation history to save LLM context window
    while preserving conversational memory across long sessions.
    """
    if len(ns.conversation_history) < 12:
        return
    old_messages = ns.conversation_history[:-6]
    summary_prompt = (
        f"You are the memory keeper for {npc_name} in a mystery story. "
        "Summarize the following past exchanges with the player (Viscount) into 2 concise sentences. "
        "Capture what was discussed, what commitments or hints were shared, and the tone. "
        "Return ONLY the 2-sentence summary."
    )
    summary = llm.chat(
        system_prompt=summary_prompt,
        messages=old_messages,
        temperature=0.3,
    )
    if not summary.startswith("[ERROR") and len(summary.strip()) > 10:
        ns.conversation_summaries.append(summary.strip())
        # Retain only the most recent 6 messages in active context
        ns.conversation_history = ns.conversation_history[-6:]


def _extract_memories(player_msg: str, npc_response: str, ns: "NPCState"):
    """
    Extract key player facts (promises, secrets, preferences, accusations)
    to form persistent character memory.
    """
    # Sample every 3 exchanges to keep performance fast
    if ns.times_spoken % 3 != 0:
        return
    prompt = (
        "Analyze this single dialogue exchange. "
        "Extract 1-2 key facts the character should remember about the player (e.g. claims, promises, "
        "secrets revealed, suspicious inquiries, personal attitudes). "
        "Format: 1 line per fact, max 12 words each. "
        "If there are no significant personal facts revealed, output NONE."
    )
    raw = llm.chat(
        system_prompt=prompt,
        messages=[{"role": "user", "content": f'Player said: "{player_msg}"\nNPC replied: "{npc_response}"'}],
        temperature=0.2,
    )
    if raw.startswith("[ERROR") or "none" in raw.lower()[:10]:
        return
    for line in raw.strip().split("\n"):
        clean_fact = line.strip().lstrip("-*123456789. ")
        if len(clean_fact) > 6 and clean_fact.lower() != "none":
            if clean_fact not in ns.memories:
                ns.memories.append(clean_fact)
                if len(ns.memories) > 10:
                    ns.memories.pop(0)


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
        Handles tag extraction, history, summarization, and analysis.
        Returns the clean response text (no tag).
        """
        ns     = self.state
        system = self._prompt_fn(self.gs, ns)

        # Inject live temporal & memory context into character prompt
        memory_blocks = [
            f"SITUATIONAL CONTEXT:\n"
            f"- Current Time: {self.gs.get_time_str()} ({self.gs.minutes_to_toast()} minutes until the ceremonial toast).\n"
            f"- Stay strictly in character, keep responses concise (2–4 sentences), and never repeat earlier lines verbatim."
        ]
        if ns.conversation_summaries:
            recent_summaries = " ".join(ns.conversation_summaries[-3:])
            memory_blocks.append(f"PREVIOUS CONVERSATION CONTEXT:\n{recent_summaries}")
        if ns.memories:
            salient_facts = "\n- ".join(ns.memories)
            memory_blocks.append(f"THINGS YOU SPECIFICALLY REMEMBER ABOUT THIS PERSON:\n- {salient_facts}")
        if getattr(ns, "emotional_state", "neutral") != "neutral":
            memory_blocks.append(f"CURRENT EMOTIONAL STATE: {ns.emotional_state}")

        system += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" + "\n\n".join(memory_blocks)

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
        if not clean.strip():
            clean = f".....({self.name} chooses to be silent)"

        # Store tag on state object for analysis fallback
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

        # Memory extraction & periodic conversation summarization
        _extract_memories(player_message, clean, ns)
        if ns.times_spoken % 6 == 0 and len(ns.conversation_history) >= 12:
            _summarize_conversation(ns, self.name)

        return clean

    def free_conversation(self, intro_text: str = ""):
        """
        Open conversation loop.
        Empty input (just Enter) → exit the conversation.
        'log' → show evidence. 'time' → show clock. 'help' → show guidance.
        """
        if intro_text:
            D.narrate(intro_text)

        D.system_msg(
            f"Talking with {self.name}. "
            "Type naturally. Press Enter on blank line to walk away. "
            "Type 'help' for options."
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
            if cmd == "help":
                D.system_msg("Tips:")
                D.system_msg("  • Type anything in natural prose: questions, observations, jokes, or suspicions.")
                D.system_msg("  • Commands: 'log' (check evidence), 'time' (check clock), 'help' (this menu).")
                D.system_msg("  • Press Enter on a blank line to politely conclude the conversation.")
                continue

            D.player_line(raw)
            response = self.speak(raw)

            if response.startswith("[ERROR"):
                D.error_msg(response)
                D.system_msg("(Communication paused. You can try again or press Enter to step away.)")
                hist = self.state.conversation_history
                if hist: hist.pop()
                if hist: hist.pop()
                continue

            D.npc_speak(self.name, response)
            self.gs.advance_clock(5)