# Phase 1 Game Replacement Inspection

## Purpose
This document records the Phase 1 inspection for the game-system replacement program.

Phase 1 is inspection only. It identifies what currently exists, what should be reused, what should be replaced, and what should be retired from active use later.

## Files Inspected
Backend:
- [backend/games/game_service.py](d:/Users/Trader/story_universe_platform/backend/games/game_service.py)
- [backend/games/game_repository.py](d:/Users/Trader/story_universe_platform/backend/games/game_repository.py)
- [backend/games/game_generator.py](d:/Users/Trader/story_universe_platform/backend/games/game_generator.py)
- [backend/api/game_routes.py](d:/Users/Trader/story_universe_platform/backend/api/game_routes.py)
- [backend/guest/guest_service.py](d:/Users/Trader/story_universe_platform/backend/guest/guest_service.py)
- [backend/api/guest_routes.py](d:/Users/Trader/story_universe_platform/backend/api/guest_routes.py)
- route inclusion in [backend/main.py](d:/Users/Trader/story_universe_platform/backend/main.py)

Frontend:
- [frontend_pwa/src/pages/GameShelfPage.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/pages/GameShelfPage.tsx)
- [frontend_pwa/src/pages/GuestGamesPage.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/pages/GuestGamesPage.tsx)
- route and navigation usage in:
  - [frontend_pwa/src/App.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/App.tsx)
  - [frontend_pwa/src/components/ReaderAreaNav.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/components/ReaderAreaNav.tsx)
  - [frontend_pwa/src/components/ReaderPanel.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/components/ReaderPanel.tsx)
  - [frontend_pwa/src/pages/ReaderHomePage.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/pages/ReaderHomePage.tsx)
  - [frontend_pwa/src/pages/ReaderLibraryPage.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/pages/ReaderLibraryPage.tsx)
  - [frontend_pwa/src/pages/VocabularyShelfPage.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/pages/VocabularyShelfPage.tsx)
  - [frontend_pwa/src/pages/WorldInfoPage.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/pages/WorldInfoPage.tsx)
  - [frontend_pwa/src/pages/ClassicReaderPage.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/pages/ClassicReaderPage.tsx)
  - [frontend_pwa/src/pages/ClassicsShelfPage.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/pages/ClassicsShelfPage.tsx)
  - [frontend_pwa/src/pages/HomePage.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/pages/HomePage.tsx)
  - [frontend_pwa/src/pages/HowItWorksPage.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/pages/HowItWorksPage.tsx)

Analytics and summaries:
- [backend/reader_home/home_service.py](d:/Users/Trader/story_universe_platform/backend/reader_home/home_service.py)
- [backend/analytics/insight_engine.py](d:/Users/Trader/story_universe_platform/backend/analytics/insight_engine.py)
- [backend/adaptive/adaptive_repository.py](d:/Users/Trader/story_universe_platform/backend/adaptive/adaptive_repository.py)
- [backend/dashboard/dashboard_repository.py](d:/Users/Trader/story_universe_platform/backend/dashboard/dashboard_repository.py)
- [backend/goals/goal_service.py](d:/Users/Trader/story_universe_platform/backend/goals/goal_service.py)

Tests:
- [tests/test_game_generator.py](d:/Users/Trader/story_universe_platform/tests/test_game_generator.py)
- [tests/test_guest_service.py](d:/Users/Trader/story_universe_platform/tests/test_guest_service.py)
- [tests/test_route_contracts.py](d:/Users/Trader/story_universe_platform/tests/test_route_contracts.py)

## Current Reader Game System
### Current Reader Routes
Current active reader game routes:
- `/reader/:readerId/games`
- legacy compatibility route `/readers/:readerId/games`

### Current Reader Backend Endpoints
Current active reader game endpoints:
- `POST /readers/{reader_id}/games/generate`
- `POST /readers/{reader_id}/games/results`
- `GET /readers/{reader_id}/games/history`

### Current Reader Game Types
The current reader game system supports exactly four backend game types:
- `word_puzzle`
- `vocabulary_quiz`
- `story_comprehension`
- `character_memory`

### Current Reader UX
The current reader UX is a single game shelf page that:
- lets a child choose a game type
- optionally choose a story
- launches a generated question set
- checks answers locally in the browser
- saves only a summarized session result

This is a launcher pattern, not a true game suite.

### Current Reader Data Model
Current active game persistence uses:
- `game_results`

Stored fields used in practice:
- `game_result_id`
- `reader_id`
- `game_type`
- `difficulty_level`
- `score`
- `duration_seconds`
- `played_at`

This is session-summary only. It does not support per-word analytics.

## Current Guest Game System
### Current Guest Routes
Current guest game routes:
- `/games/guest`
- backend guest endpoints under `/guest/games*`

