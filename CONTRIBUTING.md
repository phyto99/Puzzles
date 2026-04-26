# Contributing to the Puzzle System

This document explains how to research new puzzle types, evaluate them against the system's philosophy, invent entirely new categories, and coordinate with other contributors so no two people duplicate work.

Read [PHILOSOPHY.md](PHILOSOPHY.md) before anything else. Read [PUZZLE_REGISTRY.md](PUZZLE_REGISTRY.md) before researching anything.

---

## The Coordination System — Avoiding Overlap

Research is expensive. Two people searching the same cognitive domain with the same prompt wastes effort that could have expanded coverage into new territory.

**Before starting any research session:**

1. Open [RESEARCH_LOG.md](RESEARCH_LOG.md)
2. Find the most recent entry for your intended search area
3. Note the date, AI engine, and coverage gaps listed in that entry
4. If it was researched recently (< 2 weeks) with the same engine, either:
   - Search a different cognitive domain (see **Open Gaps** in the Coverage Map)
   - Use a different AI engine (different models have different training distributions and will surface different papers)
   - Narrow to a specific sub-angle the previous search flagged as uncovered

5. After your session, **add an entry to RESEARCH_LOG.md** immediately. Log what you searched, what engine, what you found, and what gaps remain open.

The log is append-only. Never edit past entries.

---

## How to Research New Puzzle Types

### Step 1 — Read the Coverage Map first

[PUZZLE_REGISTRY.md](PUZZLE_REGISTRY.md) has a **Coverage Map** at the bottom listing every cognitive skill and whether it's covered. Start with `OPEN GAP` rows. If a gap has a recent log entry (< 2 weeks), pick a different gap.

### Step 2 — Construct your research prompt

Every effective research session needs a scoped prompt. Use this template when working with an AI assistant:

```
Research puzzle/benchmark datasets and generators for the cognitive domain: [DOMAIN].

Context — already implemented or queued in this system (do NOT suggest these):
[paste the current LIVE + QUEUED list from PUZZLE_REGISTRY.md]

Philosophy constraints (all must pass):
1. Novel cognitive skill not already covered, OR demonstrably deeper/richer than existing
2. Fully offline/local generation — no live API calls at puzzle generation time
3. Depth — humans can improve meaningfully over time; not memorizable
4. Natural difficulty axis (easy → hard variants exist or are configurable)
5. Open-answer and word problem formats are welcome alongside visual formats

For each candidate, find:
- GitHub repo + license
- Paper / source
- What cognitive skill it trains (specific, not vague)
- Procedural generator (infinite) or dataset (finite)?
- Offline feasibility
- Difficulty scaling method
- Format: multiple choice / open answer / interactive
- Implementation complexity estimate

Prioritize generators over static datasets. Prioritize Apache 2.0 / MIT licenses.
Flag non-commercial licenses explicitly.
```

### Step 3 — Where to search

**Primary sources (check all of these):**

| Source | What to find there |
|---|---|
| **Papers With Code** (paperswithcode.com) | Benchmarks with linked code; filter by "reasoning", "logic", "spatial", your target domain |
| **Hugging Face Datasets** (huggingface.co/datasets) | Filter by task: `question-answering`, `text-classification`, `reasoning`; look for generator code in linked repos |
| **GitHub search** | `"puzzle generator" python`, `"reasoning gym"`, `"benchmark generator" reasoning [domain]` |
| **Semantic Scholar** (semanticscholar.org) | Search "[domain] reasoning benchmark" sorted by citations; recent papers (2022–2026) |
| **arXiv cs.AI + cs.CL** (arxiv.org) | Search "procedural [domain] reasoning" or "[skill] benchmark generator" |
| **NeurIPS / ICML / ICLR proceedings** | Workshop tracks on "reasoning", "benchmarks", "generalization" |
| **AllenAI (allenai.org/data)** | Consistently releases high-quality reasoning datasets with open licenses |
| **DeepMind / Google Research GitHub** | Strong abstract reasoning and planning puzzle generators |
| **OpenAI Evals** (github.com/openai/evals) | Evaluation tasks that can be repurposed as puzzle generators |

