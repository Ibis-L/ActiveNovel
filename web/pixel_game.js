// ─────────────────────────────────────────────────────────────
//  web/pixel_game.js — 2D Pixel Art & Animation Engine
//  Connects to FastAPI /api/* endpoints powered by the exact
//  Python NPC/LLM/Story engine.
// ─────────────────────────────────────────────────────────────

const worldCanvas = document.getElementById("worldCanvas");
const ctx = worldCanvas.getContext("2d");
const pCanvas = document.getElementById("portraitCanvas");
const pCtx = pCanvas.getContext("2d");

const chatLog = document.getElementById("chatLog");
const playerInput = document.getElementById("playerInput");
const talkForm = document.getElementById("talkForm");
const quickActions = document.getElementById("quickActions");
const stationBar = document.getElementById("stationBar");
const portraitName = document.getElementById("portraitName");
const controlsHint = document.getElementById("controlsHint");

let sessionId = null;
let gameState = null;
let activeNpc = "aldous";
let busy = false;
let tick = 0;

// ── Player pixel avatar (Act 2 Manor) ────────────────────────
const player = {
  x: 240,
  y: 195,
  targetX: null,
  targetY: null,
  speed: 1.5,
  dir: 0, // 0=down,1=up,2=left,3=right
  moving: false,
};

const keys = {};
window.addEventListener("keydown", (e) => {
  if (document.activeElement === playerInput) return;
  keys[e.key.toLowerCase()] = true;
});
window.addEventListener("keyup", (e) => {
  keys[e.key.toLowerCase()] = false;
});

worldCanvas.addEventListener("click", (e) => {
  if (!gameState || gameState.current_act !== "act2") return;
  const rect = worldCanvas.getBoundingClientRect();
  const sx = ((e.clientX - rect.left) / rect.width) * worldCanvas.width;
  const sy = ((e.clientY - rect.top) / rect.height) * worldCanvas.height;
  player.targetX = sx;
  player.targetY = sy;

  // Check if clicked directly on an NPC
  const npcs = getAct2NPCs();
  for (const n of npcs) {
    if (Math.hypot(sx - n.x, sy - n.y) < 18) {
      selectNpc(n.id);
      break;
    }
  }
});

// ── Character Palettes for Pixel Sprites ─────────────────────
const CHAR_STYLE = {
  viscount:  { hair: "#3d2b24", skin: "#f0c8a8", coat: "#284166", trim: "#e6c15a", label: "Viscount" },
  aldous:    { hair: "#9e9890", skin: "#e0b392", coat: "#5a4636", trim: "#8c7258", label: "Aldous" },
  reynard:   { hair: "#cfd4dc", skin: "#ebcab2", coat: "#1c1c26", trim: "#c2c7d4", label: "Reynard" },
  fenwick:   { hair: "#b58b5c", skin: "#f2c9ae", coat: "#592b49", trim: "#e6c15a", label: "Lord Fenwick" },
  brienne:   { hair: "#2b2124", skin: "#edd0be", coat: "#16151c", trim: "#6e6a7a", label: "Lady Brienne" },
  cassian:   { hair: "#593b28", skin: "#edc3a3", coat: "#7d2130", trim: "#e6c15a", label: "Lord Cassian" },
  ophelia:   { hair: "#2b1c26", skin: "#f0d3c2", coat: "#451e42", trim: "#d93654", label: "Lady Ophelia" },
  isolde:    { hair: "#c79a52", skin: "#f5d6c3", coat: "#d9d0c1", trim: "#e6c15a", label: "Lady Isolde" },
  duke:      { hair: "#c2c6cf", skin: "#e6be9e", coat: "#203354", trim: "#e6c15a", label: "Duke Aldric" },
  demir:     { hair: "#26211e", skin: "#d9a982", coat: "#2b4d44", trim: "#d6b05c", label: "Counselor Demir" },
  kavir:     { hair: "#454240", skin: "#d19d77", coat: "#4a2e28", trim: "#a8a29e", label: "General Kavir" },
  mrs_alwen: { hair: "#8a7c75", skin: "#ecc3a5", coat: "#7a5848", trim: "#ebe6df", label: "Mrs Alwen" },
};

