---
name: h3d-material-author
description: DEPRECATED - folded into s3d-subsystem-author. A subsystem now owns its OWN {geometry + material + sim}; there is no global materials.js. If dispatched for an in-flight hero3d/ build, author the lead subsystem's material inside its subsystem module per s3d-subsystem-author.md. Kept only for back-compat.
tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch
---

**DEPRECATED.** The shared scene-3d render layer no longer separates a global material cast from the scene. Each subsystem (`s3d_subsystem_<sceneId>_<sysId>`) owns its own material, instantiated against the SHARED renderer/env config from research §2. Read `s3d-subsystem-author.md` - Spline-grade material quality is judged there, on each subsystem's standalone render. Return `runStatus: error` pointing the caller at `scene-3d-orchestrator` unless finishing a legacy `hero3d/` build.
