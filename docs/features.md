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
| Property-test authoring | State assert invariants for a function — each one runs green or tells you which failed. | `/status#status-b7-proptest` |
| Fuzz-target triage | Reproduce a fuzzer-found crash: write the minimal failing call and name the crashing line. | `/status#status-b7-fuzztriage` |
| Perf-fix exercises | Rewrite a loop-heavy function so it scores lower — AST-measured, tests stay green. | `/status#status-b7-perffix` |
| Memory-profile reading | Read a tracemalloc-style snapshot and name the top-allocating line. | `/status#status-b7-memprofile` |
| Race-hunt | Spot the shared mutable state: name the line plus the fix — local copy, lock, or parameter. | `/status#status-b7-racehunt` |
| Dead-code elimination | Cut the flagged dead function, branch, or import — remaining tests stay green. | `/status#status-b7-deadcode` |
| Config extraction | Hoist magic values into named constants; hidden tests stay green. | `/status#status-b7-configex` |
| API-signature design | Design a function signature — name, params with defaults, return annotation. | `/status#status-b7-apidesign` |
| Spec writing | Write acceptance criteria for a function: every checkbox — inputs, returns, edge cases — must appear. | `/status#status-b8-specwrite` |
| Commit-message authorship | Summarize a diff as a commit message: imperative subject naming the what and the why. | `/status#status-b8-commitmsg` |
| Changelog entry | Write a keep-a-changelog entry: pick the Added/Changed/Fixed section and state the user-visible impact. | `/status#status-b8-changelog` |
| Issue reproduction | Write a minimal repro script from a bug report; the sandbox confirms it fails. | `/status#status-b8-repro` |
| Bisect drill | Find the breaking commit in a synthetic history — hash or index. | `/status#status-b8-bisect` |
| Rebase-conflict resolution | Resolve a planted git-conflict block keeping both sides; static check stays green. | `/status#status-b8-rebase` |
| Migration authoring | Rename a record field with a default across fixture rows. | `/status#status-b8-migration` |
| Rollback planning | Order the rollback steps for a bad deploy — freeze, flag, revert, verify. | `/status#status-b8-rollback` |
| Threat modelling | List a function's abuse cases — injections, auth gaps, secrets. | `/status#status-b9-threatmodel` |
| Secret-scan | Spot the leaked credential in a snippet — quote the exact value or its line. | `/status#status-b9-secretscan` |
| Input-validation audit | Spot the inputs that reach dangerous sinks without validation. | `/status#status-b9-inputaudit` |
| Accessibility audit | Spot the access barriers in rendered HTML — missing alt, labels, roles, lang, link names, heading order. | `/status#status-b9-a11yaudit` |
| i18n extraction | List the hardcoded UI strings to extract for translation — exact set match. | `/status#status-b9-i18n` |
| Regex authoring | Write a regex that matches every required case and rejects the rest — graded on a fixed case-suite. | `/status#status-b9-regexex` |
| SQL authoring | Write a SELECT from a spec — graded on the rows it returns. | `/status#status-b9-sqlex` |
| CSS layout fix | Fix a broken CSS block to match the wireframe — static tolerant grading. | `/status#status-b9-cssfix` |
| CLI UX review | Spot the one usability flaw in a --help screen — name its category. | `/status#status-b10-cliux` |
| Log reading | Diagnose an outage from logs alone — name the exact root cause, not a red herring. | `/status#status-b10-logread` |
| Metrics reading | Spot which graph regressed at the deploy mark — reply with its letter. | `/status#status-b10-metrics` |
| Flame-graph reading | Spot the frame that dominates a flame graph — name it and say why (widest bar wins). | `/status#status-b10-flame` |
| Crash triage | Read a mini traceback — name the crashing function and the fix category. | `/status#status-b10-crashdump` |
| Dependency upgrade | Migrate a caller across a breaking pin bump — new-API shape in, old shape out. | `/status#status-b10-depupgrade` |
| License-check | Judge whether a dependency fits this AGPL-3.0 project -- verdict plus reason. | `/status#status-b10-licensecheck` |
| Containerize it | Write a Dockerfile for a small service — static build gate, no partial credit. | `/status#status-b10-containerize` |
| CI pipeline | Author a push-triggered CI pipeline — static dry-run lint, no partial credit. | `/status#status-b11-cipipe` |
| Cut the stale flag | Remove a dead feature-flag branch — grep gate plus green hidden tests. | `/status#status-b11-flagcut` |
| Backfill script | Write a backfill function that migrates old rows to the new shape — sandbox-executed over fixtures. | `/status#status-b11-backfill` |
| Page the endpoint | Retrofit paging onto a list endpoint — slices, total, and stable order checked. | `/status#status-b11-pageapi` |
| Cache invalidation | Name every mutation path that busts a cached value — exact set, no hot-path busts. | `/status#status-b11-cacheinv` |
| Idempotency double-run | Make the handler re-runnable — the grader runs it twice and both runs must agree. | `/status#status-b11-idempot` |
| Rate-limit it | Pick per-key + global limits, a window, burst handling, and 429 + Retry-After — rubric-graded with partial credit. | `/status#status-b11-ratelimit` |
| Webhook verify | Verify an HMAC-signed webhook — valid passes, tampered, wrong-secret, and replayed deliveries rejected. | `/status#status-b11-webhook` |
| Type completeness contract | Every exercise type proves six parts — generator, grader, widget, disclosure, emission, e2e answer — audited live below. | `/status#status-b12-typecontract` |
| Delayed retest | 7- and 30-day probe cards resurface owned concepts so recalls measure true retention. | `/status#status-b12-retest` |
| Unlock quests | Own X to unlock Y — each locked skill shows its unlock path, step by step. | `/status#status-b12-quests` |
| Difficulty dial | Tune challenge 1-5 from gentle to spicy — sets how forgotten review cards may be and how many new cards join each short session. | `/status#status-b12-diffdial` |
| Cold-attempt sessions | Attempt unseen concepts cold before studying — struggle first, then learn. | `/status#status-b12-coldattempt` |
| Worked-example fading | Worked traces fade per concept: full trace, then the last step hides, then only the first shows — recall grows as support shrinks. | `/status#status-b12-fading` |
| Self-explanation prompts | Every worked step asks why it exists — explain each line in your own words before moving on. | `/status#status-b12-selfexplain` |
| Elaboration drills | Connect a new concept to two you already own — shared tokens pick the partners. | `/status#status-b12-elaboration` |
| Dual-coding packs | Every key idea gets words plus a diagram plus a worked trace — two channels, one concept. | `/status#status-b13-dualcode` |
| Interleaving engine | Practice picks contrast by concept — weakest cell first, never the same idea twice running. | `/status#status-b13-interleave` |
| Spacing optimizer | Per-concept gaps from your own recalls — strong ideas stretch out, fragile ones return tomorrow. | `/status#status-b13-spacingopt` |
| Retrieval-first lessons | Every lesson asks before it tells — attempt first, then read the explanation. | `/status#status-b13-retrieval` |
| Predict-then-reveal | Every code snippet hides under a one-click cover — predict first, then reveal. | `/status#status-b13-predict` |
| Confidence-weighted scoring | Brave-correct beats shy-correct — calibration pays, overconfidence costs. | `/status#status-b13-confweight` |
| Calibration drills | Bet points on answers at explicit odds — fair when honest, profitable only when calibrated. | `/status#status-b13-calibdrill` |
| Overconfidence cards | Confidence outrunning accuracy by 25 points deals an intervention card with one counter-habit. | `/status#status-b13-overconf` |
| Mastery interview | Defend a concept aloud like an oral exam — speak it, write it, and clear half the rubric points. | `/status#status-b18-interview` |
| Transfer test | Same idea in code you have never seen — no lesson links on the front; the sandbox checks the behavior. | `/status#status-b18-transfer` |
| Far-transfer challenge | Port a pattern to the other language — Python to JS/TS or back — with every behavior intact. | `/status#status-b18-fartransfer` |
| Pressure drill | Diagnose a production-style log against a 90s clock — follow the victim request, not the noise. | `/status#status-b18-pressure` |
| Incident replay | Replay a past outage — signal, detection, mitigation, prevention, and timeline order, rubric-graded. | `/status#status-b18-incident` |
| Pre-mortem | List how this code could fail before it does -- errors, retries, races, leaks. | `/status#status-b18-premortem` |
| Reading fluency | Skim a snippet on a 90s budget, gist it in one line, then verify with three probes — keyword, locate, owner. | `/status#status-b18-fluency` |
| Naming fluency | Guess what a name does before reading its docstring — prediction then verify. | `/status#status-b18-nameguess` |
| API guessing | Predict which stdlib call fits the task, then check the docs synopsis — commit before you verify. | `/due#up-next` |
| Mental-model mapping | Draw the data flow from memory — graph-diff graded, partial credit per edge. | `/due#up-next` |
| Rubber-duck mode | Explain it to a patient bot that only asks questions — three prompts, no answers given. | `/due#up-next` |
| Protege-effect studio | Teach a simulated junior — correct the claim, answer the follow-up, both must pass. | `/due#up-next` |
| Feynman check | Explain it simply — rubric coverage gated by a jargon budget. | `/due#up-next` |
| Analogy builder | Map it onto a familiar domain — then state where the analogy breaks. | `/due#up-next` |
| Counterexample hunting | State the belief, then break it: name one input where the claim about a real function fails. | `/status#status-b19-counterex` |
| Boundary-value drills | Name the ONE edge integer to probe first — off-by-one bootcamp. | `/due#up-next` |
| Invariant stating | Write the loop invariant; the verifier checks your claim. | `/due#up-next` |
| Contract authoring | Write requires/ensures one-liners; measured tests grade them. | `/due#up-next` |
| Refactoring kata library | Same smell across many repos on a spaced schedule until the fix sticks. | `/status#status-b20-katabank` |
| Debugging kata library | Meet the eight classic bug shapes with a failing call each, drawn from synthetic and real code. | `/status#status-b20-debugkata` |
| Reading-group mode | Study one module together: shared lesson, discussion prompts, local presence sync. | `/status#status-b20-readgroup` |
| Re-taught after 30 days | A month-old concept returns with your own words beside a fresh prompt. | `/status#status-b20-reteach` |
| Your forgetting curve | Reviews timed to your decay — fast faders return sooner, slow faders later. | `/status#status-b20-forgetcurve` |
| Best time to review | Your past grades reveal when your recall peaks — review then for more passes. | `/status#status-b20-peaktime` |

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
| Whole-card module links | Every module card is one big target with a visible keyboard focus ring. | `/status#status-b7-clickcards` |
| Mark as reviewed | Re-read a lesson? Tick it reviewed — no answer, no grade, kept in your browser. | `/status#status-b7-reviewed` |
| Module status filter | The Modules library filters by status — all, in-progress, owned, stale. | `/status#status-b7-modfilter` |
| Modules pagination | Past 50 modules the library splits into pages — page links keep your filters. | `/status#status-b7-modpages` |
| Concept chips link to lessons | Every concept's status chip jumps straight to its lesson section. | `/status#status-b7-chiplinks` |
| Recently visited strip | Due opens with your last 8 modules — kept in this browser only. | `/status#status-b7-recent` |
| Unsaved-answer guard | Start typing an answer and wander off and the browser asks first. | `/status#status-b7-unsaved` |
| Result verdict auto-scroll | After grading, the verdict block takes focus and scrolls into view. | `/status#status-b7-autoscroll` |
| Spot external links at a glance | External links now show a marker plus screen-reader note while internal routes and repo paths stay plain. | `/status#status-b8-extlinks` |
| Canonical URL contract | One language-prefix-free URL per page — the full route table lives on Status. | `/status#status-b8-canonurl` |
| Origin allowlist guard | ?origin back-links only return to known app pages — open-redirect shapes fall back to the queue. | `/status#status-b8-originguard` |
| Primary button first | Every form leads with its primary action — tab order matches visual order. | `/status#status-b8-buttons` |
| Per-page hooks | Every page carries a data-page hook from a closed registry — future pages cannot ship unstyled. | `/status#status-b8-pageids` |
| Archived-module notice | Deleted modules explain themselves with search and siblings, not a bare 404. | `/status#status-b8-archived` |
| Merged site nav | Header and footer render from one nav table — one active state, no drift. | `/status#status-b8-sitenav` |
| Answer-field autofocus | Cards focus their answer box as they scroll into view — just start typing. | `/status#status-b8-autofocus` |
| Collapse answered cards | Answered Due cards collapse in place with an inline undo button instead of a full reload. | `/status#status-b9-collapse` |
| Five-minute session | One click queues about five minutes of the most-overdue cards and starts you on them. | `/status#status-b9-minisession` |
| Continue interrupted sessions | History rows offer a continue link that rebuilds the queue as it was — cards still due, same module. | `/status#status-b9-resume` |
| Shareable session snapshot | A link showing one module's answered count and accuracy — read-only, no login, no private data. | `/status#status-b9-snapshot` |
| Quarterly link audit | Every internal link the app emits is extracted from rendered HTML and checked against the canonical route table, so broken routes are caught in CI instead of once a quarter by hand. | `/status#status-b9-linkcheck` |
| Dark mode | Dark-OS users get a tested dark palette; every body-text pair passes WCAG AA contrast. | `/status#status-b9-darkmode` |
| Type scale | One ratio-based scale for every font size — headings, body, small and code share a single source, not scattered literals. | `/status#status-b9-typescale` |
| Distinctive offline-safe fonts | Headings, body, and code each get their own system-font voice — no downloads — with generic-family fallbacks that always render. | `/status#status-b9-fontstack` |
| Wordmark logo | A single inline SVG lockup (G monogram plus word) in currentColor, so the header mark adapts to every palette including dark mode with no assets and no emoji. | `/status#status-b10-wordmark` |
| Bloom chip colors | Each Bloom tier has its own chip color in cards, History, and the coach table — scan for weak skills at a glance. | `/status#status-b10-bloomchips` |
| Animated progress bars | Progress bars ease to their new width in 200ms — instant when reduced motion is set. | `/status#status-b10-progbar` |
| Owned badge reveal | Newly Owned concepts celebrate with a calm quarter-second badge reveal — CSS shapes only, motion-safe. | `/status#status-b10-ownedbadge` |
| Due cards stagger in | Queue cards fade up one after another in 35ms steps (245ms total, motion-safe) — pure CSS, no JavaScript. | `/status#status-b10-stagger` |
| Consistent disclosure carets | Every hint and grading disclosure shares one chevron that rotates open — same affordance in every browser, keyboard and screen-reader behavior unchanged. | `/status#status-b10-carets` |
| Code line numbers | Every code block numbers its lines via CSS counters, beside the Copy button it already had. | `/status#status-b10-codelines` |
| Tiny syntax highlight | Python/TS code snippets get dependency-free coloring from a single-pass tokenizer that escapes raw text before wrapping tokens, so markup can never leak. | `/status#status-b10-highlight` |
| Hint tiers at a glance | Hints show their weight: Nudge, Pointer, then Worked step — spend the cheapest help first. | `/status#status-b11-hinttiers` |
| Segmented confidence slider | Rate confidence 1–5 on a tappable segmented control with arrow-key support — same rating, no typing. | `/status#status-b11-confslider` |
| Focus-visible rings | Every link, button, field, and card shows one palette-matched ring the moment you Tab to it. | `/status#status-b11-focusrings` |
| 44px tap targets | Every button and input is at least 44px tall — full-size even in compact density. | `/status#status-b11-taptargets` |
| Unified corner radii | Cards round at 12px, controls at 8px, chips pill — one token source, no scattered literals. | `/status#status-b11-radius` |
| Section spacing rhythm | Every section gap comes from one ratio-based scale, so pages breathe evenly. | `/status#status-b11-spacing` |
| Empty-state illustrations | Dry pages greet you with a small line illustration above the next step — never a blank wall. | `/status#status-b11-emptyart` |
| Session-complete hero | An empty Due queue greets you with a calm all-caught-up banner — celebration, still with a next step. | `/status#status-b11-donehero` |
| Logbook History | History reads like a logbook: monospace dates, ruled rows, muted headers. | `/status#status-b12-logbook` |
| Library shelf | Module cards stand like books on a shelf — a spine accent in each module's own cover color with a subtle lift. | `/status#status-b12-shelf` |
| Due briefing | Due cards read as numbered mission cards — queue order needs no markup. | `/status#status-b12-briefing` |
| Verdict stamps | Result verdicts stamp PASS or FAIL in rotated bordered type — plain words, never emoji. | `/status#status-b12-verdicts` |
| Owned banner | Owned concepts get a calm full-width banner — no confetti, just the milestone. | `/status#status-b12-ownbanner` |
| Press micro-interactions | Buttons and cards press back a touch while you hold them — silent, instant, and still for reduced-motion users. | `/status#status-b12-pressfx` |
| Loading skeletons | Module pages show a static placeholder shell — title, progress, lesson rows — while lessons generate. | `/status#status-b12-skeletons` |
| Optimistic submit | Submit a card and its buttons lock with a spinner and Working status — no double grades while grading runs. | `/status#status-b12-optimistic` |
| Chrome error pages | Server errors render inside the normal header and footer with a safe label and a way back — never a naked dropped connection. | `/status#status-b13-errpage` |
| Inline form errors | Out-of-range answers fail loudly beside the field — a role=alert line naming the fix, not silence. | `/status#status-b13-formerr` |
| Selection accent | Selected text wears the page accent with ink text — forced-colors users keep native selection. | `/status#status-b13-selection` |
| Palette scrollbars | Thin palette-matched scrollbars — touch devices and forced-colors users keep natives. | `/status#status-b13-scrollbar` |
| Due-count favicon | The tab icon carries the live due count as a badge — zero means the plain mark. | `/status#status-b13-pageicon` |
| Share unfurls | Shared links unfurl with the page title and lede — no bare URLs, no localhost canonical lie. | `/status#status-b13-ogtags` |
| Compact density | One header button shrinks gaps and type for small screens — tap targets stay full-size. | `/status#status-b13-density` |
| Responsive audit | 360/768/1024/1440 audited live over the shipped CSS — phone tables and padding fixed first. | `/status#status-b13-responsive` |
| Stable Parsons drag lists | Parsons code-order lists now reserve space for every line before first paint — drag to reorder and the submit row stays put. See the reserve below. | `/status#status-b18-parsons` |
| Design tokens | One token table documents every palette and radius token in the README and the styleguide. | `/status#status-b18-tokens` |
| Page snapshot goldens | Core pages diff against committed goldens; drift fails CI. See below. | `/status#status-b18-pagesnap` |
| Emoji-free icons | No raw emoji icons -- text words, SVG chevrons and CSS shapes, all readable with styles off. | `/status#status-b18-emoji` |
| Motion budget | Every animation finishes in 300ms or less, and reduced-motion users always see the still end state. | `/status#status-b18-motion` |
| High-contrast mode | Chips, badges, and progress bars stay legible under OS high-contrast and forced-colors — system colors, not washed-out tints. | `/status#status-b18-contrast` |
| Explain it differently | Flip any lesson example-first or definition-first — same content, the order that clicks. | `/status#status-b18-explainflip` |
| Inline glossary tooltips | Jargon in leveled explainers defines itself on hover — no lookup, no lost place. | `/status#status-b18-glossary` |
| Symbol mentions link to lessons | Every function and symbol a lesson names links to its own lesson — or its file line when it has none. | `/modules/&lt;id&gt;#{lesson}` |
| Worked-example replay | Step through the measured trace one step at a time — prev/next with the state at each step. | `/status#status-b19-replay` |
| Run the worked example yourself | Every worked example grows editable inputs: change the arguments, see your call rebuilt in-page, and try neighbor variants. | `/modules/&lt;id&gt;#runinputs` |
| Before/after diff per lesson | Each lesson shows what the agent changed: added/removed counts with the capped diff one click away. | `/status#status-b19-beforafter` |
| Collapsible source blocks | Long lesson source hides behind a Show full file context expander — short snippets read on. | `/modules/&lt;id&gt;#{lesson}` |
| Why this lesson matters | Each lesson opens with the agent's own one-line reason — why this concept earns your study time. | `/modules/&lt;id&gt;#{lesson}` |
| Try-it-yourself prompts | Study paragraphs pause for a try-it-yourself nudge — restate, exemplify, or predict before reading on. | `/modules/&lt;id&gt;#{lesson}` |
| Lesson version banner | Lessons name the commit they were written for — and say when the code has moved on since. | `/status#status-b19-lessonver` |
| Lesson version diff | Old versus new code, line by line. | `/status#status-b20-lessondiff` |
| Pinned lessons | Pin must-read lessons so they stay atop the module no matter how the list is ordered. | `/status#status-b20-lessonpin` |
| Printable lesson handout | Any single lesson exports as a clean print-ready handout with its read-time estimate. | `/status#status-b20-handout` |
| Explainers remember their state | Study-first panels reopen as you left them. | `/status#status-b20-tabmemory` |
| Levels that read your calibration | Auto-level now weighs recent calibration, not just mastery. | `/status#status-b20-explcalib` |
| ELI5 and tradeoff extremes | Explainers stretch both ways: an ELI5 analogy on top, design tradeoffs below. | `/status#status-b20-levelextremes` |
| Peer level hint | Tabs note which level opted-in peers found most helpful; silent until quorum. | `/status#status-b20-peerhelp` |
| Every lesson gets a visual | Lessons missing a visual are flagged until fixed. | `/status#status-b20-diagrams` |

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