function getAct2NPCs() {
  if (!gameState) return [];
  const scene = gameState.current_scene;
  const unlocked = new Set(gameState.unlocked_stations || []);
  if (scene === "kitchen") {
    return [{ id: "mrs_alwen", x: 240, y: 120 }];
  }
  if (scene === "balcony") {
    return [];
  }
  // Party floor
  const list = [
    { id: "fenwick", x: 240, y: 135 },
    { id: "reynard", x: 405, y: 95 },
  ];
  if (unlocked.has("marrow"))     list.push({ id: "brienne", x: 75,  y: 195 });
  if (unlocked.has("vantrell")) {
    list.push({ id: "cassian", x: 115, y: 100 });
    list.push({ id: "ophelia", x: 148, y: 105 });
  }
  if (unlocked.has("delegation")) {
    list.push({ id: "demir", x: 375, y: 175 });
    list.push({ id: "kavir", x: 408, y: 175 });
  }
  if (unlocked.has("isolde") || true) list.push({ id: "isolde", x: 325, y: 215 });
  if (unlocked.has("duke"))       list.push({ id: "duke",   x: 240, y: 68 });
  return list;
}

// ── Pixel Sprite Drawing Helper ──────────────────────────────
function drawPixelChar(c, id, x, y, scale = 1, isMoving = false, frame = 0, facingLeft = false) {
  const s = CHAR_STYLE[id] || CHAR_STYLE.viscount;
  const bob = isMoving ? (Math.floor(frame / 6) % 2 === 0 ? -1 : 0) : (Math.floor(frame / 28) % 2 === 0 ? 0 : -1);
  const legOff = isMoving ? (Math.floor(frame / 6) % 2 === 0 ? 1 : -1) : 0;

  c.save();
  c.translate(Math.round(x), Math.round(y));
  c.scale(facingLeft ? -scale : scale, scale);

  // Shadow
  c.fillStyle = "rgba(0,0,0,0.45)";
  c.fillRect(-5, 6, 10, 3);

  // Legs
  c.fillStyle = "#1a1721";
  c.fillRect(-3, 2 + (legOff > 0 ? -1 : 0), 2, 5);
  c.fillRect(1,  2 + (legOff < 0 ? -1 : 0), 2, 5);

  // Coat / Torso
  c.fillStyle = s.coat;
  c.fillRect(-5, -6 + bob, 10, 9);
  c.fillStyle = s.trim;
  c.fillRect(-1, -6 + bob, 2, 7);

  // Head
  c.fillStyle = s.skin;
  c.fillRect(-4, -13 + bob, 8, 7);

  // Hair
  c.fillStyle = s.hair;
  c.fillRect(-4, -15 + bob, 8, 3);
  c.fillRect(-5, -13 + bob, 1, 3);

  // Eyes
  c.fillStyle = "#181520";
  c.fillRect(-2, -10 + bob, 1, 2);
  c.fillRect(2,  -10 + bob, 1, 2);

  // Special props (Ophelia ruby ring / Fenwick glass)
  if (id === "ophelia") {
    c.fillStyle = "#ff2e55";
    c.fillRect(5, -1 + bob, 2, 2);
  } else if (id === "fenwick") {
    c.fillStyle = "#a3223a";
    c.fillRect(5, -3 + bob, 2, 3);
  }
  c.restore();
}

function drawPortrait(id) {
  const s = CHAR_STYLE[id] || CHAR_STYLE.viscount;
  pCtx.clearRect(0, 0, 32, 32);
  pCtx.fillStyle = "#12101e";
  pCtx.fillRect(0, 0, 32, 32);
  // Subtle aura
  pCtx.fillStyle = "#221d36";
  pCtx.fillRect(2, 2, 28, 28);
  drawPixelChar(pCtx, id, 16, 23, 1.5, false, tick);
  portraitName.textContent = s.label;
}

