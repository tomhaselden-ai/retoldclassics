# Production Readiness

This document covers the remaining production-facing setup and verification steps for the Persistent Story Universe Platform.

For the full Phase 8 rollout sequence, use [PHASE_8_ROLLOUT_CHECKLIST.md](d:/Users/Trader/story_universe_platform/PHASE_8_ROLLOUT_CHECKLIST.md) alongside this document.

For the game replacement closeout and rollout specifics, also use [PHASE_8_GAME_REPLACEMENT_ROLLOUT.md](d:/Users/Trader/story_universe_platform/PHASE_8_GAME_REPLACEMENT_ROLLOUT.md).

## Required Environment

Minimum backend environment:

- `APP_ENV=production`
- `DATABASE_URL`
- `JWT_SECRET`
- `FRONTEND_APP_URL`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `SMTP_USE_TLS`
- `OPENAI_API_KEY`
- `AWS_ACCESS_KEY`
- `AWS_SECRET_KEY`
- `AWS_REGION`

Optional rate-limit tuning:

- `RATE_LIMIT_LOGIN_REQUESTS`
- `RATE_LIMIT_LOGIN_WINDOW_SECONDS`
- `RATE_LIMIT_RESET_REQUESTS`
- `RATE_LIMIT_RESET_WINDOW_SECONDS`
- `RATE_LIMIT_GENERATE_REQUESTS`
- `RATE_LIMIT_GENERATE_WINDOW_SECONDS`
- `RATE_LIMIT_MEDIA_REQUESTS`
- `RATE_LIMIT_MEDIA_WINDOW_SECONDS`
- `RATE_LIMIT_PUBLISH_REQUESTS`
- `RATE_LIMIT_PUBLISH_WINDOW_SECONDS`

Optional media worker tuning:

- `MEDIA_WORKER_IDLE_SECONDS`
- `MEDIA_WORKER_MAX_JOBS_PER_CYCLE`

## Startup Expectations

When `APP_ENV=production`, backend startup now requires:

- a configured `DATABASE_URL`
- a non-default `JWT_SECRET`
- a configured `SMTP_HOST`
- a configured `SMTP_FROM_EMAIL`

If those are missing, startup validation should fail instead of silently running in an unsafe state.

## Media Worker

Narration and illustration generation now run through a database-backed queue.

Backend API process:

- accepts story, narration, and illustration requests
- enqueues media jobs
- exposes job status for polling

Separate worker process:

- claims queued `media_jobs`
- generates narration and illustrations
- writes completion or failure state back to the database

Run both processes in production:

1. start the API with [run_backend.bat](d:/Users/Trader/story_universe_platform/run_backend.bat)
2. start the media worker with [run_media_worker.bat](d:/Users/Trader/story_universe_platform/run_media_worker.bat)

If the worker is not running, narration and illustration requests will stay queued in `pending` status.

## Critical Runtime Checks

Before production signoff, verify:

1. Auth and tenant isolation
- user A cannot access user B story memory
- user A cannot run continuity checks on user B resources

2. Reader-derived world continuity
- world continuity uses merged template + derived world context
- inherited template characters still validate correctly
- reader-added characters validate correctly

3. Password reset email
- request reset
- email arrives through Exchange
- reset link opens the frontend
- password reset succeeds

4. Media generation and publishing
- generate story
- queue narration and verify it reaches `completed`
- queue illustration and verify it reaches `completed`
- publish EPUB
- open EPUB and immersive reader

5. Classics author restrictions
- account-level allowed authors filter visible classics as expected

6. Game replacement verification
- open `/reader/:readerId/games`
- confirm the active suite shows only:
  - Build the Word
  - Guess the Word
  - Word Match
  - Word Scramble
  - Flash Cards
- confirm starting and completing a V1 game creates `game_sessions` and `game_word_attempts` rows
- confirm parent analytics reflects recent game-practice activity
- confirm guest preview at `/games/guest` launches the V1 `Build the Word` preview rather than the retired quiz flow
- confirm deprecated reader endpoints `POST /readers/{reader_id}/games/generate` and `POST /readers/{reader_id}/games/results` return `410`

## Abuse Protection Now In Place

Lightweight in-memory rate limiting is applied to:

- login
- password reset request
- story generation
- narration generation
- illustration generation
- EPUB publish/export

This is per-process protection. It is suitable as a first production guard, but if the app is later deployed behind multiple workers or instances, it should move to a shared limiter store.

## Remaining Hardening Work

Still recommended after production smoke testing:

- integration tests for tenant isolation and reader-world continuity
- shared model/table-definition cleanup
- structured operational logging improvements
- deployment and rollback runbook
- centralized/shared rate limiting if multi-instance deployment is introduced