**Search queries that work well:**

```
site:github.com "[cognitive domain] puzzle generator" python
site:arxiv.org "procedural generation" "[cognitive domain]" reasoning
"reasoning benchmark" "[cognitive domain]" generator filetype:py
paperswithcode "[cognitive domain]" reasoning benchmark -vision
```

**Red flags to filter out immediately:**
- "Requires GPT-4 to score" — not self-contained
- "HuggingFace API at inference time" — violates offline rule
- "Human annotators required for new samples" — not generatable
- "Static dataset only, no generator" — finite; check if size is sufficient before rejecting
- License: CC-BY-NC (non-commercial only) — flag, do not reject outright

### Step 4 — Evaluate each candidate

Run every candidate through this checklist before adding it to the registry:

```
[ ] What cognitive skill does it train?
[ ] Is that skill listed as OPEN GAP in the Coverage Map?
    If no: is it demonstrably richer/harder than the existing LIVE/QUEUED entry for that skill?
[ ] Can it generate puzzles fully offline (no network calls at generation time)?
[ ] Does it have a natural difficulty axis?
[ ] Is there a single-puzzle generation path (not batch-only)?
[ ] License: commercial-friendly? (MIT / Apache preferred; CC-BY-NC requires flag)
[ ] Implementation complexity: 1-3 scale (Low / Moderate / High)?
```

Pass all 6 → propose as `[QUEUED]`.
Fails offline or no difficulty axis → `[REJECTED]` with reason.
Interesting but blocked → `[SHELVED]` with specific blocker and revisit condition.

### Step 5 — Submit findings

Update [PUZZLE_REGISTRY.md](PUZZLE_REGISTRY.md):
- Add new entries in the appropriate category with correct status tag
- If a new cognitive skill category, add a new section
- Update the Coverage Map at the bottom

Add a session entry to [RESEARCH_LOG.md](RESEARCH_LOG.md) immediately.

---

## How to Invent New Puzzle Categories

Not all valuable puzzle types exist yet as published benchmarks. Sometimes the right move is to design one from scratch.

### When to invent

Invent a new puzzle type when:
- A cognitive skill is in the Open Gaps list and no published benchmark covers it
- You have a novel format idea that trains something not otherwise trainable
- An existing puzzle type has a variant with clearly higher depth or better difficulty scaling

### The invention template

Use this structure to spec a new puzzle type:

```markdown
## [PROPOSED] Name

**Cognitive skill trained:** [specific, not vague — e.g. "multi-step Bayesian belief updating"
not "reasoning"]

**Why this gap matters:** [What can a person do better in real life if they train this skill?
Tie it to the mission: making humans more cognitively capable.]

**Format:** [How does the puzzle look? What does the player see and do?]
  - Input: [what the player is shown]
  - Task: [what the player must do]
  - Answer: [multiple choice / open text / interactive / structured input]
  - Feedback: [how does the player know they're right or wrong?]

**Generation approach:** [How would you generate instances procedurally?]
  - What varies between instances?
  - What rules ensure solvability?
  - What parameters control difficulty?

**Difficulty axis:** [Specifically what makes this harder?]
  - Easy: [description]
  - Hard: [description]

**Prior art:** [Does anything like this exist? Why is it not sufficient?]

**Estimated implementation complexity:** Low / Moderate / High
**Dependencies:** [Python libraries, data, models, or external tools needed]
```

### Cognitive skill inventory for invention

These are skills that matter for human reasoning and currently have no coverage in this system. Use this list as a starting point:

**Temporal reasoning**
- Chronological ordering of events from partial information
- Duration inference ("Event A lasted until B started; B took twice as long as C...")
- Tense and sequence reasoning from natural language

**Probabilistic / Bayesian reasoning**
- Updating beliefs given new evidence
- Base rate neglect puzzles (designed to surface and correct the bias)
- Conditional probability inference from word descriptions