// ── Scene Renderers ──────────────────────────────────────────
function renderScene() {
  tick++;
  ctx.clearRect(0, 0, worldCanvas.width, worldCanvas.height);

  const act = gameState ? gameState.current_act : "prologue";

  if (act === "prologue") {
    renderPrologue();
  } else if (act === "act0") {
    renderAct0Carriage();
  } else if (act === "act1") {
    renderAct1Steps();
  } else if (act === "act2") {
    renderAct2Manor();
  } else if (act === "act3" || act.startsWith("ending_")) {
    renderAct3Toast();
  }

  drawPortrait(activeNpc);
  requestAnimationFrame(renderScene);
}

function renderPrologue() {
  ctx.fillStyle = "#08060f";
  ctx.fillRect(0, 0, 480, 270);
  // Magenta Sight aura
  const pulse = 0.25 + 0.15 * Math.sin(tick * 0.05);
  ctx.fillStyle = `rgba(217, 102, 255, ${pulse})`;
  ctx.fillRect(160, 45, 160, 160);
  // Pixel Wine Goblet
  ctx.fillStyle = "#d9d2e6";
  ctx.fillRect(228, 95, 24, 24);
  ctx.fillStyle = "#9e1934";
  ctx.fillRect(231, 102, 18, 14);
  ctx.fillStyle = "#d9d2e6";
  ctx.fillRect(238, 119, 4, 24);
  ctx.fillRect(226, 143, 28, 4);
  // Flickering candle
  const flicker = Math.floor(tick / 8) % 2;
  ctx.fillStyle = "#f5d76e";
  ctx.fillRect(130, 120 - flicker, 4, 6);
  ctx.fillStyle = "#e8e0d5";
  ctx.fillRect(129, 126, 6, 22);
}

function renderAct0Carriage() {
  // Night sky & stars
  ctx.fillStyle = "#0b1021";
  ctx.fillRect(0, 0, 480, 175);
  ctx.fillStyle = "#e6e2c8";
  for (let i = 0; i < 18; i++) {
    ctx.fillRect((i * 73) % 470, (i * 29) % 110, 2, 2);
  }
  // Parallax forest trees
  ctx.fillStyle = "#111c1a";
  const offset = (tick * 1.2) % 60;
  for (let x = -60; x < 540; x += 48) {
    const tx = x - offset;
    ctx.fillRect(tx, 105, 14, 70);
    ctx.fillRect(tx - 10, 80, 34, 35);
  }
  // Road
  ctx.fillStyle = "#26211e";
  ctx.fillRect(0, 175, 480, 95);
  // Swaying Carriage
  const sway = Math.round(Math.sin(tick * 0.12));
  ctx.fillStyle = "#3a2520";
  ctx.fillRect(150, 115 + sway, 150, 62);
  ctx.fillStyle = "#e6c15a";
  ctx.fillRect(175, 128 + sway, 32, 24); // window
  ctx.fillStyle = "#f2b84b";
  ctx.fillRect(298, 130 + sway, 6, 6); // lantern
  // Wheels
  ctx.fillStyle = "#1a1412";
  ctx.fillRect(165, 168, 22, 22);
  ctx.fillRect(265, 168, 22, 22);
  // Aldous on driver box
  drawPixelChar(ctx, "aldous", 312, 128 + sway, 1.4, false, tick, true);
}

function renderAct1Steps() {
  ctx.fillStyle = "#0c0b17";
  ctx.fillRect(0, 0, 480, 270);
  // Manor facade
  ctx.fillStyle = "#252233";
  ctx.fillRect(80, 30, 320, 160);
  // Glowing windows
  ctx.fillStyle = "#f5c45b";
  for (let wx = 105; wx <= 345; wx += 60) {
    ctx.fillRect(wx, 55, 28, 38);
  }
  // Grand doorway & steps
  ctx.fillStyle = "#14101c";
  ctx.fillRect(212, 115, 56, 75);
  ctx.fillStyle = "#484259";
  ctx.fillRect(180, 190, 120, 14);
  ctx.fillRect(160, 204, 160, 14);
  ctx.fillRect(0, 218, 480, 52);
  // Reynard & Viscount
  drawPixelChar(ctx, "reynard", 262, 185, 1.5, false, tick, true);
  drawPixelChar(ctx, "viscount", 210, 206, 1.5, false, tick, false);
}

