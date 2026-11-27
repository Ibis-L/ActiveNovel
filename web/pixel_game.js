// ─────────────────────────────────────────────────────────────
//  web/pixel_game.js — High-Detail 2D Pixel Art & Animation Engine
//  Anatomical pixel characters, detailed bust portraits,
//  Landau coach + galloping horses, Gothic castle keep,
//  and atmospheric Yes, Your Grace-style manor lighting.
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
let groupTimer = null;
let groupQueue = [];
let prologueStep = 0;
const btnInterrupt = document.getElementById("btnInterrupt");

const PROLOGUE_BEATS = [
  { type: "vision", text: "Black. Silence. Then — fragments. Like looking through broken glass at candlelight.", btn: "Continue..." },
  { type: "vision", text: "A hall full of people. Laughter. Music. A glass of deep red wine, held up in toast.", btn: "Continue..." },
  { type: "vision", text: "A hand — gloved in black — passing behind a table. Too quick. Too careful.", btn: "Continue..." },
  { type: "vision", text: "A woman's face. Half-turned. Smiling at someone you cannot see. The glass rising to her lips.", btn: "Continue..." },
  { type: "vision", text: "And then — Nothing. Just the sound of something shattering. And her gasp.", btn: "Wake Up..." },
  { type: "narration", text: "You wake with a jolt — inside the swaying carriage. Dusk trees blur past the glass. Your grandmother called it the Sight: never clear, never wrong. Tonight Grand Duke Aldric signs the peace treaty... and someone in that room is going to die.", btn: "Knock on Roof Panel →" },
];

function cancelGroupQueue(showNote = false) {
  if (groupTimer) { clearTimeout(groupTimer); groupTimer = null; }
  const hadQueued = groupQueue.length > 0;
  groupQueue = [];
  btnInterrupt.style.display = "none";
  if (showNote && hadQueued) {
    appendMsg("system", "✋ You cut into the conversation.");
    playerInput.focus();
  }
}
btnInterrupt.addEventListener("click", () => cancelGroupQueue(true));

// ── Player Avatar ────────────────────────────────────────────
const player = { x: 240, y: 212, targetX: null, targetY: null, speed: 1.45, dir: 0, moving: false };
const keys = {};
window.addEventListener("keydown", (e) => { if (document.activeElement !== playerInput) keys[e.key.toLowerCase()] = true; });
window.addEventListener("keyup", (e) => { keys[e.key.toLowerCase()] = false; });

let cam = { x: 0, y: 0 };

worldCanvas.addEventListener("click", (e) => {
  if (!gameState || gameState.current_act !== "act2") return;
  const rect = worldCanvas.getBoundingClientRect();
  const sx = ((e.clientX - rect.left) / rect.width) * worldCanvas.width;
  const sy = ((e.clientY - rect.top) / rect.height) * worldCanvas.height;
  const wx = sx + (gameState.current_scene === "party_floor" ? cam.x : 0);
  const wy = sy + (gameState.current_scene === "party_floor" ? cam.y : 0);
  player.targetX = wx;
  player.targetY = wy;
  for (const n of getAct2NPCs()) {
    if (Math.hypot(wx - n.x, wy - n.y) < 30) { selectNpc(n.id); break; }
  }
});

// ── Character Palettes ───────────────────────────────────────
const CHAR_STYLE = {
  viscount:  { hair: "#3b2621", hairHi: "#593b33", skin: "#f0c4a0", skinSh: "#cfa07c", coat: "#243b61", shade: "#15233b", trim: "#e6c15a", cravat: "#f0ebe1", type: "cloak",  label: "Viscount" },
  aldous:    { hair: "#a6a098", hairHi: "#ccc6be", skin: "#dfb08c", skinSh: "#bd8d6a", coat: "#523d2e", shade: "#36271d", trim: "#8c7156", cravat: "#bfb5a6", type: "hat",    label: "Aldous" },
  reynard:   { hair: "#d8dde6", hairHi: "#ffffff", skin: "#e8c5ab", skinSh: "#c49f85", coat: "#1a1a24", shade: "#0d0d14", trim: "#cfd6e3", cravat: "#f5f5f5", type: "butler", label: "Reynard" },
  fenwick:   { hair: "#b58654", hairHi: "#d4a674", skin: "#f0c5a8", skinSh: "#cc9d80", coat: "#5e2849", shade: "#3d182f", trim: "#e6c15a", cravat: "#f2e8dc", type: "noble",  label: "Lord Fenwick" },
  brienne:   { hair: "#261c20", hairHi: "#45343b", skin: "#ecd0be", skinSh: "#c7a793", coat: "#17151c", shade: "#0b0a0e", trim: "#736d82", cravat: "#2a2633", type: "gown",   label: "Lady Brienne" },
  cassian:   { hair: "#5c3b28", hairHi: "#82563d", skin: "#edc19f", skinSh: "#c79a79", coat: "#851e2d", shade: "#57121c", trim: "#e6c15a", cravat: "#f5ebd6", type: "cloak",  label: "Lord Cassian" },
  ophelia:   { hair: "#241620", hairHi: "#472c3f", skin: "#f2d5c4", skinSh: "#cca995", coat: "#471b45", shade: "#2b0f2a", trim: "#e63956", cravat: "#d9b8cc", type: "gown",   label: "Lady Ophelia" },
  isolde:    { hair: "#d4a659", hairHi: "#f2cf88", skin: "#f5d6c3", skinSh: "#d1ae99", coat: "#ded4c3", shade: "#b3a794", trim: "#e6c15a", cravat: "#fff8eb", type: "gown",   label: "Lady Isolde" },
  duke:      { hair: "#c5cad4", hairHi: "#ebeef5", skin: "#e6bc9c", skinSh: "#bf9575", coat: "#1b2e4f", shade: "#101c33", trim: "#e6c15a", cravat: "#f0ebe1", type: "king",   label: "Duke Aldric" },
  demir:     { hair: "#241f1c", hairHi: "#473f3a", skin: "#d6a47e", skinSh: "#b0805d", coat: "#244f46", shade: "#15302b", trim: "#d9b45b", cravat: "#d9c698", type: "robe",   label: "Counselor Demir" },
  kavir:     { hair: "#474340", hairHi: "#6e6965", skin: "#cf9974", skinSh: "#ab7855", coat: "#4f2c24", shade: "#331b16", trim: "#a8a29e", cravat: "#6e5a4f", type: "armor",  label: "General Kavir" },
  mrs_alwen: { hair: "#8a7b73", hairHi: "#b3a39b", skin: "#ecc1a3", skinSh: "#c79c7f", coat: "#785342", shade: "#52372b", trim: "#f0ebe4", type: "cook",   label: "Mrs Alwen" },
};

// ── Ambient Crowd, Musicians, Guards & Dancers (960x540 Grand Hall) ──
const AMBIENT_GUESTS = [
  // String Quartet in Northeast Musicians' Alcove
  { x: 658, y: 82,  coat: "#3b2333", hair: "#4a3326", role: "musician", phase: 0 },
  { x: 678, y: 76,  coat: "#3b2333", hair: "#b89f78", role: "musician", phase: 12 },
  { x: 698, y: 84,  coat: "#3b2333", hair: "#2b201b", role: "musician", phase: 24 },
  { x: 716, y: 78,  coat: "#3b2333", hair: "#7a5b3e", role: "musician", phase: 36 },
  // Royal Dais Guards
  { x: 356, y: 92,  coat: "#454a59", hair: "#2e2e33", role: "guard", phase: 0, facingLeft: false },
  { x: 604, y: 92,  coat: "#454a59", hair: "#2e2e33", role: "guard", phase: 0, facingLeft: true },
  { x: 432, y: 492, coat: "#454a59", hair: "#2e2e33", role: "guard", phase: 0, facingLeft: false },
  { x: 528, y: 492, coat: "#454a59", hair: "#2e2e33", role: "guard", phase: 0, facingLeft: true },
  // Guests seated/standing around tables & perimeter
  { x: 138, y: 256, coat: "#2c4740", hair: "#6b4730", role: "guest", phase: 5,  facingLeft: false },
  { x: 246, y: 256, coat: "#5c2b3d", hair: "#d4b06a", role: "guest", phase: 19, facingLeft: true,  gown: true },
  { x: 712, y: 256, coat: "#343b59", hair: "#292321", role: "guest", phase: 31, facingLeft: false },
  { x: 820, y: 256, coat: "#4d354f", hair: "#8f6948", role: "guest", phase: 8,  facingLeft: true,  gown: true },
  { x: 146, y: 440, coat: "#294052", hair: "#362a24", role: "guest", phase: 22, facingLeft: false },
  { x: 240, y: 440, coat: "#5e3d28", hair: "#c4b9ab", role: "guest", phase: 14, facingLeft: true },
  // Fireplace & East Lounge Guests
  { x: 745, y: 392, coat: "#3b4d2b", hair: "#422b20", role: "guest", phase: 29, facingLeft: false, gown: true },
  { x: 765, y: 395, coat: "#4f2738", hair: "#211b1e", role: "guest", phase: 3,  facingLeft: true },
  { x: 820, y: 332, coat: "#2b3854", hair: "#9e7c52", role: "guest", phase: 17, facingLeft: false },
  { x: 838, y: 336, coat: "#40314a", hair: "#5c4132", role: "guest", phase: 11, facingLeft: true,  gown: true },
  // West Gallery Art Admirers
  { x: 82,  y: 122, coat: "#2b4a3e", hair: "#b59d7a", role: "guest", phase: 25, facingLeft: false },
  { x: 102, y: 124, coat: "#522b2b", hair: "#332620", role: "guest", phase: 7,  facingLeft: true,  gown: true },
];

const DANCING_COUPLES = [
  { cx: 432, cy: 258, rx: 18, ry: 10, speed: 0.012, offset: 0.0, coat1: "#2d4563", coat2: "#7d2846" },
  { cx: 528, cy: 266, rx: 18, ry: 10, speed: 0.011, offset: 2.1, coat1: "#3d2d59", coat2: "#2c6154" },
  { cx: 480, cy: 326, rx: 20, ry: 11, speed: 0.013, offset: 4.2, coat1: "#5e3a24", coat2: "#6b4c7a" },
];

const PATROL_SERVANTS = [
  { x1: 290, y1: 166, x2: 670, y2: 166, speed: 0.45, offset: 0 },
  { x1: 295, y1: 374, x2: 665, y2: 374, speed: 0.38, offset: 120 },
  { x1: 650, y1: 166, x2: 650, y2: 374, speed: 0.36, offset: 60 },
  { x1: 305, y1: 166, x2: 305, y2: 374, speed: 0.34, offset: 90 },
  { x1: 120, y1: 315, x2: 320, y2: 315, speed: 0.32, offset: 40 },
];

const DUST = Array.from({ length: 48 }, (_, i) => ({ x: (i * 73) % 920 + 20, y: (i * 41) % 500 + 20, s: (i % 3) * 0.14 + 0.12 }));

function getAct2NPCs() {
  if (!gameState) return [];
  const scene = gameState.current_scene;
  const unlocked = new Set(gameState.unlocked_stations || []);
  if (scene === "kitchen") return [{ id: "mrs_alwen", x: 240, y: 128 }];
  if (scene === "balcony") return [];
  const list = [
    { id: "fenwick", x: 480, y: 425 },
    { id: "reynard", x: 544, y: 92 },
    { id: "isolde",  x: 434, y: 88 },
    { id: "duke",    x: 480, y: 86 },
  ];
  if (unlocked.has("marrow"))     list.push({ id: "brienne", x: 194, y: 383 });
  if (unlocked.has("vantrell")) { list.push({ id: "cassian", x: 162, y: 198 }, { id: "ophelia", x: 224, y: 198 }); }
  if (unlocked.has("delegation")) { list.push({ id: "demir", x: 734, y: 198 }, { id: "kavir", x: 796, y: 198 }); }
  return list;
}

