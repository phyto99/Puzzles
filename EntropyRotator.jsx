import { useState, useMemo, useCallback, useEffect } from "react";

// ═══════════════════════════════════════════════════════════════
// SHARED REGISTRY  —  keep in sync with static/entropy_engine.js
// ═══════════════════════════════════════════════════════════════
// Same STORAGE_KEY so EntropyRotator and app_v2 share live state.
const STORAGE_KEY = 'entropy_state_v2';

const PUZZLE_REGISTRY = {
  raven:     { name:"I-RAVEN",      cluster:"rule_induction", cognitiveLoad:0.90, ruleVolatility:0.95, surface:["grid","color","pattern"],
               subtypes:[{id:"standard",label:"Standard"},{id:"mesh",label:"Mesh",cogLoad:0.95,volatility:0.98}] },
  pgm:       { name:"PGM",          cluster:"rule_induction", cognitiveLoad:0.85, ruleVolatility:0.88, surface:["grid","abstract","pattern"],
               subtypes:[{id:"mixed",label:"Mixed"}] },
  marvel:    { name:"MARVEL",       cluster:"rule_induction", cognitiveLoad:0.80, ruleVolatility:0.82, surface:["image","abstract","multi-modal"],
               subtypes:[
                 {id:"Temporal Movement",   label:"Temporal Movement",   cogLoad:0.78,volatility:0.80},
                 {id:"Spatial Relationship",label:"Spatial Relationship",cogLoad:0.80,volatility:0.82},
                 {id:"Quantities",          label:"Quantities",          cogLoad:0.75,volatility:0.78},
                 {id:"2D-Geometry",         label:"2D Geometry",         cogLoad:0.82,volatility:0.85},
                 {id:"3D-Geometry",         label:"3D Geometry",         cogLoad:0.88,volatility:0.90},
                 {id:"Mathematical",        label:"Mathematical",        cogLoad:0.85,volatility:0.88},
               ]},
  bongard:   { name:"Bongard",      cluster:"rule_induction", cognitiveLoad:0.75, ruleVolatility:0.80, surface:["abstract","rule","classification"],
               subtypes:[{id:"mixed",label:"Mixed"}] },
  puzzlevqa: { name:"PuzzleVQA",    cluster:"spatial_2d",     cognitiveLoad:0.72, ruleVolatility:0.75, surface:["pattern","visual","counting"],
               subtypes:[
                 {id:"color_grid",          label:"Color Grid",      cogLoad:0.68,volatility:0.72},
                 {id:"shape_morph",         label:"Shape Morph",     cogLoad:0.72,volatility:0.75},
                 {id:"grid_number",         label:"Grid Number",     cogLoad:0.75,volatility:0.78},
                 {id:"venn",                label:"Venn",            cogLoad:0.70,volatility:0.74},
                 {id:"size_cycle",          label:"Size Cycle",      cogLoad:0.72,volatility:0.76},
                 {id:"polygon_sides_number",label:"Polygon Sides",   cogLoad:0.68,volatility:0.72},
                 {id:"numbers_triangle",    label:"Number Triangle", cogLoad:0.78,volatility:0.82},
               ]},
  acre:      { name:"ACRE",         cluster:"constraint_sat", cognitiveLoad:0.82, ruleVolatility:0.85, surface:["3d","causal","scene"],
               subtypes:[
                 {id:"IID", label:"IID",          cogLoad:0.75,volatility:0.80},
                 {id:"Comp",label:"Compositional",cogLoad:0.85,volatility:0.88},
                 {id:"Sys", label:"Systematic",   cogLoad:0.88,volatility:0.92},
               ]},
  clevr:     { name:"CLEVR",        cluster:"constraint_sat", cognitiveLoad:0.70, ruleVolatility:0.72, surface:["3d","counting","attribute"],
               subtypes:[{id:"mixed",label:"Mixed"}] },
  arc:       { name:"ARC-AGI",      cluster:"rule_induction", cognitiveLoad:0.92, ruleVolatility:0.96, surface:["grid","color","transformation"],
               subtypes:[
                 {id:"arc2",label:"ARC-AGI-2",cogLoad:0.95,volatility:0.98},
                 {id:"arc1",label:"ARC-AGI-1",cogLoad:0.88,volatility:0.92},
               ]},
  arc3:      { name:"ARC-AGI-3",    cluster:"adversarial",    cognitiveLoad:0.95, ruleVolatility:0.97, surface:["interactive","exploration","grid"],
               subtypes:[{id:"any",label:"Any Environment"}] },
  rlp:       { name:"RLP (Tatham)", cluster:"constraint_sat", cognitiveLoad:0.80, ruleVolatility:0.75, surface:["logic","puzzle","interactive"],
               subtypes:[
                 {id:"flood",   label:"Flood",       cogLoad:0.65,volatility:0.60},
                 {id:"net",     label:"Net",         cogLoad:0.72,volatility:0.70},
                 {id:"flip",    label:"Flip",        cogLoad:0.68,volatility:0.65},
                 {id:"fifteen", label:"Fifteen",     cogLoad:0.80,volatility:0.78},
                 {id:"bridges", label:"Bridges",     cogLoad:0.78,volatility:0.75},
                 {id:"loopy",   label:"Loopy",       cogLoad:0.82,volatility:0.80},
                 {id:"slant",   label:"Slant",       cogLoad:0.75,volatility:0.72},
                 {id:"signpost",label:"Signpost",    cogLoad:0.85,volatility:0.82},
                 {id:"untangle",label:"Untangle",    cogLoad:0.78,volatility:0.76},
                 {id:"pattern", label:"Nonogram",    cogLoad:0.88,volatility:0.85},
                 {id:"rect",    label:"Rectangles",  cogLoad:0.72,volatility:0.70},
                 {id:"solo",    label:"Sudoku",      cogLoad:0.85,volatility:0.65},
                 {id:"mines",   label:"Minesweeper", cogLoad:0.70,volatility:0.68},
               ]},
};

