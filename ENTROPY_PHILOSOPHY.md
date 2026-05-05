# Entropy Rotation Protocol — Design Philosophy

## The Core Problem

Most practice systems optimize for comfort. They replay problems you already
know, show you what you're good at, and let you settle into patterns. The
result is the illusion of competence — you can solve things you've seen before,
but novel problems stay hard.

The Entropy Rotation Protocol is built on the opposite principle: **the best
next problem is the one you are least prepared to predict**.

---

## The Forgetting Curve and Reconstruction Zone

Hermann Ebbinghaus (1885) showed that memory decays exponentially after a
learning event. The curve for a memory with current strength `F` and time `t`
(days) is:

```
F(t) = F₀ · exp(−k · t)
```

where `k` is a volatility coefficient — how fast a particular cognitive skill
erodes without reinforcement.

This system tracks every puzzle type and subtype with a **familiarity score**
`F ∈ [0, 1]`. Each time you pass, `F += 0.15` (capped at 1.0). Each time you
fail, `F -= 0.08` (floored at 0.0). Between sessions, `F` decays according to
the formula above, using each puzzle type's tuned `ruleVolatility` constant.

**But here is the key insight**: maximum learning does not happen when you've
forgotten everything (F < 0.15), nor when you know it too well (F > 0.78).
It happens in the **reconstruction zone** — roughly 15–78% familiarity — where
you remember enough to feel the rules clicking back into place but must still
actively reconstruct them.

```
Reconstruction score:

  if F < 0.15:  zone = 0.30  (nearly forgotten — still useful but inefficient)
  if F > 0.78:  zone = 0.10  (comfortable — deprioritise)
  else:         zone = 1.0 − |F − 0.42| / 0.45   (peaks at ~42%)

  final_score = zone × ruleVolatility × cognitiveLoad
```

The decay sparkline shown next to each subtype is a 14-day projection: it
shows exactly how long before that skill enters or leaves the reconstruction
zone. This is the scheduling signal.

---

## Interference: Why Switching Domains Is Good

Cognitive science distinguishes two types of forgetting:

- **Decay** — memory fading over time (addressed above)
- **Interference** — one mental model overwriting another

The system deliberately uses interference as a *training force*. When you
practice two cognitively distant skills back-to-back, each must be retrieved
from scratch against an interfering activation pattern. This forces stronger
encoding.

An **interference matrix** defines how much each cognitive cluster disrupts
another:

| From ↓ / To → | Rule Induction | 3D Spatial | 2D Spatial | Constraint | Adversarial |
|---|---|---|---|---|---|
| Rule Induction | 0.04 | **0.95** | 0.45 | 0.80 | **0.92** |
| 3D Spatial | **0.95** | 0.04 | 0.70 | 0.82 | 0.68 |
| 2D Spatial | 0.45 | 0.70 | 0.04 | 0.65 | **0.88** |
| Constraint Sat. | 0.80 | 0.82 | 0.65 | 0.04 | 0.78 |
| Adversarial | **0.92** | 0.68 | **0.88** | 0.78 | 0.04 |

High interference between consecutive items = high entropy = good. Doing
I-RAVEN (rule induction) immediately after ARC-AGI-3 (adversarial) maximally
disrupts both, forcing deeper retrieval of each.

---

## Two-Level Selection: Type and Subtype

Selection happens at two levels simultaneously.

### Level 1 — Puzzle Type (Session Queue)

The session queue is built by a greedy algorithm operating over all puzzle
types. Each type gets a **game-level score** derived from the minimum
familiarity across its subtypes (weakest link drives urgency). The algorithm:

1. Score every type by `reconstructionScore(minSubtypeFamiliarity)`
2. Sort descending, take the top `2 × sessionSize` as the candidate pool
3. Start with the highest-scoring type
4. For each subsequent slot: pick the candidate that maximises
   `score × interference(lastType, candidate)`
5. This simultaneously prioritises **urgent** types AND maximises **cognitive
   disruption** between consecutive items

The result is a session where no two adjacent puzzles share cognitive
machinery, and all selected types are in or near the reconstruction zone.

### Level 2 — Subtype Selection

Within the chosen puzzle type, a second pass selects the best **subtype**
(e.g., within MARVEL: Temporal Movement vs 3D Geometry vs Mathematical;
within RLP: Flood vs Nonogram vs Signpost).

