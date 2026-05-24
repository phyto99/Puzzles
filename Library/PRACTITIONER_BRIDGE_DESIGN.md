# Practitioner Bridge — Design Document
*How local generator performance connects to Observatory source recommendations.*

---

## The Problem

The Observatory is a library of elite external puzzle sources. The local training system generates infinite puzzles across cognitive clusters. These two worlds currently don't speak to each other.

A practitioner spending 6 months on ARC-AGI develops specific cognitive muscle groups. When they plateau — or when they excel — the system should be able to say: *"You are ready for the WPF Grand Prix. It runs in 12 days."* Or: *"Your constraint-satisfaction score has stagnated. The Logic Masters India monthly test opens Thursday."*

This requires a **Bridge** — a mapping from local generator performance → observatory source recommendation.

---

## What We Already Have

### The Entropy Engine (`static/entropy_engine.js`)

Already tracks at 4 levels:
- **L1** `typeId::subtypeId` — subtype familiarity (how saturated is each puzzle subtype)
- **L2** `typeId::feature::value` — per-generation-parameter familiarity (which features are stale)
- **L3** `arc3::game::gameId` — per-ARC3-game rich state (levels reached, efficiency scores)
- **L4** `progress_history` — timestamped session log per puzzle type (for charts)

### Cognitive Clusters (already defined)

```
rule_induction   — I-RAVEN, PGM, MARVEL, ARC-AGI, Bongard, PuzzleVQA
constraint_sat   — ACRE, CLEVR, RLP/Tatham
adversarial      — ARC-AGI-3
spatial_3d       — (ACRE, CLEVR share this surface)
spatial_2d       — PuzzleVQA
```

### Inter-cluster Interference (already defined)
High interference score = good interleaving (trains different muscle groups).

### Transfer Map (already defined)
`from: "raven::rule::Progression" → to: "arc", strength: 0.65`
Captures which local feature weaknesses propagate improvement to other generators.

---

## What Needs to Be Built

### 1. Observatory Source → Cluster Tag Mapping

Each observatory source needs a set of cognitive cluster tags. These are assigned by inspection of what mental operations each source demands.

```javascript
const OBS_CLUSTER_MAP = {
  // [sourceId]: [cluster, ...] — primary cognitive demands of this source
  40:  ['constraint_sat', 'rule_induction'],    // GMPuzzles
  41:  ['constraint_sat', 'rule_induction'],    // WPC
  42:  ['constraint_sat'],                       // WPF Grand Prix
  43:  ['constraint_sat'],                       // Logic Masters India
  97:  ['rule_induction', 'language'],           // IOL (new cluster: language)
  108: ['formal_proof'],                         // Lean Game Server (new cluster)
  111: ['rule_induction', 'constraint_sat'],     // ConwayLife
  116: ['formal_proof', 'constraint_sat'],       // CGT/Sprouts
  16:  ['constraint_sat', 'formal_proof'],       // Jane Street
  17:  ['constraint_sat', 'formal_proof'],       // IBM Ponder This
  18:  ['formal_proof'],                         // Putnam
  19:  ['formal_proof'],                         // IMO
  59:  ['language', 'constraint_sat'],           // Listener Crossword
  107: ['spatial_3d', 'constraint_sat'],         // Foldit
  // ... all 117 sources get tagged
};
```

**New clusters needed** (not in current entropy engine):
- `language` — linguistic pattern recognition, constraint grammar, semantics
- `formal_proof` — proof chains, formal verification, theorem derivation
- `creative_constraint` — Oulipo, puzzle hunt meta-solving, constrained generation
- `cipher` — cryptanalysis, substitution, modular arithmetic

### 2. Cluster Performance Extractor

Reads from `localStorage['entropy_state_v2']` and returns a cluster performance snapshot:

```javascript
function getClusterSnapshot() {
  const state = JSON.parse(localStorage.getItem('entropy_state_v2') || '{}');
  const snapshot = {};
  
  // For each puzzle type, read its L1/L2 state
  Object.entries(PUZZLE_REGISTRY).forEach(([typeId, reg]) => {
    const cluster = reg.cluster;
    if (!snapshot[cluster]) snapshot[cluster] = { attempts: 0, familiarity: 0, recentAccuracy: [] };
    
    const typeState = state[typeId] || {};
    snapshot[cluster].attempts += typeState.totalAttempts || 0;
    snapshot[cluster].familiarity = Math.max(
      snapshot[cluster].familiarity,
      typeState.familiarityScore || 0
    );
  });
  
  return snapshot;
}
```

### 3. Bridge Recommendation Function