**Game theory / strategic reasoning**
- Minimax in described two-player scenarios
- Nash equilibrium identification from payoff descriptions
- Common knowledge and epistemic logic ("I know that you know that I know...")

**Cipher and cryptographic reasoning**
- Substitution cipher solving
- Pattern extraction from encoded sequences
- Structural analysis of systematic transformations

**Mechanical / physical intuition**
- Lever/pulley systems described in text
- Fluid dynamics ("if valve A opens, what happens to pressure in chamber C?")
- Gear chains and mechanical linkage inference

**Narrative coherence**
- Identify the logically inconsistent sentence in a short story
- Determine what must have happened between two described states
- Narrative causation chains (why did X happen?)

**Analogical reasoning (language-only)**
- Abstract relational analogies in prose form ("Lawyer is to courtroom as __ is to __")
- Cross-domain structural mapping
- Metaphor extension and inference

**Musical / rhythmic pattern**
- Identify the rule governing a sequence of described rhythmic patterns
- Predict the next element in a melodic/rhythmic sequence (described symbolically)

**Economic / resource reasoning**
- Trade-off optimization under described constraints
- Arbitrage and comparative advantage inference
- Multi-step resource allocation chains

**Epistemic / perspective-taking**
- Theory of mind ("what does Alice believe that Bob believes?")
- Knowledge asymmetry inference
- False belief detection (Sally-Anne style, extended to 3+ levels)

---

## Integration Standard (Technical)

When a puzzle type moves from `[QUEUED]` to implementation, it must conform to one of these two API contracts.

### Static puzzles (most types)

```
GET /api/get_puzzle?generator_type=<name>[&difficulty=<level>]
→ {
    "generator_type": str,
    "context": [...],        # images (base64) or structured text/data
    "choices": [...],        # answer options (omit for open-answer)
    "answer_index": int,     # 0-indexed (omit for open-answer)
    "answer": str,           # for open-answer formats
    "explanation": str,      # optional; shown after answer
    "metadata": {
        "difficulty": str,
        "cognitive_skill": str,
        "source": str
    }
}
```

### Interactive / session-based puzzles

```
POST /api/<type>/new    → {session_id, frame_b64, available_actions, state, ...}
POST /api/<type>/step   → {frame_b64, reward, done, state, ...}
POST /api/<type>/reset  → {frame_b64, ...}
```

### Self-graded / open-answer puzzles

When correct answers cannot be verified automatically:
- Return `"answer": null` in the response
- The UI presents a "Show Answer" button after the player submits
- The player self-grades (thumbs up / down or star rating)
- This feedback can be logged for optional difficulty calibration

---

## Quality Bar

A puzzle type is ready to ship when:

- [ ] `single_generator.py` or equivalent creates one puzzle fully in memory, no disk writes
- [ ] All images returned as base64 strings
- [ ] The generator runs in < 2 seconds per puzzle on a mid-range CPU
- [ ] At least 3 distinct difficulty levels are demonstrably different
- [ ] The UI feedback loop (correct/wrong → next puzzle) works without dead time
- [ ] The puzzle type is added to PUZZLE_REGISTRY.md as `[LIVE]`
- [ ] The Coverage Map is updated

---

## Licensing Reference

| License | Commercial use | Modify | Distribute | Notes |
|---|---|---|---|---|
| MIT | Yes | Yes | Yes | Preferred |
| Apache 2.0 | Yes | Yes | Yes | Preferred |
| CC-BY 4.0 | Yes | Yes | Yes | Must attribute |
| CC-BY-NC 4.0 | **No** | Yes | Yes | Flag in registry; OK for personal/educational use |
| CC-BY-SA 4.0 | Yes | Yes | Yes (same license) | Copyleft — derivatives must share-alike |
| GPL | Yes | Yes | Yes (same license) | Strong copyleft |
| No license stated | Assume restricted | — | — | Contact authors before using |