// ── Anatomical Pixel Human Sprite Renderer ───────────────────
function drawDetailedSprite(c, s, x, y, scale = 1, isMoving = false, frame = 0, facingLeft = false, prop = null) {
  const walkCycle = isMoving ? Math.floor(frame / 5) % 4 : 0;
  const bob = isMoving ? (walkCycle % 2 === 1 ? -1 : 0) : (Math.floor(frame / 32) % 2 === 0 ? 0 : -1);
  const legL = walkCycle === 1 ? -2 : (walkCycle === 3 ? 1 : 0);
  const legR = walkCycle === 3 ? -2 : (walkCycle === 1 ? 1 : 0);
  const armSwing = isMoving ? (walkCycle === 1 ? 1 : (walkCycle === 3 ? -1 : 0)) : 0;
  const blink = (frame % 180) > 174;

  c.save();
  c.translate(Math.round(x), Math.round(y));
  c.scale(facingLeft ? -scale : scale, scale);

  // Oval ground shadow
  c.fillStyle = "rgba(0,0,0,0.48)";
  c.fillRect(-5, 6, 10, 2);
  c.fillRect(-3, 8, 6, 1);

  // Legs / Boots or Flowing Gown
  if (s.type === "gown") {
    // Tapered waist + flowing shaded skirt hem
    c.fillStyle = s.shade;
    c.fillRect(-5, -1 + bob, 10, 7);
    c.fillRect(-6, 4 + bob, 12, 3);
    c.fillStyle = s.coat;
    c.fillRect(-4, -2 + bob, 8, 7);
    c.fillStyle = s.trim;
    c.fillRect(-1, -1 + bob, 2, 7);
  } else {
    // Trousers + cuffed boots
    c.fillStyle = "#1d1a24";
    c.fillRect(-3, 1 + legL, 2, 4);
    c.fillRect(1,  1 + legR, 2, 4);
    c.fillStyle = "#110e14";
    c.fillRect(-3, 5 + legL, 3, 2);
    c.fillRect(1,  5 + legR, 3, 2);
  }

  // Back cloak / mantle
  if (s.type === "cloak" || s.type === "king") {
    c.fillStyle = s.shade;
    c.fillRect(-6, -8 + bob, 12, 11);
    c.fillRect(-5, 2 + bob, 10, 3);
  }

  // Tapered Torso (rounded shoulders, narrower waist)
  c.fillStyle = s.coat;
  c.fillRect(-4, -9 + bob, 8, 8);
  c.fillRect(-5, -8 + bob, 10, 4); // shoulders
  c.fillStyle = s.shade;
  c.fillRect(-4, -3 + bob, 8, 2);  // waist shadow

  // Cravat / Collar / Belt / Trim
  c.fillStyle = s.cravat || s.trim;
  c.fillRect(-1, -9 + bob, 2, 4);
  c.fillStyle = s.trim;
  c.fillRect(-4, -2 + bob, 8, 1);  // belt
  if (s.type === "butler" || s.type === "noble") {
    c.fillRect(-2, -9 + bob, 1, 5); // lapels
    c.fillRect(1,  -9 + bob, 1, 5);
  }
  if (s.type === "cook") {
    c.fillStyle = "#ebe6df";
    c.fillRect(-3, -2 + bob, 6, 7); // white apron
  }

  // Articulated Arms & Hands
  c.fillStyle = s.shade;
  c.fillRect(-6, -8 + bob + armSwing, 2, 5);
  c.fillStyle = s.coat;
  c.fillRect(4,  -8 + bob - armSwing, 2, 5);
  c.fillStyle = s.skin;
  c.fillRect(-6, -3 + bob + armSwing, 2, 2);
  c.fillRect(4,  -3 + bob - armSwing, 2, 2);

  // Neck
  c.fillStyle = s.skinSh;
  c.fillRect(-1, -11 + bob, 2, 2);

  // Rounded Anatomical Head (crown, cheekbones, chin)
  c.fillStyle = s.skin;
  c.fillRect(-3, -17 + bob, 6, 6);
  c.fillRect(-4, -16 + bob, 8, 4);
  c.fillStyle = s.skinSh;
  c.fillRect(-2, -11 + bob, 4, 1); // chin contour
  c.fillRect(-4, -13 + bob, 1, 2); // cheek shadow

  // Expressive Eyes (with whites & blinking)
  if (!blink) {
    c.fillStyle = "#ffffff";
    c.fillRect(-2, -14 + bob, 1, 1);
    c.fillRect(2,  -14 + bob, 1, 1);
    c.fillStyle = "#191521";
    c.fillRect(-1, -14 + bob, 1, 1);
    c.fillRect(1,  -14 + bob, 1, 1);
  } else {
    c.fillStyle = s.skinSh;
    c.fillRect(-2, -14 + bob, 2, 1);
    c.fillRect(1,  -14 + bob, 2, 1);
  }

  // Layered Hair with Highlight
  c.fillStyle = s.hair;
  c.fillRect(-4, -18 + bob, 8, 2);
  c.fillRect(-3, -19 + bob, 6, 1);
  c.fillRect(-4, -17 + bob, 1, 4);
  c.fillRect(3,  -17 + bob, 1, 3);
  if (s.hairHi) {
    c.fillStyle = s.hairHi;
    c.fillRect(-2, -18 + bob, 4, 1);
  }
  if (s.type === "gown") {
    c.fillStyle = s.hair;
    c.fillRect(-4, -14 + bob, 1, 5); // long locks
  }

  // Headwear (Coachman Hat / Duke Circlet / Cook Mobcap)
  if (s.type === "hat") {
    c.fillStyle = "#241b15";
    c.fillRect(-6, -18 + bob, 12, 2);
    c.fillRect(-4, -21 + bob, 8, 3);
    c.fillStyle = s.trim;
    c.fillRect(-4, -19 + bob, 8, 1);
  } else if (s.type === "king") {
    c.fillStyle = "#e6c15a";
    c.fillRect(-4, -19 + bob, 8, 2);
    c.fillRect(-3, -20 + bob, 1, 1);
    c.fillRect(0,  -20 + bob, 1, 1);
    c.fillRect(3,  -20 + bob, 1, 1);
  } else if (s.type === "cook") {
    c.fillStyle = "#f2ede4";
    c.fillRect(-4, -20 + bob, 8, 3);
    c.fillRect(-3, -21 + bob, 6, 1);
  }

  // Props
  if (prop === "tray") {
    c.fillStyle = "#cfd6e3"; c.fillRect(4, -3 + bob, 7, 2);
    c.fillStyle = "#9e1934"; c.fillRect(6, -6 + bob, 2, 3);
  } else if (prop === "violin") {
    c.fillStyle = "#8a4b25"; c.fillRect(3, -8 + bob, 4, 5);
    c.fillStyle = "#e6d8c5"; c.fillRect(2, -6 + bob + (Math.floor(frame / 7) % 2), 7, 1);
  } else if (prop === "halberd") {
    c.fillStyle = "#5c4330"; c.fillRect(6, -18, 1, 25);
    c.fillStyle = "#c2cbd6"; c.fillRect(5, -22, 3, 5);
  } else if (s.label === "Lady Ophelia") {
    c.fillStyle = "#ff2e55"; c.fillRect(4, -2 + bob, 2, 2); // ruby ring glint
  } else if (s.label === "Lord Fenwick") {
    c.fillStyle = "#a3223a"; c.fillRect(5, -4 + bob, 2, 3);
  }
  c.restore();
}

// ── Detailed 48×48 Bust Portrait Renderer ────────────────────
function drawPortrait(id) {
  const s = CHAR_STYLE[id] || CHAR_STYLE.viscount;
  const bob = Math.floor(tick / 36) % 2 === 0 ? 0 : 1;
  const blink = (tick % 190) > 184;

  pCtx.clearRect(0, 0, 48, 48);
  // Framed vignette backdrop
  pCtx.fillStyle = "#0e0c18";
  pCtx.fillRect(0, 0, 48, 48);
  pCtx.fillStyle = "#191529";
  pCtx.fillRect(3, 3, 42, 42);

  // Shoulders & Coat
  pCtx.fillStyle = s.shade;
  pCtx.fillRect(8, 34 + bob, 32, 14);
  pCtx.fillStyle = s.coat;
  pCtx.fillRect(11, 32 + bob, 26, 16);
  // Cravat / Brooch / Collar
  pCtx.fillStyle = s.cravat || s.trim;
  pCtx.fillRect(21, 32 + bob, 6, 10);
  pCtx.fillStyle = s.trim;
  pCtx.fillRect(22, 35 + bob, 4, 3);

  // Neck & Head
  pCtx.fillStyle = s.skinSh;
  pCtx.fillRect(21, 28 + bob, 6, 5);
  pCtx.fillStyle = s.skin;
  pCtx.fillRect(16, 13 + bob, 16, 15);
  pCtx.fillRect(15, 16 + bob, 18, 9);
  pCtx.fillStyle = s.skinSh;
  pCtx.fillRect(18, 27 + bob, 12, 2); // jawline
  pCtx.fillRect(23, 20 + bob, 2, 3);  // nose shadow
  pCtx.fillRect(21, 25 + bob, 6, 1);  // mouth

  // Eyes & Brows
  pCtx.fillStyle = s.hair;
  pCtx.fillRect(18, 17 + bob, 4, 1);
  pCtx.fillRect(26, 17 + bob, 4, 1);
  if (!blink) {
    pCtx.fillStyle = "#ffffff";
    pCtx.fillRect(18, 19 + bob, 4, 2);
    pCtx.fillRect(26, 19 + bob, 4, 2);
    pCtx.fillStyle = "#181421";
    pCtx.fillRect(20, 19 + bob, 2, 2);
    pCtx.fillRect(27, 19 + bob, 2, 2);
  } else {
    pCtx.fillStyle = s.skinSh;
    pCtx.fillRect(18, 20 + bob, 4, 1);
    pCtx.fillRect(26, 20 + bob, 4, 1);
  }

  // Hair & Accessories
  pCtx.fillStyle = s.hair;
  pCtx.fillRect(15, 9 + bob, 18, 5);
  pCtx.fillRect(17, 7 + bob, 14, 2);
  pCtx.fillRect(14, 12 + bob, 3, 10);
  pCtx.fillRect(31, 12 + bob, 3, 10);
  if (s.hairHi) {
    pCtx.fillStyle = s.hairHi;
    pCtx.fillRect(18, 9 + bob, 10, 2);
  }
  if (s.type === "king") {
    pCtx.fillStyle = "#e6c15a";
    pCtx.fillRect(16, 6 + bob, 16, 3);
    pCtx.fillRect(18, 4 + bob, 2, 2);
    pCtx.fillRect(23, 3 + bob, 2, 3);
    pCtx.fillRect(28, 4 + bob, 2, 2);
  } else if (s.type === "hat") {
    pCtx.fillStyle = "#241b15";
    pCtx.fillRect(12, 9 + bob, 24, 3);
    pCtx.fillRect(16, 4 + bob, 16, 5);
  } else if (s.type === "cook") {
    pCtx.fillStyle = "#f2ede4";
    pCtx.fillRect(15, 5 + bob, 18, 5);
  }

  portraitName.textContent = s.label;
}

// ── True Pixel-Art Circle & Ring Helpers ─────────────────────
function drawPixelCircle(c, cx, cy, r, color) {
  c.fillStyle = color;
  const r2 = r * r;
  for (let dy = -r; dy <= r; dy++) {
    for (let dx = -r; dx <= r; dx++) {
      if (dx * dx + dy * dy <= r2) {
        c.fillRect(Math.round(cx + dx), Math.round(cy + dy), 1, 1);
      }
    }
  }
}

function drawPixelRing(c, cx, cy, rOuter, rInner, color) {
  c.fillStyle = color;
  const ro2 = rOuter * rOuter;
  const ri2 = rInner * rInner;
  for (let dy = -rOuter; dy <= rOuter; dy++) {
    for (let dx = -rOuter; dx <= rOuter; dx++) {
      const d2 = dx * dx + dy * dy;
      if (d2 <= ro2 && d2 >= ri2) {
        c.fillRect(Math.round(cx + dx), Math.round(cy + dy), 1, 1);
      }
    }
  }
}

// ── Warm Radial Light Helper ─────────────────────────────────
function drawWarmLight(x, y, radius, alpha = 0.22) {
  const grad = ctx.createRadialGradient(x, y, 2, x, y, radius);
  grad.addColorStop(0, `rgba(255, 205, 105, ${alpha})`);
  grad.addColorStop(0.55, `rgba(255, 135, 45, ${alpha * 0.4})`);
  grad.addColorStop(1, "rgba(0, 0, 0, 0)");
  ctx.fillStyle = grad;
  ctx.fillRect(x - radius, y - radius, radius * 2, radius * 2);
}

// ── Scene Renderers ──────────────────────────────────────────
let execTick = 0;
let execActiveAct = null;
let balconyEdgePush = 0;
let balconyFallTick = 0;

