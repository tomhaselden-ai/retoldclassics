# Phase 8 Game Replacement Rollout

This document closes out the reader game replacement program and defines the production checks for the new active V1 literacy game system.

Use this alongside [PHASE_8_ROLLOUT_CHECKLIST.md](d:/Users/Trader/story_universe_platform/PHASE_8_ROLLOUT_CHECKLIST.md) and [PRODUCTION_READINESS.md](d:/Users/Trader/story_universe_platform/PRODUCTION_READINESS.md).

## 1. Active System

The active reader game system is now the V1 literacy suite:

- `build_the_word`
- `guess_the_word`
- `word_match`
- `word_scramble`
- `flash_cards`

The active reader entry point remains:

- `/reader/:readerId/games`

The active backend session model is:

- `game_sessions`
- `game_word_attempts`

Legacy `game_results` remains as a compatibility bridge for historical continuity and summary reporting, but it is no longer the active source of truth for the replacement system.

## 2. Retired Active Paths

The following reader endpoints are intentionally retired and must not be treated as active integration surfaces:

- `POST /readers/{reader_id}/games/generate`
- `POST /readers/{reader_id}/games/results`

Expected behavior:

- both return `410 Gone`
- error payload identifies that the game system was replaced

The old guest `classic_word_quiz` flow is also retired from active use.

## 3. Guest Preview Contract

Public guest games now use a bounded V1-style preview flow:

- route: `/games/guest`
- backend launch endpoint: `POST /guest/games/preview-session`
- current preview type: `build_the_word`

Expected behavior:

- guest session starts or resumes automatically
- a classic-backed preview launches
- preview usage consumes guest game limit correctly
- once the limit is reached, the next launch is blocked server-side

## 4. Reader Rollout Checks

Verify for at least one reader:

1. Open `/reader/:readerId/games`
2. Confirm only the five V1 product-facing game names are shown
3. Start and complete:
- Build the Word
- Guess the Word
- Word Match
- Word Scramble
- Flash Cards
4. Confirm completion summary appears
5. Confirm reader practice snapshot updates on refresh

## 5. Data And Analytics Checks

For one completed session, verify:

- one row exists in `game_sessions`
- matching per-word rows exist in `game_word_attempts`
- reader/account scoping is correct
- parent analytics reflects:
  - sessions this week
  - words practiced
  - accuracy by game type
  - repeated missed words when applicable

Compatibility checks:

- legacy `game_results` still receives the compatibility summary row
- existing higher-level reporting does not regress while fully migrated reporting uses `game_sessions` and `game_word_attempts`

## 6. UI And Navigation Checks

Verify:

- reader navigation links to the V1 game hub only
- no reader-facing UI offers the retired generator flow
- guest games page uses V1 copy and interactions, not quiz terminology
- no broken links remain from chooser, reader home, or guest funnel

## 7. Known Residual Legacy Code

The repository still contains legacy generator-oriented modules and tests for historical and low-risk compatibility reasons, including:

- [backend/games/game_service.py](d:/Users/Trader/story_universe_platform/backend/games/game_service.py)
- [backend/games/game_generator.py](d:/Users/Trader/story_universe_platform/backend/games/game_generator.py)
- [tests/test_game_generator.py](d:/Users/Trader/story_universe_platform/tests/test_game_generator.py)

These are not active reader or guest product flows anymore.

Any future cleanup should only remove them after confirming:

- no production route imports depend on them
- no reporting path still expects their legacy shapes
- historical test coverage is either replaced or intentionally retired

## 8. Remaining Follow-Ups

These are follow-ups, not blockers for the replacement rollout:

- authenticated `classics` as a first-class `source_type` in the reader V1 session model is still incomplete
- deeper integration coverage can be added around the guest preview route and end-to-end parent analytics reflection
- legacy generator files can be removed later if we decide the compatibility value is no longer worth the maintenance cost

## 9. Release Signoff

The game replacement is ready for release when:

- automated tests pass
- frontend build passes
- the V1 suite is the only active reader-facing game system
- guest preview uses the new V1 direction
- retired reader endpoints return `410`
- analytics reflects the new active session model without regressing parent or reader reporting
