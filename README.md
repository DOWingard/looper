# looper

A self-maintaining **generator–evaluator agent loop**, packaged as a Claude Code skill
(`/looper`). One **orchestrator** drives three disjoint subagents to build a non-trivial
software target — an app, a front-end, a website, a system design — and iterate it until it
converges to a quantitative quality bar. The orchestrator decides *continue / restart / stop*;
it never writes the target code or grades it itself.

## The idea

Most agent builds die not from a weak model but from a weak loop: nothing decides when to
stop, when to throw the work away and restart, and where the result lives. `looper` makes the
loop a first-class object — separated roles, state on disk, a contract negotiated before any
code is written — and adds two things on top:

- a **fitness function** that turns "is it good?" into a number, and
- a **trajectory-based restart rule** that recognizes when a run is stuck and restarts it
  with changed inputs instead of grinding.

## The four roles (disjoint)

| Role | Does | Never |
|---|---|---|
| **Orchestrator** | decides continue/restart/stop; manages the restart handoff; small prompt tweaks | codes; grades; renegotiates the contract |
| **Planner** | turns the goal into a sprint spec | codes; grades |
| **Generator** | builds everything; proposes what "done" means | grades its own work |
| **Evaluator** | grades 0–10, logs the metric vector + fitness, classifies the trajectory, signals restart | writes target code |

Keeping these apart is the point: the moment one agent both builds and grades, it turns
sycophantic and the loop converges on slop.

## The fitness function

Every evaluation criterion is scored on an empirical **0–10** scale. For a result with `N`
criteria scored `X = (x₁, …, x_N)`:

```
fitness(X) = √(Σ xᵢ²) / (10·√N) = √( (1/N) · Σ (xᵢ/10)² )
```

This is the L2 norm of the score vector normalized by the all-tens vector — equivalently the
**root-mean-square of the normalized scores**. It is `1.0` when every criterion is a 10 and
`0.0` when all are 0. RMS deliberately rewards peak excellence over uniform mediocrity in
early loops, while the high convergence target (default `0.95`) still forces near-perfect
scores across essentially every criterion.

Criteria are grouped into four categories — **design, originality, craft, functionality**.
Category *weighting is realized by allocation*: a higher-priority category gets more criteria,
so it contributes more terms to the norm and moves fitness more. A per-category floor keeps
any category from being neglected.

## The loop

A **session** is a sequence of **loops**; a loop is one initialization plus its **cycles**; a
cycle is one build → grade → classify iteration.

```
intake → bootstrap workspace
  └─ per loop:  plan → negotiate contract → ┌─ build → grade → classify ─┐
                                            └──── orchestrator decision ──┘
                                                  continue / restart / stop
```

The evaluator computes fitness and classifies the run's fitness **trajectory**, which drives
the restart decision:

| Trajectory | Action | Meaning |
|---|---|---|
| `converged` | stop | at/above target, or a settled in-band plateau |
| `converging` / `plateau` | continue | still climbing or with headroom |
| `cyclic` | restart | oscillating with no net progress |
| `diverging` | restart | trending away from target |
| `strange` | restart | erratic, off the rails |
| `stuck_low` | restart | settled below target and not improving |

The evaluator signals restart from *one* loop's trajectory; the orchestrator decides from
*all* loops' history, and on restart writes a brief that tells the next loop what failed and
what not to reconverge to — so the restart heads somewhere genuinely different rather
than repeating itself.

## Layout

```
looper/
├── SKILL.md                       orchestrator doctrine (the skill entry point)
├── references/
│   ├── fitness-and-convergence.md fitness formula, convergence/stopping, trajectory heuristics
│   ├── roles-and-restart.md       role contract, restart-signal protocol, over-determination guard
│   ├── state-and-intake.md        workspace + state schema, intake handshake, sizing
│   └── prompts/                   planner / generator / evaluator system-prompt templates
├── scripts/
│   ├── fitness.py                 deterministic fitness + trajectory classifier (+ CLI)
│   └── test_fitness.py            pytest suite
└── assets/templates/              fill-in state files (contract, feature_list, log, evals, …)
```

## Get it

```bash
# just the skill:
git clone https://github.com/DOWingard/looper.git

# …or with the recorded demonstration run (the optional submodule) included:
git clone --recurse-submodules https://github.com/DOWingard/looper.git
```

Already cloned without it and want the demonstration later:

```bash
git submodule update --init demonstration
```

## Install as a Claude Code skill

The repository *is* the skill (`SKILL.md` lives at its root). Make it available as `/looper` by
linking — or copying — it into your Claude Code skills directory:

```bash
ln -s "$(pwd)" ~/.claude/skills/looper      # run from inside the cloned repo
# or copy it:  cp -r . ~/.claude/skills/looper
```

Personal skills live in `~/.claude/skills/<name>/`; a symlink keeps `/looper` in sync with the
repo. Paths inside `SKILL.md` (e.g. `scripts/fitness.py`) are relative to the skill directory,
so linking the repo root is all that's needed. Then invoke `/looper` in Claude Code and
describe what to build — the target, ≥3 good references, ≥3 anti-references, a category
priority, and a stopping fitness; the orchestrator runs the rest.

## The demonstration

A complete, recorded run of `/looper` lives in the optional **`demonstration`** submodule
(hosted separately at `DOWingard/looper-demonstration`). It captures the loop's on-disk memory —
the empirical reference analysis, the planner's spec, the negotiated contract, the per-cycle
eval history, and the append-only log — alongside the software the loop actually produced: a
worked example of the loop converging to its fitness bar. A plain `git clone` omits it; fetch it
with `--recurse-submodules` (above) or `git submodule update --init demonstration`.

## Develop

`fitness.py` is pure standard library. Run the suite:

```bash
python -m pytest
```

Use the CLI directly:

```bash
python scripts/fitness.py score --vector 8,9,7,10
python scripts/fitness.py classify --evals path/to/evals.jsonl --target 0.95
```

## Lineage

Implements the "write the loop, not the prompt" field-notes pattern — generator/evaluator
separation, contracts negotiated on disk, file-system state, a deletable harness — with a
quantitative fitness function and a trajectory-based restart rule added on top.
