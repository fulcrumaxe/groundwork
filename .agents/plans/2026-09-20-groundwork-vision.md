## Goal

Deliver a path from today's Groundwork MVP to the PRD's full vision — "every agent session leaves you smarter" — while fixing the concrete UX complaints: (1) no real Lessons/Modules page, (2) submissions have no home on the lesson page, (3) Due and Reviews look eerily similar, (4) navigation between pages is broken/confusing, (5) visual style is plain and not fun or enticing.

## Success Criteria

- Each agent session (MCP `create_learning_module` call) produces a module with a dedicated Lessons page: study guide first, practice second, submissions third — verifiable by opening `/modules/<id>` and seeing all three.
- Due and Reviews have distinct, non-confusable purposes visible in nav, title, and layout; navigating Due → Module → Reviews → Module never strands the user (every page links back, review-result returns to its origin page).
- Every exercise attempt and its feedback is recorded and visible as submission history on the lesson/module page (not just the transient result screen).
- Visual pass makes the app feel like a learning game, not a form list, without adding a build step (still stdlib server-rendered HTML): distinct page identities, progress signals, mastery states.
- Plan stays within PRD principles: generate-before-reveal, grade-by-execution, grounded anchors, 5–10 min sessions, one process + one SQLite file, MIT/Apache-compatible.
- Validation is the repo's own suite (`python -m unittest discover -s tests`, `python -m groundwork e2e`); no scratch files outside the repo.

## Context And Current Facts

- PRD: `Open-source code learning companion — PRD.md` — practice layer over a knowledge graph, MCP-triggered micro-modules per agent session, 24 exercise types across Bloom levels, FSRS scheduling, sandbox-verified generation, creative bets (debt meter, merge gate, Socratic partner, time-travel, failure drills, teach-the-bot, voice, packs, calibration coach, team map).
- Current app (`groundwork/web.py`, 518 lines): stdlib `BaseHTTPRequestHandler`, server-rendered HTML, one inline `CSS` string (grey system-ui, 48rem column). Routes: `/` (due queue), `/reviews` (renders the same `due_html`), `/modules/<id>` (practice), `POST /cards/<id>/review`, `POST /mcp`. Nav is two links: Due · Reviews. `/` and `/reviews` both title "Due reviews" and render identical content — the source of the "eerily similar" complaint. Review-result page links only "Back to queue" (`/`), losing module context — the "navigation is broken" complaint.
- Module page today (`module_html`): Mission + "Study guide" (leveled explainer tabs Auto/1–4 via `explain.py`) + "Practice" cards with `answer_widget` per type. No submission history section; past attempts live only in the `reviews` table (grade + confidence, no submission text) and are never rendered.
- Lessons exist in data but not as a page: `pipeline.lesson_for` builds `{summary, how, worked, source, key_lines}` per concept, persisted as `modules.lessons` JSON, rendered inline as `<details>` blocks. There is no `/lessons` or per-concept route, no lesson-level progress, no per-lesson submission list.
- Exercise engine (`groundwork/exercises.py`): 13 implemented types (1 flashcard, 2 cloze, 3 signature-recall, 4 where-live, 5/6 explain, 8 predict-output, 9 trace, 11 parsons, 12 complete-function, 13 spot-bug, 14 fix-bug, 30 match-pairs). Missing vs the PRD's 24: 7 design-rationale, 10 call-path trace, 15 mutant hunter, 16 blast radius, 17 map-the-architecture, 18 odd-one-out, 19 refactor-under-test, 20 extend-feature, 21 code review, 22 compare-implementations, 23 rebuild-from-spec, 24 teach-it-back. `BLOOM_TYPES` has no evaluate/create tiers.
- Scheduler (`sched.py`, `mcp.submit_review`): simplified FSRS-like stability/difficulty/due update; `tool_list_due_reviews` excludes `stale=1`; interleaving exists. Mastery is a 0.7/0.3 rolling average per concept; no Bloom-ladder gating ("owned" only after modify/create per PRD §Mastery model).
- Creative features: only stubs exist — calibration line on Due page (accuracy vs confidence), stale detection (`mark_stale_cards`), purpose/why plumbing. No debt meter, merge gate, Socratic partner, time-travel, failure drills, teach-the-bot, voice, packs, or team map.
- Tests: `tests/test_groundwork.py` (551 lines) covers graph, diff, select, all implemented exercise types, sandbox, sched, MCP full loop, lessons persistence, widgets. Web routes have almost no tests (only `render_levels`/`answer_widget` unit checks).

## Constraints And Non-goals

