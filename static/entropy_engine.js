/**
 * entropy_engine.js  —  Puzzle Entropy Scheduler  v3
 *
 * Tracks at four levels simultaneously:
 *   L1  typeId :: subtypeId           — coarse subtype familiarity
 *   L2  typeId :: feature :: value    — per-generation-parameter familiarity
 *   L3  arc3   :: game :: gameId      — per-ARC3-game rich state (levels, efficiency)
 *   L4  progress_history              — timestamped session log per type (for charts)
 *
 * State keys:
 *   localStorage['entropy_state_v2']    — L1/L2/L3 familiarity state
 *   localStorage['entropy_progress_v1'] — L4 progress history (separate to avoid bloat)
 */

// ═══════════════════════════════════════════════════════════════
// PUZZLE REGISTRY
// ═══════════════════════════════════════════════════════════════
const PUZZLE_REGISTRY = {
  raven: {
    name: "I-RAVEN", cluster: "rule_induction",
    cognitiveLoad: 0.90, ruleVolatility: 0.95,
    surface: ["grid","color","pattern"],
    subtypes: [
      { id: "standard", label: "Standard" },
      { id: "mesh",     label: "Mesh", cogLoad: 0.95, volatility: 0.98 },
    ],
    // L2 feature dimensions — these are the "swappable" generation variables.
    // Each dimension is tracked separately; performance on one informs the others.
    features: {
      // config: the spatial layout of the 3×3 matrix
      configs: ["center_single","distribute_four","distribute_nine",
                "in_center_single_out_center_single",
                "in_distribute_four_out_center_single",
                "left_center_single_right_center_single",
                "up_center_single_down_center_single"],
      // rule: the logical transformation rule applied
      rules:   ["Constant","Progression","Arithmetic"],
      // attr: the visual attribute being transformed
      attrs:   ["Number","Position","Type","Size","Color"],
    },
    apiConfigParam: "type",
    // For "optimal formula" display — human-readable dimension names
    featureDimLabels: { config: "Layout Config", rule: "Logic Rule", attr: "Visual Attribute", combo: "Config×Rule×Attr" },
  },
  pgm: {
    name: "PGM", cluster: "rule_induction",
    cognitiveLoad: 0.85, ruleVolatility: 0.88,
    surface: ["grid","abstract","pattern"],
    subtypes: [{ id: "mixed", label: "Mixed" }],
    features: {
      shapes:  ["square","circle","triangle"],
      rules:   ["progression","XOR","OR","AND","consistent_union"],
    },
    featureDimLabels: { shape: "Object Shape", rule: "Combination Rule", complexity: "Attribute Count" },
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
    ],
    features: {
      task_configs: ["A","B","C","D","E"],
    },
    featureDimLabels: { pattern: "Reasoning Pattern", config: "Task Config" },
  },
  bongard: {
    name: "Bongard", cluster: "rule_induction",
    cognitiveLoad: 0.75, ruleVolatility: 0.80,
    surface: ["abstract","rule","classification"],
    subtypes: [{ id: "mixed", label: "Mixed" }],
    features: { categories: [] },
    featureDimLabels: { cat: "Concept Category" },
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
    ],
    features: {},
    featureDimLabels: { pattern: "Visual Pattern" },
  },
  acre: {
    name: "ACRE", cluster: "constraint_sat",
    cognitiveLoad: 0.82, ruleVolatility: 0.85,
    surface: ["3d","causal","scene"],
    subtypes: [
      { id: "IID",  label: "IID",           cogLoad: 0.75, volatility: 0.80 },
      { id: "Comp", label: "Compositional", cogLoad: 0.85, volatility: 0.88 },
      { id: "Sys",  label: "Systematic",    cogLoad: 0.88, volatility: 0.92 },
    ],
    features: {
      puzzle_types: ["cause","effect"],
      question_subtypes: ["direct","indirect","screen_off","potential"],
    },
    featureDimLabels: { regime: "Generalization Regime", qsub: "Question Subtype", ptype: "Puzzle Type" },
  },
  clevr: {
    name: "CLEVR", cluster: "constraint_sat",
    cognitiveLoad: 0.70, ruleVolatility: 0.72,
    surface: ["3d","counting","attribute"],
    subtypes: [{ id: "mixed", label: "Mixed" }],
    features: {
      question_types: ["count","exist","query_color","query_shape","query_size",
                       "query_material","compare_attr","compare_int","integer"],
    },
    featureDimLabels: { qtype: "Question Type" },
  },
  arc: {
    name: "ARC-AGI", cluster: "rule_induction",
    cognitiveLoad: 0.92, ruleVolatility: 0.96,
    surface: ["grid","color","transformation"],
    subtypes: [
      { id: "arc2", label: "ARC-AGI-2", cogLoad: 0.95, volatility: 0.98 },
      { id: "arc1", label: "ARC-AGI-1", cogLoad: 0.88, volatility: 0.92 },
    ],
    features: {},
    featureDimLabels: { version: "Dataset Version" },
  },
  arc3: {
    name: "ARC-AGI-3", cluster: "adversarial",
    cognitiveLoad: 0.95, ruleVolatility: 0.97,
    surface: ["interactive","exploration","grid"],
    // Subtypes populated dynamically from /api/arc3/envs (25 game types)
    subtypes: [{ id: "any", label: "Any (entropy picks)" }],
    features: {},
    featureDimLabels: { game: "Game Type", tag: "Game Tag" },
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
    ],
    features: {},
    featureDimLabels: { sub: "Puzzle Variant" },
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

