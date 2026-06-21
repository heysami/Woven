# Step ten - motion budget

Motion happens because *data is changing* or *the genre demands it*. Never as decoration.

Common defaults:
- Hover transitions: `0.12s` on `background`, `border-color`, `opacity`.
- State changes (selection, active): `0.15-0.2s`.
- Streaming/progress: `transition: width 0.4s ease`.
- Live signal: one ambient keyframe on a "running" indicator.

Genre overrides:
- **Marketing / portfolio**: scroll-driven entrance animations expected. `IntersectionObserver` or `animation-timeline: scroll()`.
- **Brutalist**: zero animation. No transitions, even on hover.
- **Editorial**: a single subtle parallax on hero imagery acceptable; nothing else.
- **iOS / Material**: spring-easing on state transitions, never on entrance.
- **Product UI / dashboards**: motion only for changing data. Never on entrance.