function renderScene() {
  tick++;
  ctx.clearRect(0, 0, worldCanvas.width, worldCanvas.height);

  const act = gameState ? gameState.current_act : "prologue";
  const scene = gameState ? gameState.current_scene : "dream";
  if (act === "ending_balcony") {
    balconyFallTick++;
    renderBalconyFall();
  } else if (act === "ending_d" || act === "ending_f") {
    if (execActiveAct !== act) { execActiveAct = act; execTick = 0; }
    execTick++;
    renderDungeonExecution(act);
  } else {
    execActiveAct = null;
    if (scene === "dungeon") renderDungeonInterrogation();
    else if (act === "prologue") renderPrologue();
    else if (act === "act0") renderAct0Carriage();
    else if (act === "act1") renderAct1Steps();
    else if (act === "act2") renderAct2Manor();
    else renderAct3Toast();
  }

  drawPortrait(activeNpc);
  requestAnimationFrame(renderScene);
}

function renderPrologue() {
  ctx.fillStyle = "#06040a";
  ctx.fillRect(0, 0, 480, 270);

  if (prologueStep === 0) {
    const p = 0.25 + 0.15 * Math.sin(tick * 0.08);
    ctx.fillStyle = `rgba(217, 102, 255, ${p})`;
    ctx.fillRect(180, 85, 120, 100);
    ctx.fillStyle = "#e6dcf5";
    for (const [sx, sy, sw, sh] of [[210, 120, 14, 3], [248, 108, 4, 15], [228, 148, 18, 4], [262, 138, 9, 8]]) {
      ctx.fillRect(sx, sy, sw, sh);
    }
  } else if (prologueStep === 1) {
    drawWarmLight(240, 130, 120, 0.24);
    for (const gx of [115, 165, 315, 365]) {
      drawDetailedSprite(ctx, { hair: "#2b2024", skin: "#9e8894", skinSh: "#7a6671", coat: "#24192e", shade: "#140d1a", trim: "#734f7d", cravat: "#5c4163", type: "noble" }, gx, 168, 1.35, false, tick, gx > 240);
    }
    // Curved wine chalice with specular highlight
    ctx.fillStyle = "#cfc7de";
    ctx.fillRect(226, 94, 28, 18);
    ctx.fillRect(228, 112, 24, 6);
    ctx.fillRect(232, 118, 16, 4);
    ctx.fillStyle = "#8a1129";
    ctx.fillRect(229, 101, 22, 12);
    ctx.fillStyle = "#eb3b5a";
    ctx.fillRect(231, 101, 18, 2);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(230, 96, 2, 10);
    ctx.fillStyle = "#cfc7de";
    ctx.fillRect(238, 122, 4, 24);
    ctx.fillRect(224, 146, 32, 4);
  } else if (prologueStep === 2) {
    drawWarmLight(240, 140, 95, 0.2);
    ctx.fillStyle = "#362127";
    ctx.fillRect(95, 152, 290, 44);
    ctx.fillStyle = "#cfc7de";
    ctx.fillRect(228, 116, 20, 22);
    ctx.fillStyle = "#8a1129";
    ctx.fillRect(231, 122, 14, 12);
    const hx = 175 + Math.round(Math.sin(tick * 0.06) * 28);
    ctx.fillStyle = "#0e0c14";
    ctx.fillRect(hx, 128, 28, 9);
    ctx.fillRect(hx + 24, 124, 10, 5);
    ctx.fillStyle = "#d93654";
    ctx.fillRect(hx + 28, 120 + (tick % 12), 2, 4);
  } else if (prologueStep === 3) {
    const pulse = 0.25 + 0.1 * Math.sin(tick * 0.07);
    ctx.fillStyle = `rgba(217, 102, 255, ${pulse})`;
    ctx.fillRect(150, 40, 180, 180);
    drawDetailedSprite(ctx, CHAR_STYLE.isolde, 240, 150, 2.2, false, tick, false);
    const gy = 104 - Math.round(Math.sin(tick * 0.05) * 4);
    ctx.fillStyle = "#e6e0f0"; ctx.fillRect(258, gy, 10, 12);
    ctx.fillStyle = "#9e1934"; ctx.fillRect(260, gy + 3, 6, 7);
  } else if (prologueStep === 4) {
    const flash = Math.floor(tick / 6) % 2 === 0 ? 0.35 : 0.12;
    ctx.fillStyle = `rgba(235, 160, 255, ${flash})`;
    ctx.fillRect(0, 0, 480, 270);
    ctx.fillStyle = "#ffffff";
    for (let i = 0; i < 18; i++) {
      const sx = 240 + Math.cos(i * 0.8) * (20 + (tick % 20) * 3);
      const sy = 135 + Math.sin(i * 0.8) * (15 + (tick % 20) * 2);
      ctx.fillRect(sx, sy, 4, 4);
    }
  } else {
    // Beat 5: Interior of the swaying carriage
    const sway = Math.round(Math.sin(tick * 0.14));
    ctx.fillStyle = "#17100d";
    ctx.fillRect(0, 0, 480, 270);
    ctx.fillStyle = "#33211b";
    ctx.fillRect(36, 18 + sway, 408, 234);
    ctx.fillStyle = "#241612";
    ctx.fillRect(52, 34 + sway, 376, 202);
    // Window with passing twilight forest
    ctx.fillStyle = "#0a1021";
    ctx.fillRect(140, 48 + sway, 200, 96);
    const off = (tick * 1.8) % 56;
    ctx.fillStyle = "#0d1a16";
    for (let x = 95; x < 395; x += 44) {
      ctx.fillRect(x - off, 85 + sway, 14, 60);
      ctx.fillRect(x - off - 8, 65 + sway, 30, 28);
    }
    ctx.fillStyle = "#4d3026";
    ctx.fillRect(140, 48 + sway, 200, 4);
    ctx.fillRect(239, 48 + sway, 2, 96);
    ctx.fillStyle = "#5e1c28";
    ctx.fillRect(140, 48 + sway, 22, 96);
    ctx.fillRect(318, 48 + sway, 22, 96);
    ctx.fillStyle = "#4a1723";
    ctx.fillRect(72, 174 + sway, 336, 56);
    drawWarmLight(95, 110 + sway, 68, 0.26);
    drawDetailedSprite(ctx, CHAR_STYLE.viscount, 210, 172 + sway, 1.85, false, tick, false);
  }
}

function renderAct0Carriage() {
  // Multi-tone twilight sky + stars + glowing crescent moon
  ctx.fillStyle = "#080c1a";
  ctx.fillRect(0, 0, 480, 186);
  ctx.fillStyle = "#111a33";
  ctx.fillRect(0, 90, 480, 96);
  ctx.fillStyle = "#e6e2c8";
  for (let i = 0; i < 28; i++) ctx.fillRect((i * 73) % 470, (i * 29) % 105, 1, 1);

  // Circular Pixel Moon with soft halo & craters
  drawPixelCircle(ctx, 396, 38, 20, "rgba(235, 235, 215, 0.08)");
  drawPixelCircle(ctx, 396, 38, 14, "rgba(235, 235, 215, 0.14)");
  drawPixelCircle(ctx, 396, 38, 10, "#f2eed8");
  ctx.fillStyle = "#d9d2b6";
  ctx.fillRect(392, 34, 3, 2); ctx.fillRect(399, 41, 2, 2); ctx.fillRect(394, 42, 2, 1);

  // Far castle silhouette with glowing beacon
  ctx.fillStyle = "#0d1324";
  ctx.fillRect(28, 128, 90, 58);
  ctx.fillRect(38, 108, 16, 22);
  ctx.fillRect(88, 112, 14, 18);
  ctx.fillStyle = "#f2be54";
  ctx.fillRect(45, 114, 2, 4);

  // Parallax pine layers
  const off1 = (tick * 0.6) % 64;
  ctx.fillStyle = "#0d161a";
  for (let x = -64; x < 544; x += 48) {
    ctx.fillRect(x - off1, 124, 12, 62);
    ctx.fillRect(x - off1 - 10, 98, 32, 34);
  }
  const off2 = (tick * 1.4) % 56;
  ctx.fillStyle = "#070d10";
  for (let x = -56; x < 540; x += 56) {
    ctx.fillRect(x - off2, 138, 10, 48);
    ctx.fillRect(x - off2 - 12, 116, 34, 28);
  }

  // Cobblestone road
  ctx.fillStyle = "#1d1816";
  ctx.fillRect(0, 186, 480, 84);
  ctx.fillStyle = "#2b2320";
  const rOff = (tick * 2.2) % 32;
  for (let x = -32; x < 512; x += 32) {
    ctx.fillRect(x - rOff, 198, 18, 4);
    ctx.fillRect(x - rOff + 14, 214, 14, 4);
  }

  // Team of 2 Horses (with flowing manes & 4-beat gallop)
  const gall = Math.floor(tick / 6) % 2;
  for (const hx of [302, 326]) {
    ctx.fillStyle = hx === 302 ? "#241814" : "#33221c";
    ctx.fillRect(hx, 152 + gall, 34, 18);
    ctx.fillRect(hx + 28, 136 + gall, 10, 18);
    ctx.fillRect(hx + 32, 134 + gall, 12, 8);
    ctx.fillStyle = "#140d0b";
    ctx.fillRect(hx + 2, 170, 3, 16 - gall * 2);
    ctx.fillRect(hx + 12, 170, 3, 14 + gall * 2);
    ctx.fillRect(hx + 26, 170, 3, 15 + gall * 2);
    ctx.fillRect(hx - 6, 154 + gall, 7, 13);
  }
  ctx.fillStyle = "#7a5e48";
  ctx.fillRect(268, 142, 72, 1);

  // Curved Landau Coach with undercarriage springs & lantern
  const sway = Math.round(Math.sin(tick * 0.14));
  ctx.fillStyle = "#1f120e";
  ctx.fillRect(148, 112 + sway, 120, 6);
  ctx.fillRect(140, 118 + sway, 136, 6);
  ctx.fillStyle = "#422720";
  ctx.fillRect(144, 124 + sway, 128, 50);
  ctx.fillStyle = "#2e1a15";
  ctx.fillRect(152, 168 + sway, 112, 8);
  ctx.fillStyle = "#c9a349";
  ctx.fillRect(144, 124 + sway, 128, 2);
  ctx.fillRect(184, 126 + sway, 48, 46);
  ctx.fillStyle = "#331d18";
  ctx.fillRect(186, 128 + sway, 44, 42);
  ctx.fillStyle = "#e6b85c";
  ctx.fillRect(194, 133 + sway, 28, 20);
  ctx.fillStyle = "#241612";
  ctx.fillRect(207, 133 + sway, 2, 20);
  drawWarmLight(276, 134 + sway, 48, 0.3);
  ctx.fillStyle = "#ffd166";
  ctx.fillRect(274, 131 + sway, 5, 6);

  // True Circular Rotating Spoked Wheels
  for (const wx of [160, 250]) {
    const wy = 177;
    drawPixelCircle(ctx, wx, wy, 13, "#140e0c");
    drawPixelRing(ctx, wx, wy, 12, 9, "#5c3d2e");
    drawPixelRing(ctx, wx, wy, 13, 12, "#8c7156"); // iron rim
    ctx.fillStyle = "#7a5341";
    const phase = Math.floor(tick / 4) % 2;
    if (phase === 0) {
      ctx.fillRect(wx - 1, wy - 9, 2, 18);
      ctx.fillRect(wx - 9, wy - 1, 18, 2);
    } else {
      for (let i = -7; i <= 7; i++) {
        ctx.fillRect(wx + i, wy + i, 1, 1);
        ctx.fillRect(wx + i, wy - i, 1, 1);
      }
    }
    drawPixelCircle(ctx, wx, wy, 3, "#c9a349");
  }

  drawDetailedSprite(ctx, CHAR_STYLE.aldous, 280, 128 + sway, 1.35, false, tick, false);
}

