/**
 * entropy_engine.js  —  Puzzle Entropy Scheduler
 *
 * Tracks pass/fail at (puzzleType × subtype) granularity.
 * Uses Ebbinghaus decay + reconstruction-zone scoring to pick
 * the most cognitively challenging next puzzle / subtype.
 *
 * Shared localStorage key: 'entropy_state_v2'
 * Both app_v2.html and EntropyRotator.jsx read/write this key.
 *
 * Public API (exposed as window.EntropyEngine):
 *   pickNextSubtype(typeId, lastSubtypeId?)  → subtype object
 *   recordResult(typeId, subtypeId, passed)  → void
 *   buildTypeSession(typeIds?, size?)        → { seq, interferences, entropy }
 *   getSubtypeScores(typeId)                 → [{ subtype, fam, score, zone }]
 *   getGameSummary(typeId)                   → { familiarity, lastPlayed, sessions }
 *   PUZZLE_REGISTRY, CLUSTERS
 */

// ═══════════════════════════════════════════════════════════════
// PUZZLE REGISTRY  —  single source of truth for all puzzle types
//
// Fields per type:
//   cluster         cognitive cluster (see CLUSTERS)
//   cognitiveLoad   [0-1]  working-memory demand
//   ruleVolatility  [0-1]  how fast rules decay without practice
//   surface         sensory/tactile tags (for interference hints)
//   subtypes        list of trackable variants within this type
//
// Fields per subtype:
//   id        value passed to the API (matches SUB_OPTIONS in app_v2)
//   label     human-readable name
//   cogLoad   overrides type-level cognitiveLoad (optional)
//   volatility overrides type-level ruleVolatility (optional)
// ═══════════════════════════════════════════════════════════════
const PUZZLE_REGISTRY = {
  raven: {
    name: "I-RAVEN", cluster: "rule_induction",
    cognitiveLoad: 0.90, ruleVolatility: 0.95,
    surface: ["grid","color","pattern"],
    subtypes: [
      { id: "standard", label: "Standard" },
      { id: "mesh",     label: "Mesh",     cogLoad: 0.95, volatility: 0.98 },
    ]
  },
  pgm: {
    name: "PGM", cluster: "rule_induction",
    cognitiveLoad: 0.85, ruleVolatility: 0.88,
    surface: ["grid","abstract","pattern"],
    subtypes: [
      { id: "mixed", label: "Mixed" }
    ]
  },
  marvel: {
    name: "MARVEL", cluster: "rule_induction",
    cognitiveLoad: 0.80, ruleVolatility: 0.82,
    surface: ["image","abstract","multi-modal"],
    subtypes: [
      { id: "Temporal Movement",    label: "Temporal Movement",    cogLoad: 0.78, volatility: 0.80 },
      { id: "Spatial Relationship", label: "Spatial Relationship", cogLoad: 0.80, volatility: 0.82 },
      { id: "Quantities",           label: "Quantities",           cogLoad: 0.75, volatility: 0.78 },
      { id: "2D-Geometry",          label: "2D Geometry",          cogLoad: 0.82, volatility: 0.85 },
      { id: "3D-Geometry",          label: "3D Geometry",          cogLoad: 0.88, volatility: 0.90 },
      { id: "Mathematical",         label: "Mathematical",         cogLoad: 0.85, volatility: 0.88 },
    ]
  },
  bongard: {
    name: "Bongard", cluster: "rule_induction",
    cognitiveLoad: 0.75, ruleVolatility: 0.80,
    surface: ["abstract","rule","classification"],
    subtypes: [
      { id: "mixed", label: "Mixed" }
    ]
  },
  puzzlevqa: {
    name: "PuzzleVQA", cluster: "spatial_2d",
    cognitiveLoad: 0.72, ruleVolatility: 0.75,
    surface: ["pattern","visual","counting"],
    subtypes: [
      { id: "color_grid",           label: "Color Grid",      cogLoad: 0.68, volatility: 0.72 },
      { id: "shape_morph",          label: "Shape Morph",     cogLoad: 0.72, volatility: 0.75 },
      { id: "grid_number",          label: "Grid Number",     cogLoad: 0.75, volatility: 0.78 },
      { id: "venn",                 label: "Venn",            cogLoad: 0.70, volatility: 0.74 },
      { id: "size_cycle",           label: "Size Cycle",      cogLoad: 0.72, volatility: 0.76 },
      { id: "polygon_sides_number", label: "Polygon Sides",   cogLoad: 0.68, volatility: 0.72 },
      { id: "numbers_triangle",     label: "Number Triangle", cogLoad: 0.78, volatility: 0.82 },
    ]
  },
  acre: {
    name: "ACRE", cluster: "constraint_sat",
    cognitiveLoad: 0.82, ruleVolatility: 0.85,
    surface: ["3d","causal","scene"],
    subtypes: [
      { id: "IID",  label: "IID",          cogLoad: 0.75, volatility: 0.80 },
      { id: "Comp", label: "Compositional",cogLoad: 0.85, volatility: 0.88 },
      { id: "Sys",  label: "Systematic",   cogLoad: 0.88, volatility: 0.92 },
    ]
  },
  clevr: {
    name: "CLEVR", cluster: "constraint_sat",
    cognitiveLoad: 0.70, ruleVolatility: 0.72,
    surface: ["3d","counting","attribute"],
    subtypes: [
      { id: "mixed", label: "Mixed" }
    ]
  },
  arc: {
    name: "ARC-AGI", cluster: "rule_induction",
    cognitiveLoad: 0.92, ruleVolatility: 0.96,
    surface: ["grid","color","transformation"],
    subtypes: [
      { id: "arc2", label: "ARC-AGI-2", cogLoad: 0.95, volatility: 0.98 },
      { id: "arc1", label: "ARC-AGI-1", cogLoad: 0.88, volatility: 0.92 },
    ]
  },
  arc3: {
    name: "ARC-AGI-3", cluster: "adversarial",
    cognitiveLoad: 0.95, ruleVolatility: 0.97,
    surface: ["interactive","exploration","grid"],
    subtypes: [
      { id: "any", label: "Any Environment" }
    ]
  },
  rlp: {
    name: "RLP (Tatham)", cluster: "constraint_sat",
    cognitiveLoad: 0.80, ruleVolatility: 0.75,
    surface: ["logic","puzzle","interactive"],
    subtypes: [
      { id: "flood",    label: "Flood",       cogLoad: 0.65, volatility: 0.60 },
      { id: "net",      label: "Net",         cogLoad: 0.72, volatility: 0.70 },
      { id: "flip",     label: "Flip",        cogLoad: 0.68, volatility: 0.65 },
      { id: "fifteen",  label: "Fifteen",     cogLoad: 0.80, volatility: 0.78 },
      { id: "bridges",  label: "Bridges",     cogLoad: 0.78, volatility: 0.75 },
      { id: "loopy",    label: "Loopy",       cogLoad: 0.82, volatility: 0.80 },
      { id: "slant",    label: "Slant",       cogLoad: 0.75, volatility: 0.72 },
      { id: "signpost", label: "Signpost",    cogLoad: 0.85, volatility: 0.82 },
      { id: "untangle", label: "Untangle",    cogLoad: 0.78, volatility: 0.76 },
      { id: "pattern",  label: "Nonogram",    cogLoad: 0.88, volatility: 0.85 },
      { id: "rect",     label: "Rectangles",  cogLoad: 0.72, volatility: 0.70 },
      { id: "solo",     label: "Sudoku",      cogLoad: 0.85, volatility: 0.65 },
      { id: "mines",    label: "Minesweeper", cogLoad: 0.70, volatility: 0.68 },
    ]
  },
};