// Inter-cluster interference (high = good interleaving, low = similar/interfering)
const INTERFERENCE = {
  rule_induction: { rule_induction:0.04, spatial_3d:0.95, spatial_2d:0.45, constraint_sat:0.80, adversarial:0.92 },
  spatial_3d:     { rule_induction:0.95, spatial_3d:0.04, spatial_2d:0.70, constraint_sat:0.82, adversarial:0.68 },
  spatial_2d:     { rule_induction:0.45, spatial_3d:0.70, spatial_2d:0.04, constraint_sat:0.65, adversarial:0.88 },
  constraint_sat: { rule_induction:0.80, spatial_3d:0.82, spatial_2d:0.65, constraint_sat:0.04, adversarial:0.78 },
  adversarial:    { rule_induction:0.92, spatial_3d:0.68, spatial_2d:0.88, constraint_sat:0.78, adversarial:0.04 },
};

// ═══════════════════════════════════════════════════════════════
// CROSS-PUZZLE TRANSFER MAP
// "Weakness in A → improvement transfers to B"
// strength: fraction of A's reconstruction score that propagates to B
// ═══════════════════════════════════════════════════════════════
const TRANSFER_MAP = [
  { from: "raven::rule::Progression",    to: "arc",       label: "Sequence patterns",    strength: 0.65 },
  { from: "raven::rule::Arithmetic",     to: "acre",      label: "Causal arithmetic",    strength: 0.55 },
  { from: "raven::rule::Arithmetic",     to: "pgm",       label: "Rule overlap",         strength: 0.80 },
  { from: "raven::attr::Color",          to: "arc",       label: "Color mapping",        strength: 0.70 },
  { from: "raven::attr::Position",       to: "clevr",     label: "Spatial position",     strength: 0.60 },
  { from: "raven::config::center_single",to: "raven",     label: "Config mastery base",  strength: 0.40 },
  { from: "marvel::pattern::Spatial Relationship", to: "clevr", label: "Spatial VQA",   strength: 0.72 },
  { from: "marvel::pattern::Quantities", to: "clevr",     label: "Counting",             strength: 0.68 },
  { from: "marvel::pattern::2D-Geometry",to: "puzzlevqa", label: "2D pattern reading",   strength: 0.60 },
  { from: "clevr::qtype::count",         to: "puzzlevqa", label: "Enumeration",          strength: 0.62 },
  { from: "pgm::rule::progression",      to: "raven",     label: "Rule overlap",         strength: 0.80 },
  { from: "pgm::rule::XOR",             to: "acre",      label: "Boolean logic",        strength: 0.58 },
  { from: "rlp::sub::pattern",           to: "puzzlevqa", label: "Grid reading",         strength: 0.58 },
  { from: "rlp::sub::solo",             to: "acre",      label: "Constraint logic",     strength: 0.64 },
  { from: "rlp::sub::bridges",          to: "arc",       label: "Path topology",        strength: 0.52 },
  { from: "arc3::game::any",            to: "arc",       label: "Grid transformations", strength: 0.75 },
  { from: "acre::regime::IID",          to: "acre",      label: "Regime transfer base", strength: 0.45 },
  { from: "bongard::cat::shape",        to: "raven",     label: "Shape abstraction",    strength: 0.55 },
  { from: "bongard::cat::number",       to: "clevr",     label: "Numerosity concepts",  strength: 0.62 },
];