function renderAct1Steps() {
  // Deep indigo sky + twinkling stars + crescent moon
  ctx.fillStyle = "#070914";
  ctx.fillRect(0, 0, 480, 270);
  ctx.fillStyle = "#e6e2c8";
  for (let i = 0; i < 30; i++) {
    const tw = (i + Math.floor(tick / 20)) % 9 === 0 ? 0 : 1;
    if (tw) ctx.fillRect((i * 59) % 470, (i * 19) % 62, 1, 1);
  }
  drawPixelCircle(ctx, 55, 29, 12, "rgba(235, 230, 200, 0.12)");
  drawPixelCircle(ctx, 55, 29, 8, "#f2eed8");

  // Side Wings + Central Bell Tower + Conical Slate Spires
  const wave = Math.floor(tick / 8) % 2;
  ctx.fillStyle = "#171421";
  ctx.fillRect(16, 72, 448, 134); // outer wings
  ctx.fillStyle = "#1e1b2b";
  ctx.fillRect(68, 34, 344, 172); // main keep
  ctx.fillRect(205, 16, 70, 32); // central belfry

  for (const [tx, tw, ty] of [[52, 42, 28], [386, 42, 28], [210, 60, 14]]) {
    ctx.fillStyle = "#252940";
    for (let i = 0; i < Math.floor(tw / 2); i++) ctx.fillRect(tx + i, ty - i, tw - i * 2, 2);
    ctx.fillStyle = "#8a1c33";
    ctx.fillRect(tx + Math.floor(tw / 2), ty - Math.floor(tw / 2) - 4, 12, 6 + wave);
  }
  ctx.fillStyle = "#2b263d";
  for (let bx = 96; bx <= 376; bx += 14) ctx.fillRect(bx, 28, 8, 7);

  // Stone masonry + Creeping Ivy
  ctx.fillStyle = "#262236";
  for (let y = 44; y < 196; y += 14) {
    for (let x = 74; x < 400; x += 28) ctx.fillRect(x + ((y / 14) % 2) * 12, y, 14, 5);
  }
  ctx.fillStyle = "#1c3824";
  for (const [ix, iy] of [[70, 115], [76, 130], [398, 120], [390, 142], [190, 90]]) {
    ctx.fillRect(ix, iy, 12, 26);
    ctx.fillRect(ix - 4, iy + 8, 8, 14);
  }

  // Ornate Circular Rose Window above entrance
  drawWarmLight(240, 74, 42, 0.25);
  drawPixelCircle(ctx, 240, 74, 14, "#f2be54");
  drawPixelCircle(ctx, 240, 74, 11, "#9e1934");
  drawPixelCircle(ctx, 240, 74, 5, "#f2be54");
  ctx.fillStyle = "#1e1b2b"; ctx.fillRect(239, 60, 2, 28); ctx.fillRect(226, 73, 28, 2);

  // Arched Gothic Stained-Glass Windows + Light Spills
  for (const wx of [104, 154, 298, 348]) {
    drawWarmLight(wx + 14, 92, 50, 0.24);
    ctx.fillStyle = "#f2be54"; ctx.fillRect(wx, 70, 28, 46); ctx.fillRect(wx + 4, 64, 20, 8);
    ctx.fillStyle = "#1e1b2b"; ctx.fillRect(wx + 13, 64, 2, 52); ctx.fillRect(wx, 90, 28, 2);
  }

  // Grand Carved Oak Double Doors + Iron Studs
  ctx.fillStyle = "#36201a"; ctx.fillRect(210, 116, 60, 86); ctx.fillRect(216, 108, 48, 10);
  ctx.fillStyle = "#1f110d"; ctx.fillRect(239, 108, 2, 94);
  ctx.fillStyle = "#c9a349"; ctx.fillRect(232, 156, 4, 6); ctx.fillRect(244, 156, 4, 6);

  // Wall Sconces & Wrought-Iron Courtyard Lantern Posts
  const fl = Math.floor(tick / 6) % 2;
  for (const [sx, sy] of [[196, 134], [284, 134], [116, 206], [364, 206]]) {
    drawWarmLight(sx, sy, 40, 0.26);
    ctx.fillStyle = "#ffd166"; ctx.fillRect(sx - 2, sy - 4 - fl, 4, 6);
    ctx.fillStyle = "#3a3547"; ctx.fillRect(sx - 1, sy + 2, 2, 22);
  }

  // Grand Stone Staircase + Balustrade
  ctx.fillStyle = "#463f57"; ctx.fillRect(175, 202, 130, 10);
  ctx.fillStyle = "#373145"; ctx.fillRect(155, 212, 170, 12);
  ctx.fillStyle = "#2b2638"; ctx.fillRect(135, 224, 210, 12);
  ctx.fillStyle = "#171420"; ctx.fillRect(0, 236, 480, 34);

  // Arriving Carriage parked on far left with circular wheels
  ctx.fillStyle = "#2e1a15"; ctx.fillRect(12, 188, 66, 36);
  ctx.fillStyle = "#e6b85c"; ctx.fillRect(34, 194, 20, 14);
  drawPixelCircle(ctx, 26, 226, 8, "#120e0d"); drawPixelRing(ctx, 26, 226, 7, 5, "#5c3d2e");
  drawPixelCircle(ctx, 64, 226, 8, "#120e0d"); drawPixelRing(ctx, 64, 226, 7, 5, "#5c3d2e");

  // Non-conversable arriving couples & guards
  drawDetailedSprite(ctx, { hair: "#523628", skin: "#e3b996", skinSh: "#bd8d6a", coat: "#3b233b", shade: "#211221", trim: "#e6c15a", cravat: "#f0ebe1", type: "noble" }, 96,  234, 1.3, false, tick + 4, false);
  drawDetailedSprite(ctx, { hair: "#c49c5a", skin: "#f0cbb0", skinSh: "#cc9e82", coat: "#213832", shade: "#11211d", trim: "#e6c15a", cravat: "#f0ebe1", type: "gown" },  114, 235, 1.3, false, tick + 12, true);
  drawDetailedSprite(ctx, { hair: "#2b2320", skin: "#e0b392", skinSh: "#bd8d6a", coat: "#2b3247", shade: "#181d2b", trim: "#c9a349", cravat: "#dcd3c0", type: "noble" }, 388, 232, 1.3, false, tick + 9, false);
  drawDetailedSprite(ctx, { hair: "#4a2a23", skin: "#ecc1a3", skinSh: "#c79c7f", coat: "#5e1e2b", shade: "#3b1019", trim: "#e6c15a", cravat: "#f5ebd6", type: "gown" },  406, 234, 1.3, false, tick + 18, true);
  drawDetailedSprite(ctx, { hair: "#2e2e33", skin: "#e0b392", skinSh: "#bd8d6a", coat: "#454a59", shade: "#262a36", trim: "#c2cbd6", cravat: "#454a59", type: "armor" }, 188, 200, 1.35, false, tick, false, "halberd");

  drawDetailedSprite(ctx, CHAR_STYLE.reynard, 260, 198, 1.4, false, tick, true);
  drawDetailedSprite(ctx, CHAR_STYLE.viscount, 208, 218, 1.4, false, tick, false);
}