// ═══════════════════════════════════════════════════════════════
// COGNITIVE CLUSTERS
// ═══════════════════════════════════════════════════════════════
const CLUSTERS = {
  rule_induction: { label: "Rule Induction",   hex: "#1D9E75" },
  spatial_3d:     { label: "3D / 4D Spatial",  hex: "#D85A30" },
  spatial_2d:     { label: "2D Spatial",        hex: "#7F77DD" },
  constraint_sat: { label: "Constraint Sat.",   hex: "#BA7517" },
  adversarial:    { label: "Adversarial",       hex: "#378ADD" },
};

// ═══════════════════════════════════════════════════════════════
// INTERFERENCE MATRIX  (cluster → cluster)
// High value = high interference = good sequential pairing
// ═══════════════════════════════════════════════════════════════
const INTERFERENCE = {
  rule_induction: { rule_induction:0.04, spatial_3d:0.95, spatial_2d:0.45, constraint_sat:0.80, adversarial:0.92 },
  spatial_3d:     { rule_induction:0.95, spatial_3d:0.04, spatial_2d:0.70, constraint_sat:0.82, adversarial:0.68 },
  spatial_2d:     { rule_induction:0.45, spatial_3d:0.70, spatial_2d:0.04, constraint_sat:0.65, adversarial:0.88 },
  constraint_sat: { rule_induction:0.80, spatial_3d:0.82, spatial_2d:0.65, constraint_sat:0.04, adversarial:0.78 },
  adversarial:    { rule_induction:0.92, spatial_3d:0.68, spatial_2d:0.88, constraint_sat:0.78, adversarial:0.04 },
};

