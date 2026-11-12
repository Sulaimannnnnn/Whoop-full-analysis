---
name: "whoop-full-analysis"
description: "تحليل كامل لبيانات ساعة WHOOP (ملف تصدير ZIP/CSV، لقطات شاشة، PDF) بدون تجاوز شيء — التعافي، HRV، النوم، الإجهاد، التمارين، اليوميات، مربوطة ومشروحة بلغة واضحة، بالعربية أو الإنجليزية. استعمله لأي بيانات WHOOP / ووب. Full WHOOP data analysis (ZIP/CSV export, screenshots, PDF): Recovery, HRV, sleep, strain, workouts and journal, linked and explained in plain Arabic or English."
---

# WHOOP full analysis — تحليل بيانات WHOOP الكامل

The user is not a health or data specialist. They set four conditions, and every analysis must meet all of them:

1. **Nothing ignored** — every file, column and day they send is used or explicitly accounted for, and the report proves it.
2. **Linked, not listed** — show how the metrics drive each other (sleep → Recovery, effort → next morning, habits → body), not one metric at a time.
3. **Exact** — every number comes from code run on their raw data. Never estimate, eyeball (including off a chart), or fill gaps from general knowledge.
4. **Explained** — plain language a non-specialist understands (Arabic or English, see «Language»): what each number means for *them*, why it moved, and what to do.

## Language — اللغة

Two languages, same analysis. Write in the language the user writes in: Arabic (the default, and the one to use when unsure) or English. Everything the user reads follows that one language — the report, the chat reply, the visual brief, the profile page and the morning check — and the two are not mixed: no Arabic section titles in an English report, and no English sentences in an Arabic one beyond WHOOP's own terms. If the user asks for both («بلغتين» / "both languages"), deliver the full report and the brief twice, once per language, with identical numbers.

For English, keep every rule in this skill and translate its Arabic wording as you go:

- **Evidence words:** «علاقة واضحة» → "clear link", «إشارة محتملة» → "possible signal", «تظهر بين الفترات فقط» → "shows between periods only", «ما ظهرت علاقة واضحة» → "no clear link", «البيانات ما تكفي للحكم» → "not enough data to judge".
- **Report sections, same order:** 1. The one-minute summary · 2. What I received from your data · 3. Your normal · 4. What moves your Recovery · 5. Your sleep in detail · 6. Your effort and workouts · 7. Your habits (Journal) · 8. Your week, Ramadan and travel · 9. Days your body was under stress · 10. The overall trend · 11. What WHOOP doesn't tell you · 12. Your action plan, with "Your top 3 levers" and the "14-day protocol" · 13. Quick glossary.
- **Glossary and data-export steps:** give the same explanations in plain English.
- **Visual brief:** add `"lang": "en"` to `brief.json` and write it in English; the chips, legend and layout switch to English, left to right.
- **Profile page:** add `"lang": "en"` to `profile.json` before `--page`; its artifact title is then «WHOOP - My baseline (<name>)», and the morning check looks for either title.

## 1. Get the right data

- Best input: the WHOOP data export — the ZIP from WHOOP's email, or the CSVs inside it (`physiological_cycles.csv`, `sleeps.csv`, `workouts.csv`, `journal_entries.csv`). Use every file attached; never ask the user to drop any.
- The app can export in Arabic (files such as `الدورات الفسيولوجية.csv`, `النوم.csv`, `تدريبات.csv`, `إدخالات اليوميات.csv`, with Arabic headers and answers). Feed them as they are: the engine translates the headers and keeps the originals in [brackets].
- If they have not exported yet, give these steps in Arabic: افتح تطبيق WHOOP ← أيقونة القائمة تحت يمين ← Data Export ← اختر كامل الفترة ← Export ← يوصلك إيميل فيه رابط ← نزّل ملف الـZIP وارفعه هنا مثل ما هو. It usually arrives within minutes; very long ranges can take up to 24 hours.
- Screenshots or WHOOP's PDF health report: first copy every visible number into a table, analyze what that allows with the same rules below, and say once that the CSV export unlocks the complete analysis.

## 2. Run the engine — never analyze the CSVs by hand

1. Get the three scripts at the end of this skill into `whoop.py` (the engine), `insights.py` (patterns the WHOOP app does not show, plus the morning-check profile) and `brief.py` (the visual brief, section 7). If this skill file is on disk, extract them with code instead of retyping them:

   ```bash
   python3 - <<'EOF'
   import glob, os, re
   want = {"whoop-full-analysis engine v1.1": "whoop.py", "whoop-full-analysis insights v1.2": "insights.py", "whoop-full-analysis brief v1.2": "brief.py"}
   for p in glob.glob("/mnt/skills/**/SKILL.md", recursive=True) + glob.glob(os.path.expanduser("~/.claude/skills/**/SKILL.md"), recursive=True):
       blocks = re.findall(r"```python\n(.*?)\n```", open(p, encoding="utf-8", errors="ignore").read(), re.S)
       got = {fn: b for tag, fn in want.items() for b in blocks if tag in b}
       if len(got) == len(want):
           for fn, b in got.items():
               open(fn, "w", encoding="utf-8").write(b + "\n")
           print("whoop.py, insights.py and brief.py extracted from", p); break
   else:
       print("skill file not found on disk - write whoop.py, insights.py and brief.py from the code blocks yourself")
   EOF
   ```

   If it is not on disk, write the code blocks to `whoop.py`, `insights.py` and `brief.py` exactly as given. Reuse existing files only if their second lines are `# whoop-full-analysis engine v1.1`, `# whoop-full-analysis insights v1.2` and `# whoop-full-analysis brief v1.2`; older versions cannot read Arabic exports or long gaps correctly.
2. Run the engine on all the WHOOP files at once, then the insights on its output:
   `python3 whoop.py <the ZIP, or every CSV, or their folder> --out whoop_out --weekend Fri,Sat`
   `python3 insights.py --out whoop_out`
   The weekend defaults to Friday/Saturday (Saudi). Change `--weekend` if the user's weekend is different.
3. Missing packages: `pip install pandas numpy matplotlib scipy` (scipy and matplotlib are optional; without matplotlib there are no charts). Recent matplotlib draws Arabic chart labels by itself; on an older one, `pip install arabic-reshaper python-bidi`, or the labels become codes A1… explained at the end of `summary.md`. The visual brief needs Playwright's headless Chromium (`pip install playwright`, then `python -m playwright install chromium` where the network allows); without it `brief.py` still writes `brief.html`.
4. If it fails, read the error and fix the cause. Do not fall back to reading the files by eye.

