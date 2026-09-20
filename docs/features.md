# Feature catalog

Generated from the tour registry — do not edit by hand. Run `python -m groundwork docs` to refresh.

## Features

| Capability | What it does | Where |
|---|---|---|
| Projects landing | Every repo you are learning, with owned progress — the front door. | `/#projects` |
| Comprehension debt meter | What changed versus what you can prove you own, per repo and file. | `/debt#debt-meter` |
| Traceback diagnose page | Paste a crash; every function it names links to its lesson. | `/diagnose#diagnose-form` |
| Bloom ladder | Six rungs beside each concept; lit rungs mark demonstrated skill tiers. | `/modules/&lt;id&gt;#ladder` |
| Coverage timeline | Every session, what it made, and what stuck. | `/reviews#coverage` |
| Anki export | All cards as tab-separated import: front, back, tags. | `/modules#exports` |
| RSS feed | Learning modules as RSS 2.0 for external readers. | `/modules#exports` |
| Module sharing | Export a module to JSON, import it into any Groundwork DB. Reviews stay private. | `/status#status-share` |
| CLI review | python3 -m groundwork review — the queue without a browser. | `/status#status-cli` |
| CI workflow | Tests run on every push; status surfaced below. | `/status#status-ci` |
| Pre-commit hook | hooks/pre-commit keeps bad commits out; presence shown below. | `/status#status-hooks` |
| Write-the-docstring exercises | Docstring exercise cards render an explanation box. Answer one below. | `/due#up-next` |
| Groundwork seed | Groundwork itself ships as learnable modules: export one repo's modules to a seed file, import it anywhere. | `/status#status-seed` |
| Sitemap and robots | Every page and module listed for crawlers; see the live map below. | `/status#status-sitemap` |
| Week in review | Attempts, active days and pass rate for the last 7 days — a weekly ritual. | `/reviews#week` |
| Review-log CSV export | Every attempt as CSV for personal analysis — grades, confidence, answers. | `/status#status-csv` |
| Read-only modules API | Modules with concept and card counts as JSON, for dashboards. | `/status#status-api` |
| Read-only due-queue API | The live due queue as JSON — same order as the Due page. | `/status#status-api-due` |
| Module health | Every capability area with its size and ceiling — web.py never grows. | `/status#status-modular` |
| Grade disputes | Flag a wrong reference with one click; maintainers triage the queue. | `/status#status-disputes` |
| Workload forecast | Reviews due per day for the next 30 days — see busy days coming. | `/reviews#workload` |
| Module reset | Start a module over from a confirm page — lessons stay, progress goes. | `/modules/&lt;id&gt;#reset` |
| Component gallery | Every UI building block on one dev page, with class names. | `/styleguide#styleguide` |
| Storage meter | Database size and per-module rows — growth never surprises. | `/status#status-storage` |
| North-star dashboard | Delayed accuracy on mature cards — the number that matters. | `/status#status-northstar` |
| Personal data download | Everything about you in one JSON — portable, private. | `/status#status-data` |
| Metacognition journal | Weekly what-did-you-misjudge prompt, answered privately. | `/journal#journal` |
| Just-one-card mode | Low energy? Answer a single card — no guilt design. | `/due#one-card` |
| README badge | Your live owned count as an embeddable SVG shield. | `/status#status-badge` |
| Tool-call analytics | Which MCP tools fire, with failure rates and latency. | `/status#status-tools` |
| Weekly letter | An auto-drafted private progress note — gentle, never streaky. | `/status#status-letter` |
| Serendipity cards | An adjacent concept you might love — bonus, never duty. | `/due#serendipity` |
| Blind spots | Lowest-mastery concepts — study time goes where it matters. | `/status#status-blindspots` |
| Personal bests | Strongest memory, most practiced, sharpest skill — no streaks. | `/reviews#bests` |
| Session summary | Answered, accuracy and what returns when — the debrief. | `/status#status-b5-session` |
| Garden stages | Concepts grow seed to sprout to tree; no streaks. | `/status#status-b5-garden` |
| Cover colors | Each module gets a stable cover hue from its repo hash. | `/status#status-b5-cover` |
| File map | Breadcrumbs show where a concept sits in the repo tree. | `/status#status-b5-filemap` |
| Prereq chain | Understand-X-first path with jump links atop each module. | `/status#status-b5-prereq` |
| Exit ticket | Each lesson ends with one ungraded retrieval question. | `/status#status-b5-exitticket` |
| Misconceptions | Lessons flag the wrong idea learners most often hold. | `/status#status-b5-misconceptions` |
| Lesson notes | A per-lesson scratchpad kept in your browser only. | `/status#status-b5-lessonnotes` |
| Name-that-smell | Read a real snippet and name its dominant code smell — six smells, one choice. | `/status#status-b6-smell` |
| Rename-symbol exercise | Propose a clearer name for a weak identifier; convention-checked, rubric-justified. | `/status#status-b6-renameex` |
| Complexity golf | Rewrite a nested function so it nests less — AST-measured, tests stay green. | `/status#status-b6-golf` |
| Dependency-injection swap | Rewrite a hardcoded dependency as a parameter; old tests stay green. | `/status#status-b6-diretro` |
| Error-handling retrofit exercises | Add the missing error branch: a fault-injection harness fails until your guard handles it. Try one below. | `/due#up-next` |
| Logging-retrofit exercises | Type 29 cards mark the lines that deserve a log call — you name each level, checklist-graded with no sandbox. | `/status#status-b6-logretro` |
| Type-annotation retrofit | Unannotated function in, full annotations out — AST-graded per slot. See how it is judged. | `/status#status-b6-typeanno` |
| Doc-example doctest | Write a >>> example that passes as a real doctest run. | `/status#status-b6-docdoctest` |

