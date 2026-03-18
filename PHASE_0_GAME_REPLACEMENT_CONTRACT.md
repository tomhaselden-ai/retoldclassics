# Phase 0 Game Replacement Contract

## Purpose
This document records the Phase 0 contract for replacing the current game system in the Persistent Story Universe Platform.

This is a replacement program for the active reader game experience. It is not a parallel experiment, not a temporary alternate path, and not a greenfield game platform.

The existing repository remains authoritative. The replacement must fit the current reader, vocabulary, analytics, auth, and tenant architecture.

## Why This Contract Exists
The current game shelf is functional but not aligned with the desired child-facing product direction. The next game system must:
- be easier for children to understand
- be more consistent visually
- be more strongly tied to vocabulary practice
- produce richer analytics
- remain production-safe
- replace the active old game experience instead of sitting beside it

## Replacement Scope
The replacement applies to the active reader game system and the active guest game preview system.

The replacement does not redesign:
- reader authentication
- parent/reader route separation
- vocabulary tracking
- reader-derived worlds
- analytics architecture outside game-related reporting
- classics, narration, illustrations, EPUB, memory, or continuity

## Official V1 Game Suite
The official replacement game suite is:
1. `build_the_word`
2. `guess_the_word`
3. `word_match`
4. `word_scramble`
5. `flash_cards`

Product-facing names must be:
- Build the Word
- Guess the Word
- Word Match
- Word Scramble
- Flash Cards

## Current Active System Being Replaced
The current reader game system is built around four generator-driven game types:
- `word_puzzle`
- `vocabulary_quiz`
- `story_comprehension`
- `character_memory`

The current guest game flow is:
- `classic_word_quiz`

These are the legacy active game types. They will be replaced in active product flows.

## Core Replacement Rules
- Do not preserve the old game UX just to avoid deletion.
- Do not create a second competing game shelf.
- Do not leave old reader game paths active once the new game system is verified.
- Keep historical game result data readable for analytics continuity.
- Prefer additive schema changes for the new active system.
- Retire obsolete code paths from active use only after the replacement path is stable.

## Unified Game Data Model
All new games must operate from a shared vocabulary-driven model.

Each game item should be able to use:
- `word_id`
- `word`
- `definition`
- `example_sentence` (optional)
- `difficulty_level`
- `reader_id`
- `story_id` (optional)
- `source_type`
- `trait_focus` or equivalent source metadata where already available

### Source Type Policy
`source_type` may be:
- `story`
- `classics`
- `global_vocab`

The new system should reuse current vocabulary sourcing where possible:
- reader practice vocabulary
- reader story vocabulary
- global vocabulary fallback

## Analytics Contract
Games are literacy-practice events, not standalone toys.

The active new system must support both session-level analytics and per-word analytics.

### Session-Level Analytics
The active model must support:
- `session_id`
- `reader_id`
- `game_type`
- `started_at`
- `ended_at`
- `duration_seconds`
- `difficulty_level`
- `words_attempted`
- `words_correct`
- `words_incorrect`
- `hints_used`
- `completion_status`
- `source_story_id` or equivalent source identifier when applicable

### Per-Word Analytics
The active model must support:
- `session_id`
- `word_id`
- `word_text`
- `attempt_count`
- `correct`
- `time_spent_seconds`
- `hint_used`
- `skipped`
- `game_type`

### Historical Compatibility
The current `game_results` table may remain for backward-safe history and legacy reporting continuity.

However:
- it must not remain the only active analytics store for the replacement system
- the new system must persist richer active game analytics in additive structures

## Parent Analytics Targets
The replacement must support reporting such as:
- sessions this week
- words practiced
- average success rate
- strongest game type
- weakest game type
- accuracy by game type
- time spent in practice
- repeated missed words
- improvement trend over time

These reports should extend current parent analytics rather than bypass them.

## Reader Experience Contract
The reader-facing replacement must be:
- simple
- visually clear
- fast
- encouraging
- low frustration
- mobile friendly

The reader-facing game route remains reader-scoped and should continue to live under:
- `/reader/:readerId/games`

The implementation may replace the current page and route behavior, but it must not move games out of the reader route family.

## Reward System Contract
V1 uses lightweight feedback only.

On correct answer:
- soft success sound
- small positive animation
- short encouraging message

On incorrect answer:
- soft try-again sound
- gentle feedback animation
- encouraging message

On session completion:
- short celebration
- completion summary

Explicitly out of scope for V1:
- coins
- inventory
- complex reward economies
- collectible systems

## Difficulty Contract
Difficulty remains simple and shared across the new suite:
- Easy: 3-4 letter words
- Medium: 5-7 letter words
- Hard: 8+ letter words

Reader reading level and current vocabulary logic should still inform which words are eligible.

## Guest Games Contract
The current guest game flow should not survive indefinitely as an old-system exception.

Replacement policy:
- the current guest quiz may remain temporarily during the replacement program
- the target state is a guest preview powered by the new game engine
- guest access must remain bounded and server-enforced

## Replacement Architecture Policy
### Reuse
The replacement should reuse where cleanly compatible:
- reader/account scoping
- vocabulary sourcing
- analytics/reporting infrastructure
- reader mobile route structure

### Replace
The replacement should replace:
- the generic old game generator model
- the current single-page game shelf launcher UX
- the current score-only active result model

### Retire
The replacement should retire from active use:
- `word_puzzle`
- `vocabulary_quiz`
- `story_comprehension`
- `character_memory`
- `classic_word_quiz`

Retirement means:
- removed from active reader navigation
- removed from active product labels
- no longer exposed as the official game system

Retirement does not automatically mean destructive schema deletion.

## Database Policy
Schema work must remain additive and production-safe.

Expected new active structures:
- `game_sessions`
- `game_word_attempts`

Optional supporting structures are allowed only if justified by implementation needs.

Old structures may remain if needed for:
- historical data reads
- compatibility reporting
- safe rollout

## Endpoint Policy
The current active endpoints may be superseded.

The replacement should move toward:
- game catalog or hub data
- game session start
- session progress / answer recording
- session completion
- history / summary

The final endpoint shape should remain reader-scoped and account-safe.

## Committed Implementation Phases
### Phase 1: Inspection And Deprecation Map
Document:
- all existing game files
- all current route and API entry points
- schema/tables used by games
- analytics touchpoints
- reuse/replace/retire decisions

### Phase 2: Data And Analytics Foundation
Add:
- active session model
- per-word analytics model
- shared vocabulary-driven payload contract

### Phase 3: Backend Engine Replacement
Implement backend support for the five new games.

### Phase 4: Reader Game Hub And First Playable UX
Ship the new reader game hub with the first new playable games.

### Phase 5: Complete V1 Game Suite
Ship all five official replacement games.

### Phase 6: Analytics And Parent Reporting Upgrade
Upgrade parent and reader reporting for the new active game model.

### Phase 7: Retirement Of Old Active System
Remove old active game paths from reader-facing use and deprecate obsolete backend paths.

### Phase 8: Hardening And Rollout
Add integration coverage, rollout notes, and migration confidence checks.

## Exit Criteria For Phase 0
Phase 0 is complete when:
- the official replacement scope is written down
- the old active system is explicitly named
- the new active V1 suite is explicitly named
- the analytics contract is explicit
- guest game policy is explicit
- the remaining replacement phases are committed in writing

## Next Agreed Step
Next execution phase:
- Phase 1: Inspection And Deprecation Map