// ═══════════════════════════════════════════════════════════════
// STORAGE
// ═══════════════════════════════════════════════════════════════
const STORAGE_KEY   = 'entropy_state_v2';
const PROGRESS_KEY  = 'entropy_progress_v1';
const MAX_HISTORY   = 50; // sessions per type kept in history

// Runtime ARC3 game registry (populated from /api/arc3/envs)
const _arc3Games = new Map();  // game_id → {title, tags}

function _loadState() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
  catch { return {}; }
}
function _saveState(s) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); } catch(e) {}
}

function _loadProgress() {
  try { return JSON.parse(localStorage.getItem(PROGRESS_KEY) || '{}'); }
  catch { return {}; }
}
function _saveProgress(p) {
  try { localStorage.setItem(PROGRESS_KEY, JSON.stringify(p)); } catch(e) {}
}

function _defaultState(fam = 0.50) {
  return { familiarity: fam, lastPlayed: Date.now() - 7 * 86_400_000,
           wins: 0, losses: 0, sessions: 0 };
}

// ═══════════════════════════════════════════════════════════════
// L4 — PROGRESS HISTORY  (per-session snapshots for charts)
// ═══════════════════════════════════════════════════════════════

/**
 * Record a progress snapshot after each session result.
 * histKey: e.g. "raven", "arc3::game::sk48", "arc3"
 * point: { t, fam, passed, [extra fields per type] }
 */
function _recordProgressPoint(histKey, point) {
  const prog = _loadProgress();
  if (!prog[histKey]) prog[histKey] = [];
  prog[histKey].push({ t: Date.now(), ...point });
  // Keep only last MAX_HISTORY entries
  if (prog[histKey].length > MAX_HISTORY) {
    prog[histKey] = prog[histKey].slice(-MAX_HISTORY);
  }
  _saveProgress(prog);
}

/**
 * Get progress history for a type.
 * Returns array of { t, fam, passed, ... } sorted oldest→newest.
 */
function getProgressHistory(histKey) {
  const prog = _loadProgress();
  return (prog[histKey] ?? []).sort((a, b) => a.t - b.t);
}

/**
 * Get progress for all known types, for the overview chart.
 * Returns { typeId: [{t, fam, passed},...], ... }
 */
function getAllProgressHistory() {
  return _loadProgress();
}

// ═══════════════════════════════════════════════════════════════
// ENTROPY MATH
// ═══════════════════════════════════════════════════════════════

function _decayedFam(fam, lastPlayed, volatility) {
  const days = (Date.now() - lastPlayed) / 86_400_000;
  return Math.max(0, fam * Math.exp(-volatility * 0.25 * days));
}

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
  const a = _clusterOf(typeIdA), b = _clusterOf(typeIdB);
  return INTERFERENCE[a]?.[b] ?? 0.5;
}

function _zoneLabel(fam) {
  if (fam < 0.15) return 'forgotten';
  if (fam > 0.78) return 'comfortable';
  return 'reconstruction';
}

function _zoneColor(fam) {
  if (fam < 0.15) return '#E24B4A';
  if (fam > 0.78) return '#1D9E75';
  return '#EF9F27';
}

// ═══════════════════════════════════════════════════════════════
// L1 — SUBTYPE FAMILIARITY
// ═══════════════════════════════════════════════════════════════

function pickNextSubtype(typeId, lastSubtypeId) {
  const reg = PUZZLE_REGISTRY[typeId];
  if (!reg) return null;

  if (typeId === 'arc3' && _arc3Games.size > 0) {
    return _pickNextARC3Game(lastSubtypeId);
  }

  const { subtypes } = reg;
  if (subtypes.length <= 1) return subtypes[0] ?? null;

  const state = _loadState();
  const scored = subtypes.map(st => {
    const s   = state[`${typeId}::${st.id}`] ?? _defaultState();
    const vol = st.volatility ?? reg.ruleVolatility;
    const cl  = st.cogLoad    ?? reg.cognitiveLoad;
    const fam = _decayedFam(s.familiarity, s.lastPlayed, vol);
    const base = _reconstructionScore(fam, vol, cl);
    const penalty = st.id === lastSubtypeId ? 0.15 : 1.0;
    const noise   = 1.0 + (Math.random() - 0.5) * 0.12;
    return { st, score: base * penalty * noise };
  });

  scored.sort((a, b) => b.score - a.score);
  return scored[0].st;
}

