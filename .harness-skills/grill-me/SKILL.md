---
name: grill-me
description: Interview relentlessly about a plan, product, or design until shared understanding, resolving each branch of the decision tree. Use when the user wants to stress-test a plan, get grilled on their design, or mentions "grill me" - and as the interviewer in a development-planning loop (grilling a product's flows, data model, and information architecture before building).
---

Interview the user relentlessly about every aspect of this plan, product, or design until you reach a shared, unambiguous understanding. This is a LONG, thorough interrogation, not a quick check - keep going until there is no unresolved branch left that would change what gets built. For a real app that is typically 15-30+ questions, not three.

How to run it:
- Ask ONE question at a time. Wait for the answer before the next. Give your own recommended answer with each.
- Walk down each branch of the decision tree, resolving dependencies one by one (answer the question that unblocks the most others next).
- **Explore the code/project only for FACTS** - what entities, fields, and screens already exist. Do NOT invent the answer to a JUDGEMENT or INTENT question by staring at the mockup. A mockup shows the happy-path UI; it does NOT encode the product's rules, and you must not pretend it does.
- **Grill the user on everything a mockup cannot answer.** These are the real questions, and there are many:

Drive hard at the PRODUCT, not just the schema:
- **Intent & purpose** - what is each flow actually FOR, what does success look like, what is the user really trying to accomplish that the screens only hint at.
- **Business rules** - the real logic behind each action: eligibility, limits, quotas, approval thresholds, pricing/quantum rules, what makes something valid or rejected. Mockups almost never show these.
- **Edge cases & lifecycle** - what happens on reject / timeout / resubmission / duplicate / concurrent edit / withdrawal; can a record be edited after submit, deleted, archived; what is the full set of states each record moves through and who can move it.
- **Permissions semantics** - not just "there are roles" but exactly what each role may see and do, on whose records, at which stage; the row-level rules in plain language.
- **Data meaning** - which fields are required vs optional, unique, derived vs entered, units/currency/timezone, what a status value actually means.
- **Scope & priorities** - what is in the first build vs later; which flows matter most; what is mock-only vs must-really-work.

Leave PURE IMPLEMENTATION to yourself - uuid vs serial, index choices, which API, table names. Do not spend the user's attention on those.

End by restating the resolved understanding as a short, decision-by-decision summary the user can confirm or correct.