It writes to `whoop_out/`: `summary.md` (every computed number, 15 sections), `coverage.csv` (every column and what it was used for), `findings.json`, `daily_enriched.csv` (one row per WHOOP day with every metric, each Journal answer as `journal: …`, extra columns as `extra: …`, the wear period as `era`, and `prev_cycle_ok`) and `charts/*.png`. `insights.py` adds `insights.md` (10 patterns the WHOOP app does not spell out, then the ranked leverage points), `insights.json`, and `profile.json` with `profile.html` (the user's normal, for the morning check in section 8).

## 3. Read everything before writing

- Read all of `summary.md` and `insights.md`, and look at every chart. Describe charts in words; take every number from `summary.md` or from code, never from reading a chart.
- Section 14 must say PASS on every line, and the coverage table must give every column a use. If anything says CHECK, find out why before reporting.
- Any extra number you need, including for follow-up questions, is computed from `daily_enriched.csv` with code — never from memory. For "the day before" comparisons use rows where `prev_cycle_ok` is true. Check rounding on the exact value (88.49 is 88, not 89).

## 4. How to read the results

- **Alignment (WHOOP's own logic).** A WHOOP day runs from falling asleep to the next time you fall asleep, and is labelled with the day you woke up — so a "Friday" row is Thursday night's sleep plus Friday's effort. The sleep that starts a day explains that morning's Recovery. That day's Strain, workouts, naps and Journal answers show up the NEXT morning (WHOOP stores Journal answers on the day the behaviour happened). Keep this in every explanation («الصبح اللي بعده»).
- **Extra columns** are tested twice, as "same day" and "day before". Use the one that fits what the column measures: a day total (water, steps) can only affect the next morning; a morning measurement belongs to the same day.
- **Evidence words.** Never show p, q, rho, standardized weights or model coefficients. Translate the engine's verdicts:
  - `clear` → «علاقة واضحة» (strong, very unlikely to be chance, and it holds inside the same month)
  - `possible` → «إشارة محتملة» (needs confirming)
  - `between periods only` → «تظهر بين الفترات فقط» (see the same-month check below)
  - `no clear link` → «ما ظهرت علاقة واضحة»
  - `not enough data`, the "Not enough yes/no answers" line, or the LOW DATA warning → «البيانات ما تكفي للحكم» — which is not the same as "no effect".
- **The same-month check.** Every link is re-tested inside each calendar month, so slow changes (a new routine, a season, a new strap or app update, a long gap) cannot create it. Read the "Same-month check" column:
  - `confirmed` → keep the verdict. `confirmed, but weaker inside the month` → quote the same-month size (the "per +1" slope in that column, or the Journal table's "Same month (adj.)" columns), not the whole-period one.
  - `partly` → it is «إشارة محتملة» at most.
  - `between periods only` (`not confirmed`, `reversed`, or `answered in long blocks`) → the difference shows only when comparing different months or periods. Say «يظهر لما نقارن فترات مختلفة ويختفي داخل الشهر الواحد، فغالباً سببه شي ثاني تغيّر بنفس الوقت» — or, for `answered in long blocks`, «جوابك ثابت لشهور، فما نقدر نقارن إلا فترة بفترة». Never present it as a habit's effect and never build a recommendation on it.
  - `only inside the same month` → «إشارة محتملة» that whole-period differences were hiding.
  - `too few values inside each month to check` → «إشارة محتملة» at most; `n/a (under 2 months of data)` → the check could not run, keep the verdict.
- **Answered in long blocks.** The Journal table's "Answer changes" column counts how often an answer flipped. When it is small, the comparison is really before-versus-after a few dates: find the switch dates in `daily_enriched.csv` and check what else happened then (a stress episode, travel, a wear gap, Ramadan) and say so. To truly test such a habit, suggest switching it on and off in blocks of 2–3 weeks while logging it in the Journal.
- **Real units and counts.** Pattern: «في [N] ليلة نمت فيها أقل من [H] ساعات كان الريكفري [X]% بالمتوسط، مقابل [Y]% لما نمت [H2] ساعات». Fill it only with this user's numbers from the Effect column, the band tables and the Journal table. Say what each comparison is against: "yes vs no" compares with all other days; section 10's activity table compares with rest days and is descriptive only.
- **Correlation is not proof.** Say «يرتبط» / «يصير معه». Say «غالباً بسبب» only for well-established physiology: short sleep → lower HRV, a hard day → lower Recovery next morning, illness → higher resting HR and breathing rate, a late meal → higher night heart rate.
- **Many things are tested at once,** so one or two `clear` results can still be coincidence. Lead with findings that are large, make physiological sense, survive the same-month check, and appear in more than one measure (Recovery and HRV, or Recovery and sleep). If a result is strange (for example "enough water → lower Recovery"), call it probably coincidence or a hidden factor, and never recommend anything unhealthy because of it.
- **Wear periods and long gaps.** Section 2 lists every gap and splits the data into wear periods at gaps of 30+ days. With 2+ periods: describe the gap, treat the latest period as the user's "normal now", use section 8's wear-period table for the comparison, and quote trends from its "Latest period" columns. If the data crosses 2025, the engine prints a Device note: WHOOP launched new straps (5.0 / MG) on 8 May 2025 and updated its sleep-stage and Sleep Performance calculations in 2025, so step changes in sleep stages or sleep performance across that point may come from the device or app, not the body. Say this when sleep stages jump between periods.
- **Partial-wear days** (strap on for only part of the day) have their day totals left out; section 2 lists them. Mention them in the data-quality section.
- **Ramadan.** Each link shows its effect "outside Ramadan". If a link mostly disappears outside Ramadan, it is a Ramadan pattern, not a habit effect — say so. Sleep timing changes for everyone in Ramadan (dates are approximate): sleeping after Fajr or after Dhuhr is normal then, so compare it on its own and do not blame the user for it.
- **Clock times.** Bedtimes are counted from midnight of the wake day, so a 12:30 bedtime is a daytime sleep (Ramadan, night shifts), not an early one. Quote the median bedtime and wake time as "usual"; tables already use medians for times.
- **Naps** that start between 03:00 and 09:00 are early-morning sleep, often after Fajr — call them that.
- **Combined model.** It shows which factors still matter when the others are held equal, over the whole period and inside the same month; use the same-month column. If something is clear on its own but fades in the model, explain that it works through another factor (for example, late bedtimes hurt because they cut hours of sleep) rather than dropping it.
- **Section 5** shows how the Recovery score is built for this user (usually HRV compared with their own normal dominates). Explain it in words; it describes the score, not habits.
- **Trends:** call something improving or worsening only if section 8 says so, and give the change per month. Changes in how often a Journal answer is "yes" (last 30 days vs the 30 before) can be stated as facts.
- **Hidden patterns (`insights.md`)** are what the WHOOP app does not spell out. Drift (its section 1): WHOOP scores each morning against a recent normal that moves with the user, so a slow slide looks normal; quote the fixed windows and the best 30 days of the latest wear period. Comparisons (sections 2, 5, 6, 9) carry the same verdicts and same-month check as the links; `no clear difference` → «ما ظهر فرق واضح», worth saying when it corrects a common belief (for example bedtime against hours of sleep). Sections 3, 4, 7, 8 and 10 are counts and averages: say «في بياناتك» with the numbers, never «ثبت». Skip a section that has too little data.
- **Leverage points (`insights.md` section 11)** rank where the most Recovery points are waiting: a link's same-month effect × the room the last 30 days leave (nights short of the sweet spot; days with the costly Journal answer). Present the top three as «أقوى 3 روافع عندك», each as: the change → «تقدير: حوالي +N نقاط على متوسط الريكفري» → its evidence word. It is an estimate from links, not a promise: say «تقدير» every time, never add the gains together, and leave personal journal questions and anything unhealthy or strange out of the list. If nothing is ranked, say the data does not single out a lever yet.
- **Time-zone changes** mean travel; a few rough mornings after are expected.
- **Stress episodes:** describe as «جسمك كان تحت ضغط» and use the context column (strain, short sleep, travel, Ramadan, unusual journal answers) for likely reasons. If they look like illness (several days of low HRV with high resting HR, breathing rate or skin temperature), say so gently and ask whether the user was sick then.
- **Journal questions that don't fit.** A question that cannot apply to the user (for example a menstrual-cycle question in a man's journal), one with always the same answer, or one never answered adds nothing: say so in one neutral line and suggest removing or answering it honestly each day. Do not guess why it was answered.
- **Personal journal questions** (sexual activity, alcohol and the like): report them in the Journal table with the same neutral verdict words and nothing more — no judgement, no advice beyond the data. Leave them out of day-by-day lists (stress episodes, best and worst mornings) and out of the chat reply unless the user asks.

## 5. Write the report — for a non-specialist, in the user's language

Tone: clear, warm and direct; in Arabic a light Gulf flavour is fine. Keep WHOOP's English terms (Recovery, HRV, Strain…) and explain each in Arabic the first time. Round sensibly. Every number gets: the value → what it means → how it compares with the user's own normal (and WHOOP's band when there is one). Short paragraphs, small tables, no number repeated without a reason.

Use these sections in this order. Every section of `summary.md` must land somewhere; if one has nothing notable, say so in a line instead of skipping it.

| Report section | Built from `summary.md` |
|---|---|
| 1. **الخلاصة في دقيقة** — the 3–5 most important findings and the 3 actions that matter most, opening with «أقوى 3 روافع عندك» (the top three leverage points and their estimated gain) when `insights.md` ranks any | all |
| 2. **وش وصلني من بياناتك** — files, period, days, gaps and wear periods, partial-wear days, columns used out of the total (all of them), data-quality notes, what extra or unknown columns showed; a profile file (height, weight) is context only | 1, 2, 13, 14, 15 |
| 3. **وضعك الطبيعي** — the user's normal for each key metric (average, usual range, the latest wear period when there are several, last 30 days vs the 30 before) and how their days split across WHOOP's bands | 3, 4, 8 |
| 4. **وش يحرّك الريكفري عندك** — how their score is built, then every linked finding (sleep, effort, workouts, habits, context) with its effect size and the same-month result | 5, 6 |
| 5. **نومك بالتفصيل** — hours vs need, stages vs WHOOP's typical ranges, bedtime and its effect, daytime sleeps, the weekend shift, naps | 9 |
| 6. **مجهودك وتمارينك** — strain bands and the next morning, hard days on red mornings, load jumps, and each activity: total hours, usual time, heart-rate zones, effect next morning | 10 |
| 7. **عاداتك (Journal)** — every question: what happened the next morning (whole period and same month), how sure we are, how often the answer changed, how often it happened lately; the ones that can't be judged and why; questions to fix | 7 |
| 8. **أسبوعك ورمضان والسفر** — the weekday pattern, the Ramadan comparison, each trip | 11 |
| 9. **أيام كان جسمك فيها تحت ضغط** — episodes with dates, the signals in plain words and likely reasons; best and worst mornings; low blood-oxygen nights | 12 |
| 10. **الاتجاه العام** — what is improving, worsening or stable, inside the latest wear period first, then the wear-period comparison and the device note | 8 |
| 11. **أشياء ما يقولها لك WHOOP** — each hidden pattern that holds, in one or two lines with the user's numbers: the drift a moving baseline hides, the second-morning cost of a short night, short nights in a row, how long red mornings last, bedtime against hours, the weekend body-clock shift, where more sleep stops paying, the last 30 days in one number, and the ranking behind «أقوى 3 روافع» | insights.md |
| 12. **خطتك العملية** — at most 5 specific actions ranked by expected impact, each tied to this user's own numbers and to findings that survived the same-month check; for uncertain items, a 2–3 week test while logging it in the WHOOP Journal; then «بروتوكول 14 يوم» (below the table) | all |
| 13. **قاموس سريع** — only the terms used in the report | — |

**«بروتوكول 14 يوم»** closes the plan: the top one or two levers turned into a two-week routine the user can follow without thinking — a bedtime and wake time taken from their own numbers, the one habit to switch, and effort by morning colour. Give it one target number from their data (for example «ولا ليلة أقل من 6 ساعات», or the average Recovery the lever's estimate points to, worded as «تقدير»), what to log in the WHOOP Journal each day, and the date to send a new export for the re-check. Two levers at most; no supplements, medication, fasting, calorie or weight targets.

## 6. Deliver

- **The full report** (all 13 sections) goes into a document the user can keep: use the environment's document or artifact type if it has one; otherwise build one self-contained HTML file (`dir="rtl"` for Arabic, charts embedded as base64 images) and share it.
- **The visual brief** (section 7) goes with every full report: send `brief.png`, plus `brief.pdf` when they want to print or forward it.
- **The profile page** for the morning check (section 8): add `name` and the plan's actions as short lines (`plan`) to `profile.json`, drop personal journal questions from its `habits`, run `python3 insights.py --out whoop_out --page`, and publish `profile.html` as a private artifact titled «WHOOP — ملفي الأساسي (<name>)»; when one already exists (find it by title with the artifact tools), republish that one instead of making another. Tell the user in one line that the morning check reads it.
- **Charts:** when the document can draw live charts from data rows, give it the rows for the 2–3 charts that carry the main findings (for example Recovery by hours-asleep band, the monthly HRV line split by wear period) instead of PNGs; otherwise embed the engine's PNGs. The engine's charts have English titles; describe each one in Arabic by what it shows.
- **The chat reply stays short:** «الخلاصة في دقيقة» and «خطتك العملية», plus one line pointing to the full report and the visual brief. If no document or file can be created at all, put the full report in the reply instead.
- **Check before handing over:** every number in the report against `summary.md` or code — ideally by a second agent that did not write the report.
- New export later: run the engine again on the full new export, and add a short «وش تغيّر من آخر تحليل» section when an earlier analysis is available. When that analysis set a «بروتوكول 14 يوم», compare its target number over the protocol days with the 14 days before them, computed from `daily_enriched.csv`, and say plainly whether it moved.

## 7. Visual brief — ملخص مصوّر

A one-page summary the user can glance at on a phone or forward: clean design, one card per topic, short, but with every important point in it. Make it with every full analysis, after the report's numbers are checked, and on its own when the user asks for a short, visual or shareable summary («صورة»، «ملخص»، «مختصر»، «إنفوجرافيك»).

- **What it must carry:** the takeaway in one sentence; 3–4 key numbers for the last 30 days against the user's own normal (Recovery, HRV, sleep, resting HR, with WHOOP's colour word when there is one); one card per main topic — sleep, the clearest habit link, any decline or stress period, the week pattern, effort and workouts, Journal habits — each with one big number, at most 3 short bullets and its evidence word; the plan (at most 5 actions, each with its reason in the user's numbers); the 1–2 strongest hidden patterns from `insights.md`; «أقوى 3 روافع» as one wide card with bars (the estimated Recovery points of each) when any are ranked; any point from «Health and safety»; and a footer pointing to the full report. Same numbers and evidence words as the report, no p-values, no personal journal questions.
- **«What WHOOP doesn't tell me»:** when the user asks for it, make a second brief from `insights.md` alone, rendered with `--out whoop_out/hidden` so it does not replace the main one: the drift as 4 KPIs (last 30 days against the best 30 days of the latest wear period), one card per pattern that holds (bars for sections 3 and 10), and a 3-step plan.
- **Write `brief.json`** in the user's language (Arabic in their dialect, or English with `"lang": "en"`), then run `python3 brief.py brief.json --out whoop_out`. It writes `brief.png` (phone image, sharp at 2×), `brief.pdf` and `brief.html`. The first run fetches the IBM Plex Sans Arabic font through npm and caches it (`--no-fetch` skips that, `--font FILE` uses your own); without it the system font is used. Without Playwright's Chromium it writes only `brief.html` and says so.
- **Look at `brief.png` before sending** (in halves if it is tall): nothing cut off, numbers and arrows in the right order, no card far longer than the one beside it. Fix the spec and render again.

```json
{"overline": "ملخص WHOOP · <date>", "title": "<name>: وش تقول بياناتك", "subtitle": "<period> · <N> صباح", "headline": "<the one-sentence takeaway>",
 "kpis": [{"label": "الريكفري", "value": "50", "unit": "%", "note": "آخر 30 يوم · معدلك 57%", "tone": "warn", "tag": "أصفر"}],
 "cards": [{"icon": "sleep", "title": "النوم", "chip": "clear", "wide": true, "stat": {"value": "+8", "caption": "<what the number means>"},
            "bars": {"title": "الريكفري حسب ساعات النوم", "max": 100, "ref": {"value": 67, "label": "الخط المتقطع: بداية الأخضر 67%"},
                     "rows": [{"label": "أقل من 6 ساعات", "value": 42, "text": "42%", "note": "114 ليلة"}]},
            "bullets": ["<short line with **bold** numbers>"]}],
 "plan": [{"lead": "<the action>", "text": "<why, in the user's numbers>"}], "alerts": ["<health point>"],
 "legend": ["clear", "possible", "between"], "footer": ["<where the full report is>"]}
```

`icon` is one of sleep, heart, pulse, clock, meal, calendar, bolt, journal, down, up, check, alert. `chip` is an evidence word — clear, possible, between, nodata — or left out for a plain fact. `tone` is good, warn, bad or neutral and always comes with its `tag` word, never colour alone. `**…**` makes bold; Latin words and signed numbers (+8, −13) stay in the right order inside Arabic by themselves. Keep it to 4 KPIs, 5–7 cards and 5 plan items; mark cards with bars or long text `"wide": true`. Write arrows for right-to-left reading: «88 ← 50» means from 88 to 50.

## 8. Morning check — فحص الصباح

When the user sends a screenshot of today's WHOOP screen, or asks «فحص الصباح» / «وش أسوي اليوم؟»:

1. **Read the screenshot.** Copy every number you can actually see: Recovery %, HRV, resting HR, hours of sleep, sleep performance, Day Strain so far, sleep need, and the date. Never guess a number that is not visible; if the date is not today, say so.
2. **Get their normal**, first that exists: `whoop_out/profile.json` in this session; their profile page (find the artifact titled «WHOOP — ملفي الأساسي» with the artifact tools and read the JSON in its `<script id="whoop-profile">`); the last visual brief, if they send it (its KPIs carry their normal); otherwise WHOOP's bands only, and say once that one full export makes the check personal.
3. **Reply in at most 6 short lines**, in their language (their dialect in Arabic):
   - Today against their normal: «ريكفري اليوم 48% — أقل من معدلك (56%)» with WHOOP's colour word; HRV and resting HR the same way when visible. Inside their usual range (`p25`–`p75`) is normal.
   - Why: from what is visible plus their own patterns in the profile — last night's hours against their sweet spot, a second short night in a row, a short night two days ago, a clear journal habit (ask only when one fits and they have not said: «أكلت متأخر أمس؟»). Use the evidence words; never invent a cause.
   - Today's plan: effort by colour — green: a hard session is fine; yellow: moderate (Day Strain about 10–13); red: light (under 10). Tonight's bedtime from their plan, or the time that gives their sweet-spot hours before their usual wake time, and the last meal 3 hours before it when late eating is one of their clear habits.
   - One line from their own data that makes it concrete, for example «ثالث ليلة قصيرة ورا بعض عندك تنزل الريكفري لـ32%».
4. «Health and safety» applies; never diagnose. No report, brief or file for a morning check unless they ask.

## 9. Quick questions

When the user asks one focused question («ليش الريكفري اليوم أحمر؟», «هل القهوة تأثر على نومي؟»), still run the engine on all their data, answer that question first in a few sentences with their own numbers and the evidence words, then offer the full report and the visual brief in one line. For "today", use the morning check (section 8).

## 10. Health and safety

WHOOP is a wellness device, not a diagnostic one, so do not diagnose. Calmly suggest checking with a doctor only when: blood oxygen is under 90% on repeated nights (scattered single nights are often a loose strap — say so), resting HR stays 5+ bpm above normal while the user feels unwell, or stress episodes come with symptoms the user mentions. Do not set calorie or body-weight targets.

## 11. Arabic glossary — use these explanations

- **Recovery (الريكفري / جاهزية الجسم):** رقم من 0 إلى 100% يطلع كل صباح: قد إيش جسمك جاهز للمجهود اليوم. أخضر 67–100 جاهز، أصفر 34–66 متوسط، أحمر 0–33 جسمك يطلب راحة.
- **HRV (تقلّب نبضات القلب):** الفرق الدقيق بين نبضة والثانية بالملّي ثانية. أعلى من معدلك يعني جسمك مرتاح ومتعافي. يختلف كثير بين الناس، فالمهم مقارنته بمعدلك أنت.
- **Resting HR (نبض الراحة):** نبضك وأنت نايم. ارتفاعه عن معدلك يعني ضغط على الجسم (سهر، تعب، أكل متأخر، مرض).
- **Respiratory rate (معدل التنفس):** أنفاسك في الدقيقة وأنت نايم؛ ثابت عادةً، وارتفاعه الواضح أحياناً يسبق المرض.
- **Blood oxygen / SpO2 (أكسجين الدم):** يُقاس وأنت نايم؛ الطبيعي غالباً 95–100%.
- **Skin temp (حرارة الجلد):** المهم تغيّرها عن معدلك، مو الرقم نفسه.
- **Day Strain (مجهود اليوم):** من 0 إلى 21 لكل مجهود اليوم (تمرين، حركة، توتر). خفيف 0–9، متوسط 10–13، عالي 14–17، أقصى 18–21. السلّم مو خطي: الطلوع من 15 إلى 16 أصعب بكثير من 5 إلى 6. متوسط مستخدمي WHOOP تقريباً 11.
- **Sleep performance (أداء النوم):** كم نمت مقارنة باحتياجك؛ 85% وفوق ممتاز، 70–84% كافي، أقل من 70% ضعيف.
- **Sleep need / Sleep debt (احتياج النوم / دين النوم):** اللي يحتاجه جسمك الليلة حسب مجهودك، والنقص المتراكم من الليالي اللي قبل.
- **Sleep efficiency (كفاءة النوم):** نسبة الوقت اللي كنت نايم فيه فعلاً من وقتك في السرير. الصحيان وأنت في السرير عادةً حوالي 5% من وقت السرير.
- **Sleep consistency (انتظام النوم):** ثبات مواعيد نومك وصحيانك؛ 90% وفوق ممتاز، 80–89% كافي.
- **Deep / SWS (النوم العميق):** يرمّم الجسم والعضلات؛ غالباً 15–25% من النوم، ونسبته ترتفع لما تكون الليلة قصيرة أو الجسم مجهد. **REM (نوم الأحلام):** للذاكرة والتعلّم؛ غالباً 20–25%، ويكثر آخر الليل. **Light (الخفيف):** حوالي 50%.
- **HR zones (مناطق النبض 1–5):** من الأخف للأشد؛ زون 2 يبني اللياقة الهوائية، و4–5 شدة عالية.
- **Journal (اليوميات):** أسئلة WHOOP اليومية عن عاداتك؛ WHOOP يحتاج 5 أجوبة «نعم» و5 «لا» على الأقل عشان يحكم على أي عادة.
- **يوم WHOOP:** من لما تنام لين النومة اللي بعدها، وينسمّى باليوم اللي صحيت فيه.
- **فترة لبس:** أيام متصلة لبست فيها الإسوارة، تفصلها عن غيرها فجوة 30 يوم أو أكثر.
- **داخل نفس الشهر:** نقارن أيامك ببعض في الشهر نفسه، عشان التغيّرات البطيئة (روتين، موسم، جهاز جديد) ما تصنع علاقة مو موجودة.
- **رافعة (Leverage point):** تغيير واحد في يومك نتوقع منه أكبر فرق في الريكفري، محسوب من أثره داخل نفس الشهر × كم ينقصك منه في آخر 30 يوم. الرقم تقدير مو وعد.
- **تظهر بين الفترات فقط:** الفرق يبين لما نقارن شهور أو فترات مختلفة وما يثبت داخل الشهر الواحد، فغالباً سببه شي ثاني تغيّر بنفس الوقت.

## Engine code — `whoop.py`

```python
#!/usr/bin/env python3
# whoop-full-analysis engine v1.1
# WHOOP full analysis: python3 whoop.py <csv|zip|folder ...> --out whoop_out [--weekend Fri,Sat]
# Writes summary.md (every number), coverage.csv (every column -> its use), findings.json, daily_enriched.csv, charts/*.png
import argparse, json, math, os, re, zipfile, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
try:
    from scipy import stats as SS
except Exception:
    SS = None
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
except Exception:
    plt = None
AR_TXT = None  # Arabic chart labels: matplotlib built with libraqm shapes Arabic itself; older builds need arabic-reshaper + python-bidi
try:
    import matplotlib.ft2font as _ft
    AR_TXT = (lambda s: s) if getattr(_ft, "__libraqm_version__", None) else None
except Exception:
    pass
if AR_TXT is None:
    try:
        import arabic_reshaper; from bidi.algorithm import get_display
        AR_TXT = lambda s: get_display(arabic_reshaper.reshape(s))
    except Exception:
        AR_TXT = None

N = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
SLP = dict(onset=["sleeponset"], wake=["wakeonset"], sleep_perf=["sleepperformance"], resp=["respiratoryrate"], asleep=["asleepduration"],
           in_bed=["inbedduration"], light=["lightsleep"], deep=["deepsws", "deepsleep"], rem=["remduration", "remsleep"],
           awake=["awakeduration"], need=["sleepneed"], debt=["sleepdebt"], eff=["sleepefficiency"], cons=["sleepconsistency"])
B = dict(start=["cyclestarttime"], end=["cycleendtime"], tz=["cycletimezone"])
KEYS = dict(cycles={**B, "recovery": ["recoveryscore"], "rhr": ["restingheartrate"], "hrv": ["heartratevariability"], "skin_temp": ["skintemp"],
                    "spo2": ["bloodoxygen"], "strain": ["daystrain"], "energy": ["energyburned"], "max_hr": ["maxhr"], "avg_hr": ["averagehr"],
                    "steps": ["steps"], **SLP},
            sleeps={**B, **SLP, "nap": ["nap"]},
            workouts={**B, "w_start": ["workoutstarttime"], "w_end": ["workoutendtime"], "dur": ["duration"], "act": ["activityname"],
                      "astrain": ["activitystrain"], "energy": ["energyburned"], "max_hr": ["maxhr"], "avg_hr": ["averagehr"],
                      **{f"z{i}": [f"hrzone{i}"] for i in range(1, 6)}, "gps": ["gpsenabled"], "dist": ["distance"],
                      "alt_gain": ["altitudegain"], "alt_change": ["altitudechange"]},
            journal={**B, "q": ["questiontext"], "yes": ["answeredyes"], "notes": ["notes"]})
# key: label, unit, good direction (+1 higher better, -1 lower better, 0 neutral), decimals
MET = dict(recovery=("Recovery", "%", 1, 0), hrv=("HRV", "ms", 1, 0), rhr=("Resting HR", "bpm", -1, 0), resp=("Respiratory rate", "rpm", 0, 1),
           spo2=("Blood oxygen SpO2", "%", 1, 1), skin_temp=("Skin temp", "C", 0, 2), strain=("Day Strain", "/21", 0, 1),
           energy=("Energy burned", "kcal", 0, 0), avg_hr=("Average HR (day)", "bpm", 0, 0), max_hr=("Max HR (day)", "bpm", 0, 0),
           steps=("Steps", "steps", 1, 0), sleep_perf=("Sleep performance", "%", 1, 0), asleep_h=("Hours asleep", "h", 1, 2),
           in_bed_h=("Time in bed", "h", 0, 2), need_h=("Sleep need", "h", 0, 2), debt_h=("Sleep debt", "h", -1, 2),
           eff=("Sleep efficiency", "%", 1, 0), cons=("Sleep consistency", "%", 1, 0), light_pct=("Light sleep share", "% of sleep", 0, 1),
           deep_pct=("Deep (SWS) share", "% of sleep", 0, 1), rem_pct=("REM share", "% of sleep", 0, 1), awake_pct=("Awake share", "% of bed", -1, 1),
           deep=("Deep sleep", "min", 1, 0), rem=("REM sleep", "min", 1, 0), bed_h=("Bedtime", "clock", 0, 2), wake_h=("Wake time", "clock", 0, 2))
OK_RANGE = dict(recovery=(0, 100), hrv=(5, 300), rhr=(25, 130), resp=(6, 35), spo2=(70, 100), skin_temp=(25, 42), strain=(0, 21),
                sleep_perf=(0, 100), eff=(0, 100), cons=(0, 100), asleep=(0, 1200), in_bed=(0, 1440))
RAMADAN = [("2019-05-06", "2019-06-03"), ("2020-04-24", "2020-05-23"), ("2021-04-13", "2021-05-12"), ("2022-04-02", "2022-05-01"),
           ("2023-03-23", "2023-04-20"), ("2024-03-11", "2024-04-09"), ("2025-03-01", "2025-03-29"), ("2026-02-18", "2026-03-19"),
           ("2027-02-08", "2027-03-09"), ("2028-01-28", "2028-02-26"), ("2029-01-16", "2029-02-14"), ("2030-01-06", "2030-02-04")]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAYTOT = ["strain", "energy", "avg_hr", "max_hr", "steps"]  # accumulate during the day -> incomplete for an open cycle
# Arabic-language WHOOP exports: normalised Arabic phrase -> English header (order matters; the Arabic original is kept in [brackets])
AR_RULES = [("وقت بدء الدوره", "Cycle start time"), ("نهايه الدوره", "Cycle end time"), ("المنطقه الزمنيه", "Cycle timezone"),
            ("التعافي", "Recovery score %"), ("اثناء الراحه", "Resting heart rate (bpm)"), ("تباين", "Heart rate variability (ms)"),
            ("حراره الجلد", "Skin temp (celsius)"), ("الاكسجين", "Blood oxygen %"), ("جهد اليوم", "Day Strain"), ("جهد النشاط", "Activity Strain"),
            ("الطاقه", "Energy burned (cal)"), ("الحد الاقصي", "Max HR (bpm)"), ("المتوسط", "Average HR (bpm)"), ("بدايه النوم", "Sleep onset"),
            ("بدايه الاستيقاظ", "Wake onset"), ("جوده النوم", "Sleep performance %"), ("معدل التنفس", "Respiratory rate (rpm)"),
            ("النوم الخفيف", "Light sleep duration (min)"), ("العميق", "Deep (SWS) duration (min)"), ("حركه العين", "REM duration (min)"),
            ("مده الاستيقاظ", "Awake duration (min)"), ("احتياج النوم", "Sleep need (min)"), ("نقص النوم", "Sleep debt (min)"),
            ("كفاءه النوم", "Sleep efficiency %"), ("استمرار النوم", "Sleep consistency %"), ("في السرير", "In bed duration (min)"), ("قيلوله", "Nap"),
            ("نص السؤال", "Question text"), ("اجاب بنعم", "Answered yes"), ("ملاحظات", "Notes"), ("وقت بدء التمرين", "Workout start time"),
            ("وقت انتهاء التمرين", "Workout end time"), ("اسم النشاط", "Activity name"), ("تحديد المواقع", "GPS enabled"), ("المسافه", "Distance (meters)"),
            ("تغير الارتفاع", "Altitude change (meters)"), ("الارتفاع", "Altitude gain (meters)"), ("الخطوات", "Steps"), ("المده", "Duration (min)")]
AR_DIG = str.maketrans("٠١٢٣٤٥٦٧٨٩٫", "0123456789.")
HAS_AR = lambda s: bool(re.search(r"[-ۿ]", str(s)))
R, F, COV = [], {}, {}


def H(t): R.append(f"\n## {t}\n")
def P(t=""): R.append(t)
def T(h, rows):
    if not rows:
        return P("_(no data)_")
    R.extend(["", "| " + " | ".join(h) + " |", "|" + "---|" * len(h)] + ["| " + " | ".join(map(str, r)) + " |" for r in rows] + [""])
fin = lambda x: isinstance(x, (int, float, np.integer, np.floating)) and bool(np.isfinite(x))
f = lambda x, d=1: f"{x:,.{d}f}" if fin(x) else "-"
sg = lambda x, d=1: f"{x:+,.{d}f}" if fin(x) else "-"
def hm(h):
    if not fin(h):
        return "-"
    t = int(round(h * 60)) % 1440
    return f"{t // 60:02d}:{t % 60:02d}"
clk = lambda k: MET.get(k, ("", ""))[1] == "clock"
fmt = lambda k, x: hm(x) if clk(k) else f(x, MET.get(k, ("", "", 0, 1))[3])
agk = lambda k, s: s.median() if clk(k) else s.mean()  # clock times are summarised by their median
lab = lambda k: MET[k][0] + (f" ({MET[k][1]})" if MET[k][1] not in ("clock", "") else "")
pct = lambda a, b: (f(100 * a / b, 0) + "%") if b else "-"


def nar(s):  # normalise Arabic for matching: no diacritics/tatweel, one alef form, ta marbuta -> ha, alef maqsura -> ya
    s = re.sub(r"[ً-ْٰـ]", "", str(s)).translate(AR_DIG)
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip().lower()
def translate(cols):  # Arabic export headers -> "English [Arabic original]"; the two Arabic "مدة النوم" columns are asleep, then in bed
    out, sd = [], 0
    for c in cols:
        if not HAS_AR(c):
            out.append(c); continue
        b = nar(re.sub(r"\.\d+$", "", c)); z = re.search(r"[1-5]", b)
        if ("منطقه" in b or "zone" in b) and "نبض" in b and z:
            en = f"HR Zone {z.group()} %"
        elif "مده النوم" in b and not any(w in b for w in ("الخفيف", "العميق", "حركه", "الاستيقاظ")):
            en = "Asleep duration (min)" if sd == 0 else "In bed duration (min)"; sd += 1
        else:
            en = next((e for k, e in AR_RULES if k in b), None)
        out.append(f"{en} [{c}]" if en else c)
    return out
def num(s):
    x = pd.to_numeric(s, errors="coerce")
    if x.notna().sum() < s.notna().sum() * .5:
        y = pd.to_numeric(s.astype(str).str.translate(AR_DIG).str.replace("%", "").str.replace(",", ".").str.strip(), errors="coerce")
        x = y if y.notna().sum() > x.notna().sum() else x
    return x
def dt(s):
    s = s.astype(str).str.translate(AR_DIG).str.strip().str.replace(r"(Z|[+-]\d{2}:?\d{2})$", "", regex=True).str.replace("T", " ")
    return pd.to_datetime(s.where(~s.isin(["", "nan", "NaT", "None", "<NA>"])), errors="coerce")
def yn(s):
    v = s.astype(str).str.strip().str.lower()
    return v.map(lambda x: 1.0 if x in ("true", "yes", "1", "y", "t", "1.0", "نعم", "صحيح", "صح") else
                 0.0 if x in ("false", "no", "0", "n", "f", "0.0", "لا", "خطأ", "خطا") else np.nan)
def tzh(v):
    m = re.search(r"([+-])(\d{1,2})(?::?(\d{2}))?", str(v))
    if not m:
        return 0.0 if re.search(r"utc|gmt", str(v), re.I) else np.nan
    h = int(m.group(2)) + int(m.group(3) or 0) / 60
    return h if m.group(1) == "+" else -h
def clock(ts):  # hours from midnight: 23:30 -> -0.5, 01:15 -> 1.25
    h = ts.dt.hour + ts.dt.minute / 60
    return h.where(h < 12, h - 24)
def spear(x, y):
    m = x.notna() & y.notna(); n = int(m.sum())
    if n < 8 or x[m].nunique() < 2 or y[m].nunique() < 2:
        return np.nan, np.nan, n
    if SS is not None:
        r, p = SS.spearmanr(x[m], y[m]); return float(r), float(p), n
    r = x[m].rank().corr(y[m].rank()); z = math.atanh(max(min(r, .999999), -.999999)) * math.sqrt((n - 3) / 1.06)
    return float(r), math.erfc(abs(z) / math.sqrt(2)), n
def bh(ps):  # Benjamini-Hochberg false-discovery control
    ps = np.asarray(ps, float); q = np.full(ps.shape, np.nan); ok = np.isfinite(ps)
    if ok.any():
        p = ps[ok]; o = np.argsort(p); a = np.minimum.accumulate((p[o] * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1]
        t = np.empty(len(p)); t[o] = np.minimum(a, 1); q[ok] = t
    return q
def ols(y, X):
    d = pd.concat([y.rename("_y"), X], axis=1).dropna(); n, k = len(d), X.shape[1]
    if n < max(30, 8 * k):
        return None
    A = np.column_stack([np.ones(n), d[X.columns].values.astype(float)]); yy = d["_y"].values.astype(float)
    b = np.linalg.lstsq(A, yy, rcond=None)[0]; e = yy - A @ b; s2 = e @ e / max(n - A.shape[1], 1)
    se = np.sqrt(np.clip(np.diag(s2 * np.linalg.pinv(A.T @ A)), 0, None)); c = ["const"] + list(X.columns); ss = ((yy - yy.mean()) ** 2).sum()
    return dict(n=n, r2=1 - e @ e / ss if ss > 0 else np.nan, b=dict(zip(c, b)), sd={k_: d[k_].std() for k_ in X.columns}, sdy=d["_y"].std(),
                p=dict(zip(c, [math.erfc(abs(bi / si) / math.sqrt(2)) if si > 0 else np.nan for bi, si in zip(b, se)])))
verdict = lambda p, q: "clear" if fin(q) and q < .05 else ("possible" if fin(p) and p < .05 else "no clear link")
def within(x, y, g, binary=False):  # same-month check: does the link still hold inside the same calendar month (slow changes removed)?
    m = x.notna() & y.notna() & g.notna()
    if g[m].value_counts().ge(4).sum() < 2:
        return "short"
    d = pd.DataFrame({"x": x[m].astype(float), "y": y[m].astype(float), "g": g[m]})
    d = d[d.groupby("g")["x"].transform("nunique").gt(1) & d.groupby("g")["x"].transform("size").ge(4)]
    n, k = len(d), d["g"].nunique(); xa = x[m]
    if binary:  # yes/no must be mixed (5+ of each, 3+ of each in 2+ months) so that one switch date can't drive the result
        mixed = (d.groupby("g")["x"].agg(lambda v: min((v == 1).sum(), (v == 0).sum())) >= 3).sum()
        if n < 20 or min((d["x"] == 1).sum(), (d["x"] == 0).sum()) < 5 or (g[m].nunique() >= 3 and mixed < 2):
            sw = int((xa.diff().abs() > 0).sum())  # few changes = answered in long blocks; many = scattered single days
            return "blocks" if sw < .5 * min((xa == 1).sum(), (xa == 0).sum()) else "sparse"
    elif n < 20:
        return "sparse"
    dm = lambda v: v - v.groupby(d["g"]).transform("mean")
    rx, ry, ex, ey = dm(d["x"].rank()), dm(d["y"].rank()), dm(d["x"]), dm(d["y"])
    if rx.std() == 0 or ry.std() == 0:
        return "blocks"
    r = float(np.corrcoef(rx, ry)[0, 1]); df_ = max(n - k - 1, 1); t = r * math.sqrt(df_ / max(1 - r * r, 1e-12))
    p = float(2 * SS.t.sf(abs(t), df_)) if SS is not None else math.erfc(abs(t) / math.sqrt(2))
    b = float((ex * ey).sum() / (ex * ex).sum())
    return dict(r=r, p=p, n=n, k=k, b=b, s=r, txt=f"rho {f(r, 2)}" if binary else f"rho {f(r, 2)}; {sg(b, 2 if abs(b) < 10 else 1)} per +1")
def recheck(v, rho, w):  # whole-period verdict + same-month check -> final verdict
    if v not in ("clear", "possible"):
        return v, ""
    if w == "short":
        return v, "n/a (under 2 months of data)"
    if w == "sparse":
        return "possible", "too few values inside each month to check"
    if not isinstance(w, dict):
        return "between periods only", "answered in long blocks (yes and no rarely mixed inside a month) - only periods can be compared"
    same = np.sign(w["s"]) == np.sign(rho)
    if same and w["p"] < .05:
        return v, ("confirmed, but weaker inside the month" if abs(w["r"]) < .5 * abs(rho) else "confirmed") + f" ({w['txt']})"
    if same and w["p"] < .2:
        return "possible", f"partly ({w['txt']}, p {f(w['p'], 2)})"
    return "between periods only", ("reversed" if w["p"] < .05 else "not confirmed") + f" ({w['txt']}, p {f(w['p'], 2)})"
def ols_fe(y, X, g):  # least squares inside each month (month-to-month level differences removed)
    d = pd.concat([y.rename("_y"), X, g.rename("_g")], axis=1).dropna(); G = d["_g"].nunique() if len(d) else 0
    if len(d) < max(30, 8 * X.shape[1]) or G < 1:
        return None
    v = d.drop(columns="_g").astype(float); v = v - v.groupby(d["_g"]).transform("mean"); cols = [c for c in X.columns if v[c].std() > 1e-9]
    if not cols:
        return None
    A, yy = v[cols].values, v["_y"].values; n = len(v); b = np.linalg.lstsq(A, yy, rcond=None)[0]; e = yy - A @ b
    se = np.sqrt(np.clip(np.diag(e @ e / max(n - len(cols) - G, 1) * np.linalg.pinv(A.T @ A)), 0, None)); ss = (yy ** 2).sum()
    return dict(n=n, G=G, r2=1 - e @ e / ss if ss > 0 else np.nan, b=dict(zip(cols, b)),
                p=dict(zip(cols, [math.erfc(abs(bi / si) / math.sqrt(2)) if si > 0 else np.nan for bi, si in zip(b, se)])))


def gather(paths, tmp):
    fl, out, other = [], [], []
    for p in paths:
        if os.path.isdir(p):
            for root, _, fs in os.walk(p):
                if "_extracted" not in root:
                    fl += [os.path.join(root, x) for x in sorted(fs)]
        else:
            fl.append(p)
    for fp in fl:
        if fp.lower().endswith(".zip"):
            with zipfile.ZipFile(fp) as z:
                for m in z.namelist():
                    nm = os.path.basename(m)
                    if m.endswith("/") or "__MACOSX" in m or not nm:
                        continue
                    if nm.lower().endswith((".csv", ".tsv")):
                        dst = os.path.join(tmp, f"{len(out)}_{nm}")
                        with z.open(m) as a, open(dst, "wb") as b:
                            b.write(a.read())
                        out.append((dst, f"{os.path.basename(fp)}/{m}"))
                    else:
                        other.append(f"{os.path.basename(fp)}/{m}")
        elif fp.lower().endswith((".csv", ".tsv")):
            out.append((fp, os.path.basename(fp)))
        else:
            other.append(os.path.basename(fp))
    return out, other
def read(fp):
    df = None
    for enc in ("utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(fp, dtype=str, encoding=enc, keep_default_na=False)
            df = pd.read_csv(fp, dtype=str, encoding=enc, keep_default_na=False, sep=None, engine="python") if df.shape[1] == 1 else df
            break
        except Exception:
            continue
    if df is None:
        raise ValueError("unreadable")
    df.columns = translate([str(c).strip() for c in df.columns])
    return df.replace({"": np.nan}).dropna(how="all")
def kind_of(cols):
    n = [N(c) for c in cols]; has = lambda p: any(x.startswith(p) for x in n)
    if has("questiontext") or (has("question") and has("answered")):
        return "journal"
    if has("activityname") or has("activitystrain") or has("workoutstarttime"):
        return "workouts"
    if has("recoveryscore") or has("daystrain"):
        return "cycles"
    return "sleeps" if has("sleeponset") or has("asleepduration") else "unknown"
def match(cols, spec):
    m, used = {}, set()
    for key, pats in spec.items():
        for mode in (0, 1):
            hit = next((c for c in cols if c not in used and any(N(c).startswith(p) if mode == 0 else p in N(c) for p in pats)), None)
            if hit:
                m[key] = hit; used.add(hit); break
    return m
def mark(k, c, u, s=None): COV.setdefault(k, {})[c] = "empty in this export (no values)" if s is not None and s.notna().sum() == 0 else u
def cidx(D, ts):  # index of the cycle containing each timestamp, -1 if none
    i = np.searchsorted(D["start"].values, ts.values.astype("datetime64[ns]"), side="right") - 1
    return np.where(ts.notna().values & (i >= 0), i, -1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("inputs", nargs="+"); ap.add_argument("--out", default="whoop_out")
    ap.add_argument("--weekend", default="Fri,Sat"); ap.add_argument("--no-charts", action="store_true"); a = ap.parse_args()
    out = a.out; tmp = os.path.join(out, "_extracted"); os.makedirs(os.path.join(out, "charts"), exist_ok=True); os.makedirs(tmp, exist_ok=True)
    wkend = [d.strip()[:3].title() for d in a.weekend.split(",") if d.strip()]
    files, other = gather(a.inputs, tmp); tabs = {k: [] for k in ("cycles", "sleeps", "workouts", "journal", "unknown")}; info = []
    for fp, label in files:
        try:
            df = read(fp)
        except Exception as e:
            info.append([label, "UNREADABLE", 0, 0, str(e)[:60]]); continue
        k = kind_of(df.columns); tabs[k].append((label, df))
        info.append([label, k, len(df), df.shape[1], "Arabic export: headers translated (originals kept in [brackets])" if any("[" in c for c in df.columns) else ""])
    TB = {}
    for k, lst in tabs.items():
        if k != "unknown" and lst:
            cols = list(dict.fromkeys(c for _, d in lst for c in d.columns))
            df = pd.concat([d.reindex(columns=cols) for _, d in lst], ignore_index=True); n0 = len(df); df = df.drop_duplicates(); TB[k] = (df, n0 - len(df))
    H("1. Files received and how they were read"); T(["File", "Detected as", "Rows", "Columns", "Note"], info)
    if other:
        P(f"Non-table files: {', '.join(other)} -> read them yourself (screenshots/PDF) and add what they show.")
    if "cycles" not in TB:
        P("**No physiological_cycles file found** - Recovery / HRV / Strain analysis needs it.")

    # ---------- one row per physiological cycle (sleep onset -> next sleep onset)
    D, qual, OPEN, PART = pd.DataFrame(), [], None, set()
    if "cycles" in TB:
        cyc, dups = TB["cycles"]; m = match(list(cyc.columns), KEYS["cycles"]); D["_row"] = cyc.index.values
        for k, c in m.items():
            mark("cycles", c, f"core metric `{k}`", cyc[c])
            if k in ("start", "end", "onset", "wake"):
                D[k] = dt(cyc[c]).values
            elif k == "tz":
                D["tz_raw"] = cyc[c].values; D["tz_off"] = cyc[c].map(tzh).values
            else:
                v = num(cyc[c]); D[k] = ((v - 32) * 5 / 9 if k == "skin_temp" and "fahrenheit" in N(c) else v).values
        if "start" not in D and "onset" in D:
            D["start"] = D["onset"]
        D = D[D["start"].notna()].copy() if "start" in D else pd.DataFrame()
    if len(D):
        for k, (lo, hi) in OK_RANGE.items():
            if k in D:
                bad = D[k].notna() & ((D[k] < lo) | (D[k] > hi))
                if bad.any():
                    qual.append(f"{int(bad.sum())} implausible `{k}` values (outside {lo}-{hi}) excluded from stats"); D.loc[bad, k] = np.nan
        if {"asleep", "in_bed"} <= set(D) and (D["in_bed"] - D["asleep"]).median() < 0:
            D[["asleep", "in_bed"]] = D[["in_bed", "asleep"]].values; qual.append("Asleep and in-bed columns were reversed in the file; swapped (asleep can't exceed time in bed)")
        D["_nn"] = D.notna().sum(axis=1); n1 = len(D)
        D = D.sort_values(["start", "_nn"]).drop_duplicates("start", keep="last").reset_index(drop=True).drop(columns="_nn")
        if n1 - len(D) + dups:
            qual.append(f"{n1 - len(D) + dups} duplicate cycle rows removed (same cycle exported twice)")
        OPEN = D["start"].iloc[-1] if "end" in D and pd.isna(D["end"].iloc[-1]) else None
        if OPEN is not None:
            for k in [k for k in DAYTOT if k in D]: D.loc[D.index[-1], k] = np.nan
            qual.append("Latest cycle is still in progress (no end time): its day totals (strain, energy, heart rate, steps) are left out as incomplete")
        wk = D["wake"] if "wake" in D else pd.Series(pd.NaT, index=D.index)
        lt = D["start"] + pd.Timedelta(hours=8)  # cycle without a sleep: labelled by the middle of its waking hours
        if "end" in D:
            ln = D["end"] - D["start"]; lt = (D["start"] + ln / 2).where(ln.notna() & (ln <= pd.Timedelta(hours=30)), lt)
        D["day"] = wk.where(wk.notna(), lt).dt.normalize()
        if D["day"].duplicated().any():
            qual.append(f"{int(D['day'].duplicated(keep=False).sum())} cycles share a calendar day with another cycle; each cycle is still analysed on its own")
        if "energy" in D and D["energy"].notna().sum() >= 20:
            pw = D["energy"] < .4 * D["energy"].median()
            if pw.any():
                PART = set(D.loc[pw, "start"])
                qual.append(f"{int(pw.sum())} partial-wear days (energy under 40% of your usual day = strap worn for only part of the day); their day totals "
                            "(strain, energy, heart rate, steps) are left out: " + ", ".join(str(d_.date()) for d_ in D.loc[pw, "day"]))
                for k in [k for k in DAYTOT if k in D]: D.loc[pw, k] = np.nan
        D["weekday"] = D["day"].dt.dayofweek.map(lambda i: DAYS[i]); D["weekend"] = D["weekday"].isin(wkend).astype(float)
        D["ramadan"] = sum(((D["day"] >= s) & (D["day"] <= e)) for s, e in RAMADAN).astype(float)
        for k in ("asleep", "in_bed", "need", "debt"):
            if k in D:
                D[k + "_h"] = D[k] / 60
        for k in ("light", "deep", "rem"):
            if k in D and "asleep" in D:
                D[k + "_pct"] = D[k] / D["asleep"].where(D["asleep"] > 0) * 100
        if {"asleep", "need"} <= set(D): D["gap_min"] = D["asleep"] - D["need"]
        if {"awake", "in_bed"} <= set(D): D["awake_pct"] = D["awake"] / D["in_bed"].where(D["in_bed"] > 0) * 100
        hrs = lambda ts: (ts - D["day"]).dt.total_seconds() / 3600  # hours from midnight of the wake day: 23:30 the night before -> -0.5, a 12:30 daytime sleep -> 12.5
        if "onset" in D: D["bed_h"] = hrs(D["onset"])
        if "wake" in D: D["wake_h"] = hrs(D["wake"])
        if {"onset", "wake"} <= set(D): D["mid_h"] = (D["bed_h"] + D["wake_h"]) / 2
        if "recovery" in D: D["zone"] = pd.cut(D["recovery"], [-1, 33.5, 66.5, 101], labels=["red", "yellow", "green"])
        if "strain" in D: D["strain_cat"] = pd.cut(D["strain"], [-1, 9.95, 13.95, 17.95, 22], labels=["light", "moderate", "high", "all out"])
        if "tz_raw" in D:
            z = D["tz_raw"].ffill(); D["tz_change"] = ((z != z.shift(1)) & z.shift(1).notna()).astype(float)
        g = D["start"].shift(-1) - D["start"]
        D["_ok"] = ((g > pd.Timedelta(hours=10)) & (g < pd.Timedelta(hours=44))).shift(1, fill_value=False).astype(bool)  # has a valid previous cycle
        if "hrv" in D: D["hrv_dev"] = D["hrv"] - D["hrv"].rolling(30, min_periods=10).median().shift(1)
    prev = lambda s: s.shift(1).where(D["_ok"])
    nxt = lambda s: s.shift(-1).where(D["_ok"].shift(-1, fill_value=False))

    # ---------- workouts -> per cycle
    W = None
    if "workouts" in TB and len(D):
        wd = TB["workouts"][0]; m = match(list(wd.columns), KEYS["workouts"])
        W = pd.DataFrame({k: (dt(wd[c]) if k in ("start", "end", "w_start", "w_end") else wd[c].astype(str).str.strip() if k in ("act", "tz")
                              else yn(wd[c]) if k == "gps" else num(wd[c])) for k, c in m.items()})
        for k, c in m.items():
            mark("workouts", c, {"act": "activity type -> per-activity table + next-morning effect", "gps": "GPS flag -> distance/pace from GPS workouts only",
                                 "tz": "time zone (same as cycles file; not needed)", "start": "link workout -> its day", "end": "link workout -> its day",
                                 "w_end": "workout end -> late-workout flag", "alt_gain": "altitude -> per-activity totals", "alt_change": "altitude -> per-activity totals"}
                 .get(k, f"workout `{k}` -> per-activity table / daily load"), wd[c])
        if "act" in W: W["act"] = W["act"].replace({"nan": "Unknown", "None": "Unknown", "": "Unknown"})
        W["ci"] = cidx(D, W["start"] if "start" in W else W["w_start"])
        if "dur" not in W and {"w_start", "w_end"} <= set(W): W["dur"] = (W["w_end"] - W["w_start"]).dt.total_seconds() / 60
        for i in range(1, 6):
            if f"z{i}" in W and "dur" in W: W[f"z{i}_min"] = W["dur"] * W[f"z{i}"] / 100
        if {"w_end", "end"} <= set(W): W["h_before_sleep"] = (W["end"] - W["w_end"]).dt.total_seconds() / 3600
        gw = W[W["ci"] >= 0].groupby("ci"); ag = pd.DataFrame({"wk_n": gw.size()})
        for nm, col, fn in [("wk_min", "dur", "sum"), ("wk_strain", "astrain", "max"), ("wk_energy", "energy", "sum")]:
            if col in W: ag[nm] = gw[col].agg(fn)
        if {"z4_min", "z5_min"} <= set(W): ag["wk_z45_min"] = gw["z4_min"].sum() + gw["z5_min"].sum()
        if "h_before_sleep" in W: ag["wk_late"] = gw["h_before_sleep"].min().lt(3).astype(float)
        for act, cnt in (W["act"].value_counts().items() if "act" in W else []):
            if cnt >= 5: ag[f"act_{act}"] = ag.index.isin(W.loc[(W["act"] == act) & (W["ci"] >= 0), "ci"]).astype(float)
        D = D.join(ag); D[list(ag.columns)] = D[list(ag.columns)].fillna(0)

    # ---------- naps (sleeps file)
    if "sleeps" in TB and len(D):
        sd = TB["sleeps"][0]; m = match(list(sd.columns), KEYS["sleeps"])
        S = pd.DataFrame({k: (dt(sd[c]) if k in ("start", "end", "onset", "wake") else yn(sd[c]) if k == "nap" else sd[c] if k == "tz" else num(sd[c]))
                          for k, c in m.items()})
        for k, c in m.items():
            mark("sleeps", c, "nap flag -> naps counted" if k == "nap" else "main sleeps: value-by-value cross-check vs cycles file; naps: count/minutes", sd[c])
        if {"onset", "nap"} <= set(S) and "onset" in D:
            ms = S[(S["nap"] != 1) & S["onset"].notna()].drop_duplicates("onset").set_index("onset"); Dm = D.dropna(subset=["onset"]).drop_duplicates("onset").set_index("onset")
            cm = [k for k in SLP if k not in ("onset", "wake") and k in ms and k in Dm]; ix = ms.index.intersection(Dm.index)
            dif = (ms.loc[ix, cm] - Dm.loc[ix, cm]).abs() > .5 if len(ix) and cm else pd.DataFrame()
            qual.append(f"Sleeps file cross-check: {len(ix)} main sleeps x {len(cm)} measures compared with the cycles file, {int(dif.values.sum()) if len(dif) else 0} differences; "
                        f"{len(ms.index.difference(Dm.index))} main sleeps not in the cycles file")
        if {"nap", "onset"} <= set(S):
            nps = S[(S["nap"] == 1) & S["onset"].notna()].copy(); nps["ci"] = cidx(D, nps["onset"]); gn = nps[nps["ci"] >= 0].groupby("ci")
            D["nap_n"] = gn.size().reindex(D.index).fillna(0)
            if "asleep" in nps: D["nap_min"] = gn["asleep"].sum().reindex(D.index).fillna(0)
            F["naps"] = {"count": int(len(nps)), "mean_min": float(nps["asleep"].mean()) if "asleep" in nps and len(nps) else None,
                         "early_morning": int(nps["onset"].dt.hour.between(3, 8).sum())}
            qual.append(f"Sleeps file: {int((S['nap'] != 1).sum())} main sleeps (cycles file has {int(D['onset'].notna().sum()) if 'onset' in D else '?'}) + {len(nps)} naps")

    # ---------- journal -> one column per question (1 = yes, 0 = no), stored on the day the behaviour happened
    J = pd.DataFrame(index=D.index)
    if "journal" in TB and len(D):
        jd = TB["journal"][0]; m = match(list(jd.columns), KEYS["journal"])
        for k, c in m.items():
            mark("journal", c, dict(q="each question -> its own yes/no variable", yes="answer -> next-morning effects", notes="free-text notes -> listed with dates",
                                    start="link answer -> its day", end="not needed (start time identifies the day)", tz="time zone (same as cycles file; not needed)")[k], jd[c])
        if {"q", "yes", "start"} <= set(m):
            jj = pd.DataFrame({"start": dt(jd[m["start"]]), "q": jd[m["q"]].astype(str).str.strip(), "yes": yn(jd[m["yes"]])})
            jj["ci"] = cidx(D, jj["start"]); jj = jj[jj["ci"] >= 0]
            J = jj.pivot_table(index="ci", columns="q", values="yes", aggfunc="max").reindex(D.index)
            for c in [c for c in jd.columns if c not in m.values() and num(jd[c]).notna().mean() > .5]:
                jj["_v"] = num(jd.loc[jj.index, c]).values; vv = jj.pivot_table(index="ci", columns="q", values="_v", aggfunc="mean").reindex(D.index)
                for q in vv.columns:
                    if vv[q].notna().sum() >= 10 and vv[q].nunique() > 2: J[f"{q} [{c}]"] = vv[q]
                mark("journal", c, "numeric journal value -> per-question variable")
            if "notes" in m:
                nt = jd[jd[m["notes"]].notna()]; ii = cidx(D, dt(nt[m["start"]]))
                F["journal_notes"] = [{"day": str(D["day"].iloc[i].date()) if i >= 0 else "?", "question": q, "note": n_}
                                      for i, q, n_ in zip(ii, nt[m["q"]].astype(str), nt[m["notes"]].astype(str))]

    # ---------- every remaining column gets a use (nothing ignored)
    GEN = {}
    for k, (df, _) in TB.items():
        for c in df.columns:
            if c in COV.get(k, {}):
                continue
            s = df[c]; nn = int(s.notna().sum()); v = num(s)
            if nn == 0:
                mark(k, c, "empty in this export")
            elif v.notna().sum() >= .6 * nn:
                mark(k, c, "extra numeric column -> profiled + linked to Recovery/HRV/RHR" if k == "cycles" else "extra numeric column -> profiled"); GEN[(k, c)] = v
            elif dt(s).notna().sum() >= .6 * nn:
                mark(k, c, "extra date/time column -> range reported"); GEN[(k, c)] = dt(s)
            else:
                mark(k, c, "extra text column -> values counted"); GEN[(k, c)] = s
    for label, df in tabs["unknown"]:
        for c in df.columns:
            mark(f"other file: {label}", c, "unrecognised file -> profiled"); GEN[(f"other file: {label}", c)] = df[c]
    if not len(D):
        H("Stopped"); P("No usable cycle data found - check the files."); return finish(out, D, a)

    # ---------- 2. coverage
    days = D["day"]; span = (days.max() - days.min()).days + 1; rn = int(D["recovery"].notna().sum()) if "recovery" in D else 0
    F["period"] = dict(first_day=str(days.min().date()), last_day=str(days.max().date()), calendar_days=span, cycles=len(D),
                       mornings_with_recovery=rn, wear_pct=round(100 * rn / span, 1))
    H("2. Coverage and data quality")
    P(f"- Period **{F['period']['first_day']} -> {F['period']['last_day']}**: {span} calendar days, {len(D)} cycles, {rn} mornings with a Recovery score ({F['period']['wear_pct']}%)")
    miss = sorted(set(pd.date_range(days.min(), days.max()).date) - set(days.dt.date)); runs = []
    for d_ in miss:
        if runs and (d_ - runs[-1][1]).days == 1: runs[-1][1] = d_
        else: runs.append([d_, d_])
    big = sorted([r_ for r_ in runs if (r_[1] - r_[0]).days >= 2], key=lambda r_: -(r_[1] - r_[0]).days); sm = sum((b_ - a_).days + 1 for a_, b_ in runs if (b_ - a_).days < 2)
    P(f"- Days with no data at all (strap off / not synced): {len(miss)}" + ((": " + "; ".join(f"{a_} -> {b_} ({(b_ - a_).days + 1} days)" for a_, b_ in big[:8])
      + (f"; plus {sm} days in short gaps of 1-2 days" if sm else "")) if big else (" (all in short gaps of 1-2 days)" if miss else "")))
    F["gaps"] = [dict(first=str(a_), last=str(b_), days=(b_ - a_).days + 1) for a_, b_ in big]
    D["era"] = (days.diff().dt.days > 30).cumsum().astype(int) + 1  # wear periods, split at gaps of 30+ days
    ERAS = [(g_["day"].min(), g_["day"].max(), len(g_)) for _, g_ in D.groupby("era")]; MON = days.dt.to_period("M").astype(str)
    if len(ERAS) > 1:
        P(f"- Wear periods (split at gaps of 30+ days): {len(ERAS)} - " + "; ".join(f"P{i + 1} {a_.date()} -> {b_.date()} ({n_} cycles)" for i, (a_, b_, n_) in enumerate(ERAS))
          + ". Compared in section 8; every link in sections 6-7 is also re-checked inside the same month.")
    T(["Metric", "Days with value", "Missing"], [[lab(k), int(D[k].notna().sum()), pct(D[k].isna().sum(), len(D))] for k in
      ["recovery", "hrv", "rhr", "resp", "spo2", "skin_temp", "strain", "steps", "asleep_h", "sleep_perf", "eff", "cons"] if k in D])
    for q in qual: P(f"- {q}")
    if "recovery" in D and D["recovery"].head(5).isna().sum() >= 3: P("- First days without Recovery = WHOOP's normal calibration period.")
    if "tz_change" in D: P(f"- Time-zone changes (travel): {int(D['tz_change'].sum())}")

    # ---------- 3. baselines
    H("3. Your own normal (baseline) and recent change")
    last = days.max(); w7 = days > last - pd.Timedelta(days=7); w30 = days > last - pd.Timedelta(days=30)
    p30 = (days <= last - pd.Timedelta(days=30)) & (days > last - pd.Timedelta(days=60)); rows, base = [], {}
    for k in MET:
        if k not in D or D[k].notna().sum() < 3:
            continue
        s = D[k]; d30 = s[w30].mean() - s[p30].mean() if s[p30].notna().sum() >= 5 else np.nan
        base[k] = dict(mean=s.mean(), median=s.median(), p25=s.quantile(.25), p75=s.quantile(.75), n=int(s.notna().sum()), last7=s[w7].mean(),
                       last30=s[w30].mean(), prev30=s[p30].mean(), change_30_vs_prev30=d30)
        rows.append([lab(k), base[k]["n"], fmt(k, s.mean()), fmt(k, s.median()), f"{fmt(k, s.quantile(.25))} - {fmt(k, s.quantile(.75))}",
                     f"{fmt(k, s.min())} ({days[s.idxmin()].date()})", f"{fmt(k, s.max())} ({days[s.idxmax()].date()})", fmt(k, s[w7].mean()),
                     fmt(k, s[w30].mean()), fmt(k, s[p30].mean()), (("0" if abs(d30 * 60) < .5 else sg(d30 * 60, 0)) + " min") if clk(k) and fin(d30) else sg(d30, MET[k][3] or 1)])
    T(["Metric", "n", "Mean", "Median", "Usual range (middle 50%)", "Lowest (day)", "Highest (day)", "Last 7d", "Last 30d", "Prev 30d", "Last30 - Prev30"], rows)
    F["baselines"] = {k: {kk: (round(float(v), 3) if fin(v) else None) for kk, v in d.items()} for k, d in base.items()}

    # ---------- 4. WHOOP bands
    H("4. How your days split across WHOOP's official bands")
    for col, names, note in [("zone", ["green", "yellow", "red"], "Recovery bands: green 67-100, yellow 34-66, red 0-33."),
                             ("strain_cat", ["light", "moderate", "high", "all out"], "Strain bands: light 0-9, moderate 10-13, high 14-17, all out 18-21. WHOOP member average Day Strain is about 11.")]:
        if col in D:
            z = D[col].value_counts(); tot = z.sum()
            T([{"zone": "Recovery zone", "strain_cat": "Strain band"}[col], "Days", "Share"], [[n_, int(z.get(n_, 0)), pct(z.get(n_, 0), tot)] for n_ in names]); P(note)
            F[col + "_pct"] = {n_: round(100 * z.get(n_, 0) / tot, 1) for n_ in names} if tot else {}
    if "sleep_perf" in D:
        sp = D["sleep_perf"].dropna()
        T(["Sleep performance", "Nights", "Share"], [[n_, int(c), pct(c, len(sp))] for n_, c in [("optimal >= 85%", (sp >= 85).sum()),
          ("sufficient 70-84%", ((sp >= 70) & (sp < 85)).sum()), ("poor < 70%", (sp < 70).sum())]])
    if "cons" in D:
        c_ = D["cons"].dropna(); P(f"Sleep consistency: {pct((c_ >= 90).sum(), len(c_))} of nights optimal (>= 90%), {pct(((c_ >= 80) & (c_ < 90)).sum(), len(c_))} sufficient (80-89%), {pct((c_ < 80).sum(), len(c_))} below 80%.")

    # ---------- 5. composition of the Recovery number
    H("5. What the Recovery number itself follows (same morning)")
    if "recovery" in D:
        rows = []
        for k in [k for k in ["hrv", "hrv_dev", "rhr", "resp", "sleep_perf", "spo2", "skin_temp"] if k in D]:
            r, p, n = spear(D[k], D["recovery"]); rows.append(["HRV vs your own 30-day normal" if k == "hrv_dev" else lab(k), n, f(r, 2), f(p, 4)])
        T(["Same-morning signal", "n", "Spearman rho with Recovery", "p"], rows)
        comp = [k for k in ["hrv", "rhr", "resp", "sleep_perf"] if k in D]; mo = ols(D["recovery"], D[comp]) if comp else None
        if mo:
            P(f"Together {', '.join(lab(k) for k in comp)} explain **{f(100 * mo['r2'], 0)}%** of day-to-day Recovery changes (n={mo['n']}).")
            P("Standardized weight (bigger = more influence): " + ", ".join(f"{lab(k)} {sg(mo['b'][k] * mo['sd'][k] / mo['sdy'], 2)}" for k in comp))
            F["recovery_composition_r2"] = round(mo["r2"], 3)

    # ---------- 6. links: everything vs Recovery / HRV / RHR / next sleep
    H("6. Links: what goes with higher or lower Recovery, HRV, resting HR and sleep")
    if rn < 30:
        P(f"**LOW DATA: only {rn} mornings. Links are not reliable yet; 'not judged' means not enough data, not 'no effect'. ~30 days gives first signals, 90+ solid ones.**")
        F["low_data"] = True
    P("Alignment (WHOOP's own logic): the sleep that starts a cycle -> that morning's Recovery; the day's Strain, workouts, naps and Journal answers -> the NEXT morning.")
    X, kinds = {}, {}
    def add(name, s, kind="cont"):
        if s is not None and s.notna().sum() >= 10 and s.nunique() >= 2:
            X[name] = s; kinds[name] = kind
    for k, nm in dict(asleep_h="Sleep: hours asleep", in_bed_h="Sleep: time in bed (h)", eff="Sleep: efficiency %", cons="Sleep: consistency %",
                      sleep_perf="Sleep: performance %", deep_pct="Sleep: deep share %", rem_pct="Sleep: REM share %", light_pct="Sleep: light share %",
                      awake_pct="Sleep: awake share % of bed", deep="Sleep: deep minutes", rem="Sleep: REM minutes", need_h="Sleep: need (h)",
                      debt_h="Sleep: debt (h)", gap_min="Sleep: minutes vs need", bed_h="Sleep: bedtime (h after midnight)", wake_h="Sleep: wake time (h)",
                      resp="Night: respiratory rate", spo2="Night: blood oxygen %", skin_temp="Night: skin temp").items():
        if k in D: add(nm, D[k])
    for k, nm in dict(strain="Day before: Day Strain", energy="Day before: energy kcal", avg_hr="Day before: average HR", max_hr="Day before: max HR",
                      steps="Day before: steps").items():
        if k in D: add(nm, prev(D[k]))
    for k, flag, nm in [("wk_n", "Day before: any workout", None), ("wk_min", None, "Day before: workout minutes (workout days only)"),
                        ("wk_strain", None, "Day before: hardest workout strain (workout days only)"), ("wk_z45_min", None, "Day before: minutes in HR zones 4-5 (workout days only)"),
                        ("nap_n", "Day before: any nap", None), ("nap_min", None, "Day before: nap minutes (nap days only)")]:
        if k in D:
            if flag: add(flag, prev((D[k] > 0).astype(float)), "bin")
            else: add(nm, prev(D[k].where(D["nap_n" if k.startswith("nap") else "wk_n"] > 0)))
    if "wk_late" in D: add("Day before: workout ended < 3 h before sleep", prev(D["wk_late"]), "bin")
    for c in [c for c in D.columns if c.startswith("act_")]: add(f"Day before: did {c[4:]}", prev(D[c]), "bin")
    for q in J.columns: add(f"Journal (day before): {q}", prev(J[q]), "bin" if J[q].dropna().isin([0, 1]).all() else "cont")
    for k, nm in [("tz_change", "Context: time zone changed (travel)"), ("ramadan", "Context: Ramadan (approx. dates)"), ("weekend", f"Context: weekend day ({'/'.join(wkend)})")]:
        if k in D: add(nm, D[k], "bin")
    for (k, c), s in GEN.items():
        if k == "cycles" and pd.api.types.is_numeric_dtype(s):
            add(f"Other column (same day): {c}", D["_row"].map(s)); add(f"Other column (day before): {c}", prev(D["_row"].map(s)))
    sprev = prev(D["strain"]) if "strain" in D else None
    CVJ = pd.DataFrame({"w": D["weekend"], "r": D["ramadan"]}); CVJ["s"] = sprev if sprev is not None else np.nan
    CVJ = CVJ.drop(columns=[c for c in CVJ if CVJ[c].notna().sum() < 30])  # journal checks are adjusted for day-before strain, weekend, Ramadan
    def wcheck(nm, kind, y):
        w = within(X[nm], y, MON, kind == "bin")
        if isinstance(w, dict) and nm.startswith("Journal"):
            mo = ols_fe(y, CVJ.assign(x=X[nm]), MON)
            if mo and "x" in mo["b"]: w.update(s=mo["b"]["x"], p=mo["p"]["x"], b=mo["b"]["x"], txt=f"same-month diff {sg(mo['b']['x'])}")
        return w
    targets = [t for t in ["recovery", "hrv", "rhr", "sleep_perf", "eff", "asleep_h"] if t in D]; drivers = {}
    for t in targets:
        res = []
        for nm, x in X.items():
            if t in ("sleep_perf", "eff", "asleep_h") and nm.startswith(("Sleep:", "Night:", "Other column (same day)")):
                continue
            y = D[t]; r, p, n = spear(x, y)
            if not fin(r):
                continue
            row = dict(feature=nm, kind=kinds[nm], n=n, rho=r, p=p); ok = x.notna() & y.notna(); nr_ = ok & (D["ramadan"] == 0)
            if kinds[nm] == "bin":
                a1, a0 = y[ok & (x == 1)], y[ok & (x == 0)]; d_ = a1.mean() - a0.mean()
                se = math.sqrt(a1.var(ddof=1) / len(a1) + a0.var(ddof=1) / len(a0)) if len(a1) > 1 and len(a0) > 1 else np.nan
                row.update(n_yes=len(a1), n_no=len(a0), mean_yes=a1.mean(), mean_no=a0.mean(), diff=d_, lo=d_ - 1.96 * se, hi=d_ + 1.96 * se,
                           d_noram=y[nr_ & (x == 1)].mean() - y[nr_ & (x == 0)].mean())
                if len(a1) < 5 or len(a0) < 5:
                    row.update(p=np.nan, note="too few yes/no answers")
            else:
                if (x[ok] == 0).mean() >= .25 and (x[ok] > 0).sum() >= 5:
                    row.update(zero=True, low=y[ok & (x == 0)].mean(), high=y[ok & (x > 0)].mean(), d_noram=y[nr_ & (x > 0)].mean() - y[nr_ & (x == 0)].mean())
                else:
                    q1, q3 = x[ok].quantile(.25), x[ok].quantile(.75); row.update(q1=q1, q3=q3, low=y[ok & (x <= q1)].mean(), high=y[ok & (x >= q3)].mean(),
                                                                                  d_noram=y[nr_ & (x >= q3)].mean() - y[nr_ & (x <= q1)].mean())
                row["diff"] = row["high"] - row["low"]; sd_ = x[ok].std()
                if sd_ > 0:
                    row["step"] = 10 ** math.floor(math.log10(sd_)) if sd_ >= 10 else 1
                    row["slope"] = np.polyfit(x[ok].astype(float), y[ok].astype(float), 1)[0] * row["step"]
            res.append(row)
        for r_, qv in zip(res, bh([r_["p"] for r_ in res])):
            r_["q"] = qv; r_["verdict"] = "not enough data" if "note" in r_ else verdict(r_["p"], qv); r_["check"] = ""
            if r_["verdict"] in ("clear", "possible") and not r_["feature"].startswith("Context:"):
                w = wcheck(r_["feature"], r_["kind"], D[t]); r_["raw_verdict"] = r_["verdict"]; r_["verdict"], r_["check"] = recheck(r_["verdict"], r_["rho"], w)
                if isinstance(w, dict): r_.update(w_r=w["r"], w_p=w["p"], w_k=w["k"], w_b=w["b"])
            elif r_["feature"].startswith("Context:") and r_["verdict"] in ("clear", "possible"):
                r_["check"] = "- (a period itself)"
        hid = [(r_, w) for r_ in res if r_["verdict"] == "no clear link" and not r_["feature"].startswith("Context:")
               for w in [wcheck(r_["feature"], r_["kind"], D[t])] if isinstance(w, dict)]
        for (r_, w), qv in zip(hid, bh([w["p"] for _, w in hid])):  # hidden by period differences: shows only inside the same month (FDR-controlled)
            if fin(qv) and qv < .05:
                r_.update(verdict="possible", check=f"only inside the same month ({w['txt']}, q {f(qv, 3)})", w_r=w["r"], w_p=w["p"], w_k=w["k"], w_b=w["b"])
        VO = {"clear": 0, "possible": 1, "between periods only": 2}
        drivers[t] = sorted(res, key=lambda r_: (VO.get(r_["verdict"], 3), -abs(r_["rho"])))
        P(f"\n### Links with {lab(t)}  (tested {len(res)} variables)")
        rows, ram_on = [], D["ramadan"].sum() >= 7
        for r_ in [r_ for r_ in drivers[t] if r_["verdict"] in VO and r_["n"] >= 20]:
            if r_["kind"] == "bin":
                e_ = f"yes {f(r_['mean_yes'])} vs no (all other days) {f(r_['mean_no'])} -> {sg(r_['diff'])} [{sg(r_['lo'])}, {sg(r_['hi'])}]"
            elif r_.get("zero"):
                e_ = f"none (0): {f(r_['low'])} vs some (>0): {f(r_['high'])} -> {sg(r_['diff'])}"
            else:
                th = (lambda v: hm(v)) if "bedtime" in r_["feature"] or "wake time" in r_["feature"] else (lambda v: f(v, 0 if abs(v) >= 100 else 2))
                e_ = f"low (<= {th(r_['q1'])}): {f(r_['low'])} vs high (>= {th(r_['q3'])}): {f(r_['high'])} -> {sg(r_['diff'])}"
                e_ += f"; {sg(r_['slope'], 2)} per +{f(r_['step'], 0)} unit(s)" if fin(r_.get("slope")) else ""
            e_ += f"; outside Ramadan {sg(r_.get('d_noram'))}" if ram_on else ""
            rows.append([r_["feature"], r_["n"], f(r_["rho"], 2), f(r_["p"], 4), f(r_["q"], 3), r_["verdict"], r_["check"], e_])
        T(["Variable", "n", "rho", "p", "q (FDR)", "Verdict", "Same-month check", "Effect in real units (whole period)"], rows)
        weak = [r_["feature"] for r_ in drivers[t] if r_["verdict"] == "no clear link"]
        if weak: P(("Not judged (too little data): " if rn < 30 else "No clear link (tested): ") + ", ".join(weak))
        few = [f"{r_['feature']} (yes {r_['n_yes']} / no {r_['n_no']})" for r_ in drivers[t] if r_["verdict"] == "not enough data"]
        if few: P("Not enough yes/no answers to judge: " + ", ".join(few))
    P("\nSame-month check: the same link re-tested inside each calendar month, so slow changes (new routine, season, a new strap or app update) cannot create it. "
      "'between periods only' = the link appears only when comparing different months/periods and not inside them - something else that changed at the same time is the likelier cause.")
    keep = ("feature", "n", "rho", "p", "q", "verdict", "raw_verdict", "check", "w_r", "w_p", "w_k", "w_b", "diff", "slope", "step", "mean_yes", "mean_no", "n_yes", "n_no")
    F["drivers"] = {t: [{k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else v) for k, v in r_.items() if k in keep}
                        for r_ in drivers[t] if r_["verdict"] in VO] for t in targets}
    if "recovery" in D:
        Xm = pd.DataFrame({v: D[k] for k, v in dict(asleep_h="hours asleep", eff="efficiency %", bed_h="bedtime (h)", cons="consistency %",
                                                     rem_pct="REM %", deep_pct="deep %", resp="respiratory rate").items() if k in D})
        if sprev is not None: Xm["Day Strain day before"] = sprev
        Xm = Xm[[c for c in Xm.columns if Xm[c].notna().sum() >= 30 and Xm[c].std() > 0]]; mo = ols(D["recovery"], Xm) if Xm.shape[1] else None
        mf = ols_fe(D["recovery"], Xm, MON) if Xm.shape[1] and MON.nunique() >= 2 else None
        if mo:
            P(f"\n### Combined model: Recovery vs several factors at once (n={mo['n']}; explains {f(100 * mo['r2'], 0)}% over the whole period"
              + (f", {f(100 * mf['r2'], 0)}% of the changes inside each month)" if mf else ")"))
            T(["Factor (others held equal)", "Recovery points per +1 unit (whole period)", "p", "Same month: points per +1 unit", "p (same month)"],
              [[c, sg(mo["b"][c], 2), f(mo["p"][c], 4), sg(mf["b"].get(c), 2) if mf else "-", f(mf["p"].get(c), 4) if mf else "-"] for c in Xm.columns])
            F["model"] = dict(r2=round(mo["r2"], 3), n=mo["n"], coef={c: round(mo["b"][c], 3) for c in Xm.columns}, p={c: round(mo["p"][c], 4) for c in Xm.columns},
                              same_month=dict(r2=round(mf["r2"], 3), coef={c: round(v, 3) for c, v in mf["b"].items()}, p={c: round(v, 4) for c, v in mf["p"].items()}) if mf else None)

    # ---------- 7. journal, every question
    if J.shape[1]:
        H("7. Journal: every question and what happened the next morning")
        byf = {t: {r_["feature"]: r_ for r_ in drivers.get(t, [])} for t in targets}; rows, same = [], []; JT = [t for t in ["recovery", "hrv", "rhr", "sleep_perf"] if t in D]
        for q in J.columns:
            nm = f"Journal (day before): {q}"; rr = byf.get("recovery", {}).get(nm)
            if rr is None or rr["kind"] != "bin":
                same.append([q, int((J[q] == 1).sum()), int((J[q] == 0).sum()), "always the same answer (or numeric)"]); continue
            fe = {}
            for t in JT:
                w = within(X[nm], D[t], MON, True) if nm in X else None
                mo = ols_fe(D[t], CVJ.assign(x=X[nm]), MON) if isinstance(w, dict) else None; fe[t] = (mo["b"]["x"], mo["p"]["x"]) if mo and "x" in mo["b"] else (np.nan, np.nan)
            vd = "; ".join(f"{MET[t][0]}: {byf[t][nm]['verdict']}" for t in JT if nm in byf.get(t, {}) and byf[t][nm]["verdict"] in ("clear", "possible", "between periods only"))
            vd = vd or ("not enough data" if rr["verdict"] == "not enough data" else "no clear link")
            cells = [q, rr["n_yes"], rr["n_no"], int((J[q].dropna().diff().abs() > 0).sum()), f"{f(rr['mean_yes'], 0)} vs {f(rr['mean_no'], 0)} ({sg(rr['diff'])})"]
            cells += [sg(fe[t][0]) for t in JT] + [f(fe.get("recovery", (np.nan, np.nan))[1], 3), vd,
                      f"{pct((J.loc[w30, q] == 1).sum(), J.loc[w30, q].notna().sum())} vs {pct((J.loc[p30, q] == 1).sum(), J.loc[p30, q].notna().sum())}"]
            rows.append((abs(rr["diff"]) if rr["verdict"] != "not enough data" and fin(rr["diff"]) else -1, cells))
            if rr["verdict"] != "not enough data":
                F.setdefault("journal_all", []).append(dict(question=q, n_yes=rr["n_yes"], n_no=rr["n_no"], diff=round(float(rr["diff"]), 2), lo=round(float(rr["lo"]), 2),
                                                            hi=round(float(rr["hi"]), 2), p=rr["p"], verdict=rr["verdict"], verdicts=vd,
                                                            same_month={t: (round(float(fe[t][0]), 2) if fin(fe[t][0]) else None) for t in JT}))
        T(["Question", "Yes", "No", "Answer changes", "Next-morning Recovery yes vs no (all days)"] + [f"Same month (adj.): {MET[t][0]}" for t in JT]
          + ["p (same month, Recovery)", "Verdict", "'Yes' share last 30d vs prev 30d"], [c for _, c in sorted(rows, key=lambda x: -x[0])]) if rows else P("No question had both yes and no answers to compare.")
        P("Same month (adj.) = yes-days compared with no-days inside the same calendar month, adjusted for the day-before strain and weekend (and Ramadan where it varies): "
          "slow changes (new routine, season, a new strap or app update) are removed. '-' = the answer never changes inside a month, so only periods can be compared. "
          "Answer changes = how often the answer flipped between consecutive answered days (few = answered in long blocks, so a whole-period comparison is mostly a comparison of periods).")
        if same: P("Cannot be compared:"); T(["Question", "Yes", "No", "Why"], same)
        P("WHOOP itself needs at least 5 'yes' and 5 'no' answers to judge a behaviour.")
        if F.get("journal_notes"):
            gn_ = {}
            for n_ in F["journal_notes"]: gn_.setdefault((n_["day"], n_["note"].strip()), []).append(n_["question"])
            P(f"Journal notes ({len(gn_)} distinct notes in {len(F['journal_notes'])} entries):")
            T(["Day", "Note", "Written on"], [[d_, nt_, qs[0] if len(qs) == 1 else f"{len(qs)} questions (same note)"] for (d_, nt_), qs in sorted(gn_.items(), reverse=True)][:40])

    # ---------- 8. trends
    H("8. Trends over the whole period" + (" and inside the latest wear period" if len(ERAS) > 1 else ""))
    td = (days - days.min()).dt.days.astype(float); rows, tr = [], {}; le = D["era"] == D["era"].max()
    def rd(k, sl, r, p):
        g_ = MET[k][2]
        return ("stable" if not (fin(p) and p < .05 and abs(r) >= .1) else "improving" if g_ * sl > 0 else "worsening" if g_ * sl < 0
                else ("later" if sl > 0 else "earlier") if clk(k) else ("rising" if sl > 0 else "falling"))
    s30 = lambda k, sl: (sg(sl * 60, 0) + " min") if clk(k) else sg(sl, 0 if abs(sl) >= 100 else 2)
    for k in ["recovery", "hrv", "rhr", "resp", "spo2", "skin_temp", "strain", "steps", "asleep_h", "sleep_perf", "eff", "cons", "deep", "rem", "bed_h", "debt_h"]:
        if k not in D or D[k].notna().sum() < 21:
            continue
        mk = D[k].notna(); sl = np.polyfit(td[mk], D[k][mk].astype(float), 1)[0] * 30; r, p, n = spear(td, D[k]); dirn = rd(k, sl, r, p)
        tr[k] = dict(per_30_days=round(float(sl), 3), rho=round(float(r), 3), p=round(float(p), 5), direction=dirn)
        row = [lab(k), s30(k, sl), f(r, 2), f(p, 4), dirn]
        if len(ERAS) > 1:
            m2 = mk & le
            if m2.sum() >= 21:
                sl2 = np.polyfit(td[m2], D[k][m2].astype(float), 1)[0] * 30; r2, p2, _ = spear(td[le], D[k][le]); d2 = rd(k, sl2, r2, p2)
                tr[k].update(latest_per_30_days=round(float(sl2), 3), latest_rho=round(float(r2), 3), latest_p=round(float(p2), 5), latest_direction=d2)
                row += [s30(k, sl2), f(r2, 2), f(p2, 4), d2]
            else:
                row += ["-"] * 4
        rows.append(row)
    T(["Metric", "Change per 30 days", "rho with time", "p", "Reading"] + (["Latest period: change per 30 days", "rho", "p", "Reading"] if len(ERAS) > 1 else []), rows)
    F["trends"] = tr
    if len(ERAS) > 1:
        P("\n**Wear periods compared** (separated by gaps of 30+ days without data; bedtime and wake time are medians)")
        ek = [k for k in ["recovery", "hrv", "rhr", "resp", "spo2", "skin_temp", "strain", "energy", "asleep_h", "in_bed_h", "need_h", "sleep_perf", "eff", "cons",
                          "light_pct", "deep_pct", "rem_pct", "awake_pct", "bed_h", "wake_h"] if k in D]
        rows, ER = [], {}
        for k in ek:
            v = [agk(k, D.loc[D["era"] == i + 1, k]) for i in range(len(ERAS))]; dl = v[-1] - v[-2] if fin(v[-1]) and fin(v[-2]) else np.nan
            ER[k] = [round(float(x_), 3) if fin(x_) else None for x_ in v]
            rows.append([lab(k)] + [fmt(k, x_) for x_ in v] + [((sg(dl * 60, 0) + " min") if clk(k) else sg(dl, MET[k][3] or 1)) if fin(dl) else "-"])
        if W is not None and "w_start" in W:
            wpw = [len(W[(W["w_start"] >= a_) & (W["w_start"] < b_ + pd.Timedelta(days=1))]) / max(((b_ - a_).days + 1) / 7, 1) for a_, b_, _ in ERAS]
            rows.append(["Workouts per week"] + [f(x_) for x_ in wpw] + [sg(wpw[-1] - wpw[-2])]); ER["workouts_per_week"] = [round(x_, 2) for x_ in wpw]
        T(["Metric"] + [f"P{i + 1}: {a_.date()} -> {b_.date()} ({n_} cycles)" for i, (a_, b_, n_) in enumerate(ERAS)] + ["Latest minus previous"], rows)
        F["eras"] = dict(periods=[dict(first=str(a_.date()), last=str(b_.date()), cycles=n_) for a_, b_, n_ in ERAS], means=ER)
        P("Differences between wear periods can be real change (fitness, routine, season, age) or a different strap / app version. Judge recent changes inside the latest period first.")
    if days.min() < pd.Timestamp("2025-05-08") and days.max() > pd.Timestamp("2025-07-01"):
        P("Device note: WHOOP launched new straps (5.0 / MG) on 8 May 2025 and updated its sleep-stage and Sleep Performance calculations in 2025. "
          "If your data crosses that point, a step change in sleep stages or sleep performance around then can come from the device or app, not your body.")
    mc = [k for k in ["recovery", "hrv", "rhr", "asleep_h", "sleep_perf", "strain", "resp", "bed_h"] if k in D]
    P("Month by month (bedtime = median):"); T(["Month", "Days"] + [lab(k) for k in mc], [[str(mo_) + (" (partial)" if len(g_) < 7 else ""), len(g_)] + [fmt(k, agk(k, g_[k])) for k in mc] for mo_, g_ in D.groupby(days.dt.to_period("M"))])

    # ---------- 9. sleep
    if "asleep_h" in D:
        H("9. Sleep in detail"); a_ = D["asleep_h"].dropna()
        T(["Hours asleep", "Nights", "Share"], [[n_, int(c), pct(c, len(a_))] for n_, c in [("< 6 h", (a_ < 6).sum()), ("6-7 h", ((a_ >= 6) & (a_ < 7)).sum()),
          ("7-8 h", ((a_ >= 7) & (a_ < 8)).sum()), (">= 8 h", (a_ >= 8).sum())]])
        if "need_h" in D:
            ok = D["asleep_h"].notna() & D["need_h"].notna()
            P(f"- Slept at least your need on {pct((D['asleep_h'][ok] >= D['need_h'][ok]).sum(), ok.sum())} of nights; average shortfall "
              f"{f((D['need_h'][ok] - D['asleep_h'][ok]).mean() * 60, 0)} min/night (average need {f(D['need_h'].mean(), 2)} h).")
        P("- WHOOP typical stage shares: light ~50%, REM 20-25%, deep (SWS) 15-25% of time asleep; awake ~5% of time in bed.")
        T(["Stage", "Your average share", "Your average minutes"], [[nm, (f(D[k + "_pct"].mean()) + "%") if k + "_pct" in D else "-", f(D[k].mean(), 0) if k in D else "-"]
          for k, nm in [("light", "Light"), ("deep", "Deep (SWS)"), ("rem", "REM"), ("awake", "Awake")]])
        if "bed_h" in D:
            we = D["weekend"] == 1
            P(f"- Bedtime: median {hm(D['bed_h'].median())}, usual range (middle 50%) {hm(D['bed_h'].quantile(.25))} - {hm(D['bed_h'].quantile(.75))}; "
              f"wake median {hm(D['wake_h'].median()) if 'wake_h' in D else '-'}")
            dsl = D["bed_h"] >= 6
            if dsl.any():
                P(f"- Main sleep started at 06:00 or later (daytime sleep) on {int(dsl.sum())} days" + (f", {int((dsl & (D['ramadan'] == 1)).sum())} of them in Ramadan" if D["ramadan"].sum() else ""))
            if we.any() and (~we).any():
                T(["Days", "Usual bedtime (median)", "Usual wake (median)", "Hours asleep", "Recovery"], [[nm, hm(D.loc[msk, "bed_h"].median()), hm(D.loc[msk, "wake_h"].median()) if "wake_h" in D else "-",
                  f(D.loc[msk, "asleep_h"].mean(), 2), f(D.loc[msk, "recovery"].mean(), 0) if "recovery" in D else "-"] for nm, msk in [(f"Weekend ({'/'.join(wkend)})", we), ("Work/study days", ~we)]])
                if "mid_h" in D:
                    sj = (D.loc[we, "mid_h"].median() - D.loc[~we, "mid_h"].median()) * 60; F["weekend_shift_min"] = round(float(sj), 1)
                    P(f"- Body-clock shift between weekend and other days (mid-sleep): {f(abs(sj), 0)} min {'later' if sj > 0 else 'earlier'} on weekends.")
            if "recovery" in D:
                cb = pd.cut(D["bed_h"], [-24, -1, 0, 1, 2, 6, 24], labels=["before 23:00", "23:00-00:00", "00:00-01:00", "01:00-02:00", "02:00-06:00", "06:00 or later (daytime sleep)"])
                T(["Bedtime", "Nights", "Recovery", "HRV", "Hours asleep"], [[l_, int((cb == l_).sum()), f(D.loc[cb == l_, "recovery"].mean(), 0),
                  f(D.loc[cb == l_, "hrv"].mean(), 0) if "hrv" in D else "-", f(D.loc[cb == l_, "asleep_h"].mean(), 2)] for l_ in cb.cat.categories if (cb == l_).any()])
        if "recovery" in D:
            cb = pd.cut(D["asleep_h"], [0, 6, 7, 8, 24], labels=["< 6 h", "6-7 h", "7-8 h", ">= 8 h"], right=False)
            T(["Hours asleep", "Nights", "Same-morning Recovery", "HRV"], [[l_, int((cb == l_).sum()), f(D.loc[cb == l_, "recovery"].mean(), 0),
              f(D.loc[cb == l_, "hrv"].mean(), 0) if "hrv" in D else "-"] for l_ in cb.cat.categories if (cb == l_).any()])
        if "nap_n" in D:
            nf = F.get("naps", {}); P(f"- Naps: {int(D['nap_n'].sum())} recorded" + (f", average {f(nf['mean_min'], 0)} min" if nf.get("mean_min") else "")
                                      + (f"; {nf['early_morning']} started between 03:00 and 09:00 (early-morning sleep, e.g. after Fajr), {nf['count'] - nf['early_morning']} at other times" if nf.get("count") else ""))

    # ---------- 10. strain and workouts
    if "strain" in D:
        H("10. Effort (Strain), training load and workouts")
        if "recovery" in D:
            nr, nh = nxt(D["recovery"]), (nxt(D["hrv"]) if "hrv" in D else None)
            T(["Day Strain band", "Days", "Avg strain", "NEXT-morning Recovery", "NEXT-morning HRV"], [[c_, int((D["strain_cat"] == c_).sum()),
              f(D.loc[D["strain_cat"] == c_, "strain"].mean()), f(nr[D["strain_cat"] == c_].mean(), 0), f(nh[D["strain_cat"] == c_].mean(), 0) if nh is not None else "-"]
              for c_ in ["light", "moderate", "high", "all out"] if (D["strain_cat"] == c_).any()])
            ct = pd.crosstab(D["zone"], D["strain_cat"]); T(["Morning zone \\ Day strain"] + list(map(str, ct.columns)), [[str(i)] + list(map(int, ct.loc[i])) for i in ct.index])
            pushed = D[(D["recovery"] < 34) & (D["strain"] >= 14)]; F["pushed_on_red"] = len(pushed)
            P(f"- Hard days (strain >= 14) on a RED morning: {len(pushed)}" + (f" ({', '.join(str(d.date()) for d in pushed['day'])})" if len(pushed) else ""))
            P(f"- GREEN mornings kept light (strain < 10): {int(((D['recovery'] >= 67) & (D['strain'] < 10)).sum())} of {int((D['recovery'] >= 67).sum())}")
        acwr = D["strain"].rolling(7, min_periods=5).mean() / D["strain"].rolling(28, min_periods=20).mean(); sp_ = acwr >= 1.3
        P(f"- Load jumps (7-day average strain >= 1.3x the 28-day average): {int(sp_.sum())} days" + (f", latest {D.loc[sp_, 'day'].max().date()}" if sp_.any() else "")
          + f". Current ratio {f(acwr.iloc[-1], 2)}."); F["load_ratio_now"] = round(float(acwr.iloc[-1]), 2) if fin(acwr.iloc[-1]) else None
    if W is not None and len(W):
        P("\n**Workouts by activity**"); rows = []
        for act, gg in sorted(W.groupby("act"), key=lambda x: -len(x[1])) if "act" in W else []:
            zt = [gg[f"z{i}_min"].sum() for i in range(1, 6)] if "z1_min" in gg else None; zd = gg["dur"].sum() if zt else 0
            gd = gg[(gg["gps"] == 1) & (gg["dist"] > 0)] if {"gps", "dist"} <= set(gg) else gg[gg["dist"] > 0] if "dist" in gg else gg.iloc[:0]
            km = gd["dist"].sum() / 1000 if len(gd) else np.nan
            rows.append([act, len(gg), f(gg["dur"].sum() / 60) if "dur" in gg else "-", f(gg["dur"].mean(), 0) if "dur" in gg else "-",
                         f(gg["astrain"].mean()) if "astrain" in gg else "-", f(gg["avg_hr"].mean(), 0) if "avg_hr" in gg else "-", f(gg["max_hr"].max(), 0) if "max_hr" in gg else "-",
                         (" / ".join(f(100 * z_ / zd, 0) for z_ in zt) + f" (below Z1 {f(100 - 100 * sum(zt) / zd, 0)})") if zt and zd > 0 else "-",
                         f(km) if fin(km) else "-", f(gd["dur"].sum() / km) if fin(km) and km > 0 and "dur" in gd else "-", f(gg["energy"].mean(), 0) if "energy" in gg else "-",
                         hm(clock(gg["w_start"]).median()) if "w_start" in gg else "-",
                         (lambda v: f"{v.index[0]} ({pct(v.iloc[0], v.sum())})")(gg["w_start"].dt.dayofweek.map(lambda i: DAYS[i]).value_counts()) if "w_start" in gg and gg["w_start"].notna().any() else "-",
                         f(gg["alt_gain"].sum(), 0) if "alt_gain" in gg and gg["alt_gain"].notna().any() else "-"])
        T(["Activity", "Count", "Total h", "Avg min", "Avg strain", "Avg HR", "Peak HR", "% of time in HR zones 1/2/3/4/5", "GPS km", "min/km (GPS)", "Avg kcal",
           "Usual start", "Main weekday", "Altitude gain m"], rows)
        P(f"- {f(len(W) / max(len(D) / 7, 1))} workouts per week of wear (days without data not counted)" + (f"; last 28 days: {int((W['w_start'] >= last - pd.Timedelta(days=28)).sum())}" if "w_start" in W else ""))
        if "w_start" in W:
            tod = pd.cut(W["w_start"].dt.hour, [-1, 11, 16, 20, 24], labels=["morning", "afternoon", "evening", "night (after 9pm)"])
            P("- Time of day: " + ", ".join(f"{k} {int(v)}" for k, v in tod.value_counts().reindex(tod.cat.categories).items()))
        if "recovery" in D and "wk_n" in D:
            nr = nxt(D["recovery"]); rest = nr[D["wk_n"] == 0]; rows = [["Rest day (no workout)", int(rest.notna().sum()), f(rest.mean(), 0), "-"]]
            for c, nm in [(c, f"Day with {c[4:]}") for c in D.columns if c.startswith("act_")] + ([("wk_late", "Workout ended < 3 h before sleep")] if "wk_late" in D else []):
                v = nr[D[c] == 1]
                if v.notna().sum() >= 5: rows.append([nm, int(v.notna().sum()), f(v.mean(), 0), sg(v.mean() - rest.mean())])
            T(["Day type", "Days", "NEXT-morning Recovery", "vs rest days"], rows)

    # ---------- 11. week rhythm, Ramadan, travel
    H("11. Week rhythm, Ramadan and travel")
    P("Day = the day you woke up, so the 'Fri' row is Thursday night's sleep and Friday's effort. Bedtime = median.")
    cols = [k for k in ["recovery", "hrv", "rhr", "asleep_h", "bed_h", "strain"] if k in D]
    T(["Day"] + [lab(k) for k in cols] + ["n"], [[d_ + (" (weekend)" if d_ in wkend else "")] + [fmt(k, agk(k, D.loc[D["weekday"] == d_, k])) for k in cols]
      + [int((D["weekday"] == d_).sum())] for d_ in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] if (D["weekday"] == d_).any()])
    if D["ramadan"].sum() >= 7:
        P(f"Ramadan days in data: {int(D['ramadan'].sum())} (dates approximate, +/- 1 day)")
        T(["Metric", "Ramadan", "Rest of year"], [[lab(k), fmt(k, agk(k, D.loc[D["ramadan"] == 1, k])), fmt(k, agk(k, D.loc[D["ramadan"] == 0, k]))]
          for k in ["recovery", "hrv", "rhr", "asleep_h", "bed_h", "wake_h", "strain", "sleep_perf"] if k in D])
    else:
        P("Ramadan: fewer than 7 Ramadan days in this data - not compared.")
    if D.get("tz_change", pd.Series(dtype=float)).sum():
        P("Time-zone changes (travel):")
        rows = []
        for i in D.index[D["tz_change"] == 1]:
            bf, af = D.loc[max(0, i - 14):i - 1], D.loc[i:i + 2]
            rows.append([str(D.loc[i, "day"].date()), f"{D.loc[i - 1, 'tz_raw']} -> {D.loc[i, 'tz_raw']}"] +
                        [f(w_[k].mean(), 0) if k in D else "-" for k in ("recovery", "hrv") for w_ in (bf, af)])
        T(["Day", "Change", "Recovery, 14 days before this change", "Recovery, first 3 days", "HRV, 14 days before", "HRV, first 3 days"], rows)

    # ---------- 12. unusual days
    H("12. Unusual days and body-stress signals")
    jb = [q for q in J.columns if J[q].dropna().isin([0, 1]).all() and J[q].sum() > 0]
    JR = J[jb].rolling(30, min_periods=10).mean().shift(1).fillna(J[jb].mean()) if jb else J[jb]  # your usual 'yes' share in the 30 cycles before
    unusual = lambda i: [q for q in jb if i > 0 and J.loc[i - 1, q] == 1 and JR.loc[i - 1, q] <= .5]
    sig = pd.DataFrame(index=D.index)
    for k, s_, thr in [("hrv", -1, 1.5), ("rhr", 1, 1.5), ("resp", 1, 2.0), ("skin_temp", 1, 2.0), ("spo2", -1, 2.0)]:
        if k in D and D[k].notna().sum() >= 20:
            med = D[k].rolling(30, min_periods=10).median().shift(1); mad = (D[k] - med).abs().rolling(30, min_periods=10).median().shift(1) * 1.4826
            z = (D[k] - med) / mad.replace(0, np.nan); sig[k] = (s_ * z >= thr).astype(float).where(z.notna())
    if sig.shape[1]:
        D["stress_signals"] = sig.sum(axis=1, min_count=1); eps, cur = [], []
        for i in D.index[D["stress_signals"] >= 2]:
            if cur and i - cur[-1] > 2: eps.append(cur); cur = []
            cur.append(i)
        eps += [cur] if cur else []; rows = []
        for ep in eps:
            i0 = ep[0]; ctx = ([f"strain day before {f(D.loc[i0 - 1, 'strain'])}"] if "strain" in D and i0 else []) + ([f"slept {f(D.loc[i0, 'asleep_h'])} h"] if "asleep_h" in D else [])
            ctx += ["travel"] if "tz_change" in D and D.loc[max(0, i0 - 2):i0, "tz_change"].sum() else []
            ctx += ["Ramadan"] if D.loc[i0, "ramadan"] == 1 else []
            yes_ = unusual(i0); ctx += ["journal yes: " + "; ".join(yes_[:6])] if yes_ else []
            rows.append([f"{D.loc[ep[0], 'day'].date()} -> {D.loc[ep[-1], 'day'].date()}", len(ep), ", ".join(k for k in sig.columns if sig.loc[ep, k].max() == 1),
                         f(D.loc[ep, "recovery"].mean(), 0) if "recovery" in D else "-", " | ".join(ctx)])
        P("Signals vs your own trailing 30-day normal: HRV well below, resting HR well above, breathing rate / skin temp clearly up, blood oxygen clearly down. "
          "Two or more at once = body under stress (illness, travel, short sleep, heavy load).")
        P("Journal answers in Context are only the unusual ones: 'yes' to a question you had answered 'yes' on half or fewer of the 30 days before.")
        T(["Period", "Flagged days", "Signals", "Recovery", "Context"], rows[-25:]); F["stress_episodes"] = len(rows)
    if "recovery" in D:
        ctx_row = lambda i: [str(D.loc[i, "day"].date()), f(D.loc[i, "recovery"], 0), f(D.loc[i, "hrv"], 0) if "hrv" in D else "-", f(D.loc[i, "asleep_h"]) if "asleep_h" in D else "-",
                             hm(D.loc[i, "bed_h"]) if "bed_h" in D else "-", f(D.loc[i - 1, "strain"]) if "strain" in D and i else "-",
                             "; ".join(unusual(i)[:4])]
        hd = ["Day", "Recovery", "HRV", "Slept h", "Bedtime", "Strain day before", "Unusual journal 'yes' (day before)"]
        P("Best mornings (top 5, ties included):"); T(hd, [ctx_row(i) for i in D["recovery"].nlargest(5, keep="all").index])
        P("Worst mornings (bottom 5, ties included):"); T(hd, [ctx_row(i) for i in D["recovery"].nsmallest(5, keep="all").index])
    if "spo2" in D and (D["spo2"] < 90).sum():
        lo_ = D[D["spo2"] < 90]
        P(f"- Nights with blood oxygen under 90%: {int(len(lo_))} of {int(D['spo2'].notna().sum())} (" + ", ".join(f"{d_.date()} {f(v_)}%" for d_, v_ in zip(lo_["day"], lo_["spo2"]))
          + "). Single low readings are often a loose strap; worth mentioning to a doctor if it keeps happening or comes with snoring, gasping or daytime sleepiness.")
        F["spo2_below_90"] = [str(d_.date()) for d_ in lo_["day"]]
    if "rhr" in D and D["rhr"].notna().sum() > 40 and ((D["rhr"].rolling(7, min_periods=5).mean() - D["rhr"].rolling(60, min_periods=30).median().shift(7)).iloc[-14:] >= 5).any():
        P("- Resting HR has stayed >= 5 bpm above your usual level recently. If you also feel unwell, check with a doctor.")

    # ---------- 13. every other column
    H("13. Every other column (profiled so nothing is ignored)")
    rows = []
    for (k, c), s in GEN.items():
        if pd.api.types.is_numeric_dtype(s): ex = f"mean {f(s.mean(), 2)}, range {f(s.min(), 2)} - {f(s.max(), 2)}"
        elif pd.api.types.is_datetime64_any_dtype(s): ex = f"{s.min()} -> {s.max()}"
        else: vc = s.dropna().astype(str).value_counts(); ex = f"{len(vc)} distinct; top: " + ", ".join(f"{a_} ({b_})" for a_, b_ in vc.head(5).items())
        rows.append([k, c, int(pd.Series(s).notna().sum()), ex])
    T(["File", "Column", "Values", "Summary"], rows) if rows else P("None - every column in your files already has a defined use in the sections above (section 15 lists them all).")

    # ---------- 14. self-check
    H("14. Self-check"); chk = []
    cyc = TB["cycles"][0]; m = match(list(cyc.columns), KEYS["cycles"]); st = dt(cyc[m["start"]]) if "start" in m else None
    for k in ["recovery", "hrv", "rhr", "strain"]:
        if k in m and k in D and st is not None:
            lo, hi = OK_RANGE[k]; raw = num(cyc[m[k]]); raw = raw[(raw >= lo) & (raw <= hi)]
            rv = pd.Series(raw.values, index=st[raw.index].values).groupby(level=0).last()
            rv = rv.drop([OPEN] + sorted(PART), errors="ignore").mean() if k in DAYTOT else rv.mean()
            chk.append([f"mean {k}: raw file vs analysis", f(rv, 3), f(D[k].mean(), 3), "PASS" if abs(rv - D[k].mean()) < 1e-6 else "CHECK"])
    nc = sum(d.shape[1] for d, _ in TB.values()) + sum(d.shape[1] for _, d in tabs["unknown"]); nu = sum(len(v) for v in COV.values())
    chk.append(["columns with an assigned use", nc, nu, "PASS" if nc == nu else "CHECK"])
    T(["Check", "Expected", "Got", "Result"], chk); F["self_check"] = [c[-1] for c in chk]
    finish(out, D, a, J, GEN)


def finish(out, D, a, J=None, GEN=None):
    cov = [dict(file=k, column=c, usage=u) for k, d in COV.items() for c, u in d.items()]
    pd.DataFrame(cov).to_csv(os.path.join(out, "coverage.csv"), index=False)
    H("15. Column coverage (every column -> how it was used)"); T(["File type", "Column", "Used for"], [[r["file"], r["column"], r["usage"]] for r in cov])
    if len(D):
        E = D.drop(columns=[c for c in D.columns if c.startswith("_")]); E["prev_cycle_ok"] = D["_ok"]
        for q in (J.columns if J is not None else []): E[f"journal: {q}"] = J[q]
        for (k, c), s in (GEN or {}).items():
            if k == "cycles" and pd.api.types.is_numeric_dtype(s): E[f"extra: {c}"] = D["_row"].map(s)
        E.to_csv(os.path.join(out, "daily_enriched.csv"), index=False)
        if plt is not None and not a.no_charts:
            try:
                charts(D, os.path.join(out, "charts"))
            except Exception as e:
                print("chart warning:", e)
    with open(os.path.join(out, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write("# WHOOP analysis - full numbers\n" + "\n".join(R) + "\n")
    with open(os.path.join(out, "findings.json"), "w", encoding="utf-8") as fh:
        json.dump(F, fh, ensure_ascii=False, indent=1, default=str)
    print(f"Done: {out}/summary.md, {out}/coverage.csv, {out}/findings.json, charts in {out}/charts/")


def charts(D, cd):
    key = []
    def L(s):
        s = str(s)
        if not HAS_AR(s): return s
        if AR_TXT: return AR_TXT(s)
        key.append(s); return re.sub(r"[-ۿً-ْ]+", "", s).strip(" :?") + f" [A{len(key)}]"
    def save(fig, nm):
        fig.tight_layout(); fig.savefig(os.path.join(cd, nm), dpi=130); plt.close(fig)
    import matplotlib.dates as mdates
    x = D["day"]; C = D.drop_duplicates("day", keep="last").set_index("day").asfreq("D"); cx = C.index  # calendar days: lines break where data is missing
    roll = lambda k, w=7: C[k].rolling(w, min_periods=3).mean()
    EP = [(g_["day"].min(), g_["day"].max()) for _, g_ in D.groupby("era")] if "era" in D else [(x.min(), x.max())]
    def ts(rows=1, h=4):  # one panel per wear period (gaps of 30+ days are cut out), shared y axis
        fig, axs = plt.subplots(rows, len(EP), figsize=(11, h * rows), sharey="row", squeeze=False,
                                gridspec_kw=dict(width_ratios=[max((b_ - a_).days, 30) for a_, b_ in EP], wspace=.04))
        for rr in range(rows):
            for j, (a_, b_) in enumerate(EP):
                ax = axs[rr][j]; ax.set_xlim(a_ - pd.Timedelta(days=2), b_ + pd.Timedelta(days=2)); loc = mdates.AutoDateLocator(maxticks=max(3, 7 if len(EP) == 1 else 4))
                ax.xaxis.set_major_locator(loc); ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))
                if j: ax.tick_params(left=False); ax.spines["left"].set_linestyle((0, (2, 3)))
                if j < len(EP) - 1: ax.spines["right"].set_linestyle((0, (2, 3)))
        return fig, axs
    def note(fig):
        if len(EP) > 1: fig.text(.5, .005, "panels = wear periods; gaps of 30+ days without data are cut out", ha="center", fontsize=8, color="#666")
    def c1():
        if "recovery" in D:
            fig, axs = ts(); cl = D["recovery"].map(lambda v: "#d64545" if v < 34 else "#e0b000" if v < 67 else "#2e9e5b")
            for ax in axs[0]:
                ax.scatter(x, D["recovery"], s=12, c=cl); ax.plot(cx, roll("recovery"), c="k", lw=1.5, label="7-day average")
                ax.axhline(67, c="#2e9e5b", ls=":"); ax.axhline(34, c="#d64545", ls=":"); ax.set_ylim(0, 100)
            axs[0][0].legend(loc="lower left", fontsize=8); fig.suptitle("Recovery % (dots = mornings, line = 7-day average)"); note(fig); save(fig, "01_recovery.png")
    def c2():
        ks = [k for k in ["hrv", "rhr"] if k in D]
        if ks:
            fig, axs = ts(len(ks), 3.2)
            for rr, k in enumerate(ks):
                for ax in axs[rr]:
                    ax.plot(cx, C[k], c="#9bb7d4", lw=.8); ax.plot(cx, roll(k), c="#1f4e79", lw=1.8, label="7-day")
                    ax.plot(cx, C[k].rolling(30, min_periods=10).median(), c="#999", ls="--", label="30-day normal")
                axs[rr][0].set_title(lab(k), loc="left"); axs[rr][0].legend(fontsize=8)
            note(fig); save(fig, "02_hrv_rhr.png")
    def c3():
        if "asleep_h" in D:
            fig, axs = ts()
            for ax in axs[0]:
                ax.bar(x, D["asleep_h"], color="#c9d7ea", width=1); ax.plot(cx, roll("asleep_h"), c="#1f4e79", lw=1.8, label="hours asleep (7-day)")
                if "need_h" in D: ax.plot(cx, roll("need_h"), c="#d64545", lw=1.5, ls="--", label="sleep need (7-day)")
            axs[0][0].legend(fontsize=8); fig.suptitle("Sleep: hours asleep vs need"); note(fig); save(fig, "03_sleep_vs_need.png")
    def c5():
        if "bed_h" in D:
            fig, axs = ts(); we = D["weekend"] == 1
            lo = math.floor(min(D["bed_h"].min(), 0)) - 1; hi = math.ceil(max(D["bed_h"].max(), D["wake_h"].max() if "wake_h" in D else 0)) + 1
            for ax in axs[0]:
                ax.scatter(x[~we], D["bed_h"][~we], s=10, c="#1f4e79", label="bedtime (work days)"); ax.scatter(x[we], D["bed_h"][we], s=14, c="#d64545", label="bedtime (weekend)")
                if "wake_h" in D: ax.scatter(x, D["wake_h"], s=8, c="#e0b000", label="wake time")
            tk = list(range(lo, hi + 1, 3 if hi - lo > 16 else 2)); axs[0][0].set_yticks(tk); axs[0][0].set_yticklabels([hm(h) for h in tk]); axs[0][0].set_ylim(hi, lo)
            axs[0][0].legend(fontsize=8); fig.suptitle("Bedtime and wake time (top = earlier in the evening)"); note(fig); save(fig, "05_bed_wake_times.png")
    def c6():
        if {"strain", "recovery"} <= set(D):
            nr = D["recovery"].shift(-1).where(D["_ok"].shift(-1, fill_value=False)); fig, ax = plt.subplots(figsize=(7, 5))
            ax.scatter(D["strain"], nr, s=12, alpha=.6, c="#1f4e79"); gb = pd.DataFrame({"s": D["strain"], "r": nr}).groupby(D["strain_cat"], observed=True).mean()
            ax.plot(gb["s"], gb["r"], "o-", c="#d64545", lw=2, label="band average (light / moderate / high / all out)")
            ax.set_xlabel("Day Strain"); ax.set_ylabel("Next-morning Recovery %"); ax.set_title("Does a harder day lower the next morning?"); ax.legend(); save(fig, "06_strain_vs_next_recovery.png")
    def c7():
        if "recovery" in D:
            od = [d for d in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] if (D["weekday"] == d).any()]; fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(od, D.groupby("weekday")["recovery"].mean().reindex(od).values, color=["#d64545" if D.loc[D["weekday"] == d, "weekend"].max() == 1 else "#1f4e79" for d in od])
            if "asleep_h" in D:
                a2 = ax.twinx(); hv = D.groupby("weekday")["asleep_h"].mean().reindex(od).values; a2.plot(od, hv, "o-", c="#e0b000")
                a2.set_ylim(0, np.nanmax(hv) * 1.3); a2.set_ylabel("hours asleep (yellow line)")
            ax.set_ylabel("Recovery %"); ax.set_title("Week rhythm (red = weekend)"); save(fig, "07_week_rhythm.png")
    def c8():
        rows = [r_ for r_ in F.get("drivers", {}).get("recovery", []) if r_["verdict"] in ("clear", "possible")][:14]
        if rows:
            fig, ax = plt.subplots(figsize=(9, .45 * len(rows) + 1.5)); v = [r_["rho"] for r_ in rows][::-1]
            ax.barh([L(r_["feature"][:60]) for r_ in rows][::-1], v, color=["#2e9e5b" if a_ > 0 else "#d64545" for a_ in v]); ax.axvline(0, c="k", lw=.8)
            ax.set_title("Strongest links with Recovery (green = goes with higher)"); save(fig, "08_links_recovery.png")
    def c9():
        jr = sorted(F.get("journal_all", []), key=lambda r_: r_["diff"])
        if jr:
            fig, ax = plt.subplots(figsize=(9, .45 * len(jr) + 1.8)); yy = list(range(len(jr)))
            ax.barh(yy, [r_["diff"] for r_ in jr], xerr=[[r_["diff"] - r_["lo"] for r_ in jr], [r_["hi"] - r_["diff"] for r_ in jr]],
                    color=["#2e9e5b" if r_["diff"] > 0 else "#d64545" for r_ in jr], alpha=.6, capsize=3, label="all days (bar = 95% range)")
            sm_ = [r_.get("same_month", {}).get("recovery") for r_ in jr]
            if any(v is not None for v in sm_):
                ax.scatter([v if v is not None else np.nan for v in sm_], yy, marker="D", c="k", s=30, zorder=3, label="same month (adjusted)")
            mk_ = lambda t_, m_: (f"{m_}  {L(t_)}" if HAS_AR(t_) else f"{L(t_)}  {m_}") if m_ else L(t_)  # marker next to the axis for RTL and LTR labels
            ax.set_yticks(yy); ax.set_yticklabels([mk_(r_["question"][:55], {"clear": "**", "possible": "*", "between periods only": "~"}.get(r_["verdict"], "")) for r_ in jr])
            ax.axvline(0, c="k", lw=.8); ax.legend(fontsize=8, loc="lower right")
            ax.set_title("Journal: next-morning Recovery, yes minus no\n(** clear, * possible, ~ between periods only)", fontsize=10); save(fig, "09_journal_effects.png")
    for fn in (c1, c2, c3, c5, c6, c7, c8, c9):
        try:
            fn()
        except Exception as e:
            print('chart warning:', fn.__name__, e); plt.close('all')
    if key:
        P("\nChart label key (Arabic text could not be drawn; install arabic-reshaper and python-bidi to draw it): " + "; ".join(f"A{i + 1} = {t}" for i, t in enumerate(key)))

if __name__ == "__main__":
    main()
```

## Insights code — `insights.py`

```python
#!/usr/bin/env python3
# whoop-full-analysis insights v1.2
# Patterns the WHOOP app does not spell out, from the engine's daily table: python3 insights.py --out whoop_out
# Reads whoop_out/daily_enriched.csv (+ findings.json); writes insights.md, insights.json, profile.json and profile.html (the user's normal, for the morning check)
# After editing profile.json (name, plan): python3 insights.py --out whoop_out --page  rebuilds profile.html only
import argparse, html, json, math, os, re
import numpy as np, pandas as pd
try:
    from scipy import stats as SS
except Exception:
    SS = None

fin = lambda x: isinstance(x, (int, float, np.integer, np.floating)) and bool(np.isfinite(x))
f = lambda x, d=1: f"{x:,.{d}f}" if fin(x) else "-"
sg = lambda x, d=1: f"{x:+,.{d}f}" if fin(x) else "-"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
GOOD = dict(recovery=1, hrv=1, rhr=-1, asleep_h=1, sleep_perf=1, strain=0, resp=0)
R, OUT = [], {}


def H(t): R.append(f"\n## {t}\n")
def P(t=""): R.append(t)
def T(h, rows):
    R.extend(["", "| " + " | ".join(h) + " |", "|" + "---|" * len(h)] + ["| " + " | ".join(map(str, r)) + " |" for r in rows] + [""]) if rows else P("_(no data)_")
def hm(h):
    if not fin(h):
        return "-"
    t = int(round(h * 60)) % 1440
    return f"{t // 60:02d}:{t % 60:02d}"
def num(x):
    return None if not fin(x) else round(float(x), 3)


def welch(a, b):  # mean of a minus mean of b, Welch p, verdict (strict: several patterns are tested here)
    a, b = pd.Series(a, dtype=float).dropna(), pd.Series(b, dtype=float).dropna()
    if len(a) < 2 or len(b) < 2:
        return np.nan, np.nan, "not enough data"
    d = a.mean() - b.mean(); se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    p = float(SS.ttest_ind(a, b, equal_var=False).pvalue) if SS is not None else (math.erfc(abs(d / se) / math.sqrt(2)) if se > 0 else np.nan)
    if min(len(a), len(b)) < 8:
        return d, p, "not enough data"
    return d, p, "clear" if fin(p) and p < .01 and min(len(a), len(b)) >= 15 else "possible" if fin(p) and p < .05 else "no clear difference"


def cmp(y, ga, gb, mon):  # y in group a vs group b: whole period, then inside the same month (months that have both groups)
    ga, gb = ga.fillna(False).astype(bool), gb.fillna(False).astype(bool)
    a, b = y[ga & y.notna()], y[gb & y.notna()]; d, p, v = welch(a, b)
    o = dict(n_a=int(len(a)), n_b=int(len(b)), mean_a=a.mean(), mean_b=b.mean(), diff=d, p=p, verdict=v, same_month_diff=np.nan, same_month_p=np.nan, check="n/a")
    k = (ga | gb) & y.notna() & mon.notna()
    s = pd.DataFrame({"y": y[k], "a": ga[k], "m": mon[k]})
    s = s[s.groupby("m")["a"].transform(lambda z: bool(z.any() and (~z).any()))]
    if len(s) and s["a"].sum() >= 8 and (~s["a"]).sum() >= 8 and s["m"].nunique() >= 2:
        s["r"] = s["y"] - s.groupby("m")["y"].transform("mean"); d2, p2, _ = welch(s.loc[s["a"], "r"], s.loc[~s["a"], "r"])
        o.update(same_month_diff=d2, same_month_p=p2)
        if v in ("clear", "possible"):
            same = fin(d2) and np.sign(d2) == np.sign(d)
            o["check"] = "confirmed" if same and p2 < .05 else "partly" if same and p2 < .2 else "not confirmed"
            o["verdict"] = v if o["check"] == "confirmed" else "possible" if o["check"] == "partly" else "between periods only"
    return o


def say(o, unit="", d=0):
    return (f"{f(o['mean_a'], d)}{unit} (n={o['n_a']}) vs {f(o['mean_b'], d)}{unit} (n={o['n_b']}) -> {sg(o['diff'], d)}{unit}; p {f(o['p'], 3)}; "
            f"same month {sg(o['same_month_diff'], d)}{unit} (p {f(o['same_month_p'], 3)}); verdict: {o['verdict']}")


VW = {"clear": "علاقة واضحة", "possible": "إشارة محتملة", "between periods only": "تظهر بين الفترات فقط"}
NAMES = dict(recovery=("الريكفري", "%", 0), hrv=("HRV", " ms", 0), rhr=("نبض الراحة", "", 0), asleep_h=("ساعات النوم", " ساعة", 1),
             sleep_perf=("أداء النوم", "%", 0), strain=("مجهود اليوم", "", 1), resp=("معدل التنفس", "", 1))
PCSS = ("body{margin:0;background:#f9f9f7;color:#0b0b0b;font:16px/1.7 'IBM Plex Sans Arabic','Noto Sans Arabic',Tahoma,sans-serif}"
        "main{max-width:640px;margin:0 auto;padding:24px 18px}h1{font-size:24px;margin:0}h2{font-size:18px;margin:22px 0 6px}"
        ".sub,.foot{color:#52514e;font-size:14px}table{width:100%;border-collapse:collapse;margin-top:14px;background:#fcfcfb}"
        "th,td{padding:8px 10px;border-bottom:1px solid #e7e6e2;text-align:start}th{font-size:13px;color:#52514e}"
        "td:not(:first-child){font-variant-numeric:tabular-nums;white-space:nowrap}ul,ol{padding-inline-start:20px}li{margin:4px 0}")


NAMES_EN = dict(recovery=("Recovery", "%", 0), hrv=("HRV", " ms", 0), rhr=("Resting HR", " bpm", 0), asleep_h=("Hours asleep", " h", 1),
                sleep_perf=("Sleep performance", "%", 0), strain=("Day Strain", "", 1), resp=("Respiratory rate", "", 1))
VW_EN = {"clear": "clear link", "possible": "possible signal", "between periods only": "between periods only"}


def page_en(prof, path):  # the same page in English, when profile.json has "lang": "en"
    e = lambda s: html.escape(str(s), quote=False); v = lambda x, d, u: f(x, d) + u if fin(x) else "-"
    N = prof.get("normal", {}); L3 = prof.get("last30", {}); vw = lambda k: VW_EN.get(k, k)
    rows = "".join(f"<tr><td>{n}</td><td>{v(N[k]['mean'], d, u)}</td><td>{f(N[k]['p25'], d)} to {v(N[k]['p75'], d, u)}</td><td>{v(L3.get(k), d, u)}</td></tr>"
                   for k, (n, u, d) in NAMES_EN.items() if k in N)
    li, b = [], prof.get("bedtime_median") or {}
    if b:
        li.append(f"Usual sleep: work nights {b.get('work')}, weekends {b.get('weekend')}, wake {b.get('wake_work')}")
    s = prof.get("recovery_per_extra_hour") or {}
    if fin(s.get("same_month")):
        li.append(f"Each extra hour of sleep is about {sg(s['same_month'], 0)} Recovery points ({vw(s.get('verdict'))})")
    if prof.get("sleep_sweet_spot"):
        li.append(f"Most of the benefit of sleep is reached at {prof['sleep_sweet_spot']['band']} hours")
    c = prof.get("carry_over") or {}
    if fin(c.get("recovery")):
        li.append(f"A night under 6 hours costs the second morning about {sg(c['recovery'], 0)} points ({vw(c.get('verdict'))})")
    bb = prof.get("bounce_back") or {}
    if fin(bb.get("median_days")):
        li.append(f"A red morning usually clears after {f(bb['median_days'], 0)} day(s)")
    li += [f"{h['question']}: {sg(h['recovery_same_month'], 0)} Recovery points the next morning (inside the same month, {vw(h['verdict'])})"
           for h in prof.get("habits", []) if fin(h.get("recovery_same_month"))]
    plan = "".join(f"<li>{e(x)}</li>" for x in prof.get("plan", []))
    js = json.dumps(prof, ensure_ascii=False, default=str).replace("</", "<\\/")
    title = "WHOOP - My baseline" + (f" ({prof['name']})" if prof.get("name") else "")
    doc = (f'<!DOCTYPE html><html lang="en" dir="ltr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>'
           f'<script type="application/json" id="whoop-profile">{js}</script><style>{PCSS}</style></head><body><main>'
           f'<h1>{e(title)}</h1><p class="sub">Your averages in the latest wear period ({e(prof.get("latest_period"))}). The morning check compares your day with them.</p>'
           f'<table><thead><tr><th>Metric</th><th>Your average</th><th>Your usual range</th><th>Last 30 days</th></tr></thead><tbody>{rows}</tbody></table>'
           f'<h2>Your patterns</h2><ul>{"".join(f"<li>{e(x)}</li>" for x in li)}</ul>' + (f"<h2>Your plan</h2><ol>{plan}</ol>" if plan else "")
           + f'<p class="foot">Computed from your data ({e(prof.get("made_from"))}). Updated with every new full analysis.</p></main></body></html>')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(doc)


def page(prof, path):  # small private page the morning check reads in later chats (the JSON sits in <script id="whoop-profile">)
    e = lambda s: html.escape(str(s), quote=False); v = lambda x, d, u: f(x, d) + u if fin(x) else "-"
    if str(prof.get("lang", "ar")).lower().startswith("en"):
        return page_en(prof, path)
    N, L3 = prof.get("normal", {}), prof.get("last30", {})
    rows = "".join(f"<tr><td>{n}</td><td>{v(N[k]['mean'], d, u)}</td><td>{f(N[k]['p25'], d)} – {v(N[k]['p75'], d, u)}</td><td>{v(L3.get(k), d, u)}</td></tr>"
                   for k, (n, u, d) in NAMES.items() if k in N)
    li, b = [], prof.get("bedtime_median") or {}
    if b:
        li.append(f"نومك المعتاد: ليالي الدوام {b.get('work')}، الويكند {b.get('weekend')}، والصحيان {b.get('wake_work')}")
    s = prof.get("recovery_per_extra_hour") or {}
    if fin(s.get("same_month")):
        li.append(f"كل ساعة نوم زيادة ≈ {sg(s['same_month'], 0)} نقاط ريكفري ({VW.get(s.get('verdict'), s.get('verdict'))})")
    if prof.get("sleep_sweet_spot"):
        li.append(f"أغلب فايدة النوم توصلها عند {prof['sleep_sweet_spot']['band']} ساعات")
    c = prof.get("carry_over") or {}
    if fin(c.get("recovery")):
        li.append(f"ليلة أقل من 6 ساعات تنقص الصبح الثاني ≈ {sg(c['recovery'], 0)} نقاط ({VW.get(c.get('verdict'), c.get('verdict'))})")
    bb = prof.get("bounce_back") or {}
    if fin(bb.get("median_days")):
        li.append(f"الصبح الأحمر يعدّي عادة بعد {f(bb['median_days'], 0)} يوم")
    li += [f"«{h['question']}»: {sg(h['recovery_same_month'], 0)} نقاط ريكفري الصبح اللي بعده (داخل نفس الشهر، {VW.get(h['verdict'], h['verdict'])})"
           for h in prof.get("habits", []) if fin(h.get("recovery_same_month"))]
    iso = lambda t: re.sub(r"(?<![\w.])([+\-−]\d[\d.,:]*)", r'<bdi dir="ltr">\1</bdi>', e(t))  # signed numbers read left to right
    per = lambda s: ("من " + str(s).replace(" -> ", " إلى ")) if s else ""
    plan = "".join(f"<li>{iso(x)}</li>" for x in prof.get("plan", []))
    js = json.dumps(prof, ensure_ascii=False, default=str).replace("</", "<\\/")
    title = "WHOOP — ملفي الأساسي" + (f" ({prof['name']})" if prof.get("name") else "")
    doc = (f'<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>'
           f'<script type="application/json" id="whoop-profile">{js}</script><style>{PCSS}</style></head><body><main>'
           f'<h1>{e(title)}</h1><p class="sub">معدلاتك في آخر فترة لبس ({e(per(prof.get("latest_period")))}). فحص الصباح يقارن يومك فيها.</p>'
           f'<table><thead><tr><th>المقياس</th><th>معدلك</th><th>المعتاد عندك</th><th>آخر 30 يوم</th></tr></thead><tbody>{rows}</tbody></table>'
           f'<h2>أنماطك</h2><ul>{"".join(f"<li>{iso(x)}</li>" for x in li)}</ul>' + (f"<h2>خطتك</h2><ol>{plan}</ol>" if plan else "")
           + f'<p class="foot">محسوب من بياناتك ({e(per(prof.get("made_from")))}). يتحدّث مع كل تحليل كامل جديد.</p></main></body></html>')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(doc)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="whoop_out"); ap.add_argument("--page", action="store_true"); a = ap.parse_args()
    if a.page:
        with open(os.path.join(a.out, "profile.json"), encoding="utf-8") as fh:
            page(json.load(fh), os.path.join(a.out, "profile.html"))
        return print(f"Done: {a.out}/profile.html")
    D = pd.read_csv(os.path.join(a.out, "daily_enriched.csv"), low_memory=False)
    for c in ("day", "start", "end", "onset", "wake"):
        if c in D:
            D[c] = pd.to_datetime(D[c], errors="coerce")
    D = D[D["day"].notna()].sort_values("start" if "start" in D else "day")
    F = {}
    fp = os.path.join(a.out, "findings.json")
    if os.path.exists(fp):
        with open(fp, encoding="utf-8") as fh:
            F = json.load(fh)
    if "era" not in D:
        D["era"] = 1
    C = D.drop_duplicates("day", keep="last").set_index("day").asfreq("D")  # one row per calendar day; empty rows = no data
    L = C.index.max(); mon = pd.Series(C.index.to_period("M").astype(str), index=C.index); le = C["era"] == C["era"].max()
    has = lambda k: k in C and C[k].notna().sum() >= 20
    R.append("# Patterns the WHOOP app does not spell out\n")
    P(f"Data: {D['day'].min().date()} -> {L.date()}, {len(D)} cycles. Every pattern below is computed from the engine's daily table; "
      "'same month' repeats the comparison inside each calendar month, so slow changes (routine, season, strap or app updates) cannot create it.")

    # ---------- 1. slow drift that a moving baseline hides
    H("1. Slow drift: your normal now vs 3 and 6 months ago")
    P("WHOOP judges each morning against your own recent weeks, so a slow slide moves your 'normal' with it. These are fixed windows instead.")
    rows, dr = [], {}
    for k, lab, dd in [("hrv", "HRV (ms)", 0), ("rhr", "Resting HR (bpm)", 0), ("recovery", "Recovery (%)", 0), ("asleep_h", "Hours asleep", 2)]:
        if not has(k):
            continue
        s = C[k]
        def win(lo, hi):
            v = s[(s.index >= L - pd.Timedelta(days=lo)) & (s.index <= L - pd.Timedelta(days=hi))]
            return v.mean() if v.notna().sum() >= 10 else np.nan
        now, m3, m6 = win(29, 0), win(119, 90), win(209, 180)
        rl = s.where(le).rolling(30, min_periods=15).mean(); g = GOOD.get(k, 0)
        best = (rl.max() if g >= 0 else rl.min()) if rl.notna().any() else np.nan
        bend = (rl.idxmax() if g >= 0 else rl.idxmin()) if rl.notna().any() else None
        slide = (best - now) * (1 if g >= 0 else -1) if fin(best) and fin(now) else np.nan
        dr[k] = dict(now=num(now), m3=num(m3), m6=num(m6), best30=num(best), best30_end=str(bend.date()) if bend is not None else None,
                     slide_from_best=num(slide), slide_pct=num(100 * slide / best) if fin(slide) and best else None)
        rows.append([lab, f(now, dd), f(m3, dd), f(m6, dd), f"{f(best, dd)} (30 days to {bend.date() if bend is not None else '-'})", sg(-slide if g >= 0 else slide, dd) if fin(slide) else "-"])
    T(["Metric", "Last 30 days", "3 months ago (30 days)", "6 months ago (30 days)", "Best 30 days in the latest wear period", "Now vs best"], rows)
    OUT["drift"] = dr

    sh = C["asleep_h"] if "asleep_h" in C else pd.Series(np.nan, index=C.index)
    rec = C["recovery"] if "recovery" in C else pd.Series(np.nan, index=C.index)
    hrv = C["hrv"] if "hrv" in C else pd.Series(np.nan, index=C.index)
    ok_next = C["prev_cycle_ok"].shift(-1).astype(str).str.lower().isin(["true", "1", "1.0"]) if "prev_cycle_ok" in C else pd.Series(True, index=C.index)

    # ---------- 2. carry-over of one short night
    if has("asleep_h") and has("recovery"):
        H("2. One short night costs you twice")
        P("Mornings after a normal night (6.5-8.5 h), split by the night before it: under 6 h vs 7 h or more. Same-morning effects are in the main summary; this is the second morning.")
        nn = sh.shift(-1).between(6.5, 8.5) & ok_next
        o = cmp(rec.shift(-1), (sh < 6) & nn, (sh >= 7) & nn, mon); o2 = cmp(hrv.shift(-1), (sh < 6) & nn, (sh >= 7) & nn, mon)
        P(f"- Recovery on the second morning: after a short night {say(o, '%')}")
        P(f"- HRV on the second morning: {say(o2, ' ms')}")
        OUT["carry_over"] = dict(recovery={k: (num(v) if not isinstance(v, str) else v) for k, v in o.items()}, hrv={k: (num(v) if not isinstance(v, str) else v) for k, v in o2.items()})

        # ---------- 3. short nights in a row
        H("3. Short nights in a row")
        short = sh < 6; run = short.groupby((~short).cumsum()).cumsum()
        rows, st = [], {}
        for lab_, m in [("7 h or more", sh >= 7), ("1st night under 6 h", run == 1), ("2nd in a row", run == 2), ("3rd or more in a row", run >= 3)]:
            v = rec[m & rec.notna()]
            if len(v) >= 5:
                rows.append([lab_, len(v), f(v.mean(), 0), f(hrv[m].mean(), 0)]); st[lab_] = dict(n=int(len(v)), recovery=num(v.mean()), hrv=num(hrv[m].mean()))
        T(["Night", "Mornings", "Recovery", "HRV"], rows); OUT["short_streaks"] = st

    # ---------- 4. bounce-back after a red morning
    if has("recovery"):
        H("4. How long a red morning takes to clear")
        med = rec[le].median(); starts = rec.index[(rec < 34) & ~(rec.shift(1) < 34)]; days_, nxt_red = [], 0
        for t in starts:
            nxt_red += int(fin(rec.get(t + pd.Timedelta(days=1), np.nan)) and rec.get(t + pd.Timedelta(days=1)) < 34)
            for j in range(1, 15):
                v = rec.get(t + pd.Timedelta(days=j), np.nan)
                if not fin(v):
                    break
                if v >= med:
                    days_.append(j); break
        P(f"- Red mornings that started a red spell: {len(starts)}; back to your usual level (latest-period median {f(med, 0)}%) after a median of "
          f"{f(np.median(days_), 0) if days_ else '-'} days (mean {f(np.mean(days_)) if days_ else '-'}, {len(days_)} spells with full data); "
          f"the next morning was red again in {nxt_red} of {len(starts)}.")
        OUT["bounce_back"] = dict(spells=int(len(starts)), measured=len(days_), median_days=num(np.median(days_)) if days_ else None,
                                  mean_days=num(np.mean(days_)) if days_ else None, next_also_red=nxt_red, usual=num(med))

    # ---------- 5. bedtime at the same hours of sleep
    if has("bed_h") and has("recovery"):
        H("5. Same hours of sleep, different bedtime")
        same = sh.between(6.5, 8.5) & (C["bed_h"] < 6) & (C["ramadan"] != 1 if "ramadan" in C else True)
        e_, l_ = same & (C["bed_h"] <= -0.5), same & (C["bed_h"] >= 0.5)
        o = cmp(rec, e_, l_, mon); o2 = cmp(hrv, e_, l_, mon)
        P(f"- Nights of 6.5-8.5 h (Ramadan and daytime sleep left out): asleep by 23:30 vs after 00:30. Hours asleep: {f(sh[e_].mean(), 2)} vs {f(sh[l_].mean(), 2)}")
        P(f"- Recovery: {say(o, '%')}"); P(f"- HRV: {say(o2, ' ms')}")
        OUT["bedtime_same_hours"] = dict(hours_early=num(sh[e_].mean()), hours_late=num(sh[l_].mean()), recovery={k: (num(v) if not isinstance(v, str) else v) for k, v in o.items()},
                                         hrv={k: (num(v) if not isinstance(v, str) else v) for k, v in o2.items()})

    # ---------- 6. late workouts
    if "wk_late" in C and "wk_n" in C and C["wk_n"].fillna(0).gt(0).sum() >= 16:
        H("6. Late workouts and the night after")
        wk = C["wk_n"].fillna(0) > 0; lt, er = wk & (C["wk_late"] == 1) & ok_next, wk & (C["wk_late"] == 0) & ok_next
        ob = cmp(C["bed_h"].shift(-1) * 60, lt, er, mon) if "bed_h" in C else None; os_ = cmp(sh.shift(-1), lt, er, mon); orc = cmp(rec.shift(-1), lt, er, mon)
        if ob:
            P(f"- Bedtime after the workout day, workout ended under 3 h before sleep vs earlier: {hm(C['bed_h'].shift(-1)[lt].median())} vs {hm(C['bed_h'].shift(-1)[er].median())} (medians); mean difference {say(ob, ' min')}")
        P(f"- Hours asleep that night: {say(os_, ' h', 2)}"); P(f"- Next-morning Recovery: {say(orc, '%')}")
        OUT["late_workouts"] = dict(bed_min={k: (num(v) if not isinstance(v, str) else v) for k, v in ob.items()} if ob else None,
                                    hours={k: (num(v) if not isinstance(v, str) else v) for k, v in os_.items()}, recovery={k: (num(v) if not isinstance(v, str) else v) for k, v in orc.items()})

    # ---------- 7. the days WHOOP never sees
    H("7. Days with no data inside your wear periods")
    miss, longg = [], 0
    for e, g in D.groupby("era"):
        rng = pd.date_range(g["day"].min(), g["day"].max()); have = set(g["day"].dt.normalize()); m_ = [d for d in rng if d not in have]
        runs = []
        for d in m_:
            if runs and (d - runs[-1][-1]).days == 1:
                runs[-1].append(d)
            else:
                runs.append([d])
        for r_ in runs:
            if len(r_) <= 2:
                miss += r_
            else:
                longg += 1
    wd = pd.Series([DAYS[d.dayofweek] for d in miss]).value_counts() if miss else pd.Series(dtype=int)
    P(f"- Single missing days (1-2 in a row): {len(miss)}; longer gaps inside wear periods: {longg}. By weekday: " + (", ".join(f"{k} {v}" for k, v in wd.items()) if len(wd) else "none"))
    P("- WHOOP's averages simply skip these days, so if they are your worst days (travel, late nights), your averages look better than your real week.")
    OUT["missing_days"] = dict(single=len(miss), longer_gaps=longg, by_weekday={k: int(v) for k, v in wd.items()})

    # ---------- 8. last 30 days of sleep
    if has("asleep_h"):
        H("8. The last 30 days of sleep in one number")
        w = C.index > L - pd.Timedelta(days=30); s = sh[w].dropna()
        below = float((7 - s).clip(lower=0).sum()); nd = C["need_h"][w].mean() if "need_h" in C else np.nan
        P(f"- {int((s < 7).sum())} of {len(s)} nights under 7 h; together {f(below)} hours short of 7 h a night (about {f(below / 7)} full nights). "
          f"Average {f(s.mean(), 2)} h asleep against an average WHOOP sleep need of {f(nd, 2)} h.")
        OUT["sleep_30d"] = dict(nights=int(len(s)), under7=int((s < 7).sum()), hours_below_7=num(below), nights_equiv=num(below / 7), mean=num(s.mean()), need=num(nd))

    # ---------- 9. weekend body-clock shift
    if has("mid_h") and "weekend" in C:
        H("9. Weekend body-clock shift")
        we = C["weekend"] == 1; wk_ = C["weekend"] == 0; sel = le if (le & we & C["mid_h"].notna()).sum() >= 8 else C["mid_h"].notna()
        shift = (C["mid_h"][we & sel].median() - C["mid_h"][wk_ & sel].median()) * 60
        first = wk_ & (C["weekend"].shift(1) == 1); o = cmp(rec, first, wk_ & ~first, mon) if has("recovery") else None
        P(f"- Middle of your sleep moves {f(abs(shift), 0)} min {'later' if shift > 0 else 'earlier'} on weekends (latest wear period when it has enough weekends) - "
          f"like flying {f(abs(shift) / 60)} time zones {'west' if shift > 0 else 'east'} and back every week.")
        if o:
            P(f"- First work day after the weekend vs other work days, Recovery: {say(o, '%')}")
        OUT["weekend_shift"] = dict(minutes=num(shift), first_workday={k: (num(v) if not isinstance(v, str) else v) for k, v in o.items()} if o else None)

    # ---------- 10. where more sleep stops paying
    if has("asleep_h") and has("recovery"):
        H("10. Where more sleep stops paying")
        cut = pd.cut(sh, [0, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 24], right=False, labels=["< 5.5", "5.5-6", "6-6.5", "6.5-7", "7-7.5", "7.5-8", "8-8.5", ">= 8.5"])
        gb = pd.DataFrame({"r": rec, "c": cut}).dropna().groupby("c", observed=True)["r"].agg(["mean", "count"])
        ok_ = gb[gb["count"] >= 8]
        T(["Hours asleep", "Nights", "Recovery"], [[str(i), int(r_["count"]), f(r_["mean"], 0)] for i, r_ in gb.iterrows()])
        if len(ok_) >= 3:
            top, low = ok_["mean"].max(), ok_["mean"].min(); sweet = next(i for i, r_ in ok_.iterrows() if r_["mean"] >= low + .8 * (top - low))
            P(f"- From the lowest band ({f(low, 0)}%) to the best ({f(top, 0)}%), 80% of the gain is already reached at '{sweet}' h; beyond it each extra half hour adds little (bands with 8+ nights).")
            OUT["sleep_sweet_spot"] = dict(band=str(sweet), best=num(top), lowest=num(low), table={str(i): dict(n=int(r_["count"]), recovery=num(r_["mean"])) for i, r_ in gb.iterrows()})

    # ---------- 11. leverage: where the most Recovery points are waiting
    H("11. Leverage points: same-month effect x the room left in your last 30 days")
    P("Estimated gain in average Recovery = the link's effect inside the same month x how far the last 30 days are from the better side. "
      "An estimate from links, not a promise; only links with a verdict of clear or possible are ranked, and gains must not be added together.")
    lev, w30c = [], C.index > L - pd.Timedelta(days=30)
    sl = next((r_ for r_ in F.get("drivers", {}).get("recovery", []) if r_.get("feature") == "Sleep: hours asleep"), None)
    tg = re.match(r"[\d.]+", str(OUT.get("sleep_sweet_spot", {}).get("band", "")))
    if sl and tg and sl.get("verdict") in ("clear", "possible") and fin(sl.get("w_b")) and sl["w_b"] > 0:
        gap = (float(tg.group()) - sh[w30c].dropna()).clip(lower=0)
        if len(gap) >= 10:
            lev.append(dict(lever=f"Sleep: reach {tg.group()} h on every night", effect=float(sl["w_b"]), unit="Recovery points per extra hour", verdict=sl["verdict"],
                            room=f"{int((gap > 0).sum())} of {len(gap)} nights short, {f(gap.mean() * 60, 0)} min short on average", gain=float(sl["w_b"] * gap.mean())))
    for jq in F.get("journal_all", []):
        ef = (jq.get("same_month") or {}).get("recovery"); col = f"journal: {jq['question']}"
        if jq.get("verdict") not in ("clear", "possible") or not fin(ef) or ef == 0 or col not in C:
            continue
        ans = C.loc[w30c, col].dropna(); bad = 1 if ef < 0 else 0
        if len(ans) >= 5:
            lev.append(dict(lever=f"Journal: {jq['question']} -> answer '{'no' if bad else 'yes'}'", effect=abs(float(ef)), unit="Recovery points the next morning",
                            verdict=jq["verdict"], room=f"{int((ans == bad).sum())} of {len(ans)} answered days", gain=abs(float(ef)) * float((ans == bad).mean())))
    lev = sorted([x for x in lev if x["gain"] > 0], key=lambda x: -x["gain"])
    T(["Rank", "Lever", "Effect inside the same month", "Room in the last 30 days", "Estimated gain in average Recovery", "Verdict"],
      [[i + 1, x["lever"], f"{sg(x['effect'])} {x['unit']}", x["room"], sg(x["gain"]) + " points", x["verdict"]] for i, x in enumerate(lev)])
    if not lev:
        P("No link has both a clear/possible verdict inside the same month and room in the last 30 days, so nothing is ranked yet.")
    OUT["leverage"] = [dict(x, effect=num(x["effect"]), gain=num(x["gain"])) for x in lev]

    # ---------- profile for the morning check
    Le = D[D["era"] == D["era"].max()]; w30 = D["day"] > L - pd.Timedelta(days=30)
    q = lambda s: dict(mean=num(s.mean()), p25=num(s.quantile(.25)), p75=num(s.quantile(.75)), n=int(s.notna().sum()))
    prof = dict(made_from=f"{D['day'].min().date()} -> {L.date()}", latest_period=f"{Le['day'].min().date()} -> {Le['day'].max().date()}",
                normal={k: q(Le[k]) for k in ("recovery", "hrv", "rhr", "asleep_h", "sleep_perf", "strain", "resp") if k in Le and Le[k].notna().sum() >= 10},
                last30={k: num(D.loc[w30, k].mean()) for k in ("recovery", "hrv", "rhr", "asleep_h", "strain") if k in D})
    if "bed_h" in Le and "weekend" in Le:
        prof["bedtime_median"] = dict(work=hm(Le.loc[Le["weekend"] == 0, "bed_h"].median()), weekend=hm(Le.loc[Le["weekend"] == 1, "bed_h"].median()),
                                      wake_work=hm(Le.loc[Le["weekend"] == 0, "wake_h"].median()) if "wake_h" in Le else None)
    if "recovery" in Le and "weekday" in Le:
        prof["weekday_recovery"] = {d: num(Le.loc[Le["weekday"] == d, "recovery"].mean()) for d in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] if (Le["weekday"] == d).any()}
    sl = next((r_ for r_ in F.get("drivers", {}).get("recovery", []) if r_.get("feature") == "Sleep: hours asleep"), None)
    if sl:
        prof["recovery_per_extra_hour"] = dict(whole_period=num(sl.get("slope")), same_month=num(sl.get("w_b")), verdict=sl.get("verdict"))
    prof["habits"] = [dict(question=j["question"], recovery_same_month=(j.get("same_month") or {}).get("recovery"), verdict=j.get("verdict"))
                      for j in F.get("journal_all", []) if j.get("verdict") in ("clear", "possible")]
    for k in ("sleep_sweet_spot", "bounce_back", "carry_over"):
        if k in OUT:
            prof[k] = OUT[k] if k != "carry_over" else dict(recovery=OUT[k]["recovery"]["diff"], verdict=OUT[k]["recovery"]["verdict"])
    with open(os.path.join(a.out, "insights.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(R) + "\n")
    with open(os.path.join(a.out, "insights.json"), "w", encoding="utf-8") as fh:
        json.dump(OUT, fh, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(a.out, "profile.json"), "w", encoding="utf-8") as fh:
        json.dump(prof, fh, ensure_ascii=False, indent=1, default=str)
    page(prof, os.path.join(a.out, "profile.html"))
    print(f"Done: {a.out}/insights.md, insights.json, profile.json, profile.html")


if __name__ == "__main__":
    main()
```

## Brief code — `brief.py`

```python
#!/usr/bin/env python3
# whoop-full-analysis brief v1.2
# One-page visual brief from a JSON spec: python3 brief.py brief.json --out whoop_out [--font FILE ...] [--no-fetch] [--width 720]
# Writes brief.html (self-contained), plus brief.png (phone-friendly image) and brief.pdf when a headless Chromium (Playwright) is available.
import argparse, base64, glob, html, json, os, re, shutil, subprocess, tarfile, tempfile

ICONS = dict(  # 24x24 line icons (Feather, MIT)
    sleep='<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
    heart='<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.5 1-1.1a5.5 5.5 0 0 0 0-7.8z"/>',
    pulse='<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    clock='<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    meal='<path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/>',
    calendar='<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    bolt='<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    journal='<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    down='<polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/>',
    up='<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    check='<path d="M22 11.1V12a10 10 0 1 1-5.9-9.1"/><polyline points="22 4 12 14 9 11"/>',
    alert='<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12" y2="17"/>')
FLIP = {"down", "up"}  # trend arrows point forward (to the left) in right-to-left text
ALERT = ('<svg viewBox="0 0 24 24"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" fill="#fab219"/>'
         '<path d="M12 9v4.5M12 17.2v.1" stroke="#0b0b0b" stroke-width="2.2" stroke-linecap="round"/></svg>')
CHIPS = dict(clear=("علاقة واضحة", "solid"), possible=("إشارة محتملة", "outline"), between=("تظهر بين الفترات فقط", "muted"),
             nodata=("البيانات ما تكفي للحكم", "muted"))
LEG = dict(clear="قوية وثابتة داخل نفس الشهر", possible="تحتاج تأكيد", nodata="مو معناها ما فيه تأثير",
           between="تظهر لما نقارن فترات وتختفي داخل الشهر، فسببها غالباً شي ثاني")
CHIPS_EN = dict(clear=("clear link", "solid"), possible=("possible signal", "outline"), between=("between periods only", "muted"), nodata=("not enough data", "muted"))
LEG_EN = dict(clear="strong, and it holds inside the same month", possible="needs confirming", nodata="not the same as no effect",
              between="shows when comparing periods and fades inside a month, so something else likely changed")
EN = False  # set by build(): "lang": "en" in the spec gives an English, left-to-right brief
TONES = dict(good="#0ca30c", warn="#fab219", bad="#d03b3b", neutral="#898781")  # status colours always come with a word (tag)
SUB = dict(arabic="U+0600-06FF, U+0750-077F, U+0870-08FF, U+FB50-FDFF, U+FE70-FEFC",
           latin="U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+20AC, U+2122, U+2190-2193, U+2212, U+2215")
FONT_PKG, FONT_FILE = "@fontsource/ibm-plex-sans-arabic@5", "ibm-plex-sans-arabic-{s}-{w}-normal.woff2"
CSS = """
:root{--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--ring:rgba(11,11,11,.10);--blue:#2a78d6;--blue6:#184f95;
--blue7:#0d366b;--blue1:#cde2fb;--wash:#eaf2fc;--track:#f0efec;--good:#0ca30c}
*{box-sizing:border-box;margin:0;padding:0}
html{background:var(--page)}
body{width:__W__px;padding:26px;font-family:"WBrief","IBM Plex Sans Arabic","Noto Kufi Arabic","Noto Sans Arabic","Tajawal","Cairo","Segoe UI","Geeza Pro","DejaVu Sans",sans-serif;
color:var(--ink);font-size:17px;line-height:1.7}
b{font-weight:700}
.n{unicode-bidi:isolate;white-space:nowrap}
.hero{position:relative;overflow:hidden;border-radius:26px;padding:28px 28px 24px;color:#fff;background:linear-gradient(140deg,var(--blue7) 0%,var(--blue6) 100%)}
.hero:before{content:"";position:absolute;width:250px;height:250px;border-radius:50%;border:28px solid rgba(255,255,255,.06);inset-inline-end:-90px;top:-110px}
.over{position:relative;font-size:14px;font-weight:600;color:var(--blue1)}
.hero h1{position:relative;font-size:33px;line-height:1.35;font-weight:700;margin:6px 0 4px}
.sub{position:relative;font-size:14.5px;color:var(--blue1)}
.head{position:relative;margin-top:16px;padding:12px 16px;border-radius:16px;background:rgba(255,255,255,.11);font-size:19px;font-weight:600;line-height:1.6}
.kpis{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}
.kpi{background:var(--surface);border:1px solid var(--ring);border-radius:20px;padding:15px 18px 14px}
.kpi .l{font-size:14.5px;font-weight:600;color:var(--ink2)}
.kpi .v{font-size:36px;font-weight:700;line-height:1.25;margin-top:2px}
.kpi .v small{font-size:16px;font-weight:600;color:var(--ink2)}
.kpi .nt{font-size:14px;line-height:1.5;color:var(--ink2)}
.tag{display:inline-flex;align-items:center;gap:7px;margin-top:9px;padding:2px 11px 3px;border-radius:999px;background:var(--track);font-size:13px;font-weight:600}
.tag i{width:9px;height:9px;border-radius:50%}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.card{background:var(--surface);border:1px solid var(--ring);border-radius:22px;padding:18px 20px 16px}
.wide{grid-column:1/-1}
.ch{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;margin-bottom:8px}
.ico{flex:none;display:grid;place-items:center;width:38px;height:38px;border-radius:12px;background:var(--wash)}
.ico svg{width:21px;height:21px;fill:none;stroke:var(--blue);stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.ico svg.flip{transform:scaleX(-1)}
h2{flex:1 1 auto;font-size:18.5px;font-weight:700;line-height:1.4}
.chip{flex:none;padding:2px 10px 3px;border-radius:999px;border:1.5px solid transparent;font-size:12.5px;font-weight:600;white-space:nowrap}
.chip.solid{background:var(--blue);color:#fff}
.chip.outline{border-color:var(--blue);color:var(--ink)}
.chip.muted{background:var(--track);color:var(--ink2)}
.stat{display:flex;align-items:center;gap:14px;margin:4px 0 8px}
.stat .sv{flex:none;font-size:38px;line-height:1.15;white-space:nowrap}
.stat .sv.md{font-size:31px}
.stat .cap{font-size:15px;line-height:1.55;color:var(--ink2)}
ul{list-style:none}
ul li{position:relative;margin:4px 0;padding-inline-start:16px;font-size:16px;line-height:1.7}
ul li:before{content:"";position:absolute;inset-inline-start:0;top:.75em;width:6px;height:6px;border-radius:50%;background:var(--blue)}
.bt{margin:2px 0 4px;font-size:14px;font-weight:600;color:var(--ink2)}
.bar{display:grid;grid-template-columns:118px 1fr 66px;align-items:center;gap:12px;margin:6px 0}
.bar .lb{font-size:14.5px;color:var(--ink2)}
.tr{position:relative;height:16px;border-radius:4px;background:var(--track)}
.fl{position:absolute;top:0;bottom:0;inset-inline-start:0;background:var(--blue);border-start-start-radius:1px;border-end-start-radius:1px;border-start-end-radius:4px;border-end-end-radius:4px}
.rf{position:absolute;top:-5px;bottom:-5px;width:0;border-inline-start:2px dashed var(--good)}
.vl{font-size:15.5px;font-weight:700;line-height:1.2}
.vl small{display:block;font-size:12px;font-weight:400;color:var(--muted)}
.rl{display:flex;align-items:center;gap:8px;margin:2px 0 6px;font-size:12.5px;color:var(--muted)}
.rl i{width:20px;border-top:2px dashed var(--good)}
.plan{margin-top:12px;padding:18px 20px 8px;border-radius:22px;background:var(--surface);border:1px solid var(--ring)}
.plan ol{list-style:none;counter-reset:s}
.plan li{position:relative;counter-increment:s;margin:10px 0 14px;padding-inline-start:46px;min-height:32px}
.plan li:before{content:counter(s);position:absolute;inset-inline-start:0;top:1px;display:grid;place-items:center;width:31px;height:31px;border-radius:50%;
background:var(--blue);color:#fff;font-size:15px;font-weight:700}
.plan li .pl{display:block;font-size:16.5px;line-height:1.5}
.plan li .pt{display:block;font-size:15px;line-height:1.65;color:var(--ink2)}
.alert{display:flex;gap:12px;margin-top:12px;padding:14px 18px;border-radius:20px;background:var(--surface);border:1px solid var(--ring)}
.alert svg{flex:none;width:26px;height:26px;margin-top:2px}
.alert p{font-size:14.5px;line-height:1.65;color:var(--ink2)}
.alert .lbl{color:var(--ink)}
.foot{margin-top:14px;padding:0 4px;font-size:13px;line-height:1.7;color:var(--muted)}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;margin-bottom:6px}
.legend .chip{margin-inline-end:5px}
"""


TOK = re.compile(r"\*\*|(?<![\w.])[+\-−]\d[\d.,:]*%?|[A-Za-z][A-Za-z0-9]*(?:[ .\-][A-Za-z][A-Za-z0-9]*)*")


def rich(t):  # escape, **bold**, and keep Latin words and signed numbers (+8, -13) as left-to-right islands in Arabic text
    if EN:  # English brief: bold only, so the text wraps normally
        return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(str(t), quote=False))
    s, out, i, bold = str(t), [], 0, False
    for m in TOK.finditer(s):
        out.append(html.escape(s[i:m.start()], quote=False)); g, i = m.group(), m.end()
        if g == "**":
            out.append("</b>" if bold else "<b>"); bold = not bold
        else:
            out.append(f'<span class="n" dir="ltr">{html.escape(g, quote=False)}</span>')
    out.append(html.escape(s[i:], quote=False))
    return "".join(out) + ("</b>" if bold else "")


def fonts(a):  # (path, weight, subset): --font files, else IBM Plex Sans Arabic fetched once through npm and cached
    if a.font:
        return [(p, 700 if re.search(r"700|bold", p.lower()) else 600 if re.search(r"600|semi", p.lower()) else 400,
                 "arabic" if "arabic" in os.path.basename(p).lower() else None) for p in a.font]
    cache = os.path.join(os.path.expanduser("~"), ".cache", "whoop-brief-fonts")
    want = [(s, w, os.path.join(cache, FONT_FILE.format(s=s, w=w))) for s in ("arabic", "latin") for w in (400, 600, 700)]
    if not all(os.path.exists(p) for *_, p in want) and not a.no_fetch and shutil.which("npm"):
        try:
            with tempfile.TemporaryDirectory() as td:
                subprocess.run(["npm", "pack", FONT_PKG, "--silent"], cwd=td, timeout=120, check=True, capture_output=True)
                os.makedirs(cache, exist_ok=True)
                with tarfile.open(glob.glob(os.path.join(td, "*.tgz"))[0]) as tz:
                    for s, w, p in want:
                        data = tz.extractfile(f"package/files/{FONT_FILE.format(s=s, w=w)}").read()
                        with open(p, "wb") as fh:
                            fh.write(data)
        except Exception as e:
            print("font download skipped:", (str(e) or type(e).__name__)[:120])
    return [(p, w, s) for s, w, p in want] if all(os.path.exists(p) for *_, p in want) else []


def face_css(fl):
    out = []
    for p, w, s in fl:
        ext = os.path.splitext(p)[1].lower().lstrip(".")
        fmt, mime = dict(woff2=("woff2", "font/woff2"), woff=("woff", "font/woff"), otf=("opentype", "font/otf")).get(ext, ("truetype", "font/ttf"))
        with open(p, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        rng = f";unicode-range:{SUB[s]}" if s in SUB else ""
        out.append(f'@font-face{{font-family:"WBrief";font-weight:{w};font-display:block;src:url(data:{mime};base64,{b64}) format("{fmt}"){rng}}}')
    return "\n".join(out)


def kpi(k):
    v, u = rich(k.get("value", "")), str(k.get("unit", ""))
    if not u:
        val = v
    elif re.search(r"[-ۿ]", u):  # Arabic unit follows the number in reading order
        val = f"{v} <small>{rich(u)}</small>"
    else:
        val = f'<span dir="ltr">{v}<small>{" " if u.isalpha() else ""}{rich(u)}</small></span>'
    tone = TONES.get(k.get("tone", "neutral"), TONES["neutral"])
    tag = f'<div class="tag"><i style="background:{tone}"></i>{rich(k["tag"])}</div>' if k.get("tag") else ""
    return f'<div class="kpi"><div class="l">{rich(k.get("label", ""))}</div><div class="v">{val}</div><div class="nt">{rich(k.get("note", ""))}</div>{tag}</div>'


def card(c):
    ic = c.get("icon", "pulse"); fl = " class=flip" if ic in FLIP and not EN else ""
    svg = f'<svg viewBox="0 0 24 24"{fl}>{ICONS.get(ic, ICONS["pulse"])}</svg>'
    chip = ""
    if c.get("chip"):
        txt, sty = (CHIPS_EN if EN else CHIPS).get(c["chip"], (c["chip"], "muted")); chip = f'<span class="chip {sty}">{rich(txt)}</span>'
    st = c.get("stat")
    md = " md" if st and len(str(st["value"])) > 5 else ""
    stat = f'<div class="stat"><b class="sv{md}">{rich(st["value"])}</b><span class="cap">{rich(st.get("caption", ""))}</span></div>' if st else ""
    bars, bb = "", c.get("bars")
    if bb and bb.get("rows"):
        mx = float(bb.get("max") or max(r["value"] for r in bb["rows"])); ref = bb.get("ref") or {}
        rf = f'<i class="rf" style="inset-inline-start:{100 * ref["value"] / mx:.1f}%"></i>' if "value" in ref else ""
        rows = ""
        for r in bb["rows"]:
            note = f'<small>{rich(r["note"])}</small>' if r.get("note") else ""
            rows += (f'<div class="bar"><div class="lb">{rich(r["label"])}</div><div class="tr"><i class="fl" style="width:{min(100, 100 * r["value"] / mx):.1f}%"></i>{rf}</div>'
                     f'<div class="vl">{rich(r.get("text", r["value"]))}{note}</div></div>')
        title = f'<div class="bt">{rich(bb["title"])}</div>' if bb.get("title") else ""
        leg = f'<div class="rl"><i></i>{rich(ref["label"])}</div>' if ref.get("label") else ""
        bars = f'<div class="bars">{title}{rows}{leg}</div>'
    li = "".join(f"<li>{rich(b)}</li>" for b in c.get("bullets", []))
    ul = f"<ul>{li}</ul>" if li else ""
    wide = " wide" if c.get("wide") else ""
    return f'<section class="card{wide}"><div class="ch"><div class="ico">{svg}</div><h2>{rich(c.get("title", ""))}</h2>{chip}</div>{stat}{bars}{ul}</section>'


def build(S, fcss, W):
    global EN
    EN = str(S.get("lang", "ar")).lower().startswith("en"); CH, LG = (CHIPS_EN, LEG_EN) if EN else (CHIPS, LEG)
    kp = "".join(kpi(k) for k in S.get("kpis", []))
    cards = "".join(card(c) for c in S.get("cards", []))
    plan = ""
    if S.get("plan"):
        items = "".join(f'<li><b class="pl">{rich(p.get("lead", ""))}</b>' + (f'<span class="pt">{rich(p["text"])}</span>' if p.get("text") else "") + "</li>" for p in S["plan"])
        plan = (f'<section class="plan"><div class="ch"><div class="ico"><svg viewBox="0 0 24 24">{ICONS["check"]}</svg></div>'
                f'<h2>{rich(S.get("plan_title", "Your plan" if EN else "خطتك العملية"))}</h2></div><ol>{items}</ol></section>')
    alert = ""
    if S.get("alerts"):
        lbl = f'<b class="lbl">{rich(S.get("alerts_label", "Note" if EN else "انتبه"))}:</b> '
        ps = "".join(f"<p>{lbl if i == 0 else ''}{rich(x)}</p>" for i, x in enumerate(S["alerts"]))
        alert = f'<section class="alert">{ALERT}<div>{ps}</div></section>'
    keys = S.get("legend") or list(dict.fromkeys(c.get("chip") for c in S.get("cards", []) if c.get("chip") in CHIPS))
    legend = "".join(f'<span><span class="chip {CH[k][1]}">{CH[k][0]}</span>{LG[k]}</span>' for k in keys if k in CHIPS)
    legend = f'<div class="legend">{legend}</div>' if legend else ""
    foot = "".join(f"<p>{rich(x)}</p>" for x in S.get("footer", []))
    hd = f'<div class="head">{rich(S["headline"])}</div>' if S.get("headline") else ""
    return (f'<!DOCTYPE html><html lang="{S.get("lang", "ar")}" dir="{"ltr" if EN else "rtl"}"><head><meta charset="utf-8"><meta name="viewport" content="width={W}">'
            f'<title>{html.escape(str(S.get("title", "WHOOP")))}</title><style>{fcss}\n{CSS.replace("__W__", str(W))}</style></head><body>'
            f'<header class="hero"><div class="over">{rich(S.get("overline", ""))}</div><h1>{rich(S.get("title", ""))}</h1>'
            f'<div class="sub">{rich(S.get("subtitle", ""))}</div>{hd}</header><div class="kpis">{kp}</div><div class="grid">{cards}</div>'
            f'{plan}{alert}<footer class="foot">{legend}{foot}</footer></body></html>')


NODE = """const [hp, png, pdf, W] = process.argv.slice(1); const {chromium} = require('playwright');
(async () => { const b = await chromium.launch(); const pg = await b.newPage({viewport: {width: +W, height: 900}, deviceScaleFactor: 2});
  await pg.goto('file://' + hp); await pg.evaluate(() => document.fonts.ready.then(() => 1));
  const h = await pg.evaluate(() => Math.ceil(document.documentElement.scrollHeight)); await pg.setViewportSize({width: +W, height: h});
  await pg.screenshot({path: png, fullPage: true}); await pg.emulateMedia({media: 'screen'});
  await pg.pdf({path: pdf, width: W + 'px', height: (h + 2) + 'px', printBackground: true, pageRanges: '1'}); await b.close();
})().catch(e => { console.error(e.message); process.exit(1); });"""


def render(htm, out, W):
    hp = os.path.abspath(os.path.join(out, "brief.html")); png, pdf = os.path.join(out, "brief.png"), os.path.join(out, "brief.pdf")
    with open(hp, "w", encoding="utf-8") as fh:
        fh.write(htm)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": 900}, device_scale_factor=2)
            pg.goto("file://" + hp); pg.evaluate("document.fonts.ready.then(() => 1)")
            h = pg.evaluate("Math.ceil(document.documentElement.scrollHeight)"); pg.set_viewport_size({"width": W, "height": h})
            pg.screenshot(path=png, full_page=True); pg.emulate_media(media="screen")
            pg.pdf(path=pdf, width=f"{W}px", height=f"{h + 2}px", print_background=True, page_ranges="1"); b.close()
        return hp, png, pdf, h
    except Exception as e:
        err = (str(e).splitlines() or [type(e).__name__])[0][:150]
    if shutil.which("node"):
        r = subprocess.run(["node", "-e", NODE, hp, png, pdf, str(W)], capture_output=True, text=True, timeout=180)
        if r.returncode == 0 and os.path.exists(png):
            return hp, png, pdf, None
        err += " | node: " + ((r.stderr or "").strip().splitlines() or ["failed"])[-1][:150]
    print(f"PNG/PDF not rendered ({err}). Deliver brief.html, or install a renderer: pip install playwright && python -m playwright install chromium")
    return hp, None, None, None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("--out", default="whoop_out"); ap.add_argument("--font", action="append")
    ap.add_argument("--no-fetch", action="store_true"); ap.add_argument("--width", type=int, default=720); a = ap.parse_args()
    with open(a.spec, encoding="utf-8") as fh:
        S = json.load(fh)
    os.makedirs(a.out, exist_ok=True); fl = fonts(a)
    if not fl:
        print("Arabic web font not available - the system font is used (install one, or pass --font)")
    hp, png, pdf, h = render(build(S, face_css(fl), a.width), a.out, a.width)
    print("Done:", ", ".join(x for x in (png, pdf, hp) if x) + (f" ({a.width}x{h} px at 2x)" if h else ""))


if __name__ == "__main__":
    main()
```