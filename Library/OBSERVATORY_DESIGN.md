# Observatory Design Decisions
*Append-only. Every locked decision goes here. Do not re-litigate without new evidence.*

---

## LOCKED DECISIONS — Do Not Revisit

### OD-01 · 8 Criteria = Source Prestige Only
**Decision:** The 8 criteria (RAR, INV, BAR, PED, ARC, LEG, TRN, FRN) measure properties of the *source itself* — its prestige, depth, pedigree, legitimacy. They do NOT attempt to measure human development outcomes.

**Reason:** Human development from any external source is too variable to estimate reliably. We cannot track when a student leaves our system to engage with an external site. The Observatory functions as a **library**, not a personal coach. Source quality is the appropriate and measurable signal.

**Implication:** Do not add criteria like "pedagogical scaffolding," "feedback quality," or "difficulty ramp." These belong in the local puzzle generators (which we control), not here.

---

### OD-02 · Rarity Is Intentional
**Decision:** Annual and rare events score higher on Rarity than continuous sources. This is correct and intentional.

**Reason:** The Observatory is partly **aspirational** — a curated atlas of peak human puzzle culture, not a daily practice scheduler. Annual events (WPC, IMO, MIT Mystery Hunt) carry ritual weight, community convergence, and a once-a-year urgency that continuous access cannot replicate. Rarity here means *ceremony*, not *scarcity of content*.

**Implication:** Do not "fix" the Rarity criterion to favor continuous sources. The local puzzle generators (ARC-AGI, Tatham, etc.) provide infinite continuous practice. The Observatory marks the elite seasonal summits worth aiming for.

---

### OD-03 · The Observatory Serves Four Purposes Simultaneously
**Decision:** The system must function as all four simultaneously, with information displayed at maximum density to serve each:

1. **(A) Personal practice calendar** — what is releasing soon, what is evergreen, what should I engage with now
2. **(B) Discovery / reference** — find sources across domains I haven't explored yet
3. **(C) Aspirational display** — nostalgic, monumental view of the peak of human puzzle culture
4. **(D) Research tool** — find new puzzle traditions to potentially integrate into the local training system

No purpose outranks another. Design all views (Orbital, Triage, Matrix, Scatter, Skill Map) to serve the union of these needs.

---

### OD-04 · Novel > Tradition by Preference; Tradition Has Specific Value
**Decision:** When researching new sources, novel categories are preferred over additional sources in well-covered domains. However, tradition earns its weight and should not be systematically penalized.

**What tradition uniquely provides:**
- **Constraint refinement over decades** — rules have been tested against thousands of solutions; edge cases eliminated; difficulty genuinely calibrated (not estimated)
- **Archive depth** — decades of accumulated problems enables a practitioner to start trivial and ascend to world-class within one tradition
- **Pedigree transfer** — demonstrable proof that humans can master it (motivationally critical per PHILOSOPHY.md)
- **Community meta-knowledge** — established vocabulary, canonical technique names, known failure modes; all accelerate learning
- **Legitimacy as a difficulty signal** — if the world's best minds have worked on something for 100 years and hard problems remain, the difficulty is real, not manufactured

**What novelty provides that tradition cannot:**
- No pre-existing "moves" to memorize — forces genuine reasoning, not pattern recall
- Signals the frontier of what structured human thought can explore
- Higher transfer potential (mastering genuinely new systems builds more generalizable reasoning)
- Discovery motivation (no one has solved this before)

**Resolution:** Keep Pedigree and Archive as full criteria (tradition earns them honestly). Ensure Invention (INV) is weighted equally — a highly novel source with 0 tradition can still score maximum on INV, BAR, TRN, FRN. The system is not biased toward tradition; it is balanced.

---

### OD-05 · Integration Path — Observatory ↔ Training System
**Decision:** The Observatory is deliberately semi-separate from the local training system, like a library adjacent to a gym. The integration is **one-directional and recommendation-only**:

- Local generator performance (entropy engine cluster scores) → informs which observatory sources to surface in Triage
- Observatory does NOT attempt to track engagement with external sites
- A future "Bridge" layer reads entropy_engine cluster performance and surfaces relevant observatory sources

