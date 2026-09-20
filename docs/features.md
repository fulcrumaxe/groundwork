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