function renderAct2Manor() {
  const scene = gameState ? gameState.current_scene : "party_floor";

  if (scene === "kitchen") {
    ctx.fillStyle = "#241914";
    ctx.fillRect(0, 0, 480, 270);
    // Tile floor
    for (let y = 50; y < 250; y += 20) {
      for (let x = 40; x < 440; x += 20) {
        ctx.fillStyle = ((x + y) / 20) % 2 === 0 ? "#382a23" : "#2e221c";
        ctx.fillRect(x, y, 20, 20);
      }
    }
    // Hearth fire
    ctx.fillStyle = "#ff7b29";
    ctx.fillRect(225, 34 - (Math.floor(tick / 6) % 2), 30, 16);
    // Cellar stairs
    ctx.fillStyle = "#120e0d";
    ctx.fillRect(360, 60, 56, 36);
    ctx.fillStyle = "#d9c8b4";
    ctx.font = "8px monospace";
    ctx.fillText("CELLAR", 370, 55);
  } else if (scene === "balcony") {
    ctx.fillStyle = "#080b18";
    ctx.fillRect(0, 0, 480, 160);
    ctx.fillStyle = "#16241c";
    ctx.fillRect(0, 160, 480, 110);
    // Stone balustrade
    ctx.fillStyle = "#4d4a5c";
    ctx.fillRect(40, 145, 400, 16);
    if (gameState.flags && gameState.flags.balcony_vision_seen) {
      const p = 0.2 + 0.1 * Math.sin(tick * 0.08);
      ctx.fillStyle = `rgba(217, 102, 255, ${p})`;
      ctx.fillRect(40, 20, 400, 120);
    }
  } else {
    // Ballroom floor
    ctx.fillStyle = "#120f1c";
    ctx.fillRect(0, 0, 480, 270);
    for (let y = 40; y < 250; y += 24) {
      for (let x = 32; x < 448; x += 24) {
        ctx.fillStyle = ((x + y) / 24) % 2 === 0 ? "#241e33" : "#1c1729";
        ctx.fillRect(x, y, 24, 24);
      }
    }
    // Dais & Treaty Table
    ctx.fillStyle = "#521a28";
    ctx.fillRect(190, 42, 100, 34);
    ctx.fillStyle = "#e6c15a";
    ctx.fillRect(210, 52, 60, 14);
    // Side Tables
    ctx.fillStyle = "#36253b";
    ctx.fillRect(95, 92, 70, 20);  // Vantrell
    ctx.fillRect(55, 190, 60, 20); // Marrow
    ctx.fillRect(365, 170, 62, 20);// Delegation
    // Flickering Candelabras
    const fl = Math.floor(tick / 7) % 2;
    for (const [cx, cy] of [[150, 42], [330, 42], [45, 130], [435, 130]]) {
      ctx.fillStyle = "rgba(255, 195, 77, 0.18)";
      ctx.fillRect(cx - 10, cy - 10, 20, 20);
      ctx.fillStyle = "#ffd166";
      ctx.fillRect(cx - 1, cy - 4 - fl, 3, 5);
    }
  }

  // Update & draw player + NPCs
  updatePlayerMovement();
  const npcs = getAct2NPCs();
  let nearest = null;
  let nearestDist = 999;

  for (const n of npcs) {
    const facingLeft = player.x < n.x;
    drawPixelChar(ctx, n.id, n.x, n.y, 1.35, false, tick, facingLeft);
    const d = Math.hypot(player.x - n.x, player.y - n.y);
    if (d < nearestDist) {
      nearestDist = d;
      nearest = n;
    }
    if (d < 34) {
      ctx.fillStyle = "#e6c15a";
      ctx.font = "9px monospace";
      ctx.fillText(CHAR_STYLE[n.id].label, n.x - 22, n.y - 24);
    }
  }

  if (nearest && nearestDist < 34 && nearest.id !== activeNpc) {
    selectNpc(nearest.id);
  }

  drawPixelChar(ctx, "viscount", player.x, player.y, 1.35, player.moving, tick, player.dir === 2);
}