// ═══════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════
const STORAGE_KEY = 'entropy_state_v2';

// ═══════════════════════════════════════════════════════════════
// INTERNAL UTILITIES
// ═══════════════════════════════════════════════════════════════

function _stateKey(typeId, subtypeId) {
  return `${typeId}::${subtypeId}`;
}

function _defaultSubtypeState() {
  return {
    familiarity: 0.50,
    lastPlayed:  Date.now() - 7 * 86_400_000,
    wins:        0,
    losses:      0,
    sessions:    0,
  };
}

function _loadState() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
  catch { return {}; }
}

function _saveState(s) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); } catch(e) {}
}

// Ebbinghaus decay: familiarity × e^(-volatility × 0.25 × days)
function _decayedFam(fam, lastPlayed, volatility) {
  const days = (Date.now() - lastPlayed) / 86_400_000;
  return fam * Math.exp(-volatility * 0.25 * days);
}

// Reconstruction zone score: peaks at ~42% familiarity
function _reconstructionScore(fam, volatility, cogLoad) {
  let zone;
  if      (fam < 0.15) zone = 0.30;
  else if (fam > 0.78) zone = 0.10;
  else                 zone = 1.0 - Math.abs(fam - 0.42) / 0.45;
  return zone * volatility * cogLoad;
}

function _clusterOf(typeId) {
  return PUZZLE_REGISTRY[typeId]?.cluster ?? 'rule_induction';
}

function _interferenceBetween(typeIdA, typeIdB) {
  const a = _clusterOf(typeIdA);
  const b = _clusterOf(typeIdB);
  return INTERFERENCE[a]?.[b] ?? 0.5;
}

// ═══════════════════════════════════════════════════════════════
// PUBLIC API
// ═══════════════════════════════════════════════════════════════

/**
 * Pick the highest-reconstruction subtype for a puzzle type.
 * Avoids repeating lastSubtypeId by applying a penalty.
 * Adds small ε-noise to prevent deterministic lock-in.
 *
 * Returns: subtype object (from PUZZLE_REGISTRY subtypes list)
 */
function pickNextSubtype(typeId, lastSubtypeId) {
  const reg = PUZZLE_REGISTRY[typeId];
  if (!reg) return null;
  const { subtypes } = reg;
  if (subtypes.length <= 1) return subtypes[0] ?? null;

  const state = _loadState();
  const scored = subtypes.map(st => {
    const sk  = _stateKey(typeId, st.id);
    const s   = state[sk] ?? _defaultSubtypeState();
    const vol = st.volatility ?? reg.ruleVolatility;
    const cl  = st.cogLoad    ?? reg.cognitiveLoad;
    const fam = _decayedFam(s.familiarity, s.lastPlayed, vol);
    const base = _reconstructionScore(fam, vol, cl);
    const repeatPenalty = (st.id === lastSubtypeId) ? 0.15 : 1.0;
    const noise = 1.0 + (Math.random() - 0.5) * 0.12;
    return { st, score: base * repeatPenalty * noise };
  });

  scored.sort((a, b) => b.score - a.score);
  return scored[0].st;
}

/**
 * Record a pass or fail for a specific (typeId, subtypeId) pair.
 * Pass:  familiarity += 0.15  (cap 1.0)
 * Fail:  familiarity -= 0.08  (floor 0.0)
 */
function recordResult(typeId, subtypeId, passed) {
  if (!typeId || !subtypeId) return;
  const state = _loadState();
  const key = _stateKey(typeId, subtypeId);
  const s = state[key] ?? _defaultSubtypeState();
  state[key] = {
    ...s,
    familiarity: passed
      ? Math.min(1.0, s.familiarity + 0.15)
      : Math.max(0.0, s.familiarity - 0.08),
    lastPlayed: Date.now(),
    wins:     s.wins   + (passed ? 1 : 0),
    losses:   s.losses + (passed ? 0 : 1),
    sessions: s.sessions + 1,
  };
  _saveState(state);
}

/**
 * Compute per-subtype familiarity scores for a puzzle type.
 * Returns array sorted by score descending.
 */