const GAMES = Object.entries(PUZZLE_REGISTRY).map(([id, reg]) => ({
  id,
  name:           reg.name,
  cluster:        reg.cluster,
  cognitiveLoad:  reg.cognitiveLoad,
  ruleVolatility: reg.ruleVolatility,
  surface:        reg.surface,
  subtypes:       reg.subtypes,
}));

// ═══════════════════════════════════════════════════════════════
// COGNITIVE CLUSTER DEFINITIONS
// ═══════════════════════════════════════════════════════════════
const CLUSTERS = {
  rule_induction: { label:"Rule Induction",  hex:"#1D9E75" },
  spatial_3d:     { label:"3D / 4D Spatial", hex:"#D85A30" },
  spatial_2d:     { label:"2D Spatial",      hex:"#7F77DD" },
  constraint_sat: { label:"Constraint Sat.", hex:"#BA7517" },
  adversarial:    { label:"Adversarial",     hex:"#378ADD" },
};

const INTERFERENCE = {
  rule_induction: { rule_induction:0.04, spatial_3d:0.95, spatial_2d:0.45, constraint_sat:0.80, adversarial:0.92 },
  spatial_3d:     { rule_induction:0.95, spatial_3d:0.04, spatial_2d:0.70, constraint_sat:0.82, adversarial:0.68 },
  spatial_2d:     { rule_induction:0.45, spatial_3d:0.70, spatial_2d:0.04, constraint_sat:0.65, adversarial:0.88 },
  constraint_sat: { rule_induction:0.80, spatial_3d:0.82, spatial_2d:0.65, constraint_sat:0.04, adversarial:0.78 },
  adversarial:    { rule_induction:0.92, spatial_3d:0.68, spatial_2d:0.88, constraint_sat:0.78, adversarial:0.04 },
};

// ═══════════════════════════════════════════════════════════════
// CORE ENGINE  —  pure functions
// ═══════════════════════════════════════════════════════════════

export function decayedFamiliarity(fam, lastPlayed, volatility) {
  const days = (Date.now() - lastPlayed) / 86_400_000;
  return fam * Math.exp(-volatility * 0.25 * days);
}

export function reconstructionScore(game, userState) {
  const s = userState[game.id];
  if (!s) return 0;
  const fam = decayedFamiliarity(s.familiarity, s.lastPlayed, game.ruleVolatility);
  let zoneScore;
  if (fam < 0.15)      zoneScore = 0.30;
  else if (fam > 0.78) zoneScore = 0.10;
  else                 zoneScore = 1.0 - Math.abs(fam - 0.42) / 0.45;
  return zoneScore * game.ruleVolatility * game.cognitiveLoad;
}

export function interferenceBetween(idA, idB) {
  const a = GAMES.find(g => g.id === idA)?.cluster;
  const b = GAMES.find(g => g.id === idB)?.cluster;
  return (a && b) ? (INTERFERENCE[a]?.[b] ?? 0.5) : 0.5;
}