- Constraints: one process, one SQLite file, no build step (stdlib HTTP + inline CSS/JS stays); every screen asks for an answer before showing one; grade by execution where possible; every exercise keeps commit/file/line anchors; sessions stay 5–10 minutes.
- Non-goals for this plan: general curriculum marketplace, code-review/linting tool, accounts/telemetry/hosted SaaS, leaderboards/streak-pressure mechanics (per PRD non-goals). No framework migration (no SvelteKit/HTMX switch inside this plan — style upgrade stays in the current stack). No new language sandboxes beyond Python verification in early phases.

## Key Decisions

1. **Information architecture: three first-class destinations, not two.** Due (what's next: interleaved FSRS queue), Modules (the library: every MCP session as a card with progress), Reviews becomes History/Log (what you did: submissions + grades + calibration). Decision: rename `/reviews` content to a true review-history page and add `/modules` index + keep `/modules/<id>` as the Lesson page. Rejected: keeping Due and Reviews as two queues — that is exactly the current confusion, and the scheduler only has one due queue anyway.
2. **Lesson page = Study → Practice → Submissions.** One concept = one lesson block with anchor id; its exercises render beneath it; its past submissions render beneath those. Rejected: a separate standalone Lessons section disconnected from exercises — the PRD wants study tied to practice, and users asked for submissions "on the lessons page."
3. **Store submission text, not just grades.** `reviews` table gains a `submission` column (migration via `ALTER TABLE ... ADD COLUMN`, backfill empty). Without this, submission history is impossible; grades alone cannot show what the learner tried.
4. **Navigation contract: origin-aware.** Every card form carries its origin (`/`, `/modules/<id>`, lesson anchor); review-result "Continue" returns there, plus persistent header nav (Due · Modules · History) and breadcrumbs on module pages. Rejected: JS SPA router — overkill for three pages and violates the no-build-step constraint.
5. **Style: evolve in place, game-feel via CSS + existing signals.** Keep single inline stylesheet; add per-page identity (color/theme accent + header), mastery/progress rings or bars from existing `mastery`/`stability` values, concept status chips (new/learning/owned/stale), confetti-free celebration states (pass/fail already classified `ok`/`stale`). Rejected: full design-system rewrite or dark-mode-first reskin as phase 1 — risk without fixing IA first; style lands after navigation is coherent so it reinforces distinct pages.
6. **PRD depth after UX coherence.** Order: IA/nav fix → lesson+submissions → style pass → exercise-type expansion toward 24 → one creative bet (calibration coach first — data already collected). Rejected: building new exercise types first — users can't find or enjoy the ones that exist.

## Recommended Approach

Fix the app shell first (nav + three distinct pages), then give lessons a real home with submission history (requires the small schema migration), then make it delightful (themed CSS using signals already in the DB), then extend learning depth (missing Bloom evaluate/create types + mastery gating), then prove one creative differentiator (calibration coach, then debt meter). Each phase is independently shippable and demoable from the same `python -m groundwork serve` flow.

## Work Plan

**Phase 1 — Navigation + page identities (fix "broken" and "eerily similar").**
- Surfaces: `groundwork/web.py` (`page()`, `Handler.do_GET/do_POST`, `due_html`).
- Units:
  1. Header nav → Due (`/`) · Modules (`/modules`) · History (`/reviews` repurposed); breadcrumbs on `/modules/<id>` (Modules › summary); active-link highlight.
  2. Split `due_html` into `due_html` (action queue: next-up card emphasis, "why this matters", Start buttons) vs `history_html` (past reviews, calibration chart data, per-day counts) — distinct titles, layouts, empty states.
  3. Origin-aware review flow: hidden `origin` field in `answer_widget` forms; result page renders Continue-here + Back-to-module + Back-to-queue.
  4. New `/modules` index (replaces the Due-page footer list): module cards with summary, created date, concept count, % mastered, stale count, entry link.
- Depends on: nothing. Test: new `tests/test_web.py` asserting route titles differ, nav present on all pages, result page echoes origin.

**Phase 2 — Real Lessons page + submissions home.**
- Surfaces: `groundwork/schema.sql`, `db.py`, `mcp.submit_review`, `web.module_html`, new lesson rendering.
- Units:
  1. Schema: `ALTER TABLE reviews ADD COLUMN submission TEXT DEFAULT ''`; record submission text in `submit_review`; backfill no-op.
  2. Module page restructure per concept lesson: `<section id="lesson-<slug>">` with leveled explainer (default, collapsed tabs preserved), its exercises, then its submission history (latest first: submission excerpt, pass/fail, confidence, reviewed_at, feedback) pulled via cards→reviews join.
  3. Lesson progress header per concept: status chip (New/Learning/Owned/Stale) from `mastery` + `stale`; anchor-linked table of contents at top ("In this module: add · greet").
  4. MCP sessions appear automatically — every `create_learning_module` row already lists on `/modules`; add per-module "session provenance" line (repo, commit range, task summary).
- Depends on: Phase 1 (nav shell). Test: extend `test_web.py` (submission appears after `submit_review`), migration test on a pre-migration DB file.

**Phase 3 — Fun, seamless, enticing style (in the same stack).**
- Surfaces: `CSS` string + page templates only; no Python logic changes except status-class hooks.
- Units:
  1. Per-page theme accents (Due = focus/energy, Modules = library/calm, History = reflective) via `<body data-page>` + CSS variables; keep light, readable, no build step.
  2. Progress signals: module progress bar, concept chips, streak-of-completions ("3/5 owned"), empty-state illustrations in pure CSS/emoji, celebratory result states (keep `ok`/`stale` classes, add copy).
  3. Interaction polish: sticky module TOC, smooth anchor scroll, Parsons drag affordances, confidence slider styling, reduced-motion respect.
- Depends on: Phases 1–2 (distinct pages to theme). Test: visual snapshot checklist (manual) + assert `data-page` + progress markup in `test_web.py`; `python -m groundwork e2e` still passes.

**Phase 4 — Toward the full 24 (Bloom evaluate/create + mastery gating).**
- Surfaces: `groundwork/exercises.py` (`TYPES`, `GENERATORS`, grading), `pipeline.py` planner, `select.py`, `sched.py`/mastery.
- Units (in order):
  1. Low-LLM-cost deterministic types first: 18 odd-one-out, 10 call-path trace (graph+runtime), 16 blast radius (graph impact), 7 design rationale (from `decisions` table — already stored, never used in generation).
  2. Execution-graded modify/create: 19 refactor-under-test, 20 extend-feature, 23 rebuild-from-spec (reuse hidden-tests harness from type 12).
  3. LLM-rubric evaluate/create: 21 code review, 22 compare-implementations, 24 teach-it-back (simulated-novice follow-ups).
  4. Deferred/expensive: 15 mutant hunter (needs mutation runner), 17 map-the-architecture (needs drag-graph UI).
  5. Mastery gating: concept counts "owned" only after a spaced modify/create pass (PRD mastery model); unlock ordering in planner.
- Depends on: Phases 1–3 (stable home for new types). Test: extend `ExerciseTest.test_all_types_generate` + grade cases per new type; e2e pass-rate gate ≥ 90% stays.

**Phase 5 — One creative bet to prove the vision (then stop and measure).**
- Pick calibration coach first (accuracy-vs-confidence data already recorded; smallest build): per-learner calibration chart on History page + "you're overconfident on trace exercises" nudge. Next candidate: comprehension-debt meter (agent-changed lines vs demonstrated concepts heatmap).
- Explicitly out of this plan: merge gate, Socratic partner, time-travel, failure drills, teach-the-bot, voice, packs registry, team map — listed as roadmap, not committed.
- Success check: delayed-retest accuracy at 7 days (PRD north star) becomes measurable once History + scheduler + new types ship.

## Validation Plan

- Phase 1: `python -m unittest discover -s tests` (new `tests/test_web.py`: route titles distinct, nav links on every page, origin round-trip); manual: serve, create module via MCP, click Due → Module → History → back with no dead ends.
- Phase 2: migration test (old DB opens, `submission` column appears, old reviews render); `submit_review` then `GET /modules/<id>` shows the submission text; `python -m groundwork e2e` passes.
- Phase 3: markup assertions (progress bar, chips, `data-page`); manual visual check on desktop + narrow mobile widths; e2e still passes.
- Phase 4: per-type generate+grade unit tests; sandbox verification pass-rate ≥ 90% on a real diff; full suite green.
- Phase 5: calibration chart renders from seeded reviews; manual review of nudge copy.
- Highest-risk validation: Phase 2 migration + submission rendering (touches live user DBs and the review POST path) — test against a copy of the real `groundwork.db` before shipping.

## Risks / Rollback

- Migration risk on user DBs: mitigate with `ADD COLUMN` default + backup note in README; rollback = drop new rendering, keep column (additive, non-breaking).
- Scope creep into SPA/framework rewrite: contained by "no build step" constraint; any framework proposal needs a new plan.
- LLM-dependent types (21/22/24) lowering verification pass-rate: ship deterministic types first; keep sandbox discard gate; flag-button follow-up.
- Style subjectivity: phase 3 ships behind the existing layout (additive CSS), revertible in one commit.

## Open Questions

- None blocking: defaults assumed are stdlib-only styling, History as the renamed Reviews page, calibration coach as the first creative bet. If you prefer the debt meter first, or want `/reviews` URL preserved as a redirect, say so at approval and Phase 1/5 adjust.
