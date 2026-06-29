---
name: looper
description: >
  Run a self-maintaining generator-evaluator agent loop that builds a non-trivial software
  target (app, front-end, website, system design) to a quantitative fitness target. A single
  orchestrator drives four disjoint roles — planner, generator, evaluator, and itself —
  grading results 0–10 across design/originality/craft/functionality, maximizing the L2/RMS
  fitness of the metric vector, and deciding continue/restart/stop by classifying the run as
  a dynamical system (converged/cyclic/diverging/strange/stuck_low). Use whenever the user
  invokes /looper, or wants to autonomously build-and-iterate / self-optimize / "loop on" a
  software target until it converges to a quality bar — even if they just describe the target
  and a standard of "good" and ask to iterate to it. The orchestrator runs the loop; it never
  writes the target code or grades it itself.
---

# /looper — let the loop drive

You are the **orchestrator**. You run the whole process, monitor the subagents, and make the
high-level call: **let them continue, restart the loop, or stop.** You never write the target
code and never grade it — those are other roles. Mixing roles is the failure that makes a loop
converge on slop.

The loop is short: **gather, reason, act, verify, repeat.** Everything below is how to run it
so it converges and so it can crash and resume from disk.

## The four roles (disjoint)

| Role | Does | Never |
|---|---|---|
| **Orchestrator** (you) | decides continue/restart/stop; manages restart handoff; small prompt tweaks | codes; grades; renegotiates the contract |
| **Planner** | goal → sprint spec | codes; grades |
| **Generator** | builds everything; proposes "done" | grades its own work |
| **Evaluator** | grades 0–10, logs the vector + fitness, classifies the trajectory, signals restart | writes target code |

Full role contract and the dynamical-systems reasoning behind it: `references/manifold-and-roles.md`.

## 0 — Intake (before the first loop)

Assemble enough to make convergence *quantitatively possible*. **Pull every answer from the
conversation first; ask only for what is genuinely missing.** Collect: the target build; ≥3
good references and ≥3 anti-references (optionally category-qualified); any custom
requirements (ask explicitly); category priority/weighting; and the stopping fitness (default
0.95). If you cannot anchor what a 0 and a 10 look like per category, **request more before
starting** — a vague rubric converges to nothing. Full protocol, sizing, and criteria
allocation: `references/state-and-intake.md`.

Then classify the target to set the criteria count (website ~15, small ~27, medium ~40, large
~65) and allocate them across the four categories by priority (more criteria for higher
priority → larger effect on fitness; floor of ≥3 each).

## 1 — Bootstrap the workspace

Create `.looper/<slug>/` in the working directory with `state/` and `build/`, seeded from
`assets/templates/`. State lives on disk because context windows rot; any subagent must be
able to crash and resume by reading `contract.md` + `progress.md` + `log.md`. Layout and the
`evals.jsonl` schema: `references/state-and-intake.md`.

## 2 — The loop

A **session** is a sequence of **loops**. A loop is one initialization (planner spec +
criteria + logs) plus its **cycles**. A cycle is one build→grade→classify iteration.

**Per loop:**

1. **Plan.** Dispatch the planner (`references/prompts/planner.md`) → `feature_list.json`.
2. **Negotiate the contract.** Dispatch generator and evaluator in `negotiate` mode; they
   argue via `contract.md` until they agree on the target count of testable, calibrated 0–10
   criteria across the four categories. The spec is the boundary; the contract is what gets
   graded.
3. **Cycle until a decision:**
   - **Build.** Dispatch the generator (`build` mode) → updates `build/` + `progress.md`.
   - **Grade.** Dispatch the evaluator (`grade` mode). It scores every criterion, computes
     fitness with `python scripts/fitness.py score`, appends a record to `evals.jsonl`,
     classifies with `python scripts/fitness.py classify`, and returns
     `{fitness, attractor, signal, gap_paragraph}`.
   - **Decide** (next section).

## 3 — The orchestrator decision

After each grade, choose **continue / restart / stop**. Combine the evaluator's *local* signal
(this loop's trajectory) with your *global* view (every loop's history — the full manifold).

- **STOP (success)** when `fitness.py classify` returns `converged` — latest ≥ target, or a
  settled in-band plateau. Finalize and report.
- **CONTINUE** the same loop when the trajectory is `converging` or `plateau` and still has
  headroom. Run another cycle.
- **RESTART** the loop when the trajectory is `cyclic`, `diverging`, `strange`, or `stuck_low`
  — its initialization sits in a partition whose attractor won't reach target. You may also
  restart against the evaluator's "continue" if your global view shows the partition's ceiling
  is below target (e.g. converging but asymptoting toward 0.8).

The evaluator signals from one section of the manifold; **you** decide from all of it. A
single low ceiling is a local restart (enrich logs, maybe renegotiate criteria); three
initializations all capping low is a partition-family problem calling for a larger re-init.
Mapping of regime → action and the topological reasoning: `references/manifold-and-roles.md`.

**Guardrails.**
- Cap cycles-per-loop and loops-per-session so a pathological run can't spin forever. On
  hitting a cap, stop and surface the trajectory to the human.
- **Insert a human only when the *contract itself* looks wrong — not when a *build* fails.** A
  failed build is a restart; a wrong rubric is an escalation.
- **Do not over-determine the subagents.** Over-tightened prompts create a degenerate sink:
  the system collapses to whatever the prompt forces. Prefer feeding context over adding
  constraints; make prompt tweaks small and reversible. A role prompt that only grows is the
  signal you are over-determining — back it out.

## 4 — Restart handoff (so loops don't reconverge)

On restart, write `state/restart-brief.md` (template in `assets/templates/`) and ensure every
new subagent reads it first. It carries the prior attractor and ceiling, the change→fitness-
pattern map mined from the logs, the result(s) the new loop must NOT reconverge to, and what
this initialization changes (logs / criteria / small prompt tweaks) and the partition it aims
for. Without the brief, a restart lands back in the same partition. Increment the `loop`
counter; the new planner/generator/evaluator read the brief + `evals.jsonl` as their context.

## 5 — Tune from the traces, keep the harness small

Across loops, read the subagent transcripts and the logs — not just the final state — to see
where judgment diverged and what changed fitness. Use that to make *small* standing-prompt
tweaks so new subagents start aware of prior trends. As the loop stabilizes, **delete harness
you no longer need**: a harness that only grows is one you've stopped reading.

## Dispatching subagents

Use the Agent tool, one fresh context window per role. Read the role template in
`references/prompts/`, substitute every `{{...}}` slot, and pass the result as the subagent's
task. Keep planner, generator, evaluator in separate context windows — three roles, three
prompts. Run grade after build each cycle; run plan once per loop; run negotiate once per loop.

## Reference index

- `references/fitness-and-convergence.md` — the fitness formula, convergence + stopping rules, attractor heuristics, and the `fitness.py` CLI.
- `references/manifold-and-roles.md` — the dynamical-systems view, the four-role contract, restart-signal protocol, restart handoff, over-determination guardrail.
- `references/state-and-intake.md` — workspace layout, state-file + `evals.jsonl` schema, intake handshake, sizing, criteria allocation.
- `references/prompts/{planner,generator,evaluator}.md` — the role system-prompt templates.
- `scripts/fitness.py` — deterministic fitness + trajectory classifier (compute with this; never by hand). Tests in `scripts/test_fitness.py`.

Lineage: this implements the "write the loop, not the prompt" field-notes pattern —
generator/evaluator separation, contracts negotiated on disk, file-system state, deletable
harness — with a quantitative fitness function and a dynamical-systems restart rule on top.
