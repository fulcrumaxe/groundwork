# Demo-Video System (repeatable runbook)

Trigger prompt: **"run the demo-video system"**
(with optional scope, e.g. "run the demo-video system: Batch 29 pilots"
or "run the demo-video system: I-197 + F-182").

Every shipped improvement/feature gets one **30–60s video** proving the
full behavior: Chrome beats show the live surface (Status anchor,
History report, Due review flow) while terminal beats show the code
side (pure-function output, MCP calls, DB state). Each run emits three
files per item under `demos/batch-<N>/<kind>/<name>/`, where
`<kind>` is `improvement|feature` and `<name>` is `<id>-<I-N/F-N>`
when the item has a backlog number, else the bare scenario id
(some early items were never filed):
`<id>.mp4` (1280x720 H.264), `<id>.gif` (600px looping), `<id>.json`
(manifest). Filming doubles as bug-hunting: scenario research that
touches real DOM, real queues, and real verdicts finds wiring bugs —
verify each finding against the code and patch it (step 7) instead of
filming around it.

## Procedure

1. **Pick the item.** One scenario per shipped backlog item:
   `tools/demos/<area>.py` with `SCENARIO = {id, kind, batch,
   [item], title, blurb, beats}` plus `seed_db(db_path) -> dict`
   (`batch` is the backlog batch number as a positive int; `kind`
   is improvement|feature; optional `item` is the backlog number
   like `I-197`/`F-182` and joins the id in the output folder
   name (`<id>-<item>`; bare id when the item was never filed).
   Pilots to copy:
   `answerhist.py`
   (improvement with live review submit), `halflife.py` (feature
   with backdated fixture data).

2. **Author beats (total must land 30–60s, each beat 2–20s).**
   - `title`: kicker/title/subtitle card. Open + close every video.
   - `chrome`: `url_path` + `caption` (+ optional `focus` selector
     to reframe `<main>` to one section, `js` interactions, `poll_js` /
     `poll_want` / `poll_required` waits, `assert_js` / `assert_want`
     gates). Every chrome beat SHOULD carry an assert proving the
     filmed screen shows the feature — a video of the wrong screen
     is worse than no video.
   - `terminal`: `caption` + `commands` (argv lists, run from repo
     root with `DEMO_DB` pointing at the fixture DB). Output renders
     as a terminal card and is screenshotted like everything else.

3. **Manipulate the fixture in seed_db.** The pipeline copies
   `groundwork.db` to a temp DB and calls `seed_db` BEFORE serving:
   backdate reviews, plant prior answers, force cards due. Return
   facts the beats need as `{seed_<key>}` tokens (e.g. `{seed_card_id}`
   for exact-form targeting). Never touch the served library DB.

4. **Film.** `nix run .#demo-video -- --scenario <id> --out demos/
   --keep` (`--keep` preserves per-beat frames under
   `demos/batch-<N>/<kind>/<name>/<id>-frames/` for
   inspection). The run fails nonzero when any beat assert/poll
   fails, ffmpeg/ffprobe is missing, or the mp4 lands outside
   30–60s.

5. **Watch the frames.** Open the `<id>-frames/beat*.png` in order:
   caption legible, focused section correct, interaction verdict
   visible, terminal output untruncated. Fix the scenario (not the
   pipeline) and re-film until the story reads.

6. **Publish the gifs to the wiki.** The wiki is the media home —
   README tables stay generated and `demos/` stays uncommitted:
   clone `groundwork.wiki.git` to /tmp, add one gallery page per
   batch (`Batch-<N>-Demos.md`, items grouped by kind with title,
   blurb, live anchor, and seconds), copy the batch's gifs under
   `batch-<N>/`, link the page from Home, commit, and push (wiki
   pushes need the `johnproblems` account like `origin/main` —
   switch, push, switch back). Keep gifs under ~10MB (the pipeline
   warns above it); the mp4 stays the full-quality artifact.

7. **Patch findings, don't film around them.** When scenario
   research surfaces a real bug (red gate, dead display line,
   wrong wiring): verify it against the implementation, fix it
   test-first with a regression test in the area's normal test
   file, run the focused tests, re-film every video whose surface
   changed, eyeball the new frames, and refresh the affected wiki
   gifs (same push procedure as step 6).

## Definition of done — every video, no exceptions

1. mp4 + gif + manifest exist in the batch/kind/name folder; mp4 probes
   30–60s at 1280x720.
2. The video shows the FULL behavior, not the Status demo alone: the
   real caller path (Due review, History report, MCP call) appears
   with manipulated data proving the effect.
3. Every chrome beat carries an assert or required poll that passed
   in the filming run (see the run log).
4. Frames were eyeballed in order; captions read as a story.

## Pipeline facts (learned debugging the pilots — do not regress)

- Capture is retina: every page is emulated at 1280x720x2 and shot
  as lossless PNG (client runs with `--screenshotMaxWidth 2560`);
  ffmpeg downscales to 1280x720 at CRF 18. Never drop to q60 JPEG
  intermediates — text turns to mush.
- Shots follow the LIVE viewport: app scripts (verdict
  auto-scroll) can scroll past the caption, so `frame_js` always
  ends with scrollTo(0,0). Never use position:fixed overlays.
- ffmpeg's concat demuxer ignores the FINAL entry's duration (it
  inherits the previous one): the list repeats the last file and
  both encoders trim with `-t <authored total>`.
- Due submits are intercepted by the collapse flow (fetch, no
  navigation): interaction beats that need the full verdict page
  must native-submit (`f.submit()`), which takes the plain Result
  path like no-JS browsers.
- Target seeded forms by exact action URL
  (`form[action='/cards/{seed_card_id}/review']`), never "first form
  on the page" — queue order is not global due order.
- Scenario modules are stdlib-only at import time: the film process
  runs as `tools/demo_video.py`, so only `tools/` is on sys.path —
  never `from groundwork import ...` at module level (inline
  helpers; beat command strings may import freely, they run as
  subprocesses from the repo root).
- The Due queue sleep hook (`sleepsched.defer_night_new`) pushes
  NEW cards due in quiet hours forward to 07:00 UTC (up to +9h):
  seeds asserting exact overdue-day counts need a cushion (e.g.
  backdate 45d12h, not 45d).
- `focus` reframes `<main>` only: never focus page chrome
  (`#sitenav` duplicates the header — film it unfocused), and
  focus the enclosing card/article when the anchor alone frames
  an empty shot.

## Invariants

- Pipeline stays stdlib + chromium + ffmpeg + node: no Pillow, no
  playwright, no new flake inputs. Terminal/title beats render as
  HTML and screenshot through the same Chrome client.
- `demos/` output is never committed (gitignored); scenarios and the
  pipeline are the deliverable, videos are built artifacts. Published
  gifs live in the wiki repo, not the main repo.
- Never `push`, `--amend`, or rewrite history without an explicit ask.

## Batch integration

In the feature-improvement runbook this system slots between
chrome-verify (step 8) and merge (step 9): after the batch is green
in a real browser, film one video per shipped item, eyeball the
frames, patch any findings with regression tests, publish the batch
gallery to the wiki, then merge. Backlog batches MAY film a subset
when time is short, but a filmed item always meets the definition
of done above.
