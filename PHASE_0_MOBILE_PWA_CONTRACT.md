# Phase 0 Mobile PWA Contract

## Purpose
This document records the Phase 0 contract for the Persistent Story Universe Platform mobile-first PWA transition.

Phase 0 is the guardrail and architecture-contract phase. It does not redesign the system. It defines the route structure, payload direction, schema direction, and phased implementation order for the next eight phases.

This contract is aligned to:
- the current repository
- `Persistent_Story_Universe_Master_Spec_v2_authoritative.docx`
- the existing implemented platform behavior

## Phase 0 Outcomes
Phase 0 is complete when:
- repo-level guardrails are written in `AGENTS.md`
- the current route surface is documented
- the target route families are defined
- new summary payload targets are defined
- additive schema direction is defined
- the next eight phases are committed in writing

## Current Frontend Route Baseline
Current public routes:
- `/`
- `/login`
- `/register`
- `/reset-password`
- `/reset-password/confirm`
- `/classics`
- `/classics/:storyId`
- `/classics/:storyId/read`

Current authenticated routes:
- `/dashboard`
- `/readers/:readerId/library`
- `/readers/:readerId/library/:storyId`
- `/readers/:readerId/library/:storyId/read`
- `/readers/:readerId/worlds/:worldId`
- `/readers/:readerId/games`
- `/readers/:readerId/vocabulary`

Current frontend auth behavior:
- authentication token is stored in local storage
- authenticated navigation currently centers on `/dashboard`
- protected routes redirect unauthenticated users to `/login`

## Current Backend Route Baseline
Current major route families already present in the repo:
- `/auth/*` and account-related routes without a shared prefix in some modules
- `/classics/*`
- `/stories/*`
- `/readers/*`
- `/worlds/*`
- `/continuity/*`
- `/alexa/*`
- analytics, dashboard, adaptive, media-jobs, memory, safety, and scaling route modules

Current architectural strength:
- broad service surface already exists
- media queue and worker already exist
- narration, illustration, classics, generated stories, memory, continuity, and reader-world flows already exist

Current architectural gap for the next product phase:
- route and page structure do not yet reflect Guest, Parent, and Reader product layers
- parent and reader summary payloads are not yet formalized as mobile-first contracts
- parent PIN and guest usage limits are not yet implemented as first-class product layers

## Target Product Route Families
These route families are the target structure for the next phase set.

### Public Guest Routes
- `/`
- `/classics`
- `/classics/:storyId`
- `/classics/:storyId/read`
- `/games/guest`
- `/guest/*`

Intent:
- public discovery
- bounded guest exploration
- conversion to signup

### Auth Entry And Chooser
- `/login`
- `/register`
- `/reset-password`
- `/reset-password/confirm`
- `/chooser`

Intent:
- authentication remains separate from product layers
- authenticated users land on `/chooser` rather than the legacy dashboard

### Parent Routes
- `/parent`
- `/parent/pin`
- `/parent/analytics`
- `/parent/goals`
- `/parent/readers/:readerId`
- `/parent/settings`

Intent:
- parent-only management and analytics layer
- requires authenticated account access
- requires successful parent PIN verification where specified

### Reader Routes
- `/reader/:readerId`
- `/reader/:readerId/books`
- `/reader/:readerId/words`
- `/reader/:readerId/games`
- `/reader/:readerId/goals`
- `/reader/:readerId/books/:storyId`
- `/reader/:readerId/books/:storyId/read`

Intent:
- child-first reader experience
- low-clutter navigation
- continue-reading, books, words, games, and goals surfaced clearly

### Legacy Route Policy
- existing routes remain operational during the transition
- new product routes should be introduced additively
- legacy routes may be redirected later only after the new flow is verified

## Target Summary Payload Contracts
New mobile-first pages should prefer summary payloads to reduce fragmented frontend data loading.

### Guest Payloads
Planned:
- `GET /guest/classics`
- `GET /guest/games`
- `GET /guest/limits`
- `POST /guest/session/start`

Purpose:
- anonymous session bootstrap
- bounded exploration
- conversion messaging

