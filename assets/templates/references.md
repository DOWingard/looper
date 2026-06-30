# Reference Analysis — {{slug}}

Empirical analysis of every good/anti reference, written **before** the spec. References are
evidence, not labels: each was actually loaded and exercised, and what was *observed* is
recorded here. The spec boundaries and the contract's 0/10 anchors come from this file — not
from any prior about "what good looks like".

## Per-reference observations

For each reference: its medium, whether it is a target or anti-target, any category it was
qualified for, and concretely observed context per category.

### {{good|anti}} — {{url-or-name}}  ({{medium}}; qualified for: {{category or "all"}})
- Functionality: {{what it does / how it behaves when actually used}}
- Design: {{layout, type, color, motion, hierarchy as observed}}
- Originality: {{what is distinctive vs a default in this medium}}
- Craft: {{polish, edge/error handling, performance, robustness observed}}

(repeat per reference; weight the detail toward any category the reference was qualified for)

## Invariants — the generalized metrics + spec boundaries

- **Shared by all targets** → spec boundaries the build MUST satisfy, and the 10-anchors:
  - {{e.g. "all four are 3D/WebGL spatial experiences" → a medium boundary, not optional}}
- **Shared by all anti-targets** → the 0-anchors / what to avoid:
  - {{e.g. "crude art, janky/teleporting interaction, no feedback on action"}}
- **Per-category bar** (weighted toward any qualified categories):
  - {{category → the empirical 10 the references collectively define}}

## Discrepancies for the human (pre-loop checkpoint)

- {{a property every target shares that the request did not name, or an anti-target that
   overlaps a stated goal — to resolve, add as a criterion, or set a higher-level goal}}