The subtype algorithm:

1. Score each subtype by its own `reconstructionScore(fam, volatility, cogLoad)`
2. Apply a **repeat penalty** (×0.15) to the last-played subtype, preventing
   immediate repetition
3. Add ε-noise (±6%) to prevent deterministic lock-in — the system should
   feel unpredictable even to itself
4. Pick the highest-scoring subtype after these adjustments

This means even within a puzzle type you cannot pattern-match your way to
success. If you've just done MARVEL Spatial Relationship twice and gotten good
at it, the score rises above 0.78, the zone score drops to 0.10, and the
system will route you to a harder, less-practiced category.

---

## Why This Always Generates the Best Next Problem

The claim: *for any practice state, the system reliably routes you to the
highest-growth next problem*.

**It works because:**

1. **Continuous decay** — familiarity scores are always live. The moment you
   finish a problem, the clock starts on forgetting it. The system's view of
   your state is never stale.

2. **Reconstruction zone targeting** — the score function has a hard peak at
   ~42% familiarity. Problems you're either too good at or have fully forgotten
   score low. Only problems where memory is actively fragile score high. This
   is the precise condition where re-learning effort pays off most.

3. **Interference maximisation** — the session queue isn't just urgency
   ordering. It's urgency-weighted by cognitive distance. An urgent problem
   in the same cluster as the last one is ranked below a slightly less urgent
   problem from a maximally interfering cluster. This pushes session entropy
   as high as possible.

4. **Subtype entropy** — within a type, the repeat penalty and ε-noise ensure
   you can never develop a subtype-specific pattern. Even if you've mastered
   one variant, the system routes you to the hardest variant you haven't
   recently seen.

5. **Per-problem tracking** — state is tracked at `(type, subtype)` granularity.
   A strong performance in MARVEL Quantities doesn't mask a weakness in MARVEL
   3D Geometry. Each subtype has its own familiarity trajectory.

---

## Adding New Puzzle Types

The system is fully modular. Adding a new puzzle type requires exactly one
change in `static/entropy_engine.js` (and mirrored in `EntropyRotator.jsx`):

```js
newtype: {
  name: "New Puzzle Type",
  cluster: "rule_induction",         // cognitive cluster (drives interference)
  cognitiveLoad: 0.80,               // [0-1] working memory demand
  ruleVolatility: 0.85,              // [0-1] how fast rules decay
  surface: ["tag1", "tag2"],         // descriptive tags (not used in scoring)
  subtypes: [
    { id: "variant_a", label: "Variant A", cogLoad: 0.78, volatility: 0.82 },
    { id: "variant_b", label: "Variant B" },  // inherits type-level values
  ]
},
```

The session queue, subtype selector, decay sparklines, and interference matrix
all update automatically. No other code changes.

---

## Tuning Guide

| Parameter | Effect if too high | Effect if too low |
|---|---|---|
| `cognitiveLoad` | Type dominates session queue | Type rarely appears |
| `ruleVolatility` | Skill forgotten fast, scheduled often | Skill stays "known" too long |
| Pass gain `+0.15` | Familiarity rises quickly, exits zone fast | Stays in reconstruction zone too long |
| Fail penalty `-0.08` | Failures tank familiarity sharply | Failures have little scheduling impact |
| Noise ε `±6%` | Highly unpredictable selections | More deterministic routing |
| Repeat penalty `×0.15` | Never repeats a subtype | Can repeat same subtype immediately |

The current defaults are tuned to feel like a training session that is
challenging but not demoralising: you will see things you've partially
forgotten, you will switch cognitive domains frequently, and you will never
solve the same variant twice in a row. But you will always be operating near
the peak of the learning curve.

---

## State Persistence

All state is stored in `localStorage` under the key `entropy_state_v2`, keyed
by `"typeId::subtypeId"`. Both `app_v2.html` (via `entropy_engine.js`) and
`EntropyRotator.jsx` read and write this same key. The two interfaces share
live training state — playing puzzles in the main UI automatically updates the
rotation schedule shown in the React component, and vice versa.

State survives page reloads, browser restarts, and multiple tabs (last write
wins). It can be exported as a JSON snapshot via the browser console:

```js
JSON.parse(localStorage.getItem('entropy_state_v2'))
```
