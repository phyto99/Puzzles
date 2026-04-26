# Puzzle Registry

Master list of every puzzle type evaluated for this system. Before researching or proposing anything, scan this file to avoid duplicating work.

**Status tags:**
- `[LIVE]` — Implemented and working in the unified server
- `[QUEUED]` — Researched, decided to integrate, not yet built
- `[RESEARCHED]` — Evaluated, decision pending (see notes)
- `[SHELVED]` — Attempted or evaluated; blocked on a specific issue; revisit-worthy
- `[REJECTED]` — Evaluated and ruled out; do not re-propose without new justification

---

## Category A — Abstract Visual Pattern Recognition
*3×3 matrix or analogical panel formats. Observe a rule across panels; identify the missing one.*

| Status | Name | Source | Notes |
|---|---|---|---|
| `[LIVE]` | **I-RAVEN** | github.com/husheng-liu/I-RAVEN | Procedural 3×3 matrix; rule vocab: progression, symmetry, arithmetic; two modes (standard, mesh) |
| `[LIVE]` | **PGM** | Custom generator (`pgm_generator.py`) | DeepMind PGM rule vocab: XOR, OR, AND, consistent_union; 8 answer choices |
| `[LIVE]` | **MARVEL** | github.com/1171-jpg/MARVEL_AVR | Pre-rendered panel images; label JSON; 4 answer choices |
| `[LIVE]` | **Visual Analogy** | Custom generator (`analogy_generator.py`) | A:B::C:? SVG; transformations: fill, size, shape, count, border, rotation |

---

## Category B — 3D Scene Understanding
*Reason about spatial relationships, object properties, and causal structure in rendered 3D environments.*

| Status | Name | Source | Notes |
|---|---|---|---|
| `[LIVE]` | **ACRE** | github.com/WellyZhang/ACRE | Causal block scene reasoning; subprocess isolated; Three.js renderer |
| `[LIVE]` | **CLEVR** | Custom generator (`clevr_generator.py`) | NL questions over 3D scenes (count, exist, query, compare); reuses ACRE Three.js renderer |

---

## Category C — Grid / Rule Induction (Open-ended)
*Infer a transformation rule from examples and apply it. No fixed answer set.*

| Status | Name | Source | Notes |
|---|---|---|---|
| `[LIVE]` | **ARC-AGI-1** | github.com/fchollet/ARC-AGI | 400 tasks, original benchmark; colored grid transformation |
| `[LIVE]` | **ARC-AGI-2** | github.com/arcprize/ARC-AGI-2 | 1000 tasks, harder; same format |
| `[LIVE]` | **ARC-AGI-3** | Local environment files (MIT, ARC Prize Foundation) | Interactive multi-step sessions; 6 environment files implemented |

---

## Category D — Concept Learning from Examples
*Infer a hidden rule or concept from positive/negative exemplars.*

| Status | Name | Source | Notes |
|---|---|---|---|
| `[LIVE]` | **Bongard-LOGO** | github.com/NVlabs/Bongard-LOGO | 6 pos / 6 neg → classify test image; custom SVG generator |
| `[LIVE]` | **PuzzleVQA** | github.com/declare-lab/puzzlevqa | Visual pattern + NL question; 10+ PIL-based pattern generators |

---

## Category E — Interactive Logic Puzzles
*Structured logic and deduction with discrete rule sets; interactive game loop.*

| Status | Name | Source | Notes |
|---|---|---|---|
| `[LIVE]` | **RLP / Simon Tatham Puzzles** | chiark.greenend.org.uk/~sgtatham/puzzles | ~40 classic logic game types; WSL subprocess; Xvfb virtual framebuffer; RL-style action space |

---

## Category F — Deductive / Formal Logic (Language)
*Proofs, syllogisms, rule chains, and propositional logic expressed in natural or formal language.*

