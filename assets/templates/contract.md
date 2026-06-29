# Contract — {{slug}}

Negotiated between the generator and the evaluator from the planner's spec. **This, not the
spec, is what gets graded.** Every criterion is scored 0–10 with calibration anchors so the
score is objective and the fitness number means something.

- Target build: {{target}}
- Size class / criteria count: {{class}} / {{N}}
- Category allocation: originality {{n_o}} · functionality {{n_f}} · design {{n_d}} · craft {{n_c}}
- Priority: {{priority}}
- Stopping target fitness: {{target_fitness}}
- Calibration references — good: {{good_refs}} · anti: {{anti_refs}}

Each criterion id is used as the key in `evals.jsonl.scores`. Keep ids stable across cycles
so the trajectory stays comparable.

## Functionality ({{n_f}})

| id | assertion (scored 0–10) | 0 = | 10 = |
|----|-------------------------|-----|------|
| f1 | The primary flow completes end to end without error | crashes or dead-ends on the happy path | every primary flow completes, including the awkward inputs |

## Design ({{n_d}})

| id | assertion (scored 0–10) | 0 = | 10 = |
|----|-------------------------|-----|------|
| d1 | Visual hierarchy guides the eye to the primary action | no hierarchy; primary action lost | as clear as the good *design* reference |

## Originality ({{n_o}})

| id | assertion (scored 0–10) | 0 = | 10 = |
|----|-------------------------|-----|------|
| o1 | The core interaction is not a template clone | indistinguishable from a default scaffold | a genuinely fresh take, like the good *originality* reference |

## Craft ({{n_c}})

| id | assertion (scored 0–10) | 0 = | 10 = |
|----|-------------------------|-----|------|
| c1 | Edge and error states are handled deliberately | unhandled errors, raw stack traces | every error state designed, like the good *craft* reference |
