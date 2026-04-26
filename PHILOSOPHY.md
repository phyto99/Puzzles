# Puzzle System — Philosophy & Integration Guide

## Mission

**Make humans smarter. Indefinitely.**

This system exists to give any person access to an infinite, always-challenging practice environment for abstract reasoning. The north star: a player should never be able to outgrow it. Every time they master a pattern, a harder or stranger variant should be waiting.

This is not a benchmarking tool for AI. It is a cognitive gym for humans — one that happens to use AI-research-grade puzzle formats as its raw material.

---

## Core Design Principles

### 1. Infinite Depth Over Breadth
A puzzle type is only worth adding if it has genuine depth — meaning a human can get meaningfully better at it over time, and will still be challenged after 1000 reps. Novelty alone is not enough. Depth is the filter.

### 2. Adaptive Challenge
The system should always be slightly ahead of the player. Difficulty must scale. A puzzle type with no difficulty axis (no way to make it harder) is a dead end and should be deprioritized.

### 3. Fun Is Not Optional
Hard puzzles that are not engaging are just homework. The format, feedback loop, and pacing of each puzzle type must feel like a game, not a test. Immediate feedback, clean UI, no dead time.

### 4. Pro-Humanity Framing
We are aware that AGI systems can and do outperform humans on most of these puzzle types. That is not the point of this system. **The player is competing against their own past self, not against a machine.**

On the topic of "AI vs Human" modes: this is interesting and worth exploring, but must be handled with care. A human losing to an AI at chess is instructive. A human losing to an AI at every cognitive task, repeatedly, with no path to improvement, is demoralizing — and goes against the mission. Any AI-opponent feature must be designed to teach, not to crush. If we can't make it motivating, we don't ship it.

---

## Puzzle Taxonomy

### Category 1 — Abstract Pattern Recognition
*Classic IQ-test matrix format. Observe a pattern across panels; identify the missing one.*

| Puzzle | Format | Notes |
|---|---|---|
| **I-RAVEN** | 3×3 matrix → pick from 8 | Procedural; rule vocabulary: progression, symmetry, arithmetic |
| **PGM** | 3×3 matrix → pick from 8 | DeepMind PGM rule vocabulary (XOR, OR, AND, consistent_union) |
| **MARVEL** | Abstract visual reasoning matrix | Pre-rendered panels from published dataset |
| **Visual Analogy** | A:B :: C:? → pick from 4 | Custom SVG; transformation-based (fill, size, shape, count) |

### Category 2 — 3D Scene Understanding
*Reason about spatial relationships and causal structure in rendered 3D environments.*

| Puzzle | Format | Notes |
|---|---|---|
| **ACRE** | Causal reasoning over block scenes | Subprocess isolated; Three.js renderer |
| **CLEVR** | NL question over 3D scene | Count, exist, query, compare; same Three.js renderer as ACRE |

### Category 3 — Grid / Rule Induction
*Infer a transformation rule from examples and apply it. Open-ended output.*

| Puzzle | Format | Notes |
|---|---|---|
| **ARC-AGI-1** | Grid transformation from examples | 400 tasks; original benchmark |
| **ARC-AGI-2** | Same format, harder | 1000 tasks; current frontier |
| **ARC-AGI-3** | Interactive multi-step environment | Real-time session; action-space navigation |

### Category 4 — Concept Learning from Examples
*Infer a hidden rule from positive/negative exemplars.*

| Puzzle | Format | Notes |
|---|---|---|
| **Bongard-LOGO** | 6 positive / 6 negative → classify test | Custom SVG; rule is a visual predicate |
| **PuzzleVQA** | Visual pattern + NL question | Many pattern types; PIL-based generation |

### Category 5 — Interactive Logic Puzzles
*Classic structured logic and deduction puzzles with discrete rule sets.*

| Puzzle | Format | Notes |
|---|---|---|
| **RLP (Simon Tatham)** | ~40+ puzzle types (Mines, Solo, Net, Fifteen...) | WSL subprocess; full game engine; RL-style action space |

---

## What Counts as a New Puzzle Type

A new puzzle is worth integrating if it clears all three of these:

**1. Novel reasoning demand**
Does it train a cognitive skill we don't already have? If it's another 3×3 matrix format with the same rule types as I-RAVEN and PGM, it's redundant unless it adds a meaningfully different rule vocabulary or generation axis.

**2. No superior existing coverage**
If we already have a puzzle type that covers the same reasoning skill *better* (richer generation, cleaner UI, deeper difficulty curve), don't add the weaker one. If the new one is clearly better, replace the existing version — don't keep both.