function recordResult(typeId, subtypeId, passed) {
  if (!typeId || !subtypeId) return;
  const state = _loadState();
  const key = `${typeId}::${subtypeId}`;
  const s   = state[key] ?? _defaultState();
  const newFam = passed
    ? Math.min(1, s.familiarity + 0.15)
    : Math.max(0, s.familiarity - 0.08);

  state[key] = {
    ...s,
    familiarity: newFam,
    lastPlayed: Date.now(),
    wins:     s.wins   + (passed ? 1 : 0),
    losses:   s.losses + (passed ? 0 : 1),
    sessions: s.sessions + 1,
  };
  _saveState(state);

  // L4: record progress snapshot for this type
  _recordProgressPoint(typeId, { fam: newFam, passed, subtype: subtypeId });
}

function getSubtypeScores(typeId) {
  const reg = PUZZLE_REGISTRY[typeId];
  if (!reg) return [];

  if (typeId === 'arc3' && _arc3Games.size > 0) {
    return _getARC3Scores().slice(0, 10).map(g => ({
      subtype:  { id: g.id, label: g.title },
      fam:      g.fam,
      score:    g.score,
      zone:     { label: _zoneLabel(g.fam), color: _zoneColor(g.fam) },
      wins:     g.wins,
      losses:   g.losses,
    }));
  }

  const state = _loadState();
  return reg.subtypes.map(st => {
    const s   = state[`${typeId}::${st.id}`] ?? _defaultState();
    const vol = st.volatility ?? reg.ruleVolatility;
    const cl  = st.cogLoad    ?? reg.cognitiveLoad;
    const fam = _decayedFam(s.familiarity, s.lastPlayed, vol);
    const score = _reconstructionScore(fam, vol, cl);
    return {
      subtype: st, fam, score,
      zone:    { label: _zoneLabel(fam), color: _zoneColor(fam) },
      wins:    s.wins, losses: s.losses,
    };
  }).sort((a, b) => b.score - a.score);
}

// ═══════════════════════════════════════════════════════════════
// L2 — FEATURE-LEVEL TRACKING  (per generation parameter)
// ═══════════════════════════════════════════════════════════════

/**
 * Record result at feature granularity.
 *
 * features object per type:
 *   raven:    { config, rule_info: [{name, attr}] }
 *   pgm:      { shape, rule_desc }
 *   marvel:   { pattern, task_configuration }
 *   clevr:    { question_type }
 *   acre:     { regime, question_subtype }
 *   puzzlevqa:{ pattern }
 *   arc:      { version, task_id }
 *   bongard:  { hint }
 *   rlp:      { puzzle (subtype id) }
 *   arc3:     handled separately by recordARC3Result
 */
function recordPuzzleFeatures(typeId, features, passed) {
  if (!typeId || !features) return;
  const state  = _loadState();
  const delta  = passed ? 0.15 : -0.08;
  const vol    = PUZZLE_REGISTRY[typeId]?.ruleVolatility ?? 0.85;
  const cl     = PUZZLE_REGISTRY[typeId]?.cognitiveLoad  ?? 0.80;

  const touch = (key, featVol, featCl) => {
    const s = state[key] ?? _defaultState();
    const newFam = Math.min(1, Math.max(0, s.familiarity + delta));
    state[key] = {
      ...s,
      familiarity: newFam,
      lastPlayed:  Date.now(),
      wins:        s.wins   + (passed ? 1 : 0),
      losses:      s.losses + (passed ? 0 : 1),
      sessions:    s.sessions + 1,
      volatility:  featVol ?? vol,
      cogLoad:     featCl  ?? cl,
    };
  };

  switch (typeId) {

    case 'raven': {
      // Track each dimension independently — configs, rules, attrs are separate
      // swappable axes of variation, not a single combined type
      if (features.config) touch(`raven::config::${features.config}`);
      (features.rule_info ?? []).forEach(r => {
        if (r.name) touch(`raven::rule::${r.name}`, 0.92, 0.88);
        if (r.attr)  touch(`raven::attr::${r.attr}`,  0.90, 0.85);
        // Track combos only for the optimizer — not shown as standalone subtypes
        if (r.name && r.attr && features.config)
          touch(`raven::combo::${features.config}|${r.name}|${r.attr}`, 0.95, 0.92);
      });
      break;
    }

    case 'pgm': {
      if (features.shape)     touch(`pgm::shape::${features.shape}`, 0.85, 0.80);
      if (features.rule_desc) touch(`pgm::rule::${features.rule_desc}`, 0.90, 0.88);
      if (features.n_attrs !== undefined)
        touch(`pgm::complexity::${features.n_attrs}attr`, 0.88, 0.85);
      break;
    }

    case 'marvel': {
      if (features.pattern)           touch(`marvel::pattern::${features.pattern}`, 0.82, 0.80);
      if (features.task_configuration)touch(`marvel::config::${features.task_configuration}`, 0.80, 0.78);
      break;
    }

    case 'clevr': {
      if (features.question_type) touch(`clevr::qtype::${features.question_type}`, 0.72, 0.70);
      break;
    }

    case 'acre': {
      if (features.regime)           touch(`acre::regime::${features.regime}`, 0.85, 0.82);
      if (features.question_subtype) touch(`acre::qsub::${features.question_subtype}`, 0.85, 0.82);
      if (features.puzzle_type)      touch(`acre::ptype::${features.puzzle_type}`, 0.82, 0.80);
      break;
    }

    case 'puzzlevqa': {
      if (features.pattern) touch(`puzzlevqa::pattern::${features.pattern}`, 0.75, 0.72);
      break;
    }

    case 'arc': {
      const ver = features.version ?? 'arc2';
      touch(`arc::version::${ver}`, 0.96, 0.92);
      break;
    }

    case 'bongard': {
      if (features.hint) {
        const cat = (features.hint.match(/\b(shape|size|color|number|position|count|type|inside|outside|left|right|above|below|angle|curve|line)\b/i) || ['other'])[0].toLowerCase();
        touch(`bongard::cat::${cat}`, 0.80, 0.75);
      }
      break;
    }

    case 'rlp': {
      if (features.puzzle) touch(`rlp::sub::${features.puzzle}`, 0.75, 0.80);
      break;
    }
  }

  _saveState(state);
}