function renderAct3Toast() {
  ctx.fillStyle = "#100c18";
  ctx.fillRect(0, 0, 480, 270);
  // Dais & ceremonial decanter
  ctx.fillStyle = "#591828";
  ctx.fillRect(140, 85, 200, 50);
  ctx.fillStyle = "#b81d38";
  ctx.fillRect(236, 98, 8, 12); // poisoned decanter
  drawPixelChar(ctx, "duke", 240, 82, 1.5, false, tick, false);
  drawPixelChar(ctx, "isolde", 190, 95, 1.4, false, tick, false);
  drawPixelChar(ctx, "reynard", 295, 95, 1.4, false, tick, true);
  drawPixelChar(ctx, "cassian", 120, 155, 1.4, false, tick, false);
  drawPixelChar(ctx, "ophelia", 360, 155, 1.4, false, tick, true);
  drawPixelChar(ctx, "viscount", 240, 195, 1.5, false, tick, false);
}

function updatePlayerMovement() {
  let dx = 0, dy = 0;
  if (keys["w"] || keys["arrowup"])    { dy -= player.speed; player.dir = 1; }
  if (keys["s"] || keys["arrowdown"])  { dy += player.speed; player.dir = 0; }
  if (keys["a"] || keys["arrowleft"])  { dx -= player.speed; player.dir = 2; }
  if (keys["d"] || keys["arrowright"]) { dx += player.speed; player.dir = 3; }

  if (dx !== 0 || dy !== 0) {
    player.targetX = null;
    player.targetY = null;
    player.x = Math.max(36, Math.min(444, player.x + dx));
    player.y = Math.max(55, Math.min(245, player.y + dy));
    player.moving = true;
  } else if (player.targetX !== null) {
    const tx = player.targetX - player.x;
    const ty = player.targetY - player.y;
    const dist = Math.hypot(tx, ty);
    if (dist < 2.5) {
      player.targetX = null;
      player.targetY = null;
      player.moving = false;
    } else {
      player.x += (tx / dist) * player.speed;
      player.y += (ty / dist) * player.speed;
      player.dir = tx < 0 ? 2 : 3;
      player.moving = true;
    }
  } else {
    player.moving = false;
  }
}

// ── UI & API Helpers ─────────────────────────────────────────
function appendMsg(cls, html) {
  const div = document.createElement("div");
  div.className = `msg ${cls}`;
  div.innerHTML = html;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function renderEvents(events) {
  for (const ev of events || []) {
    if (ev.type === "npc") {
      appendMsg("npc", `<strong>${ev.speaker}:</strong> ${ev.text}`);
    } else {
      appendMsg(ev.type || "system", ev.text);
    }
  }
}

function selectNpc(id) {
  activeNpc = id;
  drawPortrait(id);
}

function syncHUD() {
  if (!gameState) return;
  document.getElementById("hudAct").textContent = gameState.current_act.toUpperCase();
  document.getElementById("hudTime").textContent = gameState.time_str;
  document.getElementById("hudEvidence").textContent = gameState.evidence_log.length;

  // Quick actions per act
  quickActions.innerHTML = "";
  stationBar.innerHTML = "";
  const act = gameState.current_act;

  if (act === "prologue") {
    controlsHint.textContent = "Prologue Vision — Click 'Wake & Board Carriage' to begin";
    addQuickBtn("Wake & Board Carriage →", async () => {
      const data = await post("/api/advance_prologue", { session_id: sessionId });
      applyResponse(data);
      selectNpc("aldous");
    }, "primary");
  } else if (act === "act0") {
    controlsHint.textContent = "Act 0: Speak freely with Aldous, or arrive at the estate";
    selectNpc("aldous");
    addQuickBtn("Arrive at Estate →", async () => {
      const data = await post("/api/finish_act0", { session_id: sessionId });
      applyResponse(data);
      selectNpc("reynard");
    }, "primary");
  } else if (act === "act1") {
    controlsHint.textContent = "Act 1: Speak freely with Reynard on the steps, or step inside";
    selectNpc("reynard");
    addQuickBtn("Enter the Main Hall →", async () => {
      const data = await post("/api/enter_hall", { session_id: sessionId });
      applyResponse(data);
      selectNpc("fenwick");
    }, "primary");
  } else if (act === "act2") {
    controlsHint.textContent = "WASD / Arrows or Click to walk · Approach any character to talk";
    const stations = [
      ["party_floor", "Main Hall"],
      ["kitchen", "Kitchen & Cellar"],
      ["balcony", "The Balcony"],
    ];
    for (const [sid, label] of stations) {
      const b = document.createElement("button");
      b.textContent = label;
      b.onclick = async () => {
        if (sid === "party_floor") {
          gameState.current_scene = "party_floor";
          syncHUD();
          return;
        }
        const data = await post("/api/visit_station", { session_id: sessionId, target: sid });
        applyResponse(data);
        if (sid === "kitchen") selectNpc("mrs_alwen");
      };
      stationBar.appendChild(b);
    }
    if (gameState.current_scene === "kitchen") {
      addQuickBtn("🔍 Inspect Wine Seal & Cellar Log", async () => {
        const data = await post("/api/inspect_cellar", { session_id: sessionId, target: "BOTH" });
        applyResponse(data);
      }, "primary");
    }
    addQuickBtn("🍷 Head to the Toast (Act 3)", async () => {
      const data = await post("/api/start_act3", { session_id: sessionId });
      applyResponse(data);
      selectNpc("duke");
    }, "danger");
  } else if (act === "act3") {
    controlsHint.textContent = "ACT 3 CLIMAX — Type your accusation, evidence, or physical action!";
  } else if (act.startsWith("ending_")) {
    controlsHint.textContent = `THE END — ${act.toUpperCase()}`;
  }
}

function addQuickBtn(label, onClick, cls = "") {
  const b = document.createElement("button");
  b.type = "button";
  if (cls) b.className = cls;
  b.textContent = label;
  b.onclick = onClick;
  quickActions.appendChild(b);
}

async function post(url, body) {
  busy = true;
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return await r.json();
  } finally {
    busy = false;
  }
}

