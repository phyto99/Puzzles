# Research Log

Append-only. Every research session gets one entry. Never edit past entries.

**Entry format:**
```
## YYYY-MM-DD | [AI Engine] | [Researcher]
**Domain searched:** [cognitive domain or search angle]
**Prompt scope:** [broad survey / narrow sub-domain / specific gap]
**Finds (added to registry):** [list of names → status assigned]
**Rejected (added to registry):** [list of names → rejection reason summary]
**Shelved (added to registry):** [list of names → blocker summary]
**Remaining open gaps in this domain after this search:**
- [gap 1]
- [gap 2]
**Recommended next search angle:** [what a follow-up researcher should target]
```

---

## 2026-04-26 | claude-sonnet-4-6 | phyto99

**Domain searched:** General survey — all cognitive domains not covered by existing implemented puzzles

**Prompt scope:** Broad survey across all open cognitive skill gaps

**Finds (added to registry):**
- Reasoning-Gym (`open-thought/reasoning-gym`) → `[QUEUED]` — covers ~40 sub-types: knights_knaves, syllogisms, propositional_logic, circuit_logic, self_reference, word_ladder, sentence_reordering, countdown/24-game, cryptarithmetic, number_sequences, zebra_puzzles, survo, kakurasu
- CLadder (`causalNLP/cladder`) → `[QUEUED]` — causal/counterfactual reasoning, Pearl hierarchy
- StepGame (`ZhengxiangShi/StepGame`) → `[QUEUED]` — text-only multi-hop spatial reasoning
- ZebraLogic / Logic Grid (`tuchandra/zebra` + `allenai/ZebraLogicBench`) → `[QUEUED]` — constraint satisfaction logic grid
- ProntoQA (`asaparov/prontoqa`) → `[QUEUED]` — formal proof chain tracing
- RuleTaker (`allenai/ruletaker`) → `[QUEUED]` — rule-following deduction in prose
- FOLIO (`Yale-LILY/FOLIO`) → `[QUEUED]` — expert FOL in fluent English, 1,430 items (challenge mode)
- MathNet (`ShadeAlsha/MathNet`) → `[QUEUED]` — 30K+ olympiad problems
- LogiQA 2.0 (`csitfun/LogiQA2.0`) → `[QUEUED]` — 35K LSAT-style argument questions
- AR-LSAT (`LogiTorch/logitorch`) → `[QUEUED]` — 2,046 real LSAT items
- CLUTRR (`facebookresearch/clutrr`) → `[QUEUED]` — kinship reasoning; NOTE: CC-BY-NC license

**Rejected (added to registry):**
- GSM8K → static 8.5K, Reasoning-Gym strictly better
- OmniMath → subset of MathNet, smaller
- RiddleSense → finite riddles, no depth
- CRT → no generator, 3-7 static items
- Enigmata → overlaps Reasoning-Gym, less mature
- WinoGrande → finite, narrow, low ceiling
- SpatialBench/CVBench → requires images/video, not text spatial

**Shelved (added to registry):**
- Time Puzzles (arXiv:2601.07148) → no public code as of 2026-04-26; revisit when authors release generator

**Remaining open gaps in this domain after this search:**
- Temporal / chronological reasoning (no generator found with public code)
- Cipher / cryptographic reasoning (Reasoning-Gym may have partial coverage — verify)
- Musical / rhythmic pattern reasoning (no benchmark found)
- Game theory / strategic reasoning (no generatable benchmark found)
- Probabilistic / Bayesian reasoning (no generatable benchmark found)
- Epistemic / theory-of-mind reasoning (beyond basic knights-and-knaves)
- Mechanical / physical intuition in language
- Narrative coherence / story consistency
- Analogical reasoning in language only (non-visual)
- Economic / resource reasoning

**Recommended next search angle:**
- Search specifically for Bayesian reasoning generators and probabilistic puzzle benchmarks
- Search for epistemic logic / theory-of-mind puzzle generators (multi-level "I know that you know")
- Search for cipher/code-breaking puzzle generators (distinct from cryptarithmetic)
- Check whether Reasoning-Gym's full 105-task list covers any of the remaining gaps (read the full task inventory at github.com/open-thought/reasoning-gym/tree/main/reasoning_gym/games)
- Search for narrative coherence / story-inconsistency benchmarks with generator code