/**
 * Return all L2 feature state for a type, grouped by dimension.
 * Each group is sorted by reconstruction score desc.
 */
function getFeatureBreakdown(typeId) {
  const state   = _loadState();
  const prefix  = typeId + '::';
  const groups  = {};

  Object.keys(state).forEach(key => {
    if (!key.startsWith(prefix)) return;
    const rest  = key.slice(prefix.length);
    const parts = rest.split('::');
    if (parts.length < 2) return; // skip L1 subtype keys
    const [dim, val] = parts;
    const s   = state[key];
    const v   = s.volatility ?? (PUZZLE_REGISTRY[typeId]?.ruleVolatility ?? 0.85);
    const c   = s.cogLoad    ?? (PUZZLE_REGISTRY[typeId]?.cognitiveLoad  ?? 0.80);
    const fam = _decayedFam(s.familiarity, s.lastPlayed, v);
    const sc  = _reconstructionScore(fam, v, c);

    if (!groups[dim]) groups[dim] = [];
    groups[dim].push({
      key, dim, val, fam, score: sc,
      wins: s.wins, losses: s.losses, sessions: s.sessions,
      zone: { label: _zoneLabel(fam), color: _zoneColor(fam) },
      volatility: v,
    });
  });

  Object.keys(groups).forEach(d => groups[d].sort((a, b) => b.score - a.score));
  return groups;
}

// ═══════════════════════════════════════════════════════════════
// OPTIMAL NEXT FORMULA
// "What combination of generation params gives the most growth?"
// ═══════════════════════════════════════════════════════════════

/**
 * Analyze L2 feature state and return the optimal next puzzle formula.
 * Returns { components: [{dim, val, score, fam, zone}], formulaStr, topScore }
 *
 * For Raven: picks best config + best rule + best attr independently
 * For others: picks the highest-score value per tracked dimension
 */
function getNextBestFormula(typeId) {
  const breakdown = getFeatureBreakdown(typeId);
  const reg = PUZZLE_REGISTRY[typeId];
  if (!breakdown || !Object.keys(breakdown).length) return null;

  const dimLabels = reg?.featureDimLabels ?? {};
  const components = [];

  // Skip combo dim — use individual dims for the formula
  const dims = Object.keys(breakdown).filter(d => d !== 'combo');

  dims.forEach(dim => {
    const items = breakdown[dim];
    if (!items?.length) return;
    // Pick the item with highest reconstruction score in this dimension
    const best = items[0]; // already sorted desc by score
    if (best.score < 0.05) return; // skip if barely any data
    components.push({
      dim,
      dimLabel: dimLabels[dim] ?? dim,
      val: best.val,
      score: best.score,
      fam: best.fam,
      zone: best.zone,
    });
  });

  if (!components.length) return null;

  // Overall formula score = average of component reconstruction scores
  const topScore = components.reduce((a, c) => a + c.score, 0) / components.length;

  // Human-readable formula string
  const formulaStr = components
    .map(c => `${c.dimLabel}: ${c.val}`)
    .join(' × ');

  // For Raven specifically: also find the combo key that matches
  let ravenComboHint = null;
  if (typeId === 'raven' && breakdown.combo?.length) {
    ravenComboHint = breakdown.combo[0]; // highest-score recorded combo
  }

  return { components, formulaStr, topScore, ravenComboHint };
}