function applyResponse(data) {
  if (data.state) gameState = data.state;
  renderEvents(data.events);
  syncHUD();
}

talkForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (busy || !gameState) return;
  const msg = playerInput.value.trim();
  if (!msg && gameState.current_act !== "act3") return;
  playerInput.value = "";
  if (msg) appendMsg("player", `<strong>You:</strong> ${msg}`);

  if (gameState.current_act === "act3") {
    const data = await post("/api/act3_action", { session_id: sessionId, npc_id: "duke", message: msg });
    applyResponse(data);
  } else {
    const data = await post("/api/talk", { session_id: sessionId, npc_id: activeNpc, message: msg });
    if (data.reply) {
      const label = (CHAR_STYLE[activeNpc] || { label: activeNpc }).label;
      appendMsg("npc", `<strong>${label}:</strong> ${data.reply}`);
    }
    applyResponse(data);
  }
});

// Evidence modal
document.getElementById("btnLog").onclick = () => {
  const list = document.getElementById("evidenceList");
  list.innerHTML = "";
  const evs = (gameState && gameState.evidence_log) || [];
  if (!evs.length) {
    list.innerHTML = `<div class="msg system">Nothing recorded yet.</div>`;
  } else {
    evs.forEach((item, i) => {
      const d = document.createElement("div");
      d.className = "ev-item";
      d.textContent = `${i + 1}. ${item}`;
      list.appendChild(d);
    });
  }
  document.getElementById("evidenceModal").classList.add("open");
};
document.getElementById("btnCloseModal").onclick = () => {
  document.getElementById("evidenceModal").classList.remove("open");
};

document.getElementById("btnNew").onclick = startNewGame;

async function startNewGame() {
  chatLog.innerHTML = "";
  const data = await post("/api/new_game", {});
  sessionId = data.session_id;
  gameState = data.state;
  appendMsg("vision", "A hall full of candlelight and laughter. A glass of deep red wine. A gloved hand. The sound of something shattering.");
  appendMsg("narration", "You wake before dawn. Tonight, Grand Duke Aldric signs the peace treaty. Someone in that hall is going to die.");
  selectNpc("viscount");
  syncHUD();
}

startNewGame();
requestAnimationFrame(renderScene);