function renderAct2Manor() {
  const scene = gameState ? gameState.current_scene : "party_floor";

  if (scene === "kitchen") {
    cam.x = 0; cam.y = 0;
    ctx.fillStyle = "#140d09"; ctx.fillRect(0, 0, 480, 270);
    // Vaulted Stone & Timber Duke's Kitchen Walls
    ctx.fillStyle = "#2b1d17"; ctx.fillRect(16, 12, 448, 56);
    ctx.fillStyle = "#3d2a21"; ctx.fillRect(16, 12, 448, 7);
    for (let ax = 48; ax < 440; ax += 96) {
      ctx.fillStyle = "#241914"; ctx.fillRect(ax, 18, 12, 50);
    }
    // Iron Pot Rack with Copper Pots, Skillets & Hanging Herb Bundles
    ctx.fillStyle = "#1c130f"; ctx.fillRect(42, 22, 118, 3);
    for (const [px, pw, ph] of [[48, 11, 12], [66, 13, 14], [86, 9, 10], [104, 12, 13], [126, 10, 11], [142, 8, 14]]) {
      ctx.fillStyle = "#b86b35"; ctx.fillRect(px, 26, pw, ph);
      ctx.fillStyle = "#e69a5c"; ctx.fillRect(px + 2, 28, 3, ph - 4);
    }
    for (const hx of [54, 92, 132]) {
      ctx.fillStyle = "#3d6b45"; ctx.fillRect(hx, 15, 6, 8);
    }
    // Twin Roaring Duke's Stone Hearths + Turning Spit Roast & Iron Cauldron
    ctx.fillStyle = "#3d322e"; ctx.fillRect(176, 10, 128, 58);
    ctx.fillStyle = "#120c0a"; ctx.fillRect(186, 26, 54, 40); ctx.fillRect(246, 26, 48, 40);
    const fl = Math.floor(tick / 5) % 2;
    drawWarmLight(240, 48, 110, 0.32);
    ctx.fillStyle = "#ff5e14"; ctx.fillRect(192, 44 - fl, 42, 18); ctx.fillRect(252, 46 - fl, 36, 16);
    ctx.fillStyle = "#ffd166"; ctx.fillRect(202, 50 - fl, 24, 10); ctx.fillRect(260, 51 - fl, 20, 9);
    ctx.fillStyle = "#8a4224"; ctx.fillRect(198, 34, 30, 10); // spit roast
    ctx.fillStyle = "#9ca3af"; ctx.fillRect(188, 38, 50, 2);
    ctx.fillStyle = "#222429"; ctx.fillRect(260, 36, 18, 14); // simmering cauldron

    // Spice, Silverware & Banquet Plate Shelves
    ctx.fillStyle = "#4d3325"; ctx.fillRect(312, 20, 62, 4); ctx.fillRect(312, 38, 62, 4);
    ctx.fillStyle = "#e6dfd3";
    for (let sx = 316; sx < 368; sx += 9) ctx.fillRect(sx, 14, 6, 6);
    ctx.fillStyle = "#5cb874";
    for (let sx = 316; sx < 368; sx += 13) ctx.fillRect(sx, 31, 5, 7);

    // Flagstone Floor
    for (let y = 68; y < 254; y += 24) {
      for (let x = 16; x < 464; x += 24) {
        ctx.fillStyle = ((x + y) / 24) % 2 === 0 ? "#362821" : "#2b1f1a";
        ctx.fillRect(x, y, 24, 24);
      }
    }
    // Banquet Prep Tables (Plated Roasts, Pastries, Dough, Wine Ewers)
    ctx.fillStyle = "#593b29"; ctx.fillRect(52, 98, 116, 28); ctx.fillRect(52, 182, 102, 26);
    ctx.fillStyle = "#d9d0c1"; ctx.fillRect(62, 102, 26, 16); ctx.fillRect(96, 102, 26, 16);
    ctx.fillStyle = "#e3b874"; ctx.fillRect(130, 104, 16, 12); ctx.fillRect(68, 188, 22, 12);
    ctx.fillStyle = "#f2ebe0"; ctx.fillRect(102, 188, 18, 12);
    // Stone Scullery Basin (bottom-center-left)
    ctx.fillStyle = "#4f4a48"; ctx.fillRect(190, 220, 44, 22);
    ctx.fillStyle = "#2b4b69"; ctx.fillRect(196, 224, 32, 14);

    // Oak Wine Barrels & Cellar Archway
    for (const [bx, by] of [[396, 168], [422, 168], [409, 194]]) {
      ctx.fillStyle = "#4a2e1d"; ctx.fillRect(bx, by, 20, 24);
      ctx.fillStyle = "#1f1c24"; ctx.fillRect(bx, by + 5, 20, 2); ctx.fillRect(bx, by + 17, 20, 2);
    }
    ctx.fillStyle = "#120c0a"; ctx.fillRect(382, 68, 66, 44);
    ctx.fillStyle = "#6e655f";
    for (let s = 0; s < 4; s++) ctx.fillRect(388, 74 + s * 8, 54, 4);
    ctx.fillStyle = "#e6c15a"; ctx.font = "9px monospace"; ctx.fillText("CELLAR ↓", 392, 62);

    // 5 Non-Conversable Kitchen Staff bustling
    drawDetailedSprite(ctx, { hair: "#6b4730", skin: "#ecc1a3", skinSh: "#c79c7f", coat: "#6e5144", shade: "#47332b", trim: "#ebe6df", cravat: "#ebe6df", type: "cook" }, 118, 142, 1.3, false, tick + 6, true);
    drawDetailedSprite(ctx, { hair: "#3d2a20", skin: "#e0b392", skinSh: "#bd8d6a", coat: "#52463d", shade: "#362d27", trim: "#dcd3c0", cravat: "#dcd3c0", type: "butler" }, 288, 76, 1.25, false, tick + 14, true);
    drawDetailedSprite(ctx, { hair: "#8a6d56", skin: "#ecc1a3", skinSh: "#c79c7f", coat: "#5c4033", shade: "#3d2920", trim: "#f0ebe4", cravat: "#f0ebe4", type: "cook" }, 104, 224, 1.3, false, tick + 21, false);
    drawDetailedSprite(ctx, { hair: "#474340", skin: "#d6a47e", skinSh: "#b0805d", coat: "#3b3532", shade: "#24201e", trim: "#8c7156", cravat: "#8c7156", type: "noble" }, 372, 186, 1.3, false, tick + 3, false, "tray");
    drawDetailedSprite(ctx, { hair: "#a67c52", skin: "#f0cbb0", skinSh: "#cc9e82", coat: "#6e4e3f", shade: "#473228", trim: "#f0ebe4", cravat: "#f0ebe4", type: "cook" }, 212, 212, 1.25, false, tick + 17, false);

    updatePlayerMovement();
    const npcs = getAct2NPCs();
    for (const n of npcs) {
      drawDetailedSprite(ctx, CHAR_STYLE[n.id], n.x, n.y, 1.35, false, tick, player.x < n.x);
      if (Math.hypot(player.x - n.x, player.y - n.y) < 42) {
        ctx.fillStyle = "#e6c15a"; ctx.font = "9px monospace";
        ctx.fillText(CHAR_STYLE[n.id].label, n.x - 24, n.y - 26);
      }
    }
    drawDetailedSprite(ctx, CHAR_STYLE.viscount, player.x, player.y, 1.35, player.moving, tick, player.dir === 2);
    return;
  }

  if (scene === "balcony") {
    cam.x = 0; cam.y = 0;
    ctx.fillStyle = "#040611"; ctx.fillRect(0, 0, 480, 40);
    ctx.fillStyle = "#070c1e"; ctx.fillRect(0, 40, 480, 40);
    ctx.fillStyle = "#0c1530"; ctx.fillRect(0, 80, 480, 42);

    // Subtle steady stars
    ctx.fillStyle = "#dfe4f2";
    for (let i = 0; i < 36; i++) {
      ctx.fillRect((i * 61 + 17) % 470, (i * 23 + 7) % 86, 1, 1);
    }

    // True Circular Pixel Moon with gentle craters & soft halo
    drawPixelCircle(ctx, 372, 42, 26, "rgba(215, 228, 255, 0.06)");
    drawPixelCircle(ctx, 372, 42, 18, "rgba(225, 235, 255, 0.11)");
    drawPixelCircle(ctx, 372, 42, 13, "#f4f1e1");
    ctx.fillStyle = "#dcd5be";
    ctx.fillRect(366, 37, 4, 3); ctx.fillRect(376, 45, 3, 3); ctx.fillRect(369, 48, 3, 2);

    // 3 Layered Distant Mountain Ridges
    ctx.fillStyle = "#111c36";
    for (let mx = -20; mx < 490; mx += 76) {
      for (let h = 0; h < 34; h++) ctx.fillRect(mx + h, 122 - h, 76 - h * 2, 2);
    }
    ctx.fillStyle = "#0b1426";
    for (let mx = 10; mx < 480; mx += 64) {
      for (let h = 0; h < 24; h++) ctx.fillRect(mx + h, 122 - h, 64 - h * 2, 2);
    }

    // Moonlit Valley River / Lake + Gentle Silver Path Reflection
    ctx.fillStyle = "#0a172e"; ctx.fillRect(0, 118, 480, 38);
    ctx.fillStyle = "#112445"; ctx.fillRect(0, 124, 480, 18);
    const ripple = Math.floor(tick / 16) % 3;
    ctx.fillStyle = "#c9d8f0";
    for (let ry = 121; ry < 152; ry += 5) {
      const rw = Math.max(4, 24 - (ry - 121) * 0.6);
      ctx.fillRect(362 + ((ry + ripple) % 4), ry, rw, 1);
    }

    // Distant Riverside Village Warm Lights
    ctx.fillStyle = "#f2c166";
    for (const [vx, vy] of [[84, 117], [92, 116], [108, 117], [142, 116], [150, 117]]) {
      ctx.fillRect(vx, vy, 2, 2);
    }

    // Royal Garden Terrace Below
    ctx.fillStyle = "#0d1a14"; ctx.fillRect(0, 154, 480, 116);
    ctx.fillStyle = "#16291e";
    for (let hx = 34; hx < 446; hx += 68) ctx.fillRect(hx, 186, 46, 20);
    // Symmetrical Stone Walkways
    ctx.fillStyle = "#2b2836"; ctx.fillRect(224, 154, 32, 116);
    ctx.fillRect(60, 204, 360, 14);

    // Tall Cypress Trees framing the valley
    for (const cx of [44, 422]) {
      ctx.fillStyle = "#08140e";
      ctx.fillRect(cx, 114, 14, 68);
      ctx.fillRect(cx + 3, 98, 8, 18);
      ctx.fillRect(cx + 5, 88, 4, 12);
    }

    // Circular Tiered Marble Fountain with gentle water arc
    drawPixelCircle(ctx, 240, 204, 18, "#4b475c");
    drawPixelCircle(ctx, 240, 204, 14, "#1e3759");
    drawPixelCircle(ctx, 240, 202, 5,  "#635e78");
    const drop = Math.floor(tick / 6) % 4;
    ctx.fillStyle = "#8ec5ff";
    ctx.fillRect(239, 186 + drop, 2, 14 - drop);
    ctx.fillRect(233, 193 + drop, 2, 7); ctx.fillRect(245, 193 + drop, 2, 7);

    // Grand Foreground Stone Balcony Terrace + Carved Balustrade + Ivy
    ctx.fillStyle = "#312d3d"; ctx.fillRect(0, 142, 480, 14);
    ctx.fillStyle = "#4c475e"; ctx.fillRect(16, 138, 448, 5);
    for (let px = 28; px < 452; px += 16) {
      ctx.fillStyle = "#1c1926"; ctx.fillRect(px, 143, 8, 11);
    }
    // Stone Arch Columns Framing Left & Right
    ctx.fillStyle = "#252130"; ctx.fillRect(0, 0, 24, 270); ctx.fillRect(456, 0, 24, 270);
    ctx.fillStyle = "#183320"; ctx.fillRect(18, 28, 10, 44); ctx.fillRect(452, 34, 10, 38);

    // Steady Warm Balcony Lanterns (soft glow, no strobe!)
    drawWarmLight(76, 128, 44, 0.20); drawWarmLight(404, 128, 44, 0.20);
    ctx.fillStyle = "#ffd166"; ctx.fillRect(74, 126, 4, 6); ctx.fillRect(402, 126, 4, 6);

    // Gentle slow-drifting garden fireflies
    ctx.fillStyle = "#d9f285";
    for (let f = 0; f < 4; f++) {
      const fx = 120 + f * 75 + Math.round(Math.sin(tick * 0.03 + f) * 12);
      const fy = 175 + Math.round(Math.cos(tick * 0.04 + f * 2) * 8);
      ctx.fillRect(fx, fy, 1, 1);
    }

    // Non-Conversable Noble Couple admiring the moonlit valley
    drawDetailedSprite(ctx, { hair: "#3b2621", skin: "#e3b996", skinSh: "#bd8d6a", coat: "#283954", shade: "#162133", trim: "#e6c15a", cravat: "#f0ebe1", type: "cloak" }, 144, 152, 1.3, false, tick + 5, false);
    drawDetailedSprite(ctx, { hair: "#b88a4d", skin: "#f2d5c4", skinSh: "#cca995", coat: "#52243b", shade: "#331424", trim: "#e6c15a", cravat: "#f5ebd6", type: "gown" },  162, 153, 1.3, false, tick + 14, true);

    updatePlayerMovement();
    drawDetailedSprite(ctx, CHAR_STYLE.viscount, player.x, player.y, 1.35, player.moving, tick, player.dir === 2);
    return;
  }

  // ── SPLENDID 960x540 GRAND BANQUET HALL (Camera-Scrolling) ──
  updatePlayerMovement();
  cam.x = Math.max(0, Math.min(480, Math.round(player.x - 240)));
  cam.y = Math.max(0, Math.min(270, Math.round(player.y - 135)));

  ctx.save();
  ctx.translate(-cam.x, -cam.y);

  // Outer Stone Perimeter & Wainscoted Hall Walls (960x540)
  ctx.fillStyle = "#0c0a12"; ctx.fillRect(0, 0, 960, 540);
  ctx.fillStyle = "#211c2e"; ctx.fillRect(28, 14, 904, 52);
  ctx.fillStyle = "#332b45"; ctx.fillRect(28, 60, 904, 6);

  // Checkered Marble Grand Floor (960x540)
  for (let y = 66; y < 516; y += 24) {
    for (let x = 28; x < 932; x += 24) {
      ctx.fillStyle = ((x + y) / 24) % 2 === 0 ? "#241e33" : "#1b1626";
      ctx.fillRect(x, y, 24, 24);
    }
  }

  // Royal Crimson Carpet Runner from Grand Entrance to High Dais
  ctx.fillStyle = "#541625"; ctx.fillRect(450, 148, 60, 368);
  ctx.fillStyle = "#c9a349"; ctx.fillRect(450, 148, 3, 368); ctx.fillRect(507, 148, 3, 368);

  // Tall Leaded Moonlit Windows + Crimson Banners + Ornate Gilt-Framed Paintings
  for (const wx of [120, 290, 670, 840]) {
    ctx.fillStyle = "#162342"; ctx.fillRect(wx, 18, 28, 36);
    ctx.fillStyle = "#0f1526"; ctx.fillRect(wx + 13, 18, 2, 36); ctx.fillRect(wx, 34, 28, 2);
  }
  for (const px of [64, 210, 405, 555, 750, 896]) {
    ctx.fillStyle = "#c9a349"; ctx.fillRect(px - 14, 20, 28, 22);
    ctx.fillStyle = px % 2 === 0 ? "#2f4858" : "#5c2735"; ctx.fillRect(px - 11, 23, 22, 16);
    ctx.fillStyle = "#e6c15a"; ctx.fillRect(px - 4, 28, 8, 6);
  }
  for (const bx of [358, 602]) {
    ctx.fillStyle = "#6e192d"; ctx.fillRect(bx - 10, 16, 20, 42);
    ctx.fillStyle = "#e6c15a"; ctx.fillRect(bx - 3, 24, 6, 16);
  }

  // Marble Statues on Pedestals & Porcelain Ming Vases with Flowers
  for (const [sx, sy] of [[96, 86], [280, 86], [680, 86], [864, 86]]) {
    ctx.fillStyle = "#3f3b4d"; ctx.fillRect(sx - 10, sy - 6, 20, 14);
    ctx.fillStyle = "#9da3b3"; ctx.fillRect(sx - 5, sy - 24, 10, 18);
    drawPixelCircle(ctx, sx, sy - 27, 4, "#c5cad6");
  }
  for (const [vx, vy] of [[156, 76], [234, 76], [726, 76], [804, 76], [428, 496], [532, 496]]) {
    ctx.fillStyle = "#264e70"; ctx.fillRect(vx - 5, vy - 10, 10, 12);
    ctx.fillStyle = "#e6c15a"; ctx.fillRect(vx - 4, vy - 12, 8, 2);
    ctx.fillStyle = "#3b7049"; ctx.fillRect(vx - 6, vy - 18, 12, 6);
    ctx.fillStyle = "#d95b72"; ctx.fillRect(vx - 3, vy - 20, 3, 3); ctx.fillRect(vx + 2, vy - 19, 3, 3);
  }

  // Grand Roaring East Fireplace (x=888, y=285)
  ctx.fillStyle = "#3d3345"; ctx.fillRect(888, 278, 42, 92);
  ctx.fillStyle = "#120c0f"; ctx.fillRect(890, 294, 28, 60);
  const fl = Math.floor(tick / 6) % 2;
  drawWarmLight(896, 324, 86, 0.28);
  ctx.fillStyle = "#ff5e14"; ctx.fillRect(894, 314 - fl, 18, 28);
  ctx.fillStyle = "#ffd166"; ctx.fillRect(898, 322 - fl, 10, 16);

  // Center Inlaid Parquet Dance Floor Medallion (x=480, y=290)
  drawPixelCircle(ctx, 480, 290, 88, "#2b2024");
  drawPixelRing(ctx, 480, 290, 86, 82, "#c9a349");
  drawPixelRing(ctx, 480, 290, 56, 53, "#541625");

  // Animated Waltzing Couples on Dance Floor (graceful ballroom hold, 3/4 sway, no running)
  for (const dc of DANCING_COUPLES) {
    drawWaltzCouple(ctx, dc, tick);
  }

  // Majestic North Dais & Royal High Table (Duke Aldric & Lady Isolde)
  ctx.fillStyle = "#4d1725"; ctx.fillRect(344, 68, 272, 82);
  ctx.fillStyle = "#702035"; ctx.fillRect(350, 72, 260, 74);
  ctx.fillStyle = "#c9a349"; ctx.fillRect(344, 146, 272, 3);
  ctx.fillStyle = "rgba(0,0,0,0.45)"; ctx.fillRect(378, 98, 206, 28);
  ctx.fillStyle = "#472c26"; ctx.fillRect(376, 94, 208, 28);
  ctx.fillStyle = "#ebe4d5"; ctx.fillRect(382, 98, 196, 18);
  ctx.fillStyle = "#e6c15a"; ctx.fillRect(410, 102, 10, 8); ctx.fillRect(475, 101, 12, 9); ctx.fillRect(540, 102, 10, 8);
  ctx.fillStyle = "#9e1934"; ctx.fillRect(442, 104, 6, 6); ctx.fillRect(512, 104, 6, 6);

  // Banquet Wing Tables (Vantrell West, Delegation East, Marrow Southwest)
  const wingTables = [
    { x: 120, y: 205, w: 148, h: 36, cloth: "#1f4739", label: "House Vantrell" },
    { x: 692, y: 205, w: 148, h: 36, cloth: "#5e1e2b", label: "Foreign Delegation" },
    { x: 130, y: 390, w: 128, h: 34, cloth: "#2d2a38", label: "House Marrow" },
  ];
  for (const t of wingTables) {
    ctx.fillStyle = "rgba(0,0,0,0.45)"; ctx.fillRect(t.x + 3, t.y + 4, t.w, t.h);
    ctx.fillStyle = "#472c26"; ctx.fillRect(t.x, t.y, t.w, t.h);
    ctx.fillStyle = t.cloth; ctx.fillRect(t.x + 4, t.y + 4, t.w - 8, t.h - 8);
    ctx.fillStyle = "#e6dfd3"; ctx.fillRect(t.x + 8, t.y + 7, t.w - 16, t.h - 14);
    ctx.fillStyle = "#e6c15a";
    ctx.fillRect(t.x + 24, t.y + 12, 8, 8);
    ctx.fillRect(t.x + Math.floor(t.w / 2) - 5, t.y + 11, 10, 9);
    ctx.fillRect(t.x + t.w - 32, t.y + 12, 8, 8);
    ctx.fillStyle = "#9e1934"; ctx.fillRect(t.x + 48, t.y + 13, 5, 5); ctx.fillRect(t.x + t.w - 54, t.y + 13, 5, 5);
  }

  // Grand Chandeliers & Warm Candelabra Glows
  for (const [cx, cy] of [[194, 220], [766, 220], [194, 405], [480, 105], [480, 290]]) {
    drawWarmLight(cx, cy, 95, 0.16);
    ctx.fillStyle = "#ffd166"; ctx.fillRect(cx - 1, cy - 4 - fl, 3, 4);
  }

  // Non-Conversable Ambient Crowd, Musicians & Guards
  for (const g of AMBIENT_GUESTS) {
    const style = {
      hair: g.hair, skin: "#e3b996", skinSh: "#bd8d6a",
      coat: g.coat, shade: "#181421", trim: "#9c8559", cravat: "#dcd3c0",
      type: g.role === "guard" ? "armor" : (g.gown ? "gown" : "noble"),
    };
    const prop = g.role === "musician" ? "violin" : (g.role === "guard" ? "halberd" : null);
    drawDetailedSprite(ctx, style, g.x, g.y, 1.25, false, tick + g.phase, !!g.facingLeft, prop);
  }

  for (const s of PATROL_SERVANTS) {
    const t = ((tick * s.speed + s.offset) % 200) / 200;
    const ping = t < 0.5 ? t * 2 : (1 - t) * 2;
    const sx = s.x1 + (s.x2 - s.x1) * ping;
    const sy = s.y1 + (s.y2 - s.y1) * ping;
    const facingLeft = t >= 0.5 && s.x2 > s.x1;
    const sStyle = { hair: "#52463d", skin: "#e6bea0", skinSh: "#bf9575", coat: "#2b2833", shade: "#18161f", trim: "#ebe6df", cravat: "#ffffff", type: "butler" };
    drawDetailedSprite(ctx, sStyle, sx, sy, 1.25, true, tick, facingLeft, "tray");
  }

  ctx.fillStyle = "rgba(255, 226, 153, 0.28)";
  for (const d of DUST) {
    const dy = (d.y - tick * d.s) % 520;
    ctx.fillRect(d.x, dy < 0 ? dy + 520 : dy, 1, 1);
  }

  const npcs = getAct2NPCs();
  let nearest = null, nearestDist = 999;
  for (const n of npcs) {
    const facingLeft = player.x < n.x;
    drawDetailedSprite(ctx, CHAR_STYLE[n.id], n.x, n.y, 1.35, false, tick, facingLeft);
    const d = Math.hypot(player.x - n.x, player.y - n.y);
    if (d < nearestDist) { nearestDist = d; nearest = n; }
    if (d < 56) {
      ctx.fillStyle = "#e6c15a"; ctx.font = "9px monospace";
      ctx.fillText(CHAR_STYLE[n.id].label, n.x - 24, n.y - 26);
    }
  }
  if (nearest && nearestDist < 56 && nearest.id !== activeNpc) selectNpc(nearest.id);
  drawDetailedSprite(ctx, CHAR_STYLE.viscount, player.x, player.y, 1.35, player.moving, tick, player.dir === 2);

  ctx.restore();
}

