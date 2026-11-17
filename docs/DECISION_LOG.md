# Technical Decision Log

Record decisions that materially affect architecture, data, model selection, cost, or scope. Newest entries at the bottom.

## Decision template

### DEC-XXX — Short title
- **Date:**
- **Status:** Proposed / Accepted / Superseded
- **Context/problem:**
- **Options considered:**
- **Decision:**
- **Reasoning/trade-offs:**
- **Consequences/migration:**
- **Evidence/links:**
- **Approver:**

## Initial constraints (not all are final technical decisions)

### DEC-001 — No facial recognition
- **Date:** 2026-11-13
- **Status:** Accepted project constraint
- **Context/problem:** Need identify rostered players from video.
- **Decision:** Do not use facial recognition or face embeddings.
- **Reasoning/trade-offs:** Use team, jersey number, roster, tracking continuity, and non-face visual evidence; uncertain cases go to review.
- **Consequences/migration:** Identity design and model selection must comply.

### DEC-002 — Keep permanent player identity separate from tracker IDs
- **Date:** 2026-11-13
- **Status:** Accepted design principle
- **Context/problem:** Visual tracker IDs can change after occlusion, camera movement, or a player leaving/returning.
- **Decision:** Maintain a permanent roster `playerId` registry that can link multiple temporary track IDs with evidence.
- **Reasoning/trade-offs:** Avoid identity fragmentation and incorrect player histories.
- **Consequences/migration:** Identity mapping must be auditable and confidence-aware.
