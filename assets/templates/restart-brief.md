# Restart Brief — {{slug}}

Written by the orchestrator when it restarts the loop. **Every new subagent reads this
before acting**, so the new loop traverses to a different region of the manifold instead of
reconverging to the same failure. Without this brief, a restart usually lands back in the
same partition.

## Prior loop
- Loop: {{loop}}   Cycles run: {{cycles}}   Fitness ceiling: {{ceiling}}   Attractor: {{attractor}}

## What happened (change → fitness pattern)
- {{change}} → {{pattern it produced}}
- e.g. "pushed originality criteria hard → functionality regressed; fitness oscillated 0.6↔0.75 (cyclic)"

## Do not reconverge to
- {{result or approach}} — because {{why it capped fitness}}

## This initialization changes
- **Logs provided:** {{what failure context the new subagents now read}}
- **Criteria:** {{renegotiation, if any — otherwise "unchanged"}}
- **Prompt tweaks:** {{small standing-prompt changes, if any — otherwise "none"}}
- **Intended partition:** {{the better attractor this re-initialization is meant to reach}}
