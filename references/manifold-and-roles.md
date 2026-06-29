# The Manifold & The Roles

Two things that must stay coherent: **who does what** (four disjoint roles) and **how the
orchestrator reasons about the run as a whole** (the dynamical-systems view that drives its
restart decisions). They are in one file because the role boundaries *are* defined by the
manifold: the evaluator sees one section of it, the orchestrator sees all of it.

## The run as a dynamical system

Model one loop as a dynamical system on a manifold:

| Component | Role in the system |
|---|---|
| **Initialization & mechanics** | the **planner's** spec + the accumulated **logs** + the negotiated **criteria** — the starting point and the rules of motion |
| **Time evolution** | the **generator** — evolves the initialized system forward by building |
| **State determination** | the **evaluator** — reads out the system's state as a fitness vector |

Run the generator→evaluator cycle repeatedly under a fixed initialization and the
fitness trajectory falls toward some **attractor**. The manifold has **topologically
separated regions**, each with its own attractor:

- **Sink / fixed point** — the trajectory settles to one result regardless of cycle-to-cycle
  noise. Good if that fixed point is at/above target (`converged`); bad if below it
  (`stuck_low`).
- **Limit cycle** — the trajectory oscillates through a repeating pattern, never settling
  (`cyclic`).
- **Strange attractor** — erratic, initialization-sensitive, never coheres (`strange`).
- **Divergence** — no attractor in reach; fitness trends away from target (`diverging`).

**Which partition the system lands in is set by the initialization.** A fixed
planner-spec + criteria + logs will, via the generator, drive the evaluator toward the same
attractor every time. So the only way to reach a better attractor is to **change the
initialization** — and that is exactly what a restart does.

### Topological traversal = re-initialization

The orchestrator's ultimate job: **ensure the initialization sits in a partition whose
attractor reaches the target.** When a loop's attractor is one of the bad regimes, the
orchestrator re-initializes to traverse to a different partition. The levers, smallest
first:

1. **Enriched logs** — feed the new subagents the prior loop's failure context (what
   changes produced which fitness patterns) so they do not re-trace the same trajectory.
   This alone often moves the system to a new partition.
2. **Criteria adjustment** — renegotiate the contract if the rubric itself steered into the
   bad attractor (e.g. criteria that pull design and functionality into conflict).
3. **Small system-prompt tweaks** — adjust a role's standing prompt only when the logs show
   a recurring failure no amount of context will fix.

### The over-determination guardrail

Tightening the subagent prompts too far **creates** a degenerate sink: the system collapses
to whatever narrow result the over-specified prompt forces, with no room to discover a
better one. The orchestrator must therefore make **small, reversible tweaks** and prefer
context over constraint. A monotonically growing pile of MUSTs in a role prompt is the
signal that the orchestrator is over-determining the system — back it out. (This mirrors the
source's "delete the harness" discipline: the harness should shrink as the models improve,
not accrete.)

## The four roles (disjoint)

| Role | Owns | Forbidden from | Restart authority |
|---|---|---|---|
| **Orchestrator** | the whole run; continue/restart/stop decisions; restart context-handoff; small prompt tweaks | writing target code; grading; renegotiating the contract itself | **Global** — may restart on the full-manifold picture across all loops |
| **Planner** | turning the human's goal into a sprint spec; reading loop history to inform the next spec | touching code; grading | none (informs, does not signal) |
| **Generator** | building everything; proposing what "done" looks like | grading its own work | none |
| **Evaluator** | grading each result 0–10; logging the vector + fitness; analyzing the local trajectory | writing target code | **Local** — may signal restart from one loop's fitness history |

**Mixing roles is the primary failure mode.** The moment one agent both builds and grades,
it turns sycophantic and the loop converges on slop. Keep three context windows / three
system prompts for planner, generator, evaluator; the orchestrator is the agent running the
skill and never assumes another role.

## The restart-signal protocol

Two parties can call for a restart, distinguished by **what they can see**:

- **Evaluator (local).** After grading, it runs `classify_attractor` on *this loop's*
  fitness history. A `cyclic` / `diverging` / `strange` / `stuck_low` verdict is its signal
  to the orchestrator: "this section of the manifold won't reach target." It signals; it
  does not itself restart.
- **Orchestrator (global).** It holds every loop's history. It restarts on the
  **full-manifold** picture — e.g. three different initializations all landing in low sinks
  means the partition family is wrong, calling for a larger re-initialization than any
  single evaluator could justify. It also decides what to *change* on restart.
- **Planner** reads the same history (to write a better next spec) but has **no** restart
  authority — it acts only when the orchestrator opens a new loop.

## The restart handoff (so loops don't reconverge)

When the orchestrator restarts a loop it writes a **restart brief** (template:
`assets/templates/restart-brief.md`) into the workspace and ensures every new subagent reads
it before acting. The brief is the explicit interface between the dead loop and the new one,
and must carry:

- the prior attractor type and the fitness ceiling it hit;
- **which changes produced which fitness patterns** (mined from the logs);
- the specific result(s) the new loop must *not* reconverge to, and why;
- what is being changed in this initialization (logs / criteria / prompt tweaks) and the
  partition it is meant to reach.

A restart without this brief usually lands the system back in the same partition — the brief
is what makes traversal actually happen.