| Status | Name | Source | Notes |
|---|---|---|---|
| `[QUEUED]` | **Knights and Knaves** | reasoning-gym (`knights_knaves`) | Truth-teller/liar constraint solving; Smullyan-style; part of Reasoning-Gym |
| `[QUEUED]` | **Syllogisms** | reasoning-gym (`syllogisms`) | Aristotelian syllogism reasoning; part of Reasoning-Gym |
| `[QUEUED]` | **Propositional Logic** | reasoning-gym (`propositional_logic`) | Boolean formula evaluation; part of Reasoning-Gym |
| `[QUEUED]` | **Circuit Logic** | reasoning-gym (`circuit_logic`) | Logic gate chain evaluation; part of Reasoning-Gym |
| `[QUEUED]` | **Self-Referential Logic** | reasoning-gym (`self_reference`) | Liar paradox variants; part of Reasoning-Gym |
| `[QUEUED]` | **ProntoQA** | github.com/asaparov/prontoqa (MIT) | Formal proof-chain tracing; fictional entities prevent shortcutting; hop depth configurable |
| `[QUEUED]` | **RuleTaker / ProofWriter** | github.com/allenai/ruletaker (Apache 2.0) | Rule-following deduction in prose English; True/False/Unknown; Problog backend |
| `[QUEUED]` | **FOLIO** | github.com/Yale-LILY/FOLIO (CC-BY 4.0) | Expert-written first-order logic in fluent English; 1,430 items; use as expert/challenge mode |

---

## Category G — Constraint Satisfaction (Language)
*Multi-entity constraint elimination and logic grid puzzles.*

| Status | Name | Source | Notes |
|---|---|---|---|
| `[QUEUED]` | **Zebra / Logic Grid Puzzles** | github.com/tuchandra/zebra (MIT, Python+z3); allenai/ZebraLogicBench (1K starter set) | Einstein-puzzle style; N entities × N attributes; 2×2 trivial → 6×6 very hard; interactive grid UI needed |
| `[QUEUED]` | **Zebra Puzzles (Reasoning-Gym)** | reasoning-gym (`zebra_puzzles`) | Same cognitive skill as above; may replace or complement the standalone generator |

---

## Category H — Causal and Counterfactual Reasoning
*Formal causal inference, intervention reasoning, and counterfactual thinking.*

| Status | Name | Source | Notes |
|---|---|---|---|
| `[QUEUED]` | **CLadder** | github.com/causalNLP/cladder (MIT) | Pearl's causal hierarchy: association/intervention/counterfactual; offline generator + 10K question dataset; expert human ~85% |

---

## Category I — Spatial Reasoning (Language, No Images)
*Deduce spatial relationships from textual descriptions only.*

| Status | Name | Source | Notes |
|---|---|---|---|
| `[QUEUED]` | **StepGame** | github.com/ZhengxiangShi/StepGame | k-hop text spatial chains; 8 directions; 50K pre-generated items (k=1–10); offline script for more |

---

## Category J — Relational / Compositional Reasoning
*Multi-hop inference over structured relations expressed in language.*

| Status | Name | Source | Notes |
|---|---|---|---|
| `[QUEUED]` | **CLUTRR** | github.com/facebookresearch/clutrr (CC-BY-NC) | Multi-hop kinship chain reasoning; k-hop difficulty axis; non-commercial license — flag if distributing |

---

## Category K — Argument Analysis (Informal Logic)
*LSAT-style reasoning: identify assumptions, flaws, inferences in natural arguments.*

| Status | Name | Source | Notes |
|---|---|---|---|
| `[QUEUED]` | **LogiQA 2.0** | github.com/csitfun/LogiQA2.0 | 35K LSAT-style argument questions; 4 subtypes (deduction, abduction, induction, assumption) |
| `[QUEUED]` | **AR-LSAT** | github.com/LogiTorch/logitorch (MIT) | 2,046 real LSAT analytical reasoning items; accessible via LogiTorch library |

---

## Category L — Word / Linguistic Puzzles
*Language-based pattern manipulation and combinatorial word challenges.*

| Status | Name | Source | Notes |
|---|---|---|---|
| `[QUEUED]` | **Word Ladder** | reasoning-gym (`word_ladder`) | Sequential single-letter word transformations; part of Reasoning-Gym |
| `[QUEUED]` | **Sentence Reordering** | reasoning-gym (`sentence_reordering`) | Temporal/sequential ordering of scrambled sentences; part of Reasoning-Gym |

---

## Category M — Arithmetic and Mathematical Reasoning
*Numerical puzzles, combinatorial arithmetic, and competition-level math.*