function renderAct3Toast() {
  ctx.fillStyle = "#0e0a16"; ctx.fillRect(0, 0, 480, 270);
  drawWarmLight(240, 100, 125, 0.24);
  ctx.fillStyle = "#591828"; ctx.fillRect(140, 84, 200, 48);
  ctx.fillStyle = "#dcd3c0"; ctx.fillRect(156, 94, 168, 22);
  ctx.fillStyle = "#a3142e"; ctx.fillRect(236, 98, 8, 12);

  for (const gx of [65, 90, 390, 415]) {
    drawDetailedSprite(ctx, { hair: "#4a3326", skin: "#e0b392", skinSh: "#bd8d6a", coat: "#2c334a", shade: "#181c29", trim: "#c9a349", cravat: "#dcd3c0", type: "noble" }, gx, 195, 1.25, false, tick, gx > 240);
  }
  drawDetailedSprite(ctx, CHAR_STYLE.duke,     240, 78,  1.45, false, tick, false);
  drawDetailedSprite(ctx, CHAR_STYLE.isolde,   192, 92,  1.35, false, tick, false);
  drawDetailedSprite(ctx, CHAR_STYLE.reynard,  292, 92,  1.35, false, tick, true);
  drawDetailedSprite(ctx, CHAR_STYLE.cassian,  125, 155, 1.35, false, tick, false);
  drawDetailedSprite(ctx, CHAR_STYLE.ophelia,  355, 155, 1.35, false, tick, true);
  drawDetailedSprite(ctx, CHAR_STYLE.viscount, 240, 198, 1.45, false, tick, false);
}

function drawDungeonBackdrop() {
  // Deep stone cavern background
  ctx.fillStyle = "#08070c"; ctx.fillRect(0, 0, 480, 270);

  // Staggered stone brick walls
  for (let row = 0; row < 7; row++) {
    const y = row * 24;
    const off = (row % 2) * 20;
    for (let x = -20; x < 480; x += 40) {
      ctx.fillStyle = ((row + Math.floor(x / 40)) % 3 === 0) ? "#1f1d26" : "#18161f";
      ctx.fillRect(x + off + 1, y + 1, 38, 22);
      ctx.fillStyle = "#292633";
      ctx.fillRect(x + off + 2, y + 2, 36, 2);
    }
  }

  // Moss & damp stains
  ctx.fillStyle = "rgba(35, 62, 45, 0.32)";
  for (const [mx, my, mw, mh] of [[24, 108, 28, 56], [426, 98, 34, 66], [198, 118, 22, 46]]) {
    ctx.fillRect(mx, my, mw, mh);
  }

  // Twin arched iron-barred dungeon cells
  for (const cx of [74, 314]) {
    ctx.fillStyle = "#060509";
    ctx.fillRect(cx, 54, 92, 114);
    ctx.fillStyle = "#363342";
    ctx.fillRect(cx - 6, 48, 104, 8);
    ctx.fillRect(cx - 6, 54, 6, 114);
    ctx.fillRect(cx + 92, 54, 6, 114);
    // Vertical iron bars + horizontal crossbars
    ctx.fillStyle = "#525866";
    for (let bx = cx + 10; bx < cx + 88; bx += 14) {
      ctx.fillRect(bx, 56, 3, 112);
    }
    ctx.fillStyle = "#3e434f";
    ctx.fillRect(cx, 88, 92, 4);
    ctx.fillRect(cx, 134, 92, 4);
  }

  // Flagstone dungeon floor
  for (let y = 168; y < 270; y += 22) {
    for (let x = 0; x < 480; x += 32) {
      ctx.fillStyle = ((x / 32 + y / 22) % 2 === 0) ? "#1a1821" : "#131118";
      ctx.fillRect(x, y, 31, 21);
    }
  }

  // Hanging iron shackles on center pillar
  ctx.fillStyle = "#6e7585";
  ctx.fillRect(224, 78, 2, 24); ctx.fillRect(254, 78, 2, 28);
  ctx.fillRect(221, 102, 8, 5); ctx.fillRect(251, 106, 8, 5);

  // Wooden crates & barrel in alcove
  ctx.fillStyle = "#3d281a"; ctx.fillRect(18, 174, 34, 28);
  ctx.fillStyle = "#2b1b11"; ctx.fillRect(20, 176, 30, 2); ctx.fillRect(18, 188, 34, 2);
  ctx.fillStyle = "#4a2e1d"; ctx.fillRect(426, 170, 26, 32);
  ctx.fillStyle = "#1f1c24"; ctx.fillRect(426, 178, 26, 2); ctx.fillRect(426, 192, 26, 2);

  // Flickering wall torches
  const fl = Math.floor(tick / 4) % 3;
  for (const tx of [186, 294]) {
    drawWarmLight(tx, 76, 88 + fl * 4, 0.28);
    ctx.fillStyle = "#3d332c"; ctx.fillRect(tx - 2, 82, 4, 16);
    ctx.fillStyle = "#ff6b1a"; ctx.fillRect(tx - 4, 72 - fl, 8, 10 + fl);
    ctx.fillStyle = "#ffd166"; ctx.fillRect(tx - 2, 75 - fl, 4, 6);
  }

  // Dripping water droplet
  const dropY = 120 + ((tick * 2) % 68);
  ctx.fillStyle = "#5c85b8";
  ctx.fillRect(120, dropY, 2, 4);
  ctx.fillStyle = "rgba(92, 133, 184, 0.25)";
  ctx.fillRect(114, 188, 14, 3);
}

function renderDungeonInterrogation() {
  drawDungeonBackdrop();
  const guardStyle = { hair: "#3d3835", skin: "#d6a47e", skinSh: "#b0805d", coat: "#3b3e4a", shade: "#22242e", trim: "#8c96a3", cravat: "#525866", type: "noble" };
  drawDetailedSprite(ctx, guardStyle, 72, 192, 1.3, false, tick, false, "lantern");
  drawDetailedSprite(ctx, guardStyle, 408, 192, 1.3, false, tick + 12, true);
  drawDetailedSprite(ctx, CHAR_STYLE.viscount, 196, 204, 1.45, false, tick, false);
  drawDetailedSprite(ctx, CHAR_STYLE.reynard,  284, 204, 1.45, false, tick, true);
}