### Parent Payloads
Planned:
- `GET /parent/summary`
- `GET /parent/analytics`
- `GET /parent/pin/status`

Purpose:
- compact family summary
- analytics rollups
- PIN setup and verification state

### Reader Payloads
Planned:
- `GET /reader/:readerId/home`

Purpose:
- continue reading
- recommendations
- goals
- recent activity
- quick actions

## Additive Schema Direction
Schema work must remain additive.

### Parent PIN Fields
Planned account-level or equivalent additions:
- `parent_pin_hash`
- `parent_pin_enabled`
- `failed_pin_attempts`
- `parent_pin_locked_until`

### Guest Usage Tracking
Planned additions:
- `guest_sessions`
- `guest_usage_events` or summarized guest-usage counters

Requirement:
- guest limits must not rely only on client storage

### Goals
Planned additions:
- `reader_goals`
- `reader_goal_progress`

Requirement:
- storage must remain simple and legible for both parent analytics and child-facing progress

## Guardrails For All Remaining Phases
- no speculative rewrites
- no breaking reader-derived world architecture
- no regression in tenant isolation
- no bypass around parent versus reader separation
- preserve worker-based narration and illustration pipeline
- preserve current classics and generated reading capabilities

## Committed Remaining Phases

### Phase 1: Navigation And Route Scaffolding
Goal:
- introduce Guest, Chooser, Parent, and Reader route groups without breaking current flows

Scope:
- route map implementation
- chooser redirect behavior
- placeholder pages only where required
- no parent PIN yet
- no full guest limits yet

Exit criteria:
- new route scaffolding exists
- existing flows still work
- login can transition toward chooser flow

### Phase 2: Guest Layer
Goal:
- implement the bounded public guest experience

Scope:
- landing page structure
- guest classics access
- guest game access
- guest session bootstrap
- guest usage limits
- conversion prompts

Exit criteria:
- anonymous usage is bounded and server-enforced
- guest routes are stable and testable

### Phase 3: Chooser And Parent PIN
Goal:
- implement the logged-in chooser and parent access protection

Scope:
- chooser page
- parent PIN setup
- parent PIN verification
- lockout and route gating

Exit criteria:
- parent area is protected
- reader area remains simple to enter

### Phase 4: Parent Area
Goal:
- build a compact parent management and analytics surface

Scope:
- parent summary page
- reader management entry points
- shelf visibility
- controls and settings entry points

Exit criteria:
- parents can understand family reading activity quickly

### Phase 5: Reader Area
Goal:
- implement the child-first reader home and navigation model

Scope:
- continue reading
- books
- words
- games
- goals
- child-safe navigation

Exit criteria:
- the reader experience is simple, calm, and useful on mobile

### Phase 6: Analytics And Goals
Goal:
- elevate analytics and goals into first-class product features

Scope:
- parent analytics
- parent goal management
- reader goal progress

Exit criteria:
- analytics are parent-legible
- goals are visible and actionable

### Phase 7: Growth Layer
Goal:
- add the public growth and trust surfaces after the core family flow is stable

Scope:
- expanded landing content
- content/SEO plumbing
- trust messaging and conversion support

Exit criteria:
- public funnel supports discovery and signup without destabilizing core product flows

### Phase 8: Hardening And Rollout
Goal:
- production-confidence verification for the new product architecture

Scope:
- integration coverage
- mobile route correctness
- guest limits verification
- parent PIN verification
- tenant isolation verification
- worker and operational reliability checks

Exit criteria:
- new layers are reliable enough for production rollout planning

## Working Rules For Future Phase Prompts
Every future implementation prompt should require:
1. inspect relevant files first
2. state exact implementation plan
3. implement only the scoped phase
4. validate routes, auth, and tenant boundaries
5. summarize changed files, validations, assumptions, and remaining follow-ups

## Recommended Immediate Next Step
Next execution phase:
- Phase 1: Navigation And Route Scaffolding

This is the correct next step because it creates the product route foundation without forcing the guest, parent PIN, parent dashboard, or reader-home feature work to happen prematurely.
