---
name: h3d-scene-author
description: DEPRECATED - superseded by s3d-subsystem-author. The monolithic scene.js (one author building all geometry + lights + camera + composition) is replaced by a per-SUBSYSTEM fan-out where each chunk renders + is verified STANDALONE, plus the runtime composer owning the shared lights/camera/env. If dispatched for an in-flight hero3d/ build, author the lead subsystem per s3d-subsystem-author.md. Kept only for back-compat.
tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, mcp__claude_preview__preview_start, mcp__claude_preview__preview_stop, mcp__claude_preview__preview_eval, mcp__claude_preview__preview_console_logs, mcp__claude_preview__preview_inspect, mcp__claude_preview__preview_snapshot, mcp__claude_preview__preview_screenshot
---

**DEPRECATED.** A single scene.js author was the back-loaded-integration failure: it produced a module that rendered nothing alone, only at composition. The shared scene-3d render layer splits the scene into subsystems (`s3d_subsystem_<sceneId>_<sysId>`), each of which MUST paint a real standalone frame before composition, and the runtime composer (`s3d-runtime-composer.md`) owns the shared camera / lights / env. Read `s3d-subsystem-author.md` + `s3d-runtime-composer.md`. Return `runStatus: error` pointing the caller at `scene-3d-orchestrator` unless finishing a legacy `hero3d/` build.
