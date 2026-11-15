#!/usr/bin/env python3
# whoop-full-analysis insights v1.3
# Patterns the WHOOP app does not spell out, from the engine's daily table: python3 insights.py --out whoop_out
# Reads whoop_out/daily_enriched.csv (+ findings.json); writes insights.md, insights.json, profile.json and profile.html (the user's normal, for the morning check)
# After editing profile.json (name, plan, lang, strings): python3 insights.py --out whoop_out --page  rebuilds profile.html only
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


PCSS = ("body{margin:0;background:#f9f9f7;color:#0b0b0b;font:16px/1.7 'IBM Plex Sans Arabic','Noto Sans Arabic',system-ui,-apple-system,'Segoe UI','Noto Sans','Noto Sans CJK JP','PingFang SC','Hiragino Sans',Tahoma,sans-serif}"
        "main{max-width:640px;margin:0 auto;padding:24px 18px}h1{font-size:24px;margin:0}h2{font-size:18px;margin:22px 0 6px}"
        ".sub,.foot{color:#52514e;font-size:14px}table{width:100%;border-collapse:collapse;margin-top:14px;background:#fcfcfb}"
        "th,td{padding:8px 10px;border-bottom:1px solid #e7e6e2;text-align:start}th{font-size:13px;color:#52514e}"
        "td:not(:first-child){font-variant-numeric:tabular-nums;white-space:nowrap}ul,ol{padding-inline-start:20px}li{margin:4px 0}")


# Profile page text. Arabic and English are built in; any other language: put "lang" and a "strings" object with the same keys in
# profile.json (translate the English values, keep the {placeholders}); missing keys fall back to English and are reported.
PSTR = dict(
    en=dict(title="WHOOP - My baseline", sub="Your averages in the latest wear period ({period}). The morning check compares your day with them.",
            th_metric="Metric", th_avg="Your average", th_range="Your usual range", th_last30="Last 30 days", range_to="to", period="{a} to {b}",
            h_patterns="Your patterns", h_plan="Your plan", foot="Computed from your data ({period}). Updated with every new full analysis.",
            sleep_usual="Usual sleep: work nights {work}, weekends {weekend}, wake {wake}",
            per_hour="Each extra hour of sleep is about {n} Recovery points ({v})", sweet="Most of the benefit of sleep is reached at {band} hours",
            carry="A night under 6 hours costs the second morning about {n} points ({v})", bounce="A red morning usually clears after {n} day(s)",
            habit="{q}: {n} Recovery points the next morning (inside the same month, {v})",
            m_recovery="Recovery", m_hrv="HRV", m_rhr="Resting HR", m_asleep_h="Hours asleep", m_sleep_perf="Sleep performance", m_strain="Day Strain",
            m_resp="Respiratory rate", u_ms=" ms", u_bpm=" bpm", u_h=" h",
            v_clear="clear link", v_possible="possible signal", v_between="between periods only"),
    ar=dict(title="WHOOP — ملفي الأساسي", sub="معدلاتك في آخر فترة لبس ({period}). فحص الصباح يقارن يومك فيها.",
            th_metric="المقياس", th_avg="معدلك", th_range="المعتاد عندك", th_last30="آخر 30 يوم", range_to="–", period="من {a} إلى {b}",
            h_patterns="أنماطك", h_plan="خطتك", foot="محسوب من بياناتك ({period}). يتحدّث مع كل تحليل كامل جديد.",
            sleep_usual="نومك المعتاد: ليالي الدوام {work}، الويكند {weekend}، والصحيان {wake}",
            per_hour="كل ساعة نوم زيادة ≈ {n} نقاط ريكفري ({v})", sweet="أغلب فايدة النوم توصلها عند {band} ساعات",
            carry="ليلة أقل من 6 ساعات تنقص الصبح الثاني ≈ {n} نقاط ({v})", bounce="الصبح الأحمر يعدّي عادة بعد {n} يوم",
            habit="«{q}»: {n} نقاط ريكفري الصبح اللي بعده (داخل نفس الشهر، {v})",
            m_recovery="الريكفري", m_hrv="HRV", m_rhr="نبض الراحة", m_asleep_h="ساعات النوم", m_sleep_perf="أداء النوم", m_strain="مجهود اليوم",
            m_resp="معدل التنفس", u_ms=" ms", u_bpm="", u_h=" ساعة",
            v_clear="علاقة واضحة", v_possible="إشارة محتملة", v_between="تظهر بين الفترات فقط"))
RTL_LANGS = {"ar", "fa", "ur", "he", "iw", "ps", "ckb", "ku", "yi", "dv", "sd", "ug"}
# metric key -> unit key, decimals
PMET = dict(recovery=(None, 0), hrv=("u_ms", 0), rhr=("u_bpm", 0), asleep_h=("u_h", 1), sleep_perf=(None, 0), strain=(None, 1), resp=(None, 1))