```javascript
function getObservatoryRecommendations(maxResults = 5) {
  const snapshot = getClusterSnapshot();
  const accepted = S.filter(s => s.accepted); // S = Observatory source array
  
  // Score each observatory source by how relevant it is to the practitioner's current state
  return accepted.map(source => {
    const clusters = OBS_CLUSTER_MAP[source.id] || [];
    let relevanceScore = 0;
    let reason = '';
    
    clusters.forEach(cluster => {
      const perf = snapshot[cluster];
      if (!perf) return;
      
      if (perf.familiarity > 0.75) {
        // High familiarity → ready to try the elite external version
        relevanceScore += 3;
        reason = `Strong performance in ${cluster} — ready for championship level`;
      } else if (perf.familiarity > 0.40 && perf.attempts > 20) {
        // Moderate familiarity + decent attempts → growth zone
        relevanceScore += 2;
        reason = `Building ${cluster} skills — this source offers the next tier`;
      } else if (perf.attempts < 5) {
        // Unexplored cluster → discovery recommendation
        relevanceScore += 1;
        reason = `Unexplored cluster: ${cluster}`;
      }
    });
    
    // Boost by temporal urgency (releasing soon)
    const days = daysUntil(source);
    if (days !== null && days <= 7 && days > 0) relevanceScore += 2;
    if (days === 0 || source.f === 'continuous') relevanceScore += 1;
    
    return { source, relevanceScore, reason };
  })
  .filter(r => r.relevanceScore > 0)
  .sort((a, b) => b.relevanceScore - a.relevanceScore)
  .slice(0, maxResults);
}
```

### 4. Bridge UI Surface

The Bridge surfaces in **two places**:

**A. Triage view — new "For You" panel** (3rd column on wide screens)
Shows top 3-5 sources recommended based on current cluster performance. Updated each time the Triage tab is opened (reads from localStorage).

```
┌─ FOR YOUR PROFILE ──────────────────────┐
│  Based on your entropy engine history:  │
│                                         │
│  ● WPF Grand Prix        in 3 days      │
│    Strong constraint_sat performance    │
│                                         │
│  ● Logic Masters India   in 8 days      │
│    Building constraint_sat skills       │
│                                         │
│  ● IOL Archive           Evergreen      │
│    Unexplored cluster: language         │
└─────────────────────────────────────────┘
```

**B. Matrix view — "Relevance" sort option**
A new sort column "REL" that ranks sources by Bridge score for the current practitioner. Invisible to anyone without entropy data; defaults to Score sort if no local history.

---

## Cluster Gap Analysis

Reading the entropy engine's open cognitive skill gaps against current observatory coverage:

| Open Gap (from RESEARCH_LOG) | Observatory Coverage | Bridge Cluster |
|---|---|---|
| Cipher / cryptographic reasoning | NSA Periodical, CryptoHack, GCHQ, Cicada 3301, Kryptos | `cipher` |
| Musical / rhythmic pattern reasoning | **NONE** | — (future source research) |
| Game theory / strategic reasoning | CGT/Sprouts (#116) | `formal_proof` |
| Probabilistic / Bayesian reasoning | **NONE** | — (future source research) |
| Epistemic / theory-of-mind reasoning | **NONE** | — (future source research) |
| Temporal / chronological reasoning | **NONE** | — (future source research) |
| Mechanical / physical intuition | Foldit (#107), IPP archive | `spatial_3d` |
| Narrative coherence reasoning | **NONE** | — (future source research) |
| Analogical reasoning (language only) | IOL (#97), NACLO (#114), Oulipo (#113) | `language` |

**Priority gaps for next Observatory research session:**
1. Musical/rhythmic pattern reasoning — no source exists yet; highest gap
2. Probabilistic/Bayesian reasoning — no source exists yet
3. Epistemic/theory-of-mind — no source exists yet
4. Temporal/chronological — no source exists yet; Time Puzzles shelved pending code release

---

## Implementation Phases

### Phase 1 (now possible): Cluster tagging
- Tag all 117 sources with `OBS_CLUSTER_MAP`
- No UI changes required
- Store as a JS constant in `puzzle-observatory.html`

### Phase 2 (requires entropy engine access): Read performance
- The Observatory HTML and the main app (`app_v2.html`) share `localStorage`
- The Observatory can read `entropy_state_v2` directly — no server needed
- Add `getClusterSnapshot()` to observatory JS

### Phase 3 (UI): Surface recommendations
- Add "For You" panel to Triage view (show only if entropy data exists, otherwise hide)
- Add "REL" sort column to Matrix view

### Phase 4 (future): Session integration
- Before each practice session: observatory surfaces "today's summit to aim for"
- After session: entropy engine updates; observatory recommendations refresh
- The practitioner sees the external library and the local gym as one coherent environment

---

## What This Is NOT

- Not personalized coaching (OD-01 — not our job)
- Not tracking user behavior on external sites (OD-05 — impossible)
- Not a guarantee of transfer (transfer is probabilistic; the bridge suggests, not prescribes)
- Not a replacement for the astronomer's intuition about what to practice

The Bridge is a **relevance filter on the library catalog**. The library exists regardless. The Bridge just answers "given what you've been doing, which shelf should you visit today?"