// ═══════════════════════════════════════════════════════════════
// L3 — ARC3 GAME-LEVEL TRACKING
// ═══════════════════════════════════════════════════════════════

/**
 * Call this after fetching /api/arc3/envs to populate the game registry.
 * games: [{ game_id, title, tags }]
 */
function registerARC3Games(games) {
  games.forEach(g => {
    if (!_arc3Games.has(g.game_id)) {
      _arc3Games.set(g.game_id, { title: g.title, tags: g.tags || [] });
    }
  });
}

/**
 * Record ARC3 game result with rich metrics.
 * levelsCompleted: 0-7 integer
 * winLevels: total levels in game (usually 7)
 * totalMoves: moves taken this session
 * passed: boolean (won the game)
 */
function recordARC3Result(gameId, levelsCompleted, winLevels, totalMoves, passed) {
  if (!gameId) return;
  const state = _loadState();
  const sk    = `arc3::game::${gameId}`;
  const s     = state[sk] ?? {
    familiarity: 0.50, lastPlayed: Date.now() - 7 * 86_400_000,
    wins: 0, losses: 0, sessions: 0,
    maxLevel: 0, winLevels: winLevels ?? 7,
    totalMoves: 0, sessionCount: 0,
    levelCompletions: Array(7).fill(0),
    sessionHistory: [], // per-game history [{t, levels, eff, passed}]
  };

  const efficiency = (winLevels && totalMoves > 0)
    ? Math.min(1, (levelsCompleted / winLevels) / (totalMoves / Math.max(1, levelsCompleted * 8)))
    : 0;

  const levelRatio = winLevels > 0 ? levelsCompleted / winLevels : 0;
  const famDelta   = passed ? 0.15 : (levelRatio * 0.10 - 0.05);

  const newLevelCompletions = [...(s.levelCompletions ?? Array(7).fill(0))];
  for (let l = 0; l < Math.min(levelsCompleted, 7); l++) newLevelCompletions[l]++;

  const newFam = Math.min(1, Math.max(0, s.familiarity + famDelta));

  // Append session to per-game history (keep last 20)
  const sessionHistory = [...(s.sessionHistory ?? []),
    { t: Date.now(), levels: levelsCompleted, eff: efficiency, passed }
  ].slice(-20);

  state[sk] = {
    ...s,
    familiarity:       newFam,
    lastPlayed:        Date.now(),
    wins:              s.wins   + (passed ? 1 : 0),
    losses:            s.losses + (passed ? 0 : 1),
    sessions:          s.sessions + 1,
    maxLevel:          Math.max(s.maxLevel ?? 0, levelsCompleted),
    winLevels:         winLevels ?? s.winLevels ?? 7,
    lastLevels:        levelsCompleted,
    lastEfficiency:    efficiency,
    lastMoves:         totalMoves,
    totalMoves:        (s.totalMoves ?? 0) + (totalMoves ?? 0),
    sessionCount:      (s.sessionCount ?? 0) + 1,
    levelCompletions:  newLevelCompletions,
    sessionHistory,
  };

  _saveState(state);

  // L4: progress snapshot for this specific game
  _recordProgressPoint(`arc3::game::${gameId}`, { fam: newFam, passed, levels: levelsCompleted, eff: efficiency });
  // L4: also snapshot the arc3 type overall
  _recordProgressPoint('arc3', { fam: newFam, passed, gameId });

  // L1 subtype
  recordResult('arc3', 'any', passed);
}

function _getARC3Scores() {
  const state = _loadState();
  const result = [];

  _arc3Games.forEach((info, id) => {
    const sk  = `arc3::game::${id}`;
    const s   = state[sk];
    const fam = s ? _decayedFam(s.familiarity, s.lastPlayed, 0.92) : 0.50;
    const sc  = _reconstructionScore(fam, 0.92, 0.95);

    result.push({
      id, ...info,
      fam, score: sc,
      wins:             s?.wins    ?? 0,
      losses:           s?.losses  ?? 0,
      sessions:         s?.sessions ?? 0,
      maxLevel:         s?.maxLevel ?? 0,
      winLevels:        s?.winLevels ?? 7,
      lastEfficiency:   s?.lastEfficiency ?? 0,
      lastMoves:        s?.lastMoves ?? 0,
      levelCompletions: s?.levelCompletions ?? Array(7).fill(0),
      sessionHistory:   s?.sessionHistory ?? [],
      seen:             !!s,
      zone:             { label: _zoneLabel(fam), color: _zoneColor(fam) },
    });
  });

  return result.sort((a, b) => b.score - a.score);
}

