"""Fitness and trajectory classification for the looper agent-loop harness.

The fitness of a result is the L2 norm of its evaluation-metric vector, normalized so
a perfect result scores 1.0 and a zero result scores 0.0. Each metric is an empirical
0-10 score; with N metrics the maximum possible L2 norm is 10*sqrt(N) (every metric at
10), so dividing by that yields the root-mean-square of the normalized [0,1] scores.

RMS (rather than the arithmetic mean) is deliberate: it rewards peak excellence on some
criteria over uniform mediocrity. The very high convergence target (~0.95) still forces
near-perfect scores across essentially every criterion, so the bias only helps early
loops reward genuine breakthroughs rather than letting a flat result coast.

classify_attractor reads the *history* of fitness values across cycles and classifies the
trajectory the loop has settled into, so the evaluator and orchestrator decide
continue / restart / stop from a quantitative signal instead of by eye. Its `action`
is a recommendation, never a command: the deciding agent stays in the loop so the
system is not over-determined by this heuristic.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys


def fitness(scores):
    """L2/RMS fitness of an evaluation-metric vector.

    scores: non-empty sequence of per-criterion scores, each in [0, 10].
    returns: float in [0, 1] == sqrt(sum(s**2)) / (10 * sqrt(len(scores))).

    Raises ValueError on an empty vector or any score outside [0, 10]. A malformed
    vector is a contract violation the caller must fix, not something to silently
    clamp -- a clamped fitness would lie to the orchestrator about convergence.
    """
    vec = list(scores)
    if not vec:
        raise ValueError("score vector must be non-empty")
    for s in vec:
        if not 0 <= s <= 10:
            raise ValueError(f"score {s!r} outside [0, 10]")
    norm = math.sqrt(sum(s * s for s in vec))
    return norm / (10.0 * math.sqrt(len(vec)))


def _slope(ys):
    """Least-squares slope of ys against its integer index; 0.0 for fewer than 2 points."""
    n = len(ys)
    if n < 2:
        return 0.0
    xbar = (n - 1) / 2.0
    ybar = sum(ys) / n
    num = sum((i - xbar) * (y - ybar) for i, y in enumerate(ys))
    den = sum((i - xbar) ** 2 for i in range(n))
    return num / den if den else 0.0


def _sign_changes(deltas):
    """Count strict sign flips between consecutive deltas (oscillation evidence)."""
    return sum(1 for i in range(len(deltas) - 1) if deltas[i] * deltas[i + 1] < 0)


def converged(history, *, target=0.95, band=(0.85, 0.95), eps=0.01, window=3):
    """True when the loop has quantitatively converged.

    Either mode suffices:
      - hard:       the latest fitness >= target.
      - asymptotic: the last `window` values span <= eps (a settled plateau) and sit at
                    or above the band floor -- converged near-target, not stuck low.
    """
    if not history:
        return False
    if history[-1] >= target:
        return True
    if len(history) >= window:
        w = history[-window:]
        if max(w) - min(w) <= eps and min(w) >= band[0]:
            return True
    return False


def classify_attractor(history, *, target=0.95, band=(0.85, 0.95), eps=0.01,
                       window=3, strange_std=0.15, strange_amp=0.30):
    """Classify the trajectory of a fitness history and recommend an action.

    Returns {"label", "action", "evidence"}. Labels, in checked precedence:
      converged   stop      at/above target, or a settled in-band plateau
      strange     restart   high-variance, erratic -- off the rails
      diverging   restart   steady downward trend
      stuck_low   restart   settled below the band floor and not improving
      cyclic      restart   bounded oscillation with no net progress
      converging  continue  steady upward trend, not yet at target
      plateau     continue  slow/flat but not yet a settled plateau
      warming_up  continue  too few cycles to classify

    The bad labels (strange/diverging/stuck_low/cyclic) all recommend restart because this
    loop's inputs can't reach target; the orchestrator must restart with changed inputs
    rather than burn more cycles here.
    """
    if not history:
        return {"label": "warming_up", "action": "continue",
                "evidence": "no fitness recorded yet"}
    last = history[-1]
    if last >= target:
        return {"label": "converged", "action": "stop",
                "evidence": f"latest {last:.3f} >= target {target}"}
    if len(history) >= window:
        w = history[-window:]
        if max(w) - min(w) <= eps and min(w) >= band[0]:
            return {"label": "converged", "action": "stop",
                    "evidence": f"asymptote within {eps} in band over last {window}"}
    if len(history) < 2:
        return {"label": "warming_up", "action": "continue",
                "evidence": "fewer than 2 cycles recorded"}

    w = history[-min(len(history), 5):]
    slope = _slope(w)
    deltas = [w[i + 1] - w[i] for i in range(len(w) - 1)]
    sc = _sign_changes(deltas)
    amp = max(w) - min(w)
    sd = statistics.pstdev(w)

    # Strange is tested before diverging: an erratic trajectory can carry an incidental
    # negative slope, but its defining trait is high variance plus repeated sign flips.
    if sd > strange_std and amp > strange_amp and sc >= 2:
        return {"label": "strange", "action": "restart",
                "evidence": f"erratic: std={sd:.3f}, amp={amp:.3f}, {sc} sign-changes"}
    if slope < -eps:
        return {"label": "diverging", "action": "restart",
                "evidence": f"downward slope {slope:.4f}"}
    if abs(slope) <= eps and amp <= eps and last < band[0]:
        return {"label": "stuck_low", "action": "restart",
                "evidence": f"flat at {last:.3f}, below band floor {band[0]}"}
    if sc >= 2 and abs(slope) <= eps and amp > eps:
        return {"label": "cyclic", "action": "restart",
                "evidence": f"{sc} sign-changes, flat trend, amp={amp:.3f}"}
    if slope > eps:
        return {"label": "converging", "action": "continue",
                "evidence": f"upward slope {slope:.4f}, below target {target}"}
    return {"label": "plateau", "action": "continue",
            "evidence": f"slow/flat trend slope={slope:.4f}, not yet converged"}


# --- CLI: so the evaluator/orchestrator call this instead of hand-computing ---------

def _read_fitness_series(path):
    series = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if "fitness" in rec:
                series.append(float(rec["fitness"]))
    return series


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="looper fitness + trajectory classifier")
    sub = parser.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("score", help="compute fitness of one metric vector")
    ps.add_argument("--vector", required=True,
                    help="comma-separated 0-10 scores, e.g. 8,9,7,10")

    pc = sub.add_parser("classify",
                        help="classify the fitness history in an evals.jsonl")
    pc.add_argument("--evals", required=True, help="path to evals.jsonl")
    pc.add_argument("--target", type=float, default=0.95)
    pc.add_argument("--eps", type=float, default=0.01)
    pc.add_argument("--window", type=int, default=3)

    args = parser.parse_args(argv)
    if args.cmd == "score":
        vec = [float(x) for x in args.vector.split(",") if x.strip() != ""]
        print(json.dumps({"fitness": fitness(vec), "n": len(vec)}))
    elif args.cmd == "classify":
        series = _read_fitness_series(args.evals)
        result = classify_attractor(series, target=args.target, eps=args.eps,
                                    window=args.window)
        result["n_cycles"] = len(series)
        result["latest"] = series[-1] if series else None
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