### Current Guest Endpoints
Current guest game endpoints:
- `GET /guest/games`
- `POST /guest/games/classic-word-quiz`

### Current Guest Game Type
The current guest game flow exposes:
- `classic_word_quiz`

This is a separate guest-specific game path, not a shared engine with the reader games.

## Current Content And Vocabulary Sources
The current system already has reusable sourcing for:
- reader practice vocabulary
- reader story vocabulary
- global vocabulary fallback

The current reader game system can also pull:
- generated story events
- story scene payloads
- character names
- other event summaries

Useful current data sourcing lives in:
- [backend/games/game_repository.py](d:/Users/Trader/story_universe_platform/backend/games/game_repository.py)

## Current Analytics Touchpoints
Current analytics and adaptation depend on game summary history from `game_results`.

Observed touchpoints:
- adaptive difficulty calculations
- reader home summary
- dashboard history
- parent analytics summaries
- goal progress for `games_played`

Important consequence:
- the replacement cannot simply stop writing game-related history
- the replacement must preserve or bridge summary-level reporting while adding richer active analytics

## Reusable Pieces
These pieces are worth reusing:

### Reuse As-Is Or With Light Modification
- reader/account scoping in [backend/games/game_service.py](d:/Users/Trader/story_universe_platform/backend/games/game_service.py)
- vocabulary sourcing in [backend/games/game_repository.py](d:/Users/Trader/story_universe_platform/backend/games/game_repository.py)
- reader route family `/reader/:readerId/games`
- game history concepts already used by analytics and adaptive systems

### Reuse Conceptually, But Not In Final Product Form
- `game_results` as a backward-safe summary record
- guest usage limits and guest session tracking

## Replace
These are current active pieces that should be replaced by the new system:

### Backend
- the generic question-generator pattern in [backend/games/game_generator.py](d:/Users/Trader/story_universe_platform/backend/games/game_generator.py)
- the current `generate_game(...)` behavior in [backend/games/game_service.py](d:/Users/Trader/story_universe_platform/backend/games/game_service.py)
- the current active game type list in `SUPPORTED_GAME_TYPES`

### Frontend
- the current single-page launcher UX in [frontend_pwa/src/pages/GameShelfPage.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/pages/GameShelfPage.tsx)
- the current guest quiz UX in [frontend_pwa/src/pages/GuestGamesPage.tsx](d:/Users/Trader/story_universe_platform/frontend_pwa/src/pages/GuestGamesPage.tsx)

### Active Product Labels
- Word puzzle
- Vocabulary quiz
- Story comprehension
- Character memory
- Classic word quiz

## Retire From Active Use
These should be retired from active use after the replacement is live:
- old game option labels in the reader shelf
- legacy reader game generation flow
- guest `classic_word_quiz` as the official preview game
- any navigation copy that presents the old suite as the official system

Retirement should happen after the new system is active and verified, not before.

## Schema And Endpoint Gaps
### Missing From The Current System
The current system does not have:
- a session entity suitable for rich active game progression
- per-word analytics persistence
- a unified game payload contract across five official new game types
- a game engine designed around child-friendly play loops instead of generated question sets

### Expected Additive Structures
Likely new active tables:
- `game_sessions`
- `game_word_attempts`

Likely endpoint evolution:
- game catalog / game hub payload
- start session
- submit progress / answer
- complete session
- history / summary

## Suggested Replacement Architecture
### Backend Direction
- keep reader/account scoping
- keep vocabulary-driven sourcing
- add a session-based active model
- add per-word attempt tracking
- write summary data needed for existing analytics compatibility

### Frontend Direction
- keep `/reader/:readerId/games`
- replace the current launcher page with a true game hub
- implement one dedicated game component flow per official game type
- keep the child-facing navigation calm and mobile-first

## Deprecated Versus Active Policy
### Active After Replacement
- Build the Word
- Guess the Word
- Word Match
- Word Scramble
- Flash Cards

### Deprecated After Replacement
- `word_puzzle`
- `vocabulary_quiz`
- `story_comprehension`
- `character_memory`
- `classic_word_quiz`

Deprecated means:
- no longer shown in active UI
- no longer the official engine
- only retained in code if required temporarily for compatibility, migration, or historical reporting

## Phase 1 Summary
### What Can Be Reused
- reader/account isolation
- vocabulary sourcing
- analytics summary relationships
- reader route family
- guest session/limit infrastructure

### What Must Be Replaced
- old generator-driven game model
- current reader game shelf UX
- old active game labels and flows

### What Must Be Added
- new session model
- per-word analytics
- five-game V1 engine
- new reader game hub

## Recommended Next Step
Next execution phase:
- Phase 2: Data And Analytics Foundation

That phase should define:
- the new active schema
- the session payload contract
- the compatibility strategy for existing `game_results` reporting