function _pickNextARC3Game(lastGameId) {
  const games = _getARC3Scores();
  if (!games.length) return { id: 'any', label: 'Any Environment' };

  const scored = games.map(g => ({
    ...g,
    st: { id: g.id, label: g.title },
    adjScore: g.score * (g.id === lastGameId ? 0.15 : 1.0) * (1 + (Math.random() - 0.5) * 0.12),
  })).sort((a, b) => b.adjScore - a.adjScore);

  const best = scored[0];
  return { id: best.id, label: best.title };
}

function getARC3GameStates() {
  return _getARC3Scores();
}

/**
 * Group ARC3 games by their tags for high-level overview.
 * Returns [{ tag, games: [...], avgFam, avgScore }] sorted by avgScore desc.
 */
function getARC3TagGroups() {
  const games = _getARC3Scores();
  const groups = {};

  games.forEach(g => {
    const tags = (g.tags ?? ['untagged']);
    tags.forEach(tag => {
      if (!groups[tag]) groups[tag] = [];
      groups[tag].push(g);
    });
  });

  return Object.entries(groups).map(([tag, gs]) => ({
    tag,
    games: gs,
    count: gs.length,
    avgFam:   gs.reduce((a, g) => a + g.fam, 0) / gs.length,
    avgScore: gs.reduce((a, g) => a + g.score, 0) / gs.length,
    maxLevel: Math.max(...gs.map(g => g.maxLevel)),
    totalSessions: gs.reduce((a, g) => a + g.sessions, 0),
  })).sort((a, b) => b.avgScore - a.avgScore);
}

// ═══════════════════════════════════════════════════════════════
// TRANSFER GRAPH
// Nodes = puzzle types (positioned by cluster), Edges = TRANSFER_MAP
// ═══════════════════════════════════════════════════════════════

/**
 * Returns the data for a visual transfer graph.
 * Nodes have fixed positions based on cluster grouping.
 * Edges carry familiarity-weighted activation (only edges where source is active).
 */
function getTransferGraph() {
  const state = _loadState();

  // Cluster-based layout positions (normalized 0–1)
  const CLUSTER_POS = {
    rule_induction: { x: 0.25, y: 0.50 },
    spatial_3d:     { x: 0.75, y: 0.18 },
    spatial_2d:     { x: 0.75, y: 0.82 },
    constraint_sat: { x: 0.50, y: 0.78 },
    adversarial:    { x: 0.50, y: 0.22 },
  };

  // Spread nodes within their cluster
  const clusterCounts = {};
  const nodes = Object.entries(PUZZLE_REGISTRY).map(([id, reg]) => {
    const cluster = reg.cluster;
    const cp = CLUSTER_POS[cluster] ?? { x: 0.5, y: 0.5 };
    const idx = clusterCounts[cluster] = (clusterCounts[cluster] ?? 0) + 1;

    // Slight jitter within cluster
    const jitterR = 0.10;
    const angle   = (idx - 1) * 2.4; // roughly spread by golden angle
    const x = cp.x + Math.cos(angle) * jitterR;
    const y = cp.y + Math.sin(angle) * jitterR;

    // Type-level familiarity for node size/color
    const summ = getGameSummary(id);
    const fam  = summ.familiarity;

    return {
      id,
      name: reg.name,
      cluster,
      clusterHex: CLUSTERS[cluster]?.hex ?? '#888',
      cogLoad: reg.cognitiveLoad,
      x: Math.max(0.05, Math.min(0.95, x)),
      y: Math.max(0.05, Math.min(0.95, y)),
      fam,
      zone: { label: _zoneLabel(fam), color: _zoneColor(fam) },
      sessions: summ.sessions,
    };
  });

  // Build edges from TRANSFER_MAP, weighted by source familiarity
  const edges = TRANSFER_MAP.map(({ from, to, label, strength }) => {
    const s = state[from];
    const vol = s?.volatility ?? 0.88;
    const srcFam = s ? _decayedFam(s.familiarity, s.lastPlayed, vol) : 0;

    // fromType = first segment, toType = to field
    const fromType = from.split('::')[0];
    const toType   = to.split('::')[0];

    // Edge is "active" (highlighted) when source is in reconstruction zone
    const active = srcFam > 0.15 && srcFam < 0.78;

    return {
      fromType, toType,
      fromFeature: from.split('::').slice(1).join('::'),
      label,
      strength,
      srcFam,
      active,
      // Weight = strength * zone-activation (brighter when in reconstruction zone)
      weight: strength * (active ? 1.0 : (srcFam === 0 ? 0.2 : 0.4)),
    };
  });

  // Cluster-level interference edges (for background graph)
  const clusterEdges = [];
  Object.keys(CLUSTERS).forEach((ca, i) => {
    Object.keys(CLUSTERS).forEach((cb, j) => {
      if (j <= i) return;
      const iScore = INTERFERENCE[ca]?.[cb] ?? 0;
      if (iScore > 0.5) {
        clusterEdges.push({ fromCluster: ca, toCluster: cb, interference: iScore });
      }
    });
  });

  return { nodes, edges, clusterEdges, clusterPositions: CLUSTER_POS };
}