export function buildSession(games, userState, size = 6) {
  const pool = games
    .map(g => ({
      game:  g,
      fam:   decayedFamiliarity(userState[g.id]?.familiarity ?? 0.1,
                                 userState[g.id]?.lastPlayed ?? (Date.now() - 86400000),
                                 g.ruleVolatility),
      score: reconstructionScore(g, userState),
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, Math.min(size * 2, games.length));

  if (!pool.length) return { seq: [], interferences: [], entropy: 0 };

  const seq = [pool[0]];
  const rem = new Set(pool.slice(1).map(p => p.game.id));

  while (seq.length < Math.min(size, pool.length)) {
    let bestId = null, bestVal = -1;
    const lastId = seq[seq.length - 1].game.id;
    for (const id of rem) {
      const c   = pool.find(p => p.game.id === id);
      const val = c.score * interferenceBetween(lastId, id);
      if (val > bestVal) { bestVal = val; bestId = id; }
    }
    if (!bestId) break;
    seq.push(pool.find(p => p.game.id === bestId));
    rem.delete(bestId);
  }

  const interferences = seq.slice(0, -1).map((item, i) =>
    interferenceBetween(item.game.id, seq[i + 1].game.id)
  );
  const entropy = interferences.length
    ? interferences.reduce((a, b) => a + b, 0) / interferences.length
    : 0;

  return { seq, interferences, entropy };
}

export function recordPlay(userState, gameId, gain = 0.15) {
  const s = userState[gameId];
  if (!s) return userState;
  return {
    ...userState,
    [gameId]: {
      ...s,
      familiarity: Math.min(1, s.familiarity + gain),
      lastPlayed:  Date.now(),
      sessions:    s.sessions + 1,
    },
  };
}

// ═══════════════════════════════════════════════════════════════
// LOAD STATE from localStorage (shared with app_v2.html)
// ═══════════════════════════════════════════════════════════════

function loadEntropyState() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
  catch { return {}; }
}

// Aggregate per-subtype state into a game-level summary
function aggregateGameState(gameId) {
  const reg   = PUZZLE_REGISTRY[gameId];
  if (!reg) return null;
  const state = loadEntropyState();

  const rows = reg.subtypes.map(st => {
    const s   = state[`${gameId}::${st.id}`];
    const vol = st.volatility ?? reg.ruleVolatility;
    if (!s) return { fam: 0.5, lastPlayed: Date.now() - 7 * 86_400_000, sessions: 0 };
    return {
      fam:       decayedFamiliarity(s.familiarity, s.lastPlayed, vol),
      lastPlayed: s.lastPlayed,
      sessions:  s.sessions,
    };
  });

  return {
    familiarity: Math.min(...rows.map(r => r.fam)),
    lastPlayed:  Math.max(...rows.map(r => r.lastPlayed)),
    sessions:    rows.reduce((a, r) => a + r.sessions, 0),
  };
}

function initUserState(games) {
  // Try to load real data from localStorage first
  const real = {};
  let hasRealData = false;
  games.forEach(g => {
    const agg = aggregateGameState(g.id);
    if (agg) { real[g.id] = agg; hasRealData = true; }
  });
  if (hasRealData) return real;

  // Fallback: seeded demo values if no history yet
  const famSeeds  = [0.55, 0.78, 0.42, 0.30, 0.65, 0.18, 0.82, 0.48, 0.36, 0.72];
  const daySeeds  = [0.5,  1.2,  2.0,  3.1,  0.8,  4.5,  1.7,  2.8,  1.1,  3.5];
  const sessSeeds = [8,    12,   5,    3,    9,    2,    15,   7,    4,    11];
  const s = {};
  games.forEach((g, i) => {
    s[g.id] = {
      familiarity: famSeeds[i % famSeeds.length],
      lastPlayed:  Date.now() - daySeeds[i % daySeeds.length] * 86_400_000,
      sessions:    sessSeeds[i % sessSeeds.length],
    };
  });
  return s;
}

// ═══════════════════════════════════════════════════════════════
// UI HELPERS
// ═══════════════════════════════════════════════════════════════

function interferenceColor(v) {
  if (v > 0.75) return "#1D9E75";
  if (v > 0.45) return "#BA7517";
  return "#E24B4A";
}

function famZone(fam) {
  if (fam < 0.15) return { label:"forgotten",     color:"#E24B4A" };
  if (fam > 0.78) return { label:"comfortable",   color:"#1D9E75" };
  return               { label:"reconstruction",  color:"#EF9F27" };
}

// ── Mini decay sparkline ─────────────────────────────────────
function DecaySparkline({ fam, volatility }) {
  const W = 60, H = 18;
  const pts = Array.from({ length: 15 }, (_, d) => {
    const f = fam * Math.exp(-volatility * 0.25 * d);
    return `${(d / 14) * W},${H - f * H}`;
  }).join(" ");
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ overflow:"visible", display:"block" }}>
      <rect x={0} y={H - 0.78 * H} width={W} height={(0.78 - 0.15) * H} fill="#EF9F2720" />
      <polyline points={pts} fill="none" stroke="#EF9F27" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={0} cy={H - fam * H} r="2" fill="#EF9F27" />
    </svg>
  );
}

