---
name: grill-me
description: Interview relentlessly about a plan or design until shared understanding, resolving each branch of the decision tree. Use when the user wants to stress-test a plan, get grilled on their design, or mentions "grill me" - and as the interviewer in a development-planning loop (grilling a project's flows, data model, and information architecture before building).
---

Interview relentlessly about every aspect of this plan or design until you reach a shared, unambiguous understanding. Walk down each branch of the decision tree, resolving dependencies between decisions one at a time. For every question, give your own recommended answer.

Rules:
- Ask ONE question at a time. Wait for the answer before the next.
- If a question can be answered by exploring the codebase / the project (e.g. `prototype.json` entities, the screens, the design system), explore and answer it yourself instead of asking.
- Prefer the question whose answer unblocks the most other decisions next.
- Stop when there are no unresolved branches left that change what gets built - not before, not long after.

When grilling a DEVELOPMENT PLAN (the two-agent loop, where one side holds the project knowledge and you interrogate it before any code is written), drive specifically at the things that break apps if left vague:
- **Data model:** every entity's real fields + types, identity/keys, required vs optional, relationships and their cardinality (one-to-many? many-to-many through what?), what is derived vs stored, soft-delete vs hard-delete, audit needs.
- **Flows:** the real end-to-end paths (e.g. apply -> review -> offer -> accept -> pay), every state a record moves through, who can move it, what happens on rejection / timeout / resubmission, and the empty / error / partial states each screen must handle.
- **Information architecture:** which screen reads/writes which entity, the navigation + permission structure, what is shared vs per-user vs per-role.
- **Roles & access:** the distinct roles, exactly what each can see and do, and the row-level rules ("an applicant sees only their own; an officer sees those assigned to them").
- **Edge cases & rules:** validation, uniqueness, concurrency, money/rounding, dates/time zones, file types/sizes, and any domain rule a mockup quietly skipped.

End by restating the resolved plan as a short, decision-by-decision summary the user can confirm or correct.
