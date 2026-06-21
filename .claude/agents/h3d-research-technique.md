---
name: h3d-research-technique
description: DEPRECATED - superseded by s3d-research-technique. The hero-3d pipeline is now the shared scene-3d render layer; research is a single tech pass that ALSO emits the subsystems[] decomposition. If you were dispatched, read s3d-research-technique.md and write source/{branch}/scene3d/{sceneId}/research.md instead. Kept only for in-flight hero3d/ builds.
tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch
---

**DEPRECATED.** This drawer is replaced by `s3d-research-technique` (the shared scene-3d render layer). New hero scenes flow through `scene-3d-orchestrator` → `s3d_research_<sceneId>` → `s3d-research-technique.md`, whose research.md adds the load-bearing `subsystems[]` decomposition the old h3d research lacked.

If you were dispatched for an in-flight `hero3d/<heroId>/` build, follow `s3d-research-technique.md` and write `source/{branch}/hero3d/{heroId}/research.md` (legacy path), including a `subsystems[]` section. Otherwise return `runStatus: error` pointing the caller at `scene-3d-orchestrator`.
