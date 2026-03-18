# Persistent Story Universe Platform Handoff Prompt

You are reviewing and helping continue development on an existing production-scale storytelling platform.

This is not a greenfield project.

The code already exists and runs.

Your job is to review the repository as it currently stands, understand the implemented architecture, validate assumptions against the code, and recommend the safest next steps.

## Repository Root

`D:\Users\Trader\story_universe_platform`

## Technology Stack

Backend:

- Python 3.11
- FastAPI
- SQLAlchemy
- MySQL

Frontend:

- React
- Vite
- TypeScript

## Core Product Areas

- account auth and dashboard
- reader profiles
- classics shelf and classic immersive reading
- generated story library by reader and world
- reader-derived worlds
- story generation
- narration generation
- illustration generation
- EPUB publishing
- memory and continuity tooling
- vocabulary and games

## Important Current Architecture

- Shared template worlds exist in the global `worlds` table.
- Readers work through `reader_worlds`.
- A reader world can reference both:
  - a parent template world
  - a reader-owned derived/custom world
- Runtime story context is merged from parent + derived world state.
- Generated stories are stored against `reader_world_id`.
- Reader-facing world tooling should prefer reader-scoped routes over raw template-world routes.

## Current System State

These items are already implemented and should be treated as the current baseline unless the code contradicts them:

1. Memory and continuity routes were hardened around account and reader scoping.
2. Production runtime validation now blocks unsafe defaults for DB/JWT/SMTP configuration.
3. Password reset email is SMTP-backed with a development fallback.
4. Narration and illustration now run through a database-backed media queue with a separate worker process.
5. Generated story illustration was stabilized to a single story-level illustration flow instead of scene-per-image as the default user experience.
6. Classics shelf fetch-loop flicker was fixed.
7. Generated and classic immersive readers support:
   - play / pause
   - play from beginning
   - click a word to restart from that word
8. Generated story speech-mark alignment was corrected so word highlighting matches the visible text rather than SSML offsets.

## Important Operational Detail

Narration and illustration require both processes to be running:

- API process: `run_backend.bat`
- media worker: `run_media_worker.bat`

If the worker is not running, queued narration and illustration jobs will remain pending.

## Key Repository Areas

Frontend:

- `frontend_pwa/src/pages`
- `frontend_pwa/src/components`
- `frontend_pwa/src/services/api.ts`
- `frontend_pwa/src/services/auth.tsx`
- `frontend_pwa/src/App.tsx`

Backend:

- `backend/api`
- `backend/story_engine`
- `backend/worlds`
- `backend/reader`
- `backend/narration`
- `backend/visuals`
- `backend/media_jobs`
- `backend/library`
- `backend/classics`
- `backend/memory`
- `backend/continuity`
- `backend/vocabulary`
- `backend/games`
- `backend/db`

Supporting:

- `db/schema.sql`
- `tests`
- `PRODUCTION_READINESS.md`
- `consensus_audit_response.md`

## What To Focus On

Please:

1. inspect the code before making assumptions
2. identify remaining production-readiness risks
3. prioritize security, tenant isolation, data integrity, and operational correctness
4. identify frontend/backend contract mismatches
5. identify anything fragile in the media queue, narration, illustration, and immersive-reader flows
6. recommend the safest next implementation steps without redesigning the whole platform

## Constraints

- Do not assume the app needs a rewrite.
- Prefer additive changes and bounded refactors.
- Assume user data may already exist in the database.
- Be careful with schema and migration recommendations.
- Preserve the reader-derived world model.
- Avoid removing working features unless clearly necessary.

## Useful Context For Review

- `PRODUCTION_READINESS.md` summarizes runtime and deployment expectations.
- `consensus_audit_response.md` summarizes prior audit validation and remediation decisions.
- `tests` contains targeted coverage for some recent changes, but not full integration coverage.

## Deliverable

Produce:

1. a short current-state assessment
2. validated risks or concerns, ordered by severity
3. misunderstandings or false alarms if you find them
4. a concise phased plan to move the system closer to production readiness

Use the attached codebase as the source of truth.
