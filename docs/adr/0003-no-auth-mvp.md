# ADR 0003: No user accounts/auth in the MVP

## Status
Accepted

## Context
One of the core use cases is a family member or friend checking on someone else's flight without being the
traveler themselves. Needed to decide whether that requires accounts (e.g. "add a family member, they get
notified") or can be satisfied more simply.

## Decision
No user accounts, authentication, or sessions in the MVP. Any flight is looked up by flight number + date and
produces a shareable URL (`/flight/:ident/:date`) that anyone can open.

## Rationale
The flight number + date *is* a sufficient, publicly-known identifier for a specific flight instance — it
requires no private/personal data to look up, unlike (say) a boarding pass or a specific traveler's itinerary.
A shareable link satisfies the "watch a loved one's flight" use case directly: the traveler (or whoever knows
their flight number) sends the link, anyone can open it, no signup friction on either side. This mirrors how
airlines' own "flight status" pages already work.

Building accounts first would front-load significant work (auth flow, session management, a users table, and
all the security surface that comes with it) before validating whether the core lookup/tracking experience is
even useful. Deferring it keeps the MVP small and shippable.

## Alternatives considered
- **Accounts + saved trips + notify-on-change**: more powerful (e.g. proactive push notifications when a
  gate changes) but a much larger build, and not required to satisfy the stated use case. Revisit if the
  no-login model proves limiting in real use — see `docs/ROADMAP.md`.

## Consequences
- No personalized experience (no saved flights, no notification subscriptions) until/unless a future phase
  adds accounts.
- Cache invalidation and cost-control logic (`docs/DATA_SOURCES.md#cost-control`) has to work off "is anyone
  currently viewing this flight" (`last_viewed_at`) rather than a per-user subscription list, since there's no
  concept of "users" to attach a subscription to.
- Anyone who knows (or guesses) a valid flight number + date can view that flight's data — acceptable here
  since none of it is private information, but this assumption would need revisiting if any private/user-
  specific data is ever added to a flight's detail page.