// ═══════════════════════════════════════════════════════════════
// SESSION QUEUE (cross-type)
// ═══════════════════════════════════════════════════════════════

function getGameSummary(typeId) {
  const reg = PUZZLE_REGISTRY[typeId];
  if (!reg) return { familiarity: 0.5, lastPlayed: Date.now() - 86_400_000, sessions: 0 };
  const state = _loadState();

  const rows = reg.subtypes.map(st => {
    const s   = state[`${typeId}::${st.id}`] ?? _defaultState();
    const vol = st.volatility ?? reg.ruleVolatility;
    return { fam: _decayedFam(s.familiarity, s.lastPlayed, vol), lastPlayed: s.lastPlayed, sessions: s.sessions };
  });

  return {
    familiarity: Math.min(...rows.map(r => r.fam)),
    lastPlayed:  Math.max(...rows.map(r => r.lastPlayed)),
    sessions:    rows.reduce((a, r) => a + r.sessions, 0),
  };
}

function buildTypeSession(typeIds, size) {
  typeIds = typeIds ?? Object.keys(PUZZLE_REGISTRY);
  size    = size    ?? 6;

  const pool = typeIds.map(id => {
    const reg  = PUZZLE_REGISTRY[id];
    const summ = getGameSummary(id);
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

  seq.forEach(item => { item.nextSubtype = pickNextSubtype(item.typeId, null); });

  const interferences = seq.slice(0, -1).map((item, i) =>
    _interferenceBetween(item.typeId, seq[i + 1].typeId)
  );
  const entropy = interferences.length
    ? interferences.reduce((a, b) => a + b, 0) / interferences.length : 0;

  return { seq, interferences, entropy };
}

// ═══════════════════════════════════════════════════════════════
// TRANSFER INFERENCE
// ═══════════════════════════════════════════════════════════════

function getTransferHints(limit) {
  limit = limit ?? 5;
  const state = _loadState();
  const hints = [];

  TRANSFER_MAP.forEach(({ from, to, label, strength }) => {
    const s = state[from];
    if (!s) return;
    const vol = s.volatility ?? 0.88;
    const fam = _decayedFam(s.familiarity, s.lastPlayed, vol);
    if (fam < 0.15 || fam > 0.78) return;
    const sc = _reconstructionScore(fam, vol, 0.85) * strength;
    hints.push({ from, to, label, fam, score: sc, strength });
  });

  return hints.sort((a, b) => b.score - a.score).slice(0, limit);
}

// ═══════════════════════════════════════════════════════════════
// EXPOSE
// ═══════════════════════════════════════════════════════════════
window.EntropyEngine = {
  // Registry
  PUZZLE_REGISTRY,
  CLUSTERS,
  INTERFERENCE,
  TRANSFER_MAP,
  STORAGE_KEY,
  PROGRESS_KEY,

  // L1 — subtype
  pickNextSubtype,
  recordResult,
  getSubtypeScores,
  getGameSummary,
  buildTypeSession,

  // L2 — feature
  recordPuzzleFeatures,
  getFeatureBreakdown,

  // L3 — ARC3 games
  registerARC3Games,
  recordARC3Result,
  getARC3GameStates,
  getARC3TagGroups,

  // L4 — progress history
  getProgressHistory,
  getAllProgressHistory,

  // Optimal formula
  getNextBestFormula,

  // Transfer graph
  getTransferGraph,
  getTransferHints,

  // Helpers (for dev panel)
  _decayedFam,
  _reconstructionScore,
  _zoneLabel,
  _zoneColor,
};