// ── Subtype expansion panel ─────────────────────────────────
function SubtypePanel({ game, liveState }) {
  const state = loadEntropyState();
  const rows = game.subtypes.map(st => {
    const key = `${game.id}::${st.id}`;
    const s   = state[key];
    const vol = st.volatility ?? game.ruleVolatility;
    const cl  = st.cogLoad    ?? game.cognitiveLoad;
    const fam = s ? decayedFamiliarity(s.familiarity, s.lastPlayed, vol) : 0.5;
    const zone = famZone(fam);
    const wins = s?.wins ?? 0, losses = s?.losses ?? 0;
    return { st, fam, zone, wins, losses };
  }).sort((a, b) => b.fam - a.fam);

  const mono = "var(--font-mono)";
  return (
    <div style={{ padding:"6px 10px 4px 24px", borderLeft:"2px solid #eee", marginTop:4 }}>
      {rows.map(({ st, fam, zone, wins, losses }) => (
        <div key={st.id} style={{ display:"flex", alignItems:"center", gap:6, marginBottom:3 }}>
          <span style={{ fontSize:9, color:"#888", minWidth:100, fontFamily:mono }}>{st.label}</span>
          <div style={{ position:"relative", flex:1, height:4, background:"#eee", borderRadius:2, maxWidth:80 }}>
            <div style={{ position:"absolute", left:0, width:`${fam*100}%`, height:"100%", background:zone.color, borderRadius:2 }} />
          </div>
          <span style={{ fontSize:9, color:"#aaa", minWidth:22, fontFamily:mono }}>{(fam*100).toFixed(0)}%</span>
          <span style={{ fontSize:8, color:"#bbb", fontFamily:mono }}>{wins}W/{losses}L</span>
        </div>
      ))}
    </div>
  );
}

