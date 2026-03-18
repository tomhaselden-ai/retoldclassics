# AGENTS.md

## Project
Persistent Story Universe Platform

## Mission
Implement the mobile-first PWA evolution of the existing platform without redesigning the core architecture.

## Current Stack
- Backend: Python 3.11, FastAPI, SQLAlchemy, MySQL
- Frontend: React, Vite, TypeScript, PWA
- Media: Amazon Polly narration, illustration generation, EPUB export

## Authoritative Architecture
The existing repository is authoritative.

The following core systems must remain intact and be extended additively:
- accounts and auth
- readers
- template worlds
- reader-derived worlds
- generated stories
- classics
- narration
- illustrations
- EPUB
- memory
- continuity
- vocabulary
- games
- analytics
- media job queue and worker

## Product Direction
The platform is evolving into a three-layer mobile-first PWA:
1. Guest experience
2. Parent/master experience
3. Reader/child experience

The public landing page, chooser, parent area, and reader area must be implemented as product layers on top of the current repository, not as a rewrite.

## Non-Negotiable Rules
- Do not redesign the platform.
- Do not replace working systems with greenfield rewrites.
- Do not rename major existing modules unless necessary for correctness.
- Prefer additive, minimal, production-safe changes.
- Preserve multi-tenant scoping and account isolation.
- Preserve reader-derived world architecture and merged reader-world runtime behavior.
- Preserve existing narration, illustration, EPUB, classics, memory, and continuity capabilities unless explicitly replacing them with a backward-compatible improvement.
- Parent-facing protected areas must remain distinct from reader-facing areas.
- Reader runtime flows must use reader-scoped routes where applicable.

## Current Architectural Constraints
- Template worlds remain global/shared.
- Reader worlds are reader-scoped and may reference both template and derived world state.
- Story generation operates on merged parent + derived world context.
- Generated stories remain tied to `reader_world_id`.
- Narration and illustration generation run through the backend media job queue and worker.
- Generated and classic immersive readers already support word-level narration interaction and should not be regressed.

## Route Family Rules
- Public guest routes must remain public and bounded.
- Parent routes must require authenticated account access and, where specified, parent PIN verification.
- Reader routes must require authenticated account access to the owning reader.
- Reader-facing world and story flows should prefer reader-scoped route families rather than raw template-world routes.
- New summary endpoints should be introduced additively rather than replacing proven lower-level service routes prematurely.

## Guest Layer Requirements
- Public landing page
- Limited anonymous access to selected classics and games
- Conversion to free signup
- No credit card required for the free path
- Usage limits must be server-enforceable and testable

## Parent Layer Requirements
- Logged-in chooser page before parent or reader entry
- Parent/master account entry requires PIN
- Parent area must expose:
  - reader management
  - shelves
  - controls
  - analytics
  - goals
  - settings

## Reader Layer Requirements
- Child-first mobile UI
- Continue Reading
- Books
- Words
- Games
- Goals
- Low-friction, low-clutter design

## Engineering Rules
- Inspect before modifying.
- Reuse existing services where possible.
- Keep changes scoped to the current phase.
- Do not leave placeholder code paths that cannot work.
- Prefer summary payloads for new mobile-first parent and reader surfaces.
- Keep schema changes additive and explicit.
- Document changed files and rationale at the end of each task.

## Validation Requirements
For every implementation phase:
- run or add relevant tests
- confirm route behavior
- confirm auth and tenant boundaries
- confirm mobile-first route flow still works
- summarize remaining risks and follow-ups

## Required Workflow For Codex Tasks
For each scoped phase:
1. Inspect the relevant existing files first.
2. State the exact implementation plan.
3. Make only the scoped changes.
4. Add or update tests where appropriate.
5. Summarize:
   - what was inspected
   - what changed
   - what assumptions were made
   - what validations ran
   - what remains for the next phase

## Phase Discipline
- Only implement one agreed phase at a time.
- Keep Git checkpoints before and after each phase.
- If a later phase appears to require an earlier contract change, update the phase contract first instead of freelancing the architecture.