## Improvements

| Capability | What it does | Where |
|---|---|---|
| Nav badge counts | Due, Modules and History counts live in the nav — no guessing. | `/#sitenav` |
| Resume links | Each module card jumps straight to its first unowned lesson. | `/modules#resume` |
| Queue position | Card i of n plus an Up-next tag on the first card. | `/due#up-next` |
| Difficulty dots | Five-dot FSRS difficulty meter on every card. Hover for the number. | `/due#difficulty` |
| Confidence pills | Rate 1–5 confidence with every answer; powers the calibration coach. | `/due#confidence` |
| Ctrl+Enter to submit | Submit from any text field with Ctrl/Cmd+Enter. Try it in the box below. | `/due#up-next` |
| Copy buttons | Every code block grows a Copy button. Try one in the lesson below. | `/modules/&lt;id&gt;#{lesson}` |
| Answer drafts | Type an answer, reload the page — your text survives. Cleared on submit. | `/due#up-next` |
| Give-up path | Stuck? Give up shows the answer and records the lapse honestly. | `/due#giveup` |
| Due-why tooltips | Hover why-due: memory strength, days overdue, lapse count. | `/due#due-why` |
| Relative timestamps | History reads as “just now” and “3h ago” — hover any time for the exact timestamp. | `/reviews#timestamps` |
| Memory-strength bars | Each Due card shows its FSRS memory strength in days, as a bar. | `/due#memory` |
| Module sorting | The Modules library toggles newest-first and oldest-first. | `/modules#sort` |
| Snooze a card | Not today? Snooze pushes one card to tomorrow — no grade recorded. | `/due#snooze` |
| Back-to-top link | Long module pages grow a floating Back to top link. | `/modules#top` |
| Next-gap forecast | Each Due card estimates its next gap at steady passes. | `/due#forecast` |
| Queue status chips | Due, overdue and new cards carry distinct chips in the queue. | `/due#queue-status` |
| Grading disclosures | Every card says how it is judged before you answer. | `/due#grading` |
| Lesson read times | The module table of contents estimates minutes per lesson. | `/modules/&lt;id&gt;#readtime` |
| Keyboard shortcuts | g then d jumps to Due, ? opens the cheat sheet — typing never hijacked. | `/#shortcuts` |
| Skip links | Skip to content link plus header/nav/main/footer landmarks. | `/#main` |
| Helpful 404 | Unknown paths get links and a project search, never a bare error. | `/404#not-found` |
| Queue grouped by module | Due cards gather under collapsible per-module sections. | `/due#queue-groups` |
| Daily digest | Today at a glance: due now, new cards, and where to start. | `/due#digest` |
| Month in review | Concepts owned, accuracy trend and effort across the last 30 days. | `/reviews#month` |
| Related modules | Same repo or shared concepts — keep following the thread. | `/modules/&lt;id&gt;#related` |
| Decision quotes | Agent chose-X-over-Y rationale quoted inside the lesson it shaped. | `/modules/&lt;id&gt;#decisions` |
| Clarity votes | Rate each lesson 1–5; averages feed generation quality. | `/modules/&lt;id&gt;#clarity` |
| Already-know skip | Know it? Skip the line — the cards verify you in 30 days. | `/modules/&lt;id&gt;#already-know` |
| Undo last review | Misclick recovery within 60 seconds — scheduling restored. | `/reviews#undo` |
| Unique page titles | Every page names its context; browser tabs stay distinct. | `/status#status-b5-titles` |
| Empty states | No dead ends: every dry page offers a next step. | `/status#status-b5-empty` |
| Palette variables | One :root token source for ink, paper, accents, pass/fail/stale. | `/status#status-b5-palette` |
| Copy links | Every lesson section carries its own deep link. | `/status#status-b5-copylink` |
| Reading progress | A slim bar shows how far through a module page you are. | `/status#status-b5-readprogress` |
| Char counts | Code textareas report chars, lines and words as you type. | `/status#status-b5-charcount` |
| Print stylesheet | Lessons print cleanly as serif study sheets. | `/status#status-b5-printcss` |
| Answer guard | Blank submits get an inline warning instead of silence. | `/status#status-b5-answerguard` |
| Header search | One box in the header searches concepts, modules, and symbols — press / to focus from any page. | `/#site-search` |
| Page breadcrumbs | Every nested page opens with its trail — Due, Modules or History first, then module, lesson, card. | `/status#status-b6-crumbs` |
| Explainer level carries over | Pick Plain words once and every link keeps it — the level rides the URL. | `/status#status-b6-levelcarry` |
| Sticky TOC section highlight | The sticky module TOC now marks the section you are reading — scroll a module page and watch the current lesson light up. | `/modules/&lt;id&gt;#readtime` |
| Card deep-links | Every History attempt links straight to the exact card on its module page — no more scrolling to find the one you missed. | `/reviews#attempts` |
| Lesson pager | Each lesson article ends with previous/next card links — walk a module one card at a time. | `/status#status-b6-pager` |
| Footer sitemap | Every page ends in a grouped site map — Due, Modules, History, About — so no page is a dead end. | `/#site-footer` |
| Keep your place in the queue | Answering a card and coming back lands you where you left off, not at the top. | `/due#queue` |

## The original loop

| Capability | What it does | Where |
|---|---|---|
| Spaced review queue | One card at a time, most overdue first. This is the loop. | `/due#queue` |
| Module library | Every agent session as a lesson card with owned-progress bars. | `/modules#library` |
| Leveled explainers | Each concept explains itself three ways: plain, practitioner, expert. | `/modules/&lt;id&gt;#{lesson}` |
| Exercise widgets | Parsons drag-and-drop, fill-in blanks, predict-the-output and more. | `/modules/&lt;id&gt;#practice` |
| Attempt history | Every try recorded with grade, confidence and timestamp. | `/reviews#attempts` |
| Honest result screen | Answer any card: verdict, feedback, next-due — then back where you came from. | `/due#up-next` |
| Calibration coach | Accuracy vs confidence per skill; nudges your overconfident blind spots. | `/reviews#calibration` |
| MCP endpoint | Agents file learning modules with create_learning_module. | `/status#status-mcp` |
