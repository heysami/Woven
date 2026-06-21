---
name: im-output-3d
description: DEPRECATED - the 3D output is now the shared scene-3d layer. When an interactive piece declares a 3d output medium, the interactive-media-orchestrator LINKS scene-3d-orchestrator (mode=host-driven); the mapping module's output params drive the scene via window.__scene3d.step(params, alpha). Shader/particle/audio outputs keep their own drawers. Kept only for in-flight builds.
tools: Read, Write, Edit, Bash, Glob, Grep, mcp__Claude_Preview__preview_start, mcp__Claude_Preview__preview_stop, mcp__Claude_Preview__preview_eval, mcp__Claude_Preview__preview_console_logs, mcp__Claude_Preview__preview_screenshot
---

**DEPRECATED.** A concept-bearing 3D output is no longer hand-built here. The render is the shared `scene-3d` layer (per-subsystem fan-out, drivable output). The interactive-media-orchestrator co-dispatches `scene-3d-orchestrator` with `mode: host-driven`, exposing the handles the mapping output drives; `mapping.js`'s param vector is fed each frame via `window.__scene3d.step(params, alpha)`. Read `scene-3d-orchestrator.md`. Return `runStatus: error` pointing the caller at `scene-3d-orchestrator` unless finishing a legacy `interactives/<imId>/` 3D-output build.