function renderDungeonExecution(act) {
  const shakeX = (execTick >= 124 && execTick <= 136) ? ((execTick % 2 === 0) ? 3 : -3) : 0;
  const shakeY = (execTick >= 124 && execTick <= 136) ? ((execTick % 3 === 0) ? 2 : -2) : 0;
  ctx.save();
  ctx.translate(shakeX, shakeY);
  drawDungeonBackdrop();

  const guardStyle = { hair: "#2b2826", skin: "#cfa07c", skinSh: "#a37856", coat: "#343742", shade: "#1c1e26", trim: "#9aa4b2", cravat: "#454a57", type: "noble" };
  // Flanking guards watching
  drawDetailedSprite(ctx, guardStyle, 118, 196, 1.38, false, tick, false);
  drawDetailedSprite(ctx, guardStyle, 362, 196, 1.38, false, tick + 8, true);

  // Wooden chopping block
  ctx.fillStyle = "#3b2314"; ctx.fillRect(222, 206, 36, 18);
  ctx.fillStyle = "#26160c"; ctx.fillRect(224, 206, 32, 4);

  const fallen = execTick >= 126;
  if (!fallen) {
    // Viscount kneeling & chained in irons
    ctx.save();
    ctx.translate(212, 208);
    // Kneeling cloak & torso
    ctx.fillStyle = "#17202e"; ctx.fillRect(-7, -14, 14, 16);
    ctx.fillStyle = "#2c3d55"; ctx.fillRect(-6, -16, 12, 12);
    // Head bowed forward
    ctx.fillStyle = "#f2c6a0"; ctx.fillRect(-4, -24, 8, 8);
    ctx.fillStyle = "#2b1d12"; ctx.fillRect(-5, -26, 10, 4);
    // Iron wrist chains + floor chain
    ctx.fillStyle = "#8c96a3";
    ctx.fillRect(4, -10, 8, 3);
    ctx.fillRect(-10, -2, 6, 3);
    ctx.fillRect(-18, 0, 10, 2);
    ctx.restore();
  } else {
    // Aftermath: crimson pool + fallen cloak + severed silhouette
    ctx.fillStyle = "#6e0d1c"; ctx.fillRect(198, 214, 48, 8);
    ctx.fillStyle = "#a3142e"; ctx.fillRect(206, 216, 32, 5);
    ctx.fillStyle = "#17202e"; ctx.fillRect(184, 210, 28, 10);
    ctx.fillStyle = "#2c3d55"; ctx.fillRect(188, 208, 20, 6);
    ctx.fillStyle = "#8c96a3"; ctx.fillRect(178, 215, 10, 2);
    ctx.fillStyle = "#f2c6a0"; ctx.fillRect(246, 215, 7, 7);
    ctx.fillStyle = "#2b1d12"; ctx.fillRect(245, 214, 9, 3);
  }

  // Executioner guard on right with animated broadsword swing
  drawDetailedSprite(ctx, { hair: "#1a181c", skin: "#c99974", skinSh: "#9e7351", coat: "#24191e", shade: "#140d10", trim: "#a3142e", cravat: "#140d10", type: "noble" }, 284, 202, 1.48, false, tick, true);
  ctx.save();
  ctx.translate(274, 186);
  let angle = -0.35;
  if (execTick >= 35 && execTick < 90) angle = -0.35 - ((execTick - 35) / 55) * 1.15;
  else if (execTick >= 90 && execTick < 115) angle = -1.5;
  else if (execTick >= 115 && execTick < 126) angle = -1.5 + ((execTick - 115) / 11) * 2.15;
  else if (execTick >= 126) angle = 0.65;
  ctx.rotate(angle);
  // Sword hilt & gleaming steel blade
  ctx.fillStyle = "#593b29"; ctx.fillRect(-2, -4, 4, 8);
  ctx.fillStyle = "#c9a349"; ctx.fillRect(-5, -6, 10, 2);
  ctx.fillStyle = "#cfd8e3"; ctx.fillRect(-2, -34, 4, 28);
  ctx.fillStyle = "#ffffff"; ctx.fillRect(-1, -32, 1, 24);
  ctx.restore();

  // Brief crimson flash on impact
  if (execTick >= 124 && execTick <= 132) {
    ctx.fillStyle = "rgba(163, 20, 46, 0.35)";
    ctx.fillRect(0, 0, 480, 270);
  }

  // Grim banner
  if (execTick >= 134) {
    ctx.fillStyle = "rgba(8, 7, 12, 0.72)";
    ctx.fillRect(130, 18, 220, 24);
    ctx.fillStyle = "#ff8a9b";
    ctx.font = "bold 11px monospace";
    ctx.fillText(act === "ending_d" ? "EXECUTED IN THE DUNGEON" : "THE CONSPIRACY PREVAILS", 156, 34);
  }
  ctx.restore();
}

function drawWaltzCouple(c, dc, frame) {
  const ang = frame * dc.speed + dc.offset;
  const cx = dc.cx + Math.cos(ang) * dc.rx;
  const cy = dc.cy + Math.sin(ang) * dc.ry;
  const sway = Math.sin(frame * 0.07 + dc.offset) * 1.5;
  const rise = Math.abs(Math.sin(frame * 0.105 + dc.offset)) * -2;
  const spin = Math.cos(frame * 0.045 + dc.offset);
  const sep = 4.5 + Math.abs(spin) * 1.2;

  c.save();
  c.translate(Math.round(cx + sway), Math.round(cy + rise));

  // Shared shadow
  c.fillStyle = "rgba(0,0,0,0.38)";
  c.fillRect(-10, 7 - rise, 20, 3);

  // Partner 1 (Gentleman, left/leading)
  const gX = spin >= 0 ? -sep : sep;
  c.fillStyle = "#1a1721"; c.fillRect(gX - 2, 1, 2, 5); c.fillRect(gX + 1, 1, 2, 5);
  c.fillStyle = dc.coat1; c.fillRect(gX - 4, -8, 8, 10);
  c.fillStyle = "#e6c15a"; c.fillRect(gX - 1, -7, 2, 6);
  c.fillStyle = "#e6bea0"; c.fillRect(gX - 3, -15, 6, 7);
  c.fillStyle = "#3d261c"; c.fillRect(gX - 3, -17, 6, 3);

  // Partner 2 (Lady, flared swirling gown)
  const lX = -gX;
  const flare = Math.round(Math.abs(Math.sin(frame * 0.09 + dc.offset)) * 2);
  c.fillStyle = "#26121b"; c.fillRect(lX - 5 - flare, -1, 10 + flare * 2, 7);
  c.fillStyle = dc.coat2; c.fillRect(lX - 4 - Math.floor(flare / 2), -8, 8 + flare, 10);
  c.fillStyle = "#e6c15a"; c.fillRect(lX - 1, -6, 2, 9);
  c.fillStyle = "#f0cbb0"; c.fillRect(lX - 3, -15, 6, 7);
  c.fillStyle = "#b88a4d"; c.fillRect(lX - 3, -17, 6, 4);

  // Joined ballroom arms
  c.fillStyle = "#f0ebe1";
  c.fillRect(-3, -6, 6, 2);
  c.fillStyle = "#e6bea0";
  c.fillRect(0, -10, 2, 2);
  c.restore();
}

function renderBalconyFall() {
  // Draw moonlit balcony scenery without player standing on terrace
  ctx.fillStyle = "#040611"; ctx.fillRect(0, 0, 480, 40);
  ctx.fillStyle = "#070c1e"; ctx.fillRect(0, 40, 480, 40);
  ctx.fillStyle = "#0c1530"; ctx.fillRect(0, 80, 480, 42);
  for (const [sx, sy] of [[42, 16], [118, 28], [186, 14], [254, 34], [326, 20], [438, 18]]) {
    ctx.fillStyle = "#d9e6ff"; ctx.fillRect(sx, sy, 2, 2);
  }
  drawPixelCircle(ctx, 368, 44, 18, "#f5f0d6");
  ctx.fillStyle = "#111b36";
  ctx.beginPath(); ctx.moveTo(0, 118); ctx.lineTo(90, 74); ctx.lineTo(185, 106); ctx.lineTo(285, 64); ctx.lineTo(395, 102); ctx.lineTo(480, 72); ctx.lineTo(480, 128); ctx.lineTo(0, 128); ctx.closePath(); ctx.fill();
  ctx.fillStyle = "#0c162b"; ctx.fillRect(0, 118, 480, 32);
  ctx.fillStyle = "#162d47"; ctx.fillRect(105, 122, 270, 22);
  ctx.fillStyle = "#312d3d"; ctx.fillRect(0, 142, 480, 14);
  ctx.fillStyle = "#4c475e"; ctx.fillRect(16, 138, 448, 5);
  ctx.fillStyle = "#1c1926"; ctx.fillRect(0, 154, 480, 116);
  drawPixelCircle(ctx, 240, 204, 18, "#4b475c");
  drawPixelCircle(ctx, 240, 204, 14, "#1e3759");

  // Falling Viscount animation over the balustrade into the valley below
  const t = Math.min(1, balconyFallTick / 85);
  const fx = Math.max(48, Math.min(432, player.x)) + Math.sin(t * 9) * 4;
  const fy = t < 0.2 ? 150 - Math.sin((t / 0.2) * Math.PI) * 16 : 150 - (t - 0.2) * 35;
  const sc = Math.max(0.25, 1.35 * (1 - t * 0.82));
  ctx.save();
  ctx.translate(fx, fy);
  ctx.rotate(t * 4.2);
  ctx.scale(sc, sc);
  ctx.fillStyle = "#243b61"; ctx.fillRect(-5, -8, 10, 12);
  ctx.fillStyle = "#f0c4a0"; ctx.fillRect(-3, -14, 6, 6);
  ctx.fillStyle = "#e6c15a"; ctx.fillRect(-6, -4, 12, 2);
  ctx.restore();

  if (balconyFallTick >= 86 && balconyFallTick <= 94) {
    ctx.fillStyle = "rgba(163, 20, 46, 0.32)";
    ctx.fillRect(0, 0, 480, 270);
  }
  if (balconyFallTick >= 92) {
    ctx.fillStyle = "rgba(8, 7, 12, 0.78)";
    ctx.fillRect(105, 18, 270, 24);
    ctx.fillStyle = "#ff8a9b";
    ctx.font = "bold 11px monospace";
    ctx.fillText("THE VISCOUNT FELL FROM THE BALCONY", 122, 34);
  }
}

function getSceneCollisions(scene) {
  if (scene === "balcony") {
    // Smooth movement across the entire stone balcony terrace; pushing past minY triggers fall
    return {
      bounds: { minX: 30, maxX: 450, minY: 152, maxY: 254 },
      boxes: [{ x: 224, y: 188, w: 32, h: 30 }],
    };
  }
  if (scene === "kitchen") {
    return {
      bounds: { minX: 28, maxX: 452, minY: 74, maxY: 244 },
      boxes: [
        { x: 48, y: 94, w: 124, h: 36 },
        { x: 48, y: 178, w: 110, h: 34 },
        { x: 186, y: 216, w: 52, h: 30 },
        { x: 392, y: 164, w: 52, h: 56 },
      ],
    };
  }
  // Grand Banquet Hall (960x540) — solid banquet tables, dais, statues, fireplace
  return {
    bounds: { minX: 42, maxX: 882, minY: 82, maxY: 502 },
    boxes: [
      { x: 372, y: 90,  w: 216, h: 34 }, // Royal High Table
      { x: 116, y: 201, w: 156, h: 42 }, // House Vantrell Table
      { x: 688, y: 201, w: 156, h: 42 }, // Foreign Delegation Table
      { x: 126, y: 386, w: 136, h: 40 }, // House Marrow Table
      { x: 882, y: 274, w: 48,  h: 98 }, // Grand Fireplace
    ],
  };
}

function tryMovePlayer(nx, ny, cfg) {
  const cx = Math.max(cfg.bounds.minX, Math.min(cfg.bounds.maxX, nx));
  const cy = Math.max(cfg.bounds.minY, Math.min(cfg.bounds.maxY, ny));
  const blocked = (px, py) => cfg.boxes.some(b => px + 7 > b.x && px - 7 < b.x + b.w && py + 6 > b.y && py - 6 < b.y + b.h);
  if (!blocked(cx, player.y)) player.x = cx;
  if (!blocked(player.x, cy)) player.y = cy;
}