See `PRACTITIONER_BRIDGE_DESIGN.md` for the full architecture.

---

## CRITERIA DEFINITIONS (v3 — in effect)

| ID | Name | 0 | 1 | 2 | 3 |
|---|---|---|---|---|---|
| RAR | **Rarity / Ritual** | No schedule; ad hoc | Irregular but periodic | Monthly or bimonthly | Annual or rarer; carries ceremony |
| INV | **Invention** | Reproduces existing forms | Extends existing forms | Significant novel rules | Creates a new *category* of solving |
| BAR | **Barrier** | Open to anyone | Hobbyist investment required | Near-expert required | Near-professional / genius filter |
| PED | **Pedigree** | No elite engagement | Some competition-level solvers | National/regional champions | World champions, olympiad medalists |
| ARC | **Archive** | No archive | Partial, unsearchable | Good archive, growing | Deep, searchable, annotated, decades |
| LEG | **Legitimacy** | No backing | Respected community backing | Significant institutional support | University / federation / agency / ancient society OR undisputed community canonical status |
| TRN | **Transcendence** | Purely mechanical | Occasional insight moment | Frequent "aha!"; aesthetic beauty | Shifts how solver perceives logic / language / reality |
| FRN | **Living Frontier** | No open problems; finite | A few hard problems remain | Active unsolved problems | Genuine open problems resist top solvers for years; OR inexhaustible creative depth that has never reached a ceiling despite decades of expert production |

**Changes from v2:**
- `INS` (Institution) → `LEG` (Legitimacy): now includes community canonical status alongside institutional backing; removes Western-academic bias
- `UNS` (Unsolved Depth) → `FRN` (Living Frontier): now explicitly includes "inexhaustible creative depth" as an alternative to formal open problems; removes systematic math-domain bonus

**Threshold:** 13/24 retained. **Soft rule added:** A source scoring 0 on INV and 0 on BAR is auto-rejected regardless of total (it is neither novel nor difficult — a reference document, not a puzzle source).

---

## OPEN QUESTIONS (not yet locked)

### OQ-01 · Skill Map Axis Positions
Current X/Y positions of categories on the Formal↔Creative / Individual↔Communal axes are hypothesis values assigned by the developer. Not empirically grounded. Options:
- (a) Label as hypotheses in UI (implemented)
- (b) Community voting via a future survey
- (c) Derive from semantic analysis of source descriptions

Status: (a) done. (b)/(c) deferred.

### OQ-02 · Scatter Plot X Axis
"Engagement Cadence" axis maps weekly→continuous on a non-linear scale. The axis is not a true continuum (a 72-hour annual hunt ≠ a 5-minute weekly crossword scaled by frequency). Current framing is functional but imprecise.

Possible fix: Replace with a "Sessions per Year" axis (estimated actual puzzle instances accessible annually) which IS a true numeric scale.

### OQ-03 · Database Migration
Current architecture: single HTML file, all data inline. Migration path under consideration:
1. → `sources.json` (data extraction, HTML fetches it) — zero cost, git-trackable
2. → Turso/libsql SQLite — if queries needed server-side
3. → Supabase — only if multi-user annotation or API needed

Decision: Deferred. Build the JSON extraction first when the RAW array exceeds manageable inline size.

---

## REJECTED APPROACHES (do not re-propose)

| Approach | Reason Rejected |
|---|---|
| Add "pedagogical scaffolding" criterion | OD-01: not the library's job |
| Penalize annual sources for low frequency | OD-02: rarity is intentional |
| Replace Rarity with "content volume per year" | OD-02: misses the ritual dimension |
| Score sources on human transfer/learning outcomes | OD-01: unmeasurable from outside |
| Single unified purpose for the Observatory | OD-03: all four purposes are permanent |
| Bias criteria toward novel over traditional | OD-04: balance; both earn their scores honestly |
| Track user engagement with external sites | OD-05: architecturally impossible; privacy concerns |
| Institution requires formal academic/government backing | LEG criterion redesign: community canonical status now qualifies |
| "Unsolved Depth" requires formal mathematical open problems | FRN criterion: inexhaustible creative depth now also qualifies for score 3 |
