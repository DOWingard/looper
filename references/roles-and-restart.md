# Roles & Restart

Two things that must stay coherent: **who does what** (four disjoint roles) and **how the
orchestrator decides** continue / restart / stop. They are in one file because the role
boundaries are defined by what each role can *see*: the evaluator sees one loop's fitness
curve, the orchestrator sees every loop's.

## The four roles (disjoint)

| Role | Owns | Forbidden from | Restart authority |
|---|---|---|---|
| **Orchestrator** | the whole run; continue/restart/stop decisions; restart context-handoff; small prompt tweaks | writing target code; grading; renegotiating the contract itself | **Global** — may restart on the whole cross-loop history |
| **Planner** | turning the human's goal into a sprint spec; reading loop history to inform the next spec | touching code; grading | none (informs, does not signal) |
| **Generator** | building everything; proposing what "done" looks like | grading its own work | none |
| **Evaluator** | grading each result 0–10; logging the vector + fitness; analyzing this loop's trajectory | writing target code | **Local** — may signal restart from one loop's fitness history |

**Mixing roles is the primary failure mode.** The moment one agent both builds and grades, it
turns sycophantic and the loop converges on slop. Keep three context windows / three system
prompts for planner, generator, evaluator; the orchestrator is the agent running the skill and
never assumes another role.

## How a restart works

One intuition to carry: **a restart is not a retry.** Re-running the same spec, criteria, and
context drives the loop to the same result — the inputs determine which results are reachable.
So a restart has to *change the inputs* and tell the next loop what failed, or it just
reconverges. The levers, smallest first:

1. **Enriched logs** — give the new subagents the prior loop's failure context (which changes
   produced which fitness patterns) so they don't re-trace the same path. Often enough alone.
2. **Criteria adjustment** — renegotiate the contract if the rubric itself steered into the bad
   result (e.g. criteria that pull design and functionality into conflict).
3. **Small system-prompt tweaks** — adjust a role's standing prompt only when the logs show a
   recurring failure no amount of context will fix.

### The over-determination guardrail

Tightening the subagent prompts too far backfires: the loop collapses to whatever narrow
result the over-specified prompt forces, with no room to find a better one. Make **small,
reversible** tweaks and prefer context over constraint. A role prompt that only grows is the
signal you are over-determining — back it out. (This mirrors the source's "delete the harness"
discipline: the harness should shrink as the models improve, not accrete.)

## The restart-signal protocol

Two parties can call for a restart, distinguished by **what they can see**:

- **Evaluator (local).** After grading, it runs `classify_attractor` on *this loop's* fitness
  history. A `cyclic` / `diverging` / `strange` / `stuck_low` verdict is its signal to the
  orchestrator: "this loop's trajectory won't reach target." It signals; it does not restart.
- **Orchestrator (global).** It holds *every* loop's history and restarts on the whole picture
  — e.g. three different initializations all capping at a low ceiling means the approach itself
  is wrong, calling for a larger change than any single evaluator could justify. It also decides
  what to change on restart.
- **Planner** reads the same history (to write a better next spec) but has **no** restart
  authority — it acts only when the orchestrator opens a new loop.

## The restart handoff (so loops don't reconverge)

When the orchestrator restarts a loop it writes a **restart brief** (template:
`assets/templates/restart-brief.md`) into the workspace and ensures every new subagent reads it
before acting. The brief is the explicit interface between the dead loop and the new one, and
must carry:

- the prior trajectory type and the fitness ceiling it hit;
- **which changes produced which fitness patterns** (mined from the logs);
- the specific result(s) the new loop must *not* reconverge to, and why;
- what this initialization changes (logs / criteria / prompt tweaks) and the result it aims for.

A restart without this brief usually lands the system back where it started — the brief is what
makes the change actually take.