function getSubtypeScores(typeId) {
  const reg = PUZZLE_REGISTRY[typeId];
  if (!reg) return [];
  const state = _loadState();

  return reg.subtypes.map(st => {
    const sk  = _stateKey(typeId, st.id);
    const s   = state[sk] ?? _defaultSubtypeState();
    const vol = st.volatility ?? reg.ruleVolatility;
    const cl  = st.cogLoad    ?? reg.cognitiveLoad;
    const fam = _decayedFam(s.familiarity, s.lastPlayed, vol);
    const score = _reconstructionScore(fam, vol, cl);
    let zone;
    if      (fam < 0.15) zone = { label: 'forgotten',       color: '#E24B4A' };
    else if (fam > 0.78) zone = { label: 'comfortable',     color: '#1D9E75' };
    else                 zone = { label: 'reconstruction',   color: '#EF9F27' };
    return { subtype: st, fam, score, zone, wins: s.wins, losses: s.losses };
  }).sort((a, b) => b.score - a.score);
}

/**
 * Aggregate subtypes into a single game-level summary for session building.
 * familiarity = min across subtypes (weakest link drives urgency)
 * lastPlayed  = max (most recent)
 * sessions    = sum
 */
function getGameSummary(typeId) {
  const reg = PUZZLE_REGISTRY[typeId];
  if (!reg) return { familiarity: 0.5, lastPlayed: Date.now() - 86_400_000, sessions: 0 };
  const state = _loadState();

  const rows = reg.subtypes.map(st => {
    const s   = state[_stateKey(typeId, st.id)] ?? _defaultSubtypeState();
    const vol = st.volatility ?? reg.ruleVolatility;
    return { fam: _decayedFam(s.familiarity, s.lastPlayed, vol), lastPlayed: s.lastPlayed, sessions: s.sessions };
  });

  return {
    familiarity: Math.min(...rows.map(r => r.fam)),
    lastPlayed:  Math.max(...rows.map(r => r.lastPlayed)),
    sessions:    rows.reduce((a, r) => a + r.sessions, 0),
  };
}

/**
 * Build an optimal ordered session of puzzle types.
 * Uses the same greedy interference algorithm as EntropyRotator.jsx.
 *
 * typeIds: array of type ids to consider (default: all)
 * size:    session length
 *
 * Returns { seq, interferences, entropy }
 *   seq            [ { typeId, name, cluster, fam, score, nextSubtype } ]
 *   interferences  pairwise interference values between consecutive items
 *   entropy        mean interference [0-1]
 */
function buildTypeSession(typeIds, size) {
  typeIds = typeIds ?? Object.keys(PUZZLE_REGISTRY);
  size    = size    ?? 6;

  const pool = typeIds.map(id => {
    const reg  = PUZZLE_REGISTRY[id];
    const summ = getGameSummary(id);
    // Reconstruct game-level score using aggregated familiarity
    const score = _reconstructionScore(summ.familiarity, reg.ruleVolatility, reg.cognitiveLoad);
    return { typeId: id, name: reg.name, cluster: reg.cluster, fam: summ.fam, score };
  }).sort((a, b) => b.score - a.score).slice(0, Math.min(size * 2, typeIds.length));

  if (!pool.length) return { seq: [], interferences: [], entropy: 0 };

  const seq = [pool[0]];
  const rem = new Set(pool.slice(1).map(p => p.typeId));

  while (seq.length < Math.min(size, pool.length)) {
    const lastId = seq[seq.length - 1].typeId;
    let bestId = null, bestVal = -1;
    for (const id of rem) {
      const c   = pool.find(p => p.typeId === id);
      const val = c.score * _interferenceBetween(lastId, id);
      if (val > bestVal) { bestVal = val; bestId = id; }
    }
    if (!bestId) break;
    seq.push(pool.find(p => p.typeId === bestId));
    rem.delete(bestId);
  }

  // Attach best next subtype for each item in queue
  seq.forEach(item => {
    item.nextSubtype = pickNextSubtype(item.typeId, null);
  });

  const interferences = seq.slice(0, -1).map((item, i) =>
    _interferenceBetween(item.typeId, seq[i + 1].typeId)
  );
  const entropy = interferences.length
    ? interferences.reduce((a, b) => a + b, 0) / interferences.length
    : 0;

  return { seq, interferences, entropy };
}

// ═══════════════════════════════════════════════════════════════
// EXPOSE
// ═══════════════════════════════════════════════════════════════
window.EntropyEngine = {
  PUZZLE_REGISTRY,
  CLUSTERS,
  INTERFERENCE,
  STORAGE_KEY,
  pickNextSubtype,
  recordResult,
  getSubtypeScores,
  getGameSummary,
  buildTypeSession,
};
