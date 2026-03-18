# Phase 8 Rollout Checklist

This checklist is the operational close-out for the mobile-first PWA transition.

It is intentionally concrete. The goal is to make rollout confidence repeatable rather than relying on memory.

## 1. Preflight

- Confirm `APP_ENV=production`
- Confirm `DATABASE_URL` points to the intended production database
- Confirm `JWT_SECRET` is non-default
- Confirm SMTP settings are valid
- Confirm `OPENAI_API_KEY` is present if generated stories, narration, or illustrations are enabled
- Confirm AWS Polly credentials and region are valid if narration is enabled
- Confirm the frontend is using the intended `VITE_API_BASE_URL`

## 2. Processes

Start and verify both:

- API process via [run_backend.bat](d:/Users/Trader/story_universe_platform/run_backend.bat)
- Media worker via [run_media_worker.bat](d:/Users/Trader/story_universe_platform/run_media_worker.bat)

Expected:

- API answers `/health`
- Worker is running and can claim `media_jobs`

## 3. Public Funnel Smoke Test

- Open `/`
- Confirm landing page loads
- Open `/classics`
- Open `/games/guest`
- Open `/for-families`
- Open `/how-it-works`
- Confirm guest session starts automatically
- Confirm guest usage counters render
- Confirm signup/login calls to action work

## 4. Guest Limits Verification

- As a guest, open three distinct classics
- Confirm the fourth new classic is blocked
- Reopen a previously opened classic
- Confirm it does not consume another classic read
- Launch guest games until the limit is reached
- Confirm the next launch is blocked with the correct message

## 5. Auth And Chooser Verification

- Register a new account
- Log in
- Confirm redirect lands on `/chooser`
- Confirm parent and reader entries are both visible

## 6. Parent PIN Verification

- Set a parent PIN
- Confirm `/parent` requires PIN verification
- Enter an invalid PIN repeatedly until lockout
- Confirm lockout is enforced
- Wait or reset in a controlled environment, then verify valid PIN access
- Clear the parent PIN session
- Confirm parent-only routes require verification again

## 7. Parent Area Verification

- Open `/parent`
- Confirm summary cards load
- Confirm reader creation, editing, and deletion still work
- Open `/parent/analytics`
- Confirm analytics, focus areas, and goal counts render
- Open `/parent/goals`
- Create, edit, pause, and reactivate at least one goal

## 8. Reader Area Verification

- Open `/reader/:readerId`
- Confirm child-facing home loads
- Open books, words, games, and goals
- Confirm goal progress renders for the same reader
- Confirm no parent-only controls appear in reader routes

## 8A. Game Replacement Verification

- Open `/reader/:readerId/games`
- Confirm only the five V1 game names are visible:
  - Build the Word
  - Guess the Word
  - Word Match
  - Word Scramble
  - Flash Cards
- Complete at least one V1 game session
- Confirm reader practice summary updates
- Confirm `POST /readers/{reader_id}/games/generate` returns `410`
- Confirm `POST /readers/{reader_id}/games/results` returns `410`
- Open `/games/guest`
- Confirm the guest game launches the V1 `Build the Word` preview, not the retired quiz flow

## 9. Media Pipeline Verification

- Generate a story
- Queue narration
- Confirm the job moves from `pending` to `completed`
- Queue illustration
- Confirm the job moves from `pending` to `completed`
- Confirm immersive reading still works after generation

## 10. Classics And Immersive Reader Verification

- Open a classic immersive reader
- Confirm narration highlighting still tracks properly
- Confirm clicking a word seeks correctly
- Confirm play from beginning still starts at the intended scope

## 11. Tenant And Route Boundary Verification

- Confirm one account cannot access another account's readers
- Confirm one account cannot access another account's stories or memory
- Confirm reader routes only work for owned readers
- Confirm parent routes remain protected by parent PIN gating at the product layer

## 12. Rollback Readiness

Before rollout:

- capture a git checkpoint
- capture a database backup or snapshot
- document the currently deployed frontend and backend artifact versions

If rollback is required:

- stop the worker first if media jobs are misbehaving
- roll back backend and frontend together when route contracts changed
- restore database only if a schema or data issue requires it

## 13. Known Residual Risks

- Parent-only protection is strongest at the product-route layer; deeper server-only parent authorization can still be improved later
- In-memory rate limiting is per-process, not shared across multiple instances
- SEO plumbing is client-side metadata, not full server-rendered indexing support

## 14. Release Signoff

Release is ready when:

- automated tests pass
- frontend build passes
- smoke tests above pass
- worker is confirmed healthy
- guest limits behave correctly
- parent PIN behaves correctly
- parent and reader route separation is confirmed