**3. Self-contained generation**
The system should work offline. Puzzles must generate entirely in memory from local code or local data files. No live API calls, no network dependencies, no HuggingFace endpoint calls at generation time. Pre-downloading datasets to local disk is fine.

---

## What We Deliberately Avoid

- **Benchmarking-first design.** We are not building a leaderboard or accuracy tracker for AI models. Those exist elsewhere.
- **Grinding the same format forever.** If a puzzle type has no difficulty ceiling or no variety, it turns into rote memorization — not reasoning practice.
- **Demoralizing human-vs-AI framing.** AI performance on these tasks is irrelevant to the player's experience. Don't surface it unless it's pedagogically useful.
- **Network-dependent generation.** Fragile, slow, rate-limited. Hard rule: generation must be deterministic and local.

---

## Backlog & Shelved Implementations

### VisuLogic *(shelved — too difficult to implement cleanly)*
- What it is: HuggingFace-hosted visual logic dataset; diverse reasoning types including spatial, numerical, and relational.
- Why shelved: Images served via live HuggingFace API calls; base64 display in frontend was broken; data parsing differed between eval and train splits. Not worth the fragility.
- **Slight priority bias when reconsidering:** VisuLogic covers reasoning types not well-represented elsewhere in the system (particularly multi-step relational reasoning over structured diagrams). Worth revisiting if/when the dataset becomes downloadable locally or a clean offline mirror exists.
- Implementation notes archived in [archive/VisuLogic_Implementation_Notes.txt](archive/VisuLogic_Implementation_Notes.txt).

---

## Integration Checklist (New Puzzle Type)

When a new benchmark or puzzle system appears and you're evaluating whether to add it:

- [ ] What reasoning skill does it train? Is that skill underrepresented in the current system?
- [ ] Does a better version of this already exist in the system? If yes, is the new one clearly superior?
- [ ] Can it generate puzzles fully offline, in memory, without network calls?
- [ ] Does it have a natural difficulty axis (something to make puzzles easier or harder)?
- [ ] Is there a clean single-problem generation path (not batch-only)?
- [ ] Can it fit the standard API contract: `GET /api/get_puzzle?generator_type=X` → `{context, choices, answer_index}`? (Or a documented variant for interactive/open-ended formats.)
- [ ] Does the UI feedback loop feel rewarding — not just correct/wrong, but *why*?

If all yes → integrate. If the current coverage of the same skill is weaker → replace, don't duplicate.

---

## Standard API Contract

All static (non-interactive) puzzle types expose:

```
GET /api/get_puzzle?generator_type=<name>
→ {
    generator_type: str,
    context: [...],        # images or structured data for the question
    choices: [...],        # answer options
    answer_index: int,     # 0-indexed correct answer
    metadata: {...}        # optional: difficulty, rule tags, explanation
  }
```

Interactive puzzle types (ARC-AGI-3, RLP) expose session-based endpoints:
```
POST /api/<type>/new    → {session_id, frame_b64, available_actions, ...}
POST /api/<type>/step   → {frame_b64, reward, done, ...}
POST /api/<type>/reset  → {frame_b64, ...}
```

Open-answer / word-problem formats (future) should target:
```
GET /api/get_puzzle?generator_type=<name>
→ {
    generator_type: str,
    question: str,
    answer: str | null,    # null if human-judged
    explanation: str
  }
```

---

## On Word Problems and Open-Answer Formats

Word problems and open-answer reasoning puzzles are **first-class citizens** of this system, not second-class citizens behind visual IQ tests. The visual matrix format is historically prominent in AI benchmarks, but it is one axis of reasoning — not the whole space.

Target areas for future open-answer puzzle types:
- Logical deduction chains (verbal)
- Mathematical word problems with novel framings
- Causal/counterfactual reasoning in language
- Spatial reasoning described in text
- Analogical reasoning in abstract or domain-specific language

The standard for adding these is identical to visual types: novel reasoning demand, no superior existing coverage, self-contained generation.

---

## Long-Term Vision

A person who practices consistently across all puzzle types in this system should develop:
- Stronger pattern recognition across visual and abstract domains
- Better inductive reasoning (inferring rules from examples)
- Improved spatial and causal reasoning
- Faster hypothesis generation and elimination
- Comfort with novel problem structures — the skill of learning to learn

This is the human cognitive stack that matters most in a world where AI handles routine tasks. This system is a deliberate investment in that stack.

We are pro-humanity. The point is not to measure how far behind humans are. The point is to make the gap smaller — one puzzle at a time.
