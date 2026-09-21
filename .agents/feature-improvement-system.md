# Feature & Improvement System (repeatable runbook)

Trigger prompt: **"run the feature & improvement system"**
(with optional scope, e.g. "run the feature & improvement system:
6 improvements + 6 features from the backlog").

Default batch: **8 improvements + 8 features**, picked from the
unshipped (`- ` without `[x]`) entries in
`.agents/backlog/500-improvements-500-features.md`.
Take the entries as listed — the runbook does not rank, prefer, or
skip kinds of items; whatever is next in the backlog is what ships.

## Procedure

1. **Branch + back up.** `git checkout -b batch<N>-f<M>-i<K>` from main.
   Work never lands directly on main; it merges at the end.
   Batch MCP writes go straight into the served library DB, which also
   holds personal reviews and scheduling — so snapshot it first:
   `cp groundwork.db /tmp/groundwork.db.pre-batch<N>`.

2. **Wave 1 — improvement subagents (max 7 concurrent + root).**
   Spawn one read-only child per item (`subagent_spawn`, shared
   worktree, no file writes, no commits). Each child brief:
   - read `groundwork/readtime.py` (module template) + nearest
     sibling module + matching `tests/test_*.py` (test template);
   - design ONE new `groundwork/<area>.py` (<350 lines, pure
     functions, stdlib only, no DB/schema changes, no web.py edits);
   - draft its unittest + tour entry `{id, kind, title, blurb,
     path, anchor}` + one status-anchor line;
   - run the Groundwork MCP for its contribution against the served
     library DB (`--db groundwork.db`, never /tmp — /tmp DBs strand
     modules outside the library, which is why batches 2–8 never grew
     the module count):
     `echo '{"jsonrpc":"2.0","id":1,"method":"annotate_decision",
     "params":{"repo":".","symbol":"<area>.<fn>",
     "chosen":"...","rejected":"...","reason":"..."}}' |
     python3 -m groundwork --db groundwork.db mcp`
     plus one `create_learning_module` call covering the item's diff,
     so every shipped item adds learning content, not just code;
     the call MUST include agent-authored `lessons` (2–4, each with
     `concept` + `summary` in your own words: what it does and why it
     matters) and `exercises` (front/back you wrote, not template
     filler) — the pipeline still verifies them, but the words must be
     yours; report both results including `agent_errors`
     (note if unavailable);
   - RETURN all five sections delimited; parent implements.

3. **Wave 2 — feature subagents.** Same shape, `kind: "feature"`.

4. **Implement + commit per item (parent, sequential).**
   Write `groundwork/<area>.py` + `tests/test_<area>.py`, run the
   focused tests, `git add` exactly those two files,
   `git commit -m "<BACKLOG-ID>: <what> (<area>.py)"`.
   Fix test bugs against the code's real behavior — never weaken
   correct code to fit a self-authored test.

5. **Central wiring (one commit).**
   - Register each area in `groundwork/modularity.py` AREAS.
   - Add one `status-b5-*`-style anchored subsection per item on
     the Status page (Batch 3 rule: sections live in status.py or
     the area module, never web.py; web.py only gains delegation
     lines and must stay under WEB_CEILING).
   - Append tour ENTRIES (kind set correctly; path+anchor must
     render — `test_every_entry_lands_on_rendered_anchor` enforces it).
   - Update `tests/test_tour.py` kind counts.
   - `python -m groundwork docs` (regenerates README + docs/).

6. **Backlog cross-off (same or next commit).**
   Flip shipped detail lines `- I-N:` → `- [x] I-N:` and extend the
   shipped ledger with the batch section (items + module names).

7. **Verify.** `python -m unittest discover -s tests` (the CI
   command) must be fully green; `tests/test_modularity.py` guards
   the ceilings.

8. **Chrome-verify (real browser, every batch).**
   Unit tests assert on HTML source; only the rendered DOM catches
   breakage like nested `<style>` (Batch 9: dark/type/font CSS dumped
   into `<body>` as text while all source tests stayed green).
   Reproducible script (flake pins python/chromium/node):
   `nix run .#chrome-verify` — serves a temp DB copy, opens each
   fixture page in headless Chrome via chrome-devtools-mcp, asserts
   every batch item in the live DOM (collapse submit interaction
   included), saves screenshots + `report.json`, exits nonzero on
   any failure. With agent chrome-devtools tools available, the same
   checks run natively: navigate each fixture, `evaluate_script`
   the item assertions, submit one real card review to prove the
   collapse/undo flow, confirm zero console errors.
   Fix anything found (regression test first), re-run to green.

9. **Merge.** `git checkout main && git merge --no-ff <branch>`
   (local only — never push unless explicitly asked). Resolve
   conflicts in tour.py/status.py by keeping all entries from both
   sides, re-run step 7 after resolving.

## Invariants

- web.py never grows except thin delegation lines (Batch 3 rule).
- Every area module stays under 350 lines.
- Every shipped item: tour entry + status anchor + docs regen +
  MCP run + local commit.
- Never `push`, `--amend`, or rewrite history without an explicit ask.