| Status | Name | Source | Notes |
|---|---|---|---|
| `[QUEUED]` | **Countdown / 24-Game** | reasoning-gym (`countdown`, `puzzle24`) | Arithmetic combination to reach target; part of Reasoning-Gym |
| `[QUEUED]` | **Cryptarithmetic** | reasoning-gym (`cryptarithm`) | Letter-to-digit substitution arithmetic; part of Reasoning-Gym |
| `[QUEUED]` | **Number Sequences** | reasoning-gym (`number_sequences`) | Next-term inductive reasoning (text, not visual); part of Reasoning-Gym |
| `[QUEUED]` | **Survo / Kakurasu** | reasoning-gym (`survo`, `kakurasu`) | Novel constraint arithmetic grid variants; part of Reasoning-Gym |
| `[QUEUED]` | **MathNet** | github.com/ShadeAlsha/MathNet (MIT) | 30K+ olympiad problems from 143 competitions, 1985–2025; filter for text-only; open answer / proof |

---

## Category N — Shelved
*Attempted or evaluated; blocked on a specific issue. Revisit-worthy with the right conditions.*

| Status | Name | Blocked By | Revisit When |
|---|---|---|---|
| `[SHELVED]` | **VisuLogic** | Live HuggingFace API for images; broken base64 display in frontend | Dataset becomes downloadable locally or a clean offline mirror exists |
| `[SHELVED]` | **Time Puzzles** (arXiv:2601.07148) | Interesting temporal constraint format; no public code found as of 2026-04-26 | Authors release generator code |

---

## Category O — Rejected
*Evaluated and ruled out. Do not re-propose without new justification that addresses the rejection reason.*

| Status | Name | Rejection Reason |
|---|---|---|
| `[REJECTED]` | **GSM8K** | Static 8.5K dataset, shallow difficulty ceiling; Reasoning-Gym arithmetic generators are strictly superior (infinite, configurable) |
| `[REJECTED]` | **OmniMath** | 4K problems, overlaps MathNet which has 30K+ with better coverage |
| `[REJECTED]` | **RiddleSense** | 5.7K riddles; once seen = known; no depth, not renewable |
| `[REJECTED]` | **CRT (Cognitive Reflection Test)** | No procedural generator exists; the 3–7 static items are finite by design |
| `[REJECTED]` | **Enigmata** | Overlaps Reasoning-Gym substantially; less mature tooling; no unique cognitive gap |
| `[REJECTED]` | **WinoGrande** | 44K items but finite, non-renewable; narrow skill (coreference); low depth ceiling |
| `[REJECTED]` | **SpatialBench / CVBench** | Requires images/video as input; does not fit text-only spatial reasoning constraint |
| `[REJECTED]` | **OmniMath** | Subset of MathNet, smaller, no generator |

---

## Coverage Map — Cognitive Skills vs. Status

| Cognitive Skill | Covered By | Status |
|---|---|---|
| Abstract visual pattern recognition | I-RAVEN, PGM, MARVEL | LIVE |
| Analogical transformation (visual) | Visual Analogy | LIVE |
| 3D spatial scene understanding | ACRE, CLEVR | LIVE |
| Causal scene reasoning (visual) | ACRE | LIVE |
| Grid rule induction (open-ended) | ARC-AGI 1/2/3 | LIVE |
| Concept learning from examples (visual) | Bongard-LOGO, PuzzleVQA | LIVE |
| Interactive structured logic games | RLP/Simon Tatham | LIVE |
| Syllogistic / propositional logic | Reasoning-Gym | QUEUED |
| Formal proof chain tracing | ProntoQA, RuleTaker | QUEUED |
| First-order logic (fluent English) | FOLIO | QUEUED |
| Constraint satisfaction (logic grid) | ZebraLogic | QUEUED |
| Causal / counterfactual reasoning | CLadder | QUEUED |
| Text-only spatial reasoning | StepGame | QUEUED |
| Multi-hop relational reasoning | CLUTRR | QUEUED |
| Informal argument analysis | LogiQA 2.0, AR-LSAT | QUEUED |
| Word / linguistic manipulation | Reasoning-Gym | QUEUED |
| Arithmetic combinatorics | Reasoning-Gym | QUEUED |
| Olympiad-level math | MathNet | QUEUED |
| **Temporal / chronological reasoning** | — | **OPEN GAP** |
| **Cipher / cryptographic reasoning** | — | **OPEN GAP** |
| **Musical / rhythmic pattern reasoning** | — | **OPEN GAP** |
| **Game theory / strategic reasoning** | — | **OPEN GAP** |
| **Probabilistic / Bayesian reasoning** | — | **OPEN GAP** |
| **Analogical reasoning (non-visual, language)** | — | **OPEN GAP** |
| **Mechanical / physical intuition** | — | **OPEN GAP** |
| **Narrative / story coherence reasoning** | — | **OPEN GAP** |
