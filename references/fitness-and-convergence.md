# Fitness & Convergence

The objective function the whole loop maximizes, and the quantitative rules for when to
stop. The math here is **implemented and enforced** in `scripts/fitness.py` — compute with
that module's CLI, never by hand. A hand-computed fitness can drift from the real one, and
a wrong fitness lies to the orchestrator about whether the system converged.

## The fitness function

Each evaluation criterion is scored on an empirical **0–10** scale. For a result with `N`
criteria, the score vector is `|X⟩ = (x₁, …, x_N)`, each `xᵢ ∈ [0, 10]`.

```
fitness(X) = √(⟨X|X⟩) / (10·√N) = √( (1/N) · Σ (xᵢ/10)² )
```

That is the **L2 norm of the score vector, normalized by the L2 norm of the all-tens
vector** (`‖(10,…,10)‖ = 10·√N`). Equivalently, the **root-mean-square of the
normalized-to-[0,1] scores**.

- `max = 1.0` — every criterion at 10.
- `min = 0.0` — every criterion at 0.

> The normalizer is `10·√N`, **not** `10·N`. `√(Σxᵢ²)` maxes at `√(100N) = 10√N`, so only
> `10√N` puts the ceiling at exactly 1. Dividing by `10N` would cap fitness at `1/√N`.

### Why L2 / RMS (and its one sharp edge)

RMS rewards **peak excellence on some criteria over uniform mediocrity**: `(10,10,10,0,0)`
scores `0.775` while `(6,6,6,6,6)` scores `0.600`. Two consequences the design relies on:

- **Early loops** are rewarded for genuine breakthroughs rather than flat, safe results.
- **Near the target** the edge vanishes: `fitness ≥ 0.95` requires the mean of squared
  normalized scores ≥ `0.9025`, which forces ~9.5/10 on *essentially every* criterion. So
  high-fitness convergence still means uniform excellence.

The remaining risk — "spike a few criteria, neglect a whole category" in early loops — is
blunted by the **per-category criteria floor** (see `state-and-intake.md` on allocation):
every category keeps enough criteria that ignoring one caps fitness well below target.

## Convergence (when the result is good enough)

Two acceptance modes; either suffices (`converged()` in `fitness.py`):

| Mode | Condition |
|---|---|
| **Hard** | latest fitness `≥ target` (default `0.95`) |
| **Asymptotic** | the last `window` (default 3) cycle-fitnesses span `≤ eps` (default `0.01`) **and** their minimum `≥ band floor` (default `0.85`) |

The asymptotic mode is "the loop has settled to a plateau at or above 0.85 and is no longer
improving" — converged near-target rather than stuck low.

## Stopping criteria (user-settable)

Collected at intake (see `state-and-intake.md`):

- **Target fitness** — any real number in `(0, 1)`. Default `0.95`.
- **Asymptote band** — default `[0.85, 0.95]`: a settled plateau anywhere in this band is
  accepted as converged even if it never reaches the hard target.

If the user gives a custom target, pass it through to every `fitness.py classify` call via
`--target`.

## Trajectory classification (the restart signal)

`classify_attractor(history)` reads the **sequence of cycle-fitnesses within one loop** and
classifies the trajectory, returning `{label, action, evidence}`. Precedence and meaning:

| Label | Action | Meaning |
|---|---|---|
| `converged` | **stop** | at/above target, or a settled in-band plateau |
| `strange` | **restart** | high-variance, erratic — off the rails |
| `diverging` | **restart** | steady downward trend |
| `stuck_low` | **restart** | settled below the band floor and not improving |
| `cyclic` | **restart** | bounded oscillation, no net progress |
| `converging` | **continue** | steady upward trend, not yet at target |
| `plateau` | **continue** | slow/flat but not yet a settled plateau |
| `warming_up` | **continue** | too few cycles (<2) to classify |

`action` is a **recommendation**, not a command. The evaluator uses it as its local restart
signal; the orchestrator weighs it against the cross-loop history before deciding (see
`roles-and-restart.md`). This keeps a judgment in the loop so the heuristic does not
over-determine the loop.

The four "restart" labels share a diagnosis: this loop's inputs (spec + criteria + context)
can't reach target. More cycles here are wasted — the fix is to restart with changed inputs,
not to persist.

## Using the module

```bash
# fitness of one freshly-graded vector (criteria scores, comma-separated):
python scripts/fitness.py score --vector 8,9,7,10,6,9

# classify the trajectory recorded so far in this loop's evals log:
python scripts/fitness.py classify --evals .looper/<slug>/state/evals.jsonl --target 0.95
```

`score` emits `{"fitness", "n"}`; `classify` emits `{label, action, evidence, n_cycles,
latest}`. The evaluator calls `score` after grading each result and writes the fitness into
`evals.jsonl`; the evaluator and orchestrator call `classify` to read the trajectory.