// ── Add game form ────────────────────────────────────────────
function AddGameForm({ onAdd, onCancel }) {
  const [form, setForm] = useState({ name:"", cluster:"rule_induction", cognitiveLoad:0.75, ruleVolatility:0.75 });
  const f  = (k) => (e) => setForm(p => ({ ...p, [k]: e.target.value }));
  const fN = (k) => (e) => setForm(p => ({ ...p, [k]: +e.target.value }));
  const submit = () => { if (form.name.trim()) onAdd(form); };

  const mono = "var(--font-mono)";
  const row  = { display:"flex", alignItems:"center", gap:8 };
  const lbl  = { fontSize:11, color:"var(--color-text-secondary)", width:110, flexShrink:0, fontFamily:mono };
  const val  = { fontSize:11, color:"var(--color-text-tertiary)", minWidth:24, textAlign:"right", fontFamily:mono };

  return (
    <div style={{ border:"0.5px solid var(--color-border-secondary)", borderRadius:8, padding:"12px 14px", marginBottom:12, background:"var(--color-background-secondary)" }}>
      <input placeholder="puzzle type name" value={form.name} onChange={f("name")}
        style={{ width:"100%", marginBottom:8, fontSize:13, padding:"6px 8px", background:"var(--color-background-primary)", border:"0.5px solid var(--color-border-secondary)", borderRadius:4, color:"var(--color-text-primary)", fontFamily:mono, boxSizing:"border-box" }} />
      <select value={form.cluster} onChange={f("cluster")}
        style={{ width:"100%", marginBottom:8, fontSize:12, padding:"6px 8px", background:"var(--color-background-primary)", border:"0.5px solid var(--color-border-secondary)", borderRadius:4, color:"var(--color-text-primary)", fontFamily:mono }}>
        {Object.entries(CLUSTERS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
      </select>
      <div style={{ ...row, marginBottom:6 }}>
        <span style={lbl}>cognitive load</span>
        <input type="range" min="0.1" max="1" step="0.05" value={form.cognitiveLoad} onChange={fN("cognitiveLoad")} style={{ flex:1 }} />
        <span style={val}>{(form.cognitiveLoad * 100).toFixed(0)}</span>
      </div>
      <div style={{ ...row, marginBottom:10 }}>
        <span style={lbl}>rule volatility</span>
        <input type="range" min="0.1" max="1" step="0.05" value={form.ruleVolatility} onChange={fN("ruleVolatility")} style={{ flex:1 }} />
        <span style={val}>{(form.ruleVolatility * 100).toFixed(0)}</span>
      </div>
      <div style={{ display:"flex", gap:8 }}>
        <button onClick={submit} style={{ flex:1, padding:"5px 0", background:"none", border:"0.5px solid var(--color-border-primary)", borderRadius:4, color:"var(--color-text-primary)", cursor:"pointer", fontSize:12, fontFamily:mono }}>register</button>
        <button onClick={onCancel} style={{ flex:1, padding:"5px 0", background:"none", border:"0.5px solid var(--color-border-tertiary)", borderRadius:4, color:"var(--color-text-secondary)", cursor:"pointer", fontSize:12, fontFamily:mono }}>cancel</button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════
export default function EntropyRotator() {
  const [games, setGames]         = useState(GAMES);
  const [userState, setUserState] = useState(() => initUserState(GAMES));
  const [sessionSize, setSessionSize] = useState(6);
  const [showAdd, setShowAdd]     = useState(false);
  const [playedIds, setPlayedIds] = useState(new Set());
  const [showMatrix, setShowMatrix] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [tick, setTick]           = useState(0); // forces re-render on localStorage change

  // Sync with localStorage on mount and after plays
  useEffect(() => {
    const freshState = initUserState(games);
    setUserState(freshState);
  }, [tick]);

  const session = useMemo(
    () => buildSession(games, userState, sessionSize),
    [games, userState, sessionSize]
  );

  const allScored = useMemo(() =>
    games.map(g => {
      const s    = userState[g.id] ?? {};
      const fam  = decayedFamiliarity(s.familiarity ?? 0, s.lastPlayed ?? Date.now(), g.ruleVolatility);
      return {
        game:     g,
        fam,
        score:    reconstructionScore(g, userState),
        days:     ((Date.now() - (s.lastPlayed ?? Date.now())) / 86_400_000).toFixed(1),
        sessions: s.sessions ?? 0,
      };
    }).sort((a, b) => b.score - a.score),
    [games, userState]
  );

  const markPlayed = useCallback((gameId) => {
    setPlayedIds(p => new Set([...p, gameId]));
    setUserState(prev => recordPlay(prev, gameId));
    // Also write back to localStorage for app_v2.html to pick up
    try {
      const state = loadEntropyState();
      const g     = games.find(x => x.id === gameId);
      if (g) {
        g.subtypes.forEach(st => {
          const key = `${gameId}::${st.id}`;
          const s   = state[key] ?? { familiarity:0.5, lastPlayed:Date.now()-86400000, wins:0, losses:0, sessions:0 };
          state[key] = { ...s, familiarity: Math.min(1, s.familiarity + 0.15), lastPlayed: Date.now(), sessions: s.sessions + 1 };
        });
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      }
    } catch(e) {}
    setTick(t => t + 1);
  }, [games]);

  const handleAddGame = useCallback((form) => {
    const id = form.name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
    const newGame = { id, name:form.name, cluster:form.cluster, cognitiveLoad:form.cognitiveLoad,
                      ruleVolatility:form.ruleVolatility, surface:[], subtypes:[{id:"mixed",label:"Mixed"}] };
    setGames(prev => [...prev, newGame]);
    setUserState(prev => ({
      ...prev,
      [id]: { familiarity:0.05, lastPlayed: Date.now() - 7 * 86_400_000, sessions:0 },
    }));
    setShowAdd(false);
  }, []);

  const resetSession = () => setPlayedIds(new Set());

  const mono        = "var(--font-mono)";
  const capsLabel   = { fontSize:10, color:"var(--color-text-tertiary)", letterSpacing:"0.1em", fontFamily:mono };

  return (
    <div style={{ fontFamily:mono, maxWidth:960, margin:"0 auto", padding:"4px 0 16px" }}>

      {/* ── header ── */}
      <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:18, borderBottom:"0.5px solid var(--color-border-tertiary)", paddingBottom:10 }}>
        <span style={{ ...capsLabel, fontSize:11 }}>ENTROPY ROTATION PROTOCOL</span>
        <div style={{ flex:1 }} />
        <span style={capsLabel}>SESSION ENTROPY</span>
        <span style={{ fontSize:16, fontWeight:500, color:interferenceColor(session.entropy), fontFamily:mono }}>
          {(session.entropy * 100).toFixed(0)}%
        </span>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"minmax(0,1fr) minmax(0,1.15fr)", gap:20 }}>

        {/* ── LEFT: game registry ── */}
        <div>
          <div style={{ display:"flex", alignItems:"center", marginBottom:10 }}>
            <span style={capsLabel}>PUZZLE REGISTRY</span>
            <button onClick={() => setShowAdd(s => !s)}
              style={{ marginLeft:"auto", fontSize:10, padding:"3px 9px", background:"none", border:"0.5px solid var(--color-border-secondary)", borderRadius:4, color:"var(--color-text-secondary)", cursor:"pointer", fontFamily:mono }}>
              {showAdd ? "cancel" : "+ add type"}
            </button>
          </div>

          {showAdd && <AddGameForm onAdd={handleAddGame} onCancel={() => setShowAdd(false)} />}

          <div style={{ display:"flex", flexDirection:"column", gap:5 }}>
            {allScored.map(({ game, fam, score, days, sessions }) => {
              const zone   = famZone(fam);
              const clr    = CLUSTERS[game.cluster]?.hex ?? "#888";
              const inQueue = session.seq.some(s => s.game.id === game.id);
              const isExpanded = expandedId === game.id;

              return (
                <div key={game.id}>
                  <div style={{
                    borderLeft:`2px solid ${clr}`,
                    border:`0.5px solid ${inQueue ? "var(--color-border-primary)" : "var(--color-border-tertiary)"}`,
                    borderLeftWidth:2, borderLeftColor:clr,
                    borderRadius:6, padding:"7px 10px",
                    background: inQueue ? "var(--color-background-secondary)" : "transparent",
                  }}>
                    <div style={{ display:"flex", alignItems:"baseline", gap:6, marginBottom:5 }}>
                      <span style={{ fontSize:13, fontWeight:500, color:"var(--color-text-primary)" }}>{game.name}</span>
                      {inQueue && <span style={{ fontSize:9, background:"var(--color-background-info)", color:"var(--color-text-info)", padding:"1px 5px", borderRadius:3 }}>queued</span>}
                      {game.subtypes.length > 1 && (
                        <button onClick={() => setExpandedId(isExpanded ? null : game.id)}
                          style={{ fontSize:9, padding:"1px 5px", background:"none", border:"0.5px solid var(--color-border-tertiary)", borderRadius:3, color:"var(--color-text-tertiary)", cursor:"pointer", fontFamily:mono }}>
                          {isExpanded ? "▾" : `${game.subtypes.length} types`}
                        </button>
                      )}
                      <span style={{ marginLeft:"auto", fontSize:9, color:"var(--color-text-tertiary)" }}>{days}d · {sessions}×</span>
                    </div>

                    {/* familiarity bar */}
                    <div style={{ position:"relative", height:4, background:"var(--color-border-tertiary)", borderRadius:2, marginBottom:4 }}>
                      <div style={{ position:"absolute", left:"15%", width:"63%", height:"100%", background:`${zone.color}22`, borderRadius:2 }} />
                      <div style={{ position:"absolute", left:0, width:`${fam * 100}%`, height:"100%", background:zone.color, borderRadius:2, transition:"width 0.4s" }} />
                      <div style={{ position:"absolute", left:"15%", top:-1, width:1, height:6, background:`${zone.color}66` }} />
                      <div style={{ position:"absolute", left:"78%", top:-1, width:1, height:6, background:`${zone.color}66` }} />
                    </div>

                    <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
                      <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                        <span style={{ fontSize:9, color:zone.color }}>{zone.label}</span>
                        <span style={{ fontSize:9, color:"var(--color-text-tertiary)" }}>fam {(fam*100).toFixed(0)}%</span>
                      </div>
                      <div style={{ display:"flex", alignItems:"center", gap:6 }}>
                        <DecaySparkline fam={fam} volatility={game.ruleVolatility} />
                        <span style={{ fontSize:9, color:"var(--color-text-tertiary)" }}>R {(score*100).toFixed(0)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Subtype expansion */}
                  {isExpanded && <SubtypePanel game={game} />}
                </div>
              );
            })}
          </div>

          {/* cluster legend */}
          <div style={{ marginTop:14, display:"flex", flexWrap:"wrap", gap:8 }}>
            {Object.entries(CLUSTERS).map(([k, v]) => (
              <div key={k} style={{ display:"flex", alignItems:"center", gap:4 }}>
                <div style={{ width:7, height:7, borderRadius:2, background:v.hex }} />
                <span style={{ fontSize:9, color:"var(--color-text-tertiary)" }}>{v.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── RIGHT: session queue ── */}
        <div>
          <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:10 }}>
            <span style={capsLabel}>SESSION QUEUE</span>
            <div style={{ display:"flex", alignItems:"center", gap:6, marginLeft:"auto" }}>
              <span style={capsLabel}>size</span>
              <input type="range" min="2" max={Math.min(games.length, 8)} step="1" value={sessionSize}
                onChange={e => { setSessionSize(+e.target.value); resetSession(); }}
                style={{ width:64 }} />
              <span style={{ fontSize:11, color:"var(--color-text-tertiary)", minWidth:12, fontFamily:mono }}>{sessionSize}</span>
            </div>
            <button onClick={resetSession}
              style={{ fontSize:10, padding:"3px 8px", background:"none", border:"0.5px solid var(--color-border-tertiary)", borderRadius:4, color:"var(--color-text-tertiary)", cursor:"pointer", fontFamily:mono }}>
              reset
            </button>
            <button onClick={() => setTick(t => t + 1)}
              style={{ fontSize:10, padding:"3px 8px", background:"none", border:"0.5px solid var(--color-border-tertiary)", borderRadius:4, color:"var(--color-text-tertiary)", cursor:"pointer", fontFamily:mono }}
              title="Reload from app_v2 history">
              sync
            </button>
          </div>

          <div style={{ display:"flex", flexDirection:"column", gap:0 }}>
            {session.seq.map((item, i) => {
              const { game, fam, score } = item;
              const clr    = CLUSTERS[game.cluster]?.hex ?? "#888";
              const played = playedIds.has(game.id);
              const iScore = i < session.interferences.length ? session.interferences[i] : null;

              // Best next subtype for this game
              const entropyState = loadEntropyState();
              const bestSt = game.subtypes.reduce((best, st) => {
                const s = entropyState[`${game.id}::${st.id}`];
                if (!s) return best;
                const vol = st.volatility ?? game.ruleVolatility;
                const cl  = st.cogLoad    ?? game.cognitiveLoad;
                const f   = decayedFamiliarity(s.familiarity, s.lastPlayed, vol);
                const sc  = (1 - Math.abs(f - 0.42) / 0.45) * vol * cl;
                return (!best || sc > best.sc) ? { st, sc } : best;
              }, null)?.st ?? game.subtypes[0];

              return (
                <div key={game.id}>
                  <div onClick={() => !played && markPlayed(game.id)}
                    style={{
                      display:"flex", alignItems:"center", gap:10,
                      border:"0.5px solid var(--color-border-tertiary)",
                      borderRadius:6, padding:"10px 12px",
                      background: played ? "var(--color-background-secondary)" : "var(--color-background-primary)",
                      cursor: played ? "default" : "pointer",
                      opacity: played ? 0.48 : 1,
                      transition:"opacity 0.3s",
                      userSelect:"none",
                    }}>
                    <span style={{ fontSize:11, color:"var(--color-text-tertiary)", minWidth:14, fontFamily:mono }}>{i + 1}</span>
                    <div style={{ width:7, height:7, borderRadius:1, background:clr, flexShrink:0 }} />
                    <div style={{ flex:1, minWidth:0 }}>
                      <div style={{ display:"flex", alignItems:"baseline", gap:6 }}>
                        <span style={{ fontSize:13, fontWeight:500, color:"var(--color-text-primary)" }}>{game.name}</span>
                        <span style={{ fontSize:9, color:clr, whiteSpace:"nowrap" }}>{bestSt.label}</span>
                        <span style={{ fontSize:9, color:"var(--color-text-tertiary)", whiteSpace:"nowrap" }}>{CLUSTERS[game.cluster]?.label}</span>
                      </div>
                      <div style={{ fontSize:9, color:"var(--color-text-tertiary)", marginTop:2, fontFamily:mono }}>
                        fam {(fam*100).toFixed(0)}% · vol {(game.ruleVolatility*100).toFixed(0)} · R {(score*100).toFixed(0)}
                        {played && <span style={{ color:"#1D9E75", marginLeft:8 }}>✓ played</span>}
                      </div>
                    </div>
                    {!played && (
                      <span style={{ fontSize:9, color:"var(--color-text-tertiary)", border:"0.5px solid var(--color-border-tertiary)", padding:"2px 7px", borderRadius:3, flexShrink:0 }}>play</span>
                    )}
                  </div>

                  {/* interference connector */}
                  {iScore !== null && i < session.seq.length - 1 && (
                    <div style={{ display:"flex", alignItems:"center", gap:6, padding:"2px 12px 2px 36px" }}>
                      <div style={{ flex:1, height:"0.5px", background:"var(--color-border-tertiary)" }} />
                      <div style={{ display:"flex", alignItems:"center", gap:4 }}>
                        <div style={{ height:2, width:`${iScore * 44}px`, background:interferenceColor(iScore), borderRadius:1 }} />
                        <span style={{ fontSize:9, color:interferenceColor(iScore), minWidth:26, fontFamily:mono }}>Δ{(iScore*100).toFixed(0)}%</span>
                      </div>
                      <div style={{ flex:1, height:"0.5px", background:"var(--color-border-tertiary)" }} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* session stats */}
          <div style={{ marginTop:12, display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:8 }}>
            {[
              { label:"SESSION ENTROPY",  value:`${(session.entropy*100).toFixed(0)}%`,                                                               color:interferenceColor(session.entropy) },
              { label:"AVG FAMILIARITY",  value:`${session.seq.length ? (session.seq.reduce((a,b)=>a+b.fam,0)/session.seq.length*100).toFixed(0):0}%`, color:"var(--color-text-primary)" },
              { label:"CLUSTER SWITCHES", value:`${session.seq.slice(1).filter((s,i)=>s.game.cluster!==session.seq[i].game.cluster).length}/${Math.max(0,session.seq.length-1)}`, color:"var(--color-text-primary)" },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ background:"var(--color-background-secondary)", borderRadius:6, padding:"8px 10px", border:"0.5px solid var(--color-border-tertiary)" }}>
                <div style={{ ...capsLabel, marginBottom:4 }}>{label}</div>
                <div style={{ fontSize:20, fontWeight:500, color, fontFamily:mono }}>{value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── interference matrix toggle ── */}
      <div style={{ marginTop:20, borderTop:"0.5px solid var(--color-border-tertiary)", paddingTop:14 }}>
        <button onClick={() => setShowMatrix(s => !s)}
          style={{ background:"none", border:"none", cursor:"pointer", display:"flex", alignItems:"center", gap:8, padding:0 }}>
          <span style={capsLabel}>INTERFERENCE MATRIX</span>
          <span style={{ fontSize:10, color:"var(--color-text-tertiary)", fontFamily:mono }}>{showMatrix ? "▾" : "▸"}</span>
        </button>

        {showMatrix && (
          <div style={{ marginTop:10, overflowX:"auto" }}>
            <table style={{ borderCollapse:"collapse", fontSize:10, fontFamily:mono }}>
              <thead>
                <tr>
                  <td style={{ padding:"4px 10px 4px 0", color:"var(--color-text-tertiary)" }}>from ╲ to</td>
                  {Object.entries(CLUSTERS).map(([k, v]) => (
                    <td key={k} style={{ padding:"4px 6px", color:v.hex, textAlign:"center", whiteSpace:"nowrap" }}>{v.label}</td>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(INTERFERENCE).map(([from, row]) => (
                  <tr key={from}>
                    <td style={{ padding:"4px 10px 4px 0", color:CLUSTERS[from]?.hex, whiteSpace:"nowrap" }}>{CLUSTERS[from]?.label}</td>
                    {Object.entries(row).map(([to, val]) => {
                      const same = from === to;
                      const bg = same ? "var(--color-border-tertiary)" : `${interferenceColor(val)}${Math.round(val * 160).toString(16).padStart(2,"0")}`;
                      return (
                        <td key={to} style={{ padding:"3px 6px", textAlign:"center" }}>
                          <div style={{ display:"inline-flex", width:32, height:22, borderRadius:4, background:bg, alignItems:"center", justifyContent:"center", color: same ? "var(--color-text-tertiary)" : interferenceColor(val), fontSize:10, fontFamily:mono }}>
                            {same ? "—" : (val*100).toFixed(0)}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
            <p style={{ fontSize:10, color:"var(--color-text-tertiary)", marginTop:8, fontFamily:mono }}>
              green = high interference (good) · amber = medium · red = low (avoid consecutive)
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