function updatePlayerMovement() {
  const scene = gameState ? gameState.current_scene : "party_floor";
  const cfg = getSceneCollisions(scene);
  let dx = 0, dy = 0;
  if (keys["w"] || keys["arrowup"])    { dy -= player.speed; player.dir = 1; }
  if (keys["s"] || keys["arrowdown"])  { dy += player.speed; player.dir = 0; }
  if (keys["a"] || keys["arrowleft"])  { dx -= player.speed; player.dir = 2; }
  if (keys["d"] || keys["arrowright"]) { dx += player.speed; player.dir = 3; }

  if (dx !== 0 || dy !== 0) {
    player.targetX = null; player.targetY = null;
    tryMovePlayer(player.x + dx, player.y + dy, cfg);
    player.moving = true;
    if (scene === "balcony" && dy < 0 && player.y <= cfg.bounds.minY + 1) {
      balconyEdgePush++;
      if (balconyEdgePush === 18) {
        controlsHint.textContent = "⚠ Careful! Keep pushing over the balustrade and you will fall!";
      }
      if (balconyEdgePush >= 52 && gameState && gameState.current_act === "act2") {
        balconyFallTick = 0;
        gameState.current_act = "ending_balcony";
        appendMsg("narration", "You lean too far over the slick stone balustrade, lose your footing, and plunge into the moonlit valley below.");
        syncHUD();
      }
    } else {
      balconyEdgePush = Math.max(0, balconyEdgePush - 2);
    }
  } else if (player.targetX !== null) {
    const tx = player.targetX - player.x, ty = player.targetY - player.y;
    const dist = Math.hypot(tx, ty);
    if (dist < 2.5) { player.targetX = null; player.targetY = null; player.moving = false; }
    else {
      const prevX = player.x, prevY = player.y;
      tryMovePlayer(player.x + (tx / dist) * player.speed, player.y + (ty / dist) * player.speed, cfg);
      if (Math.hypot(player.x - prevX, player.y - prevY) < 0.2) { player.targetX = null; player.targetY = null; player.moving = false; }
      else { player.dir = tx < 0 ? 2 : 3; player.moving = true; }
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
    if (ev.type === "npc") appendMsg("npc", `<strong>${ev.speaker}:</strong> ${ev.text}`);
    else appendMsg(ev.type || "system", ev.text);
  }
}

function selectNpc(id) { activeNpc = id; drawPortrait(id); }

function syncHUD() {
  if (!gameState) return;
  document.getElementById("hudAct").textContent = gameState.current_act.toUpperCase();
  document.getElementById("hudTime").textContent = gameState.time_str;
  document.getElementById("hudEvidence").textContent = gameState.evidence_log.length;

  quickActions.innerHTML = "";
  stationBar.innerHTML = "";
  const act = gameState.current_act;

  if (act === "prologue") {
    const beat = PROLOGUE_BEATS[Math.min(prologueStep, PROLOGUE_BEATS.length - 1)];
    controlsHint.textContent = `Prologue (${prologueStep + 1}/${PROLOGUE_BEATS.length}) — Experience the Sight`;
    addQuickBtn(beat.btn, async () => {
      if (prologueStep < PROLOGUE_BEATS.length - 1) {
        prologueStep++;
        const nextBeat = PROLOGUE_BEATS[prologueStep];
        appendMsg(nextBeat.type, nextBeat.text);
        syncHUD();
      } else {
        const data = await post("/api/advance_prologue", { session_id: sessionId });
        applyResponse(data);
        selectNpc("aldous");
      }
    }, "primary");
  } else if (act === "act0") {
    controlsHint.textContent = "Act 0: Speak freely with Aldous, or arrive at the estate";
    selectNpc("aldous");
    addQuickBtn("Arrive at Estate →", async () => {
      const data = await post("/api/finish_act0", { session_id: sessionId });
      applyResponse(data); selectNpc("reynard");
    }, "primary");
  } else if (act === "act1") {
    controlsHint.textContent = "Act 1: Speak freely with Reynard on the steps, or step inside";
    selectNpc("reynard");
    addQuickBtn("Enter the Main Hall →", async () => {
      const data = await post("/api/enter_hall", { session_id: sessionId });
      player.x = 480; player.y = 460; player.targetX = null; player.targetY = null;
      applyResponse(data); selectNpc("fenwick");
    }, "primary");
  } else if (act === "act2") {
    controlsHint.textContent = "WASD / Arrows or Click to explore the Grand Hall · Approach any table to talk";
    for (const [sid, label] of [["party_floor", "Main Hall"], ["kitchen", "Kitchen & Cellar"], ["balcony", "The Balcony"]]) {
      const b = document.createElement("button");
      b.textContent = label;
      b.onclick = async () => {
        if (sid === "party_floor") {
          gameState.current_scene = "party_floor";
          player.x = 480; player.y = 460; player.targetX = null; player.targetY = null;
          syncHUD(); return;
        }
        const data = await post("/api/visit_station", { session_id: sessionId, target: sid });
        if (sid === "kitchen") { player.x = 240; player.y = 195; selectNpc("mrs_alwen"); }
        if (sid === "balcony") { player.x = 240; player.y = 240; balconyEdgePush = 0; }
        player.targetX = null; player.targetY = null;
        applyResponse(data);
      };
      stationBar.appendChild(b);
    }
    if (gameState.current_scene === "kitchen") {
      addQuickBtn("🔍 Inspect Wine Seal", async () => {
        const data = await post("/api/inspect_cellar", { session_id: sessionId, target: "SEAL" });
        applyResponse(data);
      });
      addQuickBtn("📒 Inspect Cellar Log", async () => {
        const data = await post("/api/inspect_cellar", { session_id: sessionId, target: "LOG" });
        applyResponse(data);
      });
      addQuickBtn("🔍 Inspect Both", async () => {
        const data = await post("/api/inspect_cellar", { session_id: sessionId, target: "BOTH" });
        applyResponse(data);
      }, "primary");
    }
    addQuickBtn("🍷 Head to the Toast (Act 3)", async () => {
      const data = await post("/api/start_act3", { session_id: sessionId });
      applyResponse(data); selectNpc("duke");
    }, "danger");
  } else if (act === "act3") {
    const phase = gameState.act3_phase || "confrontation";
    const turns = gameState.act3_turns || 0;
    if (phase === "confrontation") {
      controlsHint.textContent = `ACT 3 TOAST (Turn ${turns}/6) — Interrupt with evidence/action, or stay silent to let the toast proceed`;
      addQuickBtn("🤫 Stay Silent / Let Toast Proceed", async () => {
        const data = await post("/api/act3_action", { session_id: sessionId, npc_id: "duke", message: "" });
        applyResponse(data);
      }, "danger");
      addQuickBtn("✋ Grab / Intercept Glass", async () => {
        const data = await post("/api/act3_action", { session_id: sessionId, npc_id: "duke", message: "I step between them and grab the glass from Isolde!" });
        applyResponse(data);
      }, "primary");
    } else {
      controlsHint.textContent = `ACT 3 AFTERMATH (${phase.replace("_", " ").toUpperCase()}) — Speak, or continue in silence`;
      addQuickBtn("Continue / Say Nothing →", async () => {
        const data = await post("/api/act3_action", { session_id: sessionId, npc_id: "duke", message: "" });
        applyResponse(data);
      }, "primary");
    }
  } else if (act.startsWith("ending_")) {
    controlsHint.textContent = `THE END — ${act.toUpperCase()}`;
    const delay = (act === "ending_d" || act === "ending_f" || act === "ending_balcony") ? 2200 : 0;
    if (delay > 0) setTimeout(() => { if (gameState && gameState.current_act === act) showEndingModal(act); }, delay);
    else showEndingModal(act);
  }
}

const ENDING_TITLES = {
  ending_a: "ENDING A — FULL VICTORY",
  ending_b: "ENDING B — PYRRHIC VICTORY",
  ending_c: "ENDING C — THE WRONG TARGET",
  ending_d: "ENDING D — THE DUNGEON",
  ending_e: "ENDING E — THE CONSPIRACY CODA",
  ending_f: "ENDING F — TOTAL FAILURE",
  ending_g: "ENDING G — SELF-SACRIFICE",
  ending_balcony: "GAME OVER — FATAL FALL FROM BALCONY",
};

let shownEnding = null;
function showEndingModal(act) {
  if (shownEnding === act) return;
  shownEnding = act;
  document.getElementById("endingTitle").textContent = ENDING_TITLES[act] || act.toUpperCase();
  const evCount = (gameState.evidence_log || []).length;
  const evScore = gameState.evidence_score || 0;
  const flags = gameState.flags || {};
  const milestones = [
    ["reynard_met_warmly", "Connected with Reynard's grief"],
    ["isolde_will_avoid_wine", "Earned Lady Isolde's trust"],
    ["wine_seal_discovered", "Detected the altered wine seal"],
    ["cellar_log_found", "Found Reynard's cellar log entry"],
    ["balcony_vision_seen", "Witnessed the twilight balcony vision"],
    ["ophelia_caught", "Apprehended Ophelia Vantrell"],
    ["reynard_testified", "Reynard gave a full public confession"],
    ["easter_egg_activated", "Infiltrated via the harvest passphrase"],
  ].filter(([k]) => flags[k]).map(([, label]) => `<div class="ev-item">✓ ${label}</div>`).join("");
  document.getElementById("endingBody").innerHTML = `
    <div class="msg narration">Final Time: <strong>${gameState.time_str}</strong> · Clues Recorded: <strong>${evCount}</strong> (${evScore}/7 vital links)</div>
    ${milestones || '<div class="msg system">A quiet evening with minimal overt interventions.</div>'}
  `;
  document.getElementById("endingModal").classList.add("open");
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
    const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    return await r.json();
  } finally { busy = false; }
}

function applyResponse(data) {
  if (data.state) gameState = data.state;
  renderEvents(data.events);
  syncHUD();
}

function playTurns(turns, events) {
  cancelGroupQueue(false);
  if (!turns || !turns.length) { renderEvents(events); return; }
  const first = turns[0];
  selectNpc(first.speaker_id);
  appendMsg("npc", `<strong>${first.speaker_name}:</strong> ${first.text}`);

  if (turns.length > 1) {
    groupQueue = turns.slice(1);
    btnInterrupt.style.display = "inline-block";
    const scheduleNext = () => {
      if (!groupQueue.length) { btnInterrupt.style.display = "none"; renderEvents(events); return; }
      groupTimer = setTimeout(() => {
        const next = groupQueue.shift();
        if (next) { selectNpc(next.speaker_id); appendMsg("npc", `<strong>${next.speaker_name}:</strong> ${next.text}`); }
        scheduleNext();
      }, 1700);
    };
    scheduleNext();
  } else {
    renderEvents(events);
  }
}

talkForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (busy || !gameState) return;
  cancelGroupQueue(false);
  const msg = playerInput.value.trim();
  if (!msg && gameState.current_act !== "act3") return;
  playerInput.value = "";
  if (msg) appendMsg("player", `<strong>You:</strong> ${msg}`);

  if (gameState.current_act === "act3") {
    const data = await post("/api/act3_action", { session_id: sessionId, npc_id: "duke", message: msg });
    applyResponse(data);
  } else {
    const data = await post("/api/talk", { session_id: sessionId, npc_id: activeNpc, message: msg });
    if (data.turns && data.turns.length) {
      if (data.state) gameState = data.state;
      playTurns(data.turns, data.events);
      syncHUD();
    } else {
      if (data.reply) {
        const label = (CHAR_STYLE[activeNpc] || { label: activeNpc }).label;
        appendMsg("npc", `<strong>${label}:</strong> ${data.reply}`);
      }
      applyResponse(data);
    }
  }
});

document.getElementById("btnLog").onclick = () => {
  const list = document.getElementById("evidenceList");
  list.innerHTML = "";
  const evs = (gameState && gameState.evidence_log) || [];
  if (!evs.length) list.innerHTML = `<div class="msg system">Nothing recorded yet.</div>`;
  else evs.forEach((item, i) => { const d = document.createElement("div"); d.className = "ev-item"; d.textContent = `${i + 1}. ${item}`; list.appendChild(d); });
  document.getElementById("evidenceModal").classList.add("open");
};
document.getElementById("btnCloseModal").onclick = () => document.getElementById("evidenceModal").classList.remove("open");
document.getElementById("btnCloseEnding").onclick = () => document.getElementById("endingModal").classList.remove("open");
document.getElementById("btnEndingNew").onclick = () => { document.getElementById("endingModal").classList.remove("open"); startNewGame(); };
document.getElementById("btnNew").onclick = startNewGame;

async function startNewGame() {
  cancelGroupQueue(false);
  shownEnding = null;
  balconyEdgePush = 0;
  balconyFallTick = 0;
  cam = { x: 0, y: 0 };
  player.x = 240; player.y = 180; player.targetX = null; player.targetY = null;
  chatLog.innerHTML = "";
  prologueStep = 0;
  const data = await post("/api/new_game", {});
  sessionId = data.session_id;
  gameState = data.state;
  appendMsg(PROLOGUE_BEATS[0].type, PROLOGUE_BEATS[0].text);
  selectNpc("viscount");
  syncHUD();
}

startNewGame();
requestAnimationFrame(renderScene);