def page(prof, path):  # small private page the morning check reads in later chats (the JSON sits in <script id="whoop-profile">)
    lang = str(prof.get("lang", "ar")).strip().lower() or "ar"; base = re.split(r"[-_]", lang)[0]
    S = dict(PSTR["en"]); S.update(PSTR.get(base, {})); S.update({k: v for k, v in (prof.get("strings") or {}).items() if v})
    if base not in PSTR:
        miss = [k for k in PSTR["en"] if k not in (prof.get("strings") or {})]
        if miss:
            print(f"profile page: no translation for {len(miss)} text(s) in '{lang}' - English used for: {', '.join(miss)}. "
                  "Add them under \"strings\" in profile.json and rerun with --page.")
    rtl = prof.get("dir") == "rtl" or (prof.get("dir") != "ltr" and base in RTL_LANGS)
    e = lambda t: html.escape(str(t), quote=False); v = lambda x, d, u: f(x, d) + u if fin(x) else "-"
    vw = lambda k: S.get({"clear": "v_clear", "possible": "v_possible", "between periods only": "v_between"}.get(k, ""), k)
    pct = lambda k: "%" if k in ("recovery", "sleep_perf") else ""
    N, L3 = prof.get("normal", {}), prof.get("last30", {})
    rows = "".join(f"<tr><td>{e(S['m_' + k])}</td><td>{v(N[k]['mean'], d, S.get(u, '') if u else pct(k))}</td>"
                   f"<td>{f(N[k]['p25'], d)} {e(S['range_to'])} {v(N[k]['p75'], d, S.get(u, '') if u else pct(k))}</td>"
                   f"<td>{v(L3.get(k), d, S.get(u, '') if u else pct(k))}</td></tr>" for k, (u, d) in PMET.items() if k in N)
    li, b = [], prof.get("bedtime_median") or {}
    if b:
        li.append(S["sleep_usual"].format(work=b.get("work"), weekend=b.get("weekend"), wake=b.get("wake_work")))
    s = prof.get("recovery_per_extra_hour") or {}
    if fin(s.get("same_month")):
        li.append(S["per_hour"].format(n=sg(s["same_month"], 0), v=vw(s.get("verdict"))))
    if prof.get("sleep_sweet_spot"):
        li.append(S["sweet"].format(band=prof["sleep_sweet_spot"]["band"]))
    c = prof.get("carry_over") or {}
    if fin(c.get("recovery")):
        li.append(S["carry"].format(n=sg(c["recovery"], 0), v=vw(c.get("verdict"))))
    bb = prof.get("bounce_back") or {}
    if fin(bb.get("median_days")):
        li.append(S["bounce"].format(n=f(bb["median_days"], 0)))
    li += [S["habit"].format(q=h["question"], n=sg(h["recovery_same_month"], 0), v=vw(h["verdict"]))
           for h in prof.get("habits", []) if fin(h.get("recovery_same_month"))]
    iso = (lambda t: re.sub(r"(?<![\w.])([+\-−]\d[\d.,:]*)", r'<bdi dir="ltr">\1</bdi>', e(t))) if rtl else e  # signed numbers read left to right
    def per(x):
        m = re.match(r"\s*(\S+)\s*->\s*(\S+)\s*$", str(x or ""))
        return S["period"].format(a=m.group(1), b=m.group(2)) if m else str(x or "")
    plan = "".join(f"<li>{iso(x)}</li>" for x in prof.get("plan", []))
    js = json.dumps(prof, ensure_ascii=False, default=str).replace("</", "<\\/")
    title = S["title"] + (f" ({prof['name']})" if prof.get("name") else "")
    doc = (f'<!DOCTYPE html><html lang="{e(lang)}" dir="{"rtl" if rtl else "ltr"}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>'
           f'<script type="application/json" id="whoop-profile">{js}</script><style>{PCSS}</style></head><body><main>'
           f'<h1>{e(title)}</h1><p class="sub">{e(S["sub"].format(period=per(prof.get("latest_period"))))}</p>'
           f'<table><thead><tr><th>{e(S["th_metric"])}</th><th>{e(S["th_avg"])}</th><th>{e(S["th_range"])}</th><th>{e(S["th_last30"])}</th></tr></thead><tbody>{rows}</tbody></table>'
           f'<h2>{e(S["h_patterns"])}</h2><ul>{"".join(f"<li>{iso(x)}</li>" for x in li)}</ul>' + (f"<h2>{e(S['h_plan'])}</h2><ol>{plan}</ol>" if plan else "")
           + f'<p class="foot">{e(S["foot"].format(period=per(prof.get("made_from"))))}</p></main></body></html>')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(doc)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="whoop_out"); ap.add_argument("--page", action="store_true")
    ap.add_argument("--strings", metavar="LANG", help="print the profile page's texts (en or ar) as JSON, to translate into \"strings\" in profile.json")
    a = ap.parse_args()
    if a.strings:
        return print(json.dumps(PSTR.get(a.strings, PSTR["en"]), ensure_ascii=False, indent=1))
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
