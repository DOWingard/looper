# State & Intake

Where the loop's memory lives on disk, and what the orchestrator must collect from the user
before the first loop starts.

## Why state lives on disk

Context windows compact, rot, and hide what was said an hour ago behind summaries no one
wrote. A file on disk does not. Every fact the loop depends on is written to the workspace,
so any subagent can **crash, lose its session, and resume by reading a few files**. If the
live state cannot be described in a few files, it is too complicated.

## Workspace layout

Created in the directory where `/looper` is invoked:

```
.looper/<slug>/
├── state/
│   ├── contract.md          negotiated rubric: N criteria in 4 categories, each 0–10 + anchors
│   ├── feature_list.json    planner's sprint spec
│   ├── progress.md          current state: what's built, what's next
│   ├── log.md               append-only event log:  ## [YYYY-MM-DD] op | title
│   ├── evals.jsonl          one record per evaluated cycle (the objective-function history)
│   └── restart-brief.md     present only after a restart; the cross-loop handoff
└── build/                   the target software the generator produces
```

`<slug>` is a short kebab-case name derived from the target build.

### The 3-file recovery set

A resuming agent reconstructs *what to do next* from **`contract.md` + `progress.md` +
`log.md`** alone — the rubric it is graded against, the current state, and the ordered
history of operations. `evals.jsonl` and `restart-brief.md` are the analysis layer on top:
needed to reason about *trajectory*, not to resume *position*.

## `evals.jsonl` record schema

One JSON object per line, appended by the evaluator after it grades a cycle. Example in
`assets/templates/evals.example.jsonl`.

```json
{
  "loop": 1,                       // which initialization (increments on restart)
  "cycle": 3,                      // generate→evaluate iteration within this loop
  "ts": "2026-06-29",
  "scores": {"d1": 8, "o1": 7, "c1": 6, "f1": 9},   // per-criterion 0–10, keyed by criterion id
  "categories": {"design": 7.5, "originality": 7.0, "craft": 6.0, "functionality": 9.0},
  "fitness": 0.74,                 // from `fitness.py score` over the flat score vector
  "attractor": "converging",       // from `fitness.py classify` after this record is written
  "note": "Functionality strong; craft lags on error states — see contract c3, c5."
}
```

The `fitness` field is the one `classify` reads, so it must be present on every record. The
evaluator computes it with `python scripts/fitness.py score --vector <scores>` — never by
hand.

## Intake handshake

Before the first loop, the orchestrator assembles enough to make convergence *quantitatively
possible*. **Pull every answer from the conversation first**; ask the user only for what is
genuinely missing. Required:

1. **Target build** — what is being built (app / front-end / system design / any
   non-trivially complex software). Drives the slug and the criteria count.
2. **≥ 3 good targets** (references the result should resemble). Each may be **qualified** by
   category — "good *design* reference", "good *functionality* reference", etc. A qualified
   target is treated as generally good, with primary weight on its named category.
3. **≥ 3 anti-targets** (bad examples to avoid), optionally qualified the same way.
4. **Custom requirements** — ask explicitly whether the user wants to add any specific
   requirements, per category or overall, beyond the initial description. These become
   criteria that are evaluated and selected for.
5. **Category priority / weighting** — ask whether any of the four categories matter more
   (e.g. `functionality > design`, or `originality & craft > design & functionality`). This
   sets criteria allocation and subagent focus order (below).
6. **Stopping fitness** — ask whether they want a custom target in `(0,1)`. Default `0.95`,
   or a settled asymptote in `[0.85, 0.95]`.

### Sufficiency gate

If, after pulling from the conversation, there is not enough to write a **strict rubric with
calibration anchors** such that fitness can converge quantitatively, **request more** — more
examples, more qualifiers, sharper requirements — before starting. Specifically, you need
enough to anchor what a 0 and a 10 look like for each category. A vague rubric produces a
fitness number that converges to nothing meaningful.

## Sizing: target → criteria count

The orchestrator classifies the target and picks the total criteria count:

| Target class | ~Criteria |
|---|---|
| Website / landing page | 15 |
| Small app | 27 |
| Medium app | 40 |
| Large app | 65 |

These are anchors, not limits — interpolate for in-between targets. More criteria = finer
gradient for the generator to climb, at higher evaluation cost per cycle.

## Allocating criteria across the four categories

All criteria are grouped into **design, originality, craft, functionality**. Allocation is
how **weighting is realized**: a higher-priority category gets *more* criteria, so it
contributes more terms to `⟨X|X⟩` and thus moves fitness more. There are **no separate
weight multipliers** — the fitness function stays a pure RMS (see
`fitness-and-convergence.md`); importance is structural.

Procedure:

1. **Floor.** Give every category a minimum (default **≥ 3**) so none can be neglected —
   this is also the guardrail against L2's "spike-a-few" incentive.
2. **Rank-weight the remainder.** Distribute the criteria left after the floors in
   proportion to the priority order. With no stated priority, split evenly.
3. **More metrics for higher-priority categories** means the evaluator writes *more distinct
   ways to score* that category — not that it ignores the others. Every category is still
   optimized; the important ones simply have a larger surface to be scored on.

Worked example — medium app (40), priority `originality > functionality > design > craft`:
floors take 12 (3×4); the remaining 28 split by rank weights 4:3:2:1 →
originality ≈ 11, functionality ≈ 8, design ≈ 6, craft ≈ 3, plus floors →
**originality 14, functionality 11, design 9, craft 6** (= 40).

Subagent **focus order** follows the same priority: the generator optimizes the
higher-priority categories first, without abandoning the rest.
