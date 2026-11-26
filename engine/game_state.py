# ─────────────────────────────────────────────
#  engine/game_state.py
#  Central source of truth for everything that
#  happens, has happened, or was discovered.
# ─────────────────────────────────────────────

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
import json, os


# ── Per-NPC State ────────────────────────────

@dataclass
class NPCState:
    npc_id: str
    name: str

    # Relationship
    friendly_level: int = 0          # 0–3  — how open this NPC is with player
    suspicion_level: int = 0         # 0–3  — how suspicious of player (for Reynard etc.)
    times_spoken: int = 0
    emotional_state: str = "neutral" # neutral, guarded, warm, alarmed, solemn, etc.

    # Conversation memory
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    conversation_summaries: List[str] = field(default_factory=list) # Compressed memories
    memories: List[str] = field(default_factory=list)               # Salient facts about player

    # NPC-specific boolean flags (e.g. "backstory_mentioned", "warned_player")
    flags: Dict[str, bool] = field(default_factory=dict)

    def set_flag(self, key: str, value: bool = True):
        self.flags[key] = value

    def get_flag(self, key: str, default: bool = False) -> bool:
        return self.flags.get(key, default)

    def bump_fl(self, amount: int = 1):
        old = self.friendly_level
        self.friendly_level = min(3, self.friendly_level + amount)
        if self.friendly_level > old:
            from engine import display as D
            D.relationship_change(self.name, "friendly", "up")

    def decrease_fl(self, amount: int = 1):
        old = self.friendly_level
        self.friendly_level = max(0, self.friendly_level - amount)
        if self.friendly_level < old:
            from engine import display as D
            D.relationship_change(self.name, "friendly", "down")

    def bump_sl(self, amount: int = 1):
        old = self.suspicion_level
        self.suspicion_level = min(3, self.suspicion_level + amount)
        if self.suspicion_level > old:
            from engine import display as D
            D.relationship_change(self.name, "suspicion", "up")

    def decrease_sl(self, amount: int = 1):
        old = self.suspicion_level
        self.suspicion_level = max(0, self.suspicion_level - amount)
        if self.suspicion_level < old:
            from engine import display as D
            D.relationship_change(self.name, "suspicion", "down")


# ── Global Game State ────────────────────────

@dataclass
class GameState:
    # ── Progress ──────────────────────────────
    current_act: str = "prologue"
    current_scene: str = "dream"

    # ── Clock ─────────────────────────────────
    # Minutes offset from 7 PM (arrival).
    # Act 0 carriage: -120 (5 PM).  Toast: 180 (10 PM).
    game_clock: int = -120

    # ── Evidence Log ──────────────────────────
    # Human-readable clues written in the Viscount's voice.
    evidence_log: List[str] = field(default_factory=list)

    # ── NPC States ────────────────────────────
    npc_states: Dict[str, Any] = field(default_factory=dict)

    # ── World Flags ───────────────────────────
    # Named booleans tracking every branch decision.
    flags: Dict[str, bool] = field(default_factory=dict)

    # ── Player Choice Log ─────────────────────
    player_choices: List[str] = field(default_factory=list)

    # ── Unlocked Stations ─────────────────────
    unlocked_stations: List[str] = field(default_factory=lambda: ["kitchen", "balcony"])

    # ── Non-bool metadata ─────────────────────
    # For integers, strings, etc. that don't fit flags (which are bool-only).
    # e.g. aldous_naturalness, vision_window_open, passphrase_counter
    data: Dict[str, Any] = field(default_factory=dict)

    # ═══════════════════════════════════════════
    #  NPC helpers
    # ═══════════════════════════════════════════

    def init_npc(self, npc_id: str, name: str) -> NPCState:
        if npc_id not in self.npc_states:
            self.npc_states[npc_id] = NPCState(npc_id=npc_id, name=name)
        return self.npc_states[npc_id]

    def get_npc(self, npc_id: str) -> NPCState:
        if npc_id not in self.npc_states:
            raise KeyError(f"NPC '{npc_id}' not initialized. Call init_npc first.")
        s = self.npc_states[npc_id]
        # Re-hydrate from dict if loaded from JSON
        if isinstance(s, dict):
            self.npc_states[npc_id] = NPCState(**s)
        return self.npc_states[npc_id]

    # ═══════════════════════════════════════════
    #  Evidence helpers
    # ═══════════════════════════════════════════

    def add_evidence(self, text: str) -> bool:
        """Add an evidence entry. Returns True if it was new."""
        if text not in self.evidence_log:
            self.evidence_log.append(text)
            return True
        return False

    # ═══════════════════════════════════════════
    #  Flag helpers
    # ═══════════════════════════════════════════

    def set_flag(self, key: str, value: bool = True):
        self.flags[key] = value

    def get_flag(self, key: str, default: bool = False) -> bool:
        return self.flags.get(key, default)

    def log_choice(self, label: str):
        self.player_choices.append(label)

    def unlock_station(self, station: str):
        if station not in self.unlocked_stations:
            self.unlocked_stations.append(station)

    # ═══════════════════════════════════════════
    #  Data helpers (non-bool metadata)
    # ═══════════════════════════════════════════

    def set_data(self, key: str, value: Any):   
        self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    # ═══════════════════════════════════════════
    #  Clock helpers
    # ═══════════════════════════════════════════

    def advance_clock(self, minutes: int):
        self.game_clock += minutes

    def get_time_str(self) -> str:
        base_minutes = 19 * 60          # 7 PM in minutes from midnight
        total = base_minutes + self.game_clock
        h = (total // 60) % 24
        m = total % 60
        period = "AM" if h < 12 else "PM"
        dh = h % 12 or 12
        return f"{dh}:{m:02d} {period}"

    # ═══════════════════════════════════════════
    #  Persistence
    # ═══════════════════════════════════════════

    def save(self, path: str = "data/saves/game_state.json"):
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        data = asdict(self)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str = "data/saves/game_state.json") -> GameState:
        with open(path, "r") as f:
            data = json.load(f)
        npc_raw = data.pop("npc_states", {})
        state = cls(**data)
        state.npc_states = {k: NPCState(**v) for k, v in npc_raw.items()}
        return state
    
    def station_visits(self, station: str) -> int:
        return self.data.get(f"visits_{station}", 0)

    def record_visit(self, station: str):
        self.data[f"visits_{station}"] = self.station_visits(station) + 1

    def minutes_to_toast(self) -> int:
        return max(0, 180 - self.game_clock)

    def evidence_score(self) -> int:
        """Count how many key conspiracy clues are in the log."""
        ev = "\n".join(self.evidence_log).lower()
        clue_groups = [
            ("wine seal",),
            ("cellar staff",),
            ("reynard cellar", "reynard's cellar"),
            ("ophelia",),
            ("vision",),
            ("illness", "suddenly ill", "incapacitated"),
            ("repositioned", "cellar log"),
        ]
        return sum(1 for group in clue_groups if any(t in ev for t in group))
