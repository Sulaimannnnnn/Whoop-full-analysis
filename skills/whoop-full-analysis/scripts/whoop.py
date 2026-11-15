#!/usr/bin/env python3
# whoop-full-analysis engine v1.2
# WHOOP full analysis: python3 whoop.py <csv|zip|folder ...> --out whoop_out [--weekend Fri,Sat] [--map header_map.json]
# Exports in any app language: Arabic headers are translated built in; for any other language the engine writes
# headers_to_map.json, you fill in the English WHOOP header for each column, and rerun with --map (see the skill).
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
if plt is not None:  # chart labels in any script (Journal questions come in the app's language): fall back across installed fonts
    try:
        from matplotlib import font_manager as _fm
        _have = {x.name for x in _fm.fontManager.ttflist}
        _want = ["Noto Sans Arabic", "Noto Sans CJK JP", "Noto Sans CJK SC", "Noto Sans JP", "Noto Sans SC", "Noto Sans KR", "Hiragino Sans",
                 "PingFang SC", "Apple SD Gothic Neo", "Microsoft YaHei", "Yu Gothic", "Malgun Gothic", "Noto Sans Hebrew", "Arial Hebrew",
                 "Noto Sans Devanagari", "Kohinoor Devanagari", "Nirmala UI", "Noto Sans Thai", "Thonburi", "Tahoma", "Arial Unicode MS"]
        plt.rcParams["font.family"] = ["DejaVu Sans"] + [x for x in _want if x in _have]
    except Exception:
        pass

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
AR_DIG = str.maketrans("٠١٢٣٤٥٦٧٨٩٫۰۱۲۳۴۵۶۷۸۹०१२३४५६७८९", "0123456789." + "0123456789" * 2)  # Arabic, Persian/Urdu, Devanagari digits
HAS_AR = lambda s: bool(re.search(r"[\u0600-\u06ff]", str(s)))
ENGLISH_HEADERS = dict(
    physiological_cycles=["Cycle start time", "Cycle end time", "Cycle timezone", "Recovery score %", "Resting heart rate (bpm)",
                          "Heart rate variability (ms)", "Skin temp (celsius)", "Blood oxygen %", "Day Strain", "Energy burned (cal)", "Max HR (bpm)",
                          "Average HR (bpm)", "Sleep onset", "Wake onset", "Sleep performance %", "Respiratory rate (rpm)", "Asleep duration (min)",
                          "In bed duration (min)", "Light sleep duration (min)", "Deep (SWS) duration (min)", "REM duration (min)", "Awake duration (min)",
                          "Sleep need (min)", "Sleep debt (min)", "Sleep efficiency %", "Sleep consistency %", "Steps"],
    sleeps=["Cycle start time", "Cycle end time", "Cycle timezone", "Sleep onset", "Wake onset", "Sleep performance %", "Respiratory rate (rpm)",
            "Asleep duration (min)", "In bed duration (min)", "Light sleep duration (min)", "Deep (SWS) duration (min)", "REM duration (min)",
            "Awake duration (min)", "Sleep need (min)", "Sleep debt (min)", "Sleep efficiency %", "Sleep consistency %", "Nap"],
    workouts=["Cycle start time", "Cycle end time", "Cycle timezone", "Workout start time", "Workout end time", "Duration (min)", "Activity name",
              "Activity Strain", "Energy burned (cal)", "Max HR (bpm)", "Average HR (bpm)", "HR Zone 1 %", "HR Zone 2 %", "HR Zone 3 %", "HR Zone 4 %",
              "HR Zone 5 %", "GPS enabled", "Distance (meters)", "Altitude gain (meters)", "Altitude change (meters)"],
    journal_entries=["Cycle start time", "Cycle end time", "Cycle timezone", "Question text", "Answered yes", "Notes"])
NONASCII = lambda s: bool(re.search(r"[^\x00-\x7f]", str(s)))
MAP = dict(headers={}, values={})  # --map: {"headers": {"original header": "English WHOOP header"}, "values": {"Sí": "yes", "No": "no"}}
YES = {"true", "yes", "1", "y", "t", "1.0", "نعم", "صحيح", "صح", "sí", "si", "oui", "ja", "sim", "sì", "да", "evet", "tak", "ano", "はい", "是", "예", "ใช่", "כן", "بله", "ہاں", "हाँ", "हां", "ya", "có"}
NO = {"false", "no", "0", "n", "f", "0.0", "لا", "خطأ", "خطا", "non", "nein", "não", "nao", "нет", "hayır", "hayir", "nie", "ne", "いいえ", "否", "아니요", "ไม่", "לא", "خیر", "نہیں", "नहीं", "tidak", "không", "nej", "nei", "ei"}
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
    hm_ = {re.sub(r"\s+", " ", k).strip().casefold(): v for k, v in MAP["headers"].items()}
    for c in cols:
        mp = hm_.get(re.sub(r"\s+", " ", re.sub(r"\.\d+$", "", c)).strip().casefold())
        if mp:
            out.append(f"{mp} [{c}]"); continue
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
    v = s.astype(str).str.strip().str.casefold()
    vm = {str(k).strip().casefold(): str(x).strip().casefold() for k, x in MAP["values"].items()}
    v = v.map(lambda x: vm.get(x, x))
    return v.map(lambda x: 1.0 if x in YES else 0.0 if x in NO else np.nan)
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
    ap.add_argument("--weekend", default="Fri,Sat"); ap.add_argument("--no-charts", action="store_true")
    ap.add_argument("--map", help="JSON that maps a non-English export's headers (and yes/no answers) to WHOOP's English ones"); a = ap.parse_args()
    if a.map:
        with open(a.map, encoding="utf-8") as fh:
            mj = json.load(fh)
        MAP["headers"].update({k: v for k, v in (mj.get("headers") or {}).items() if v}); MAP["values"].update(mj.get("values") or {})
    out = a.out; tmp = os.path.join(out, "_extracted"); os.makedirs(os.path.join(out, "charts"), exist_ok=True); os.makedirs(tmp, exist_ok=True)
    wkend = [d.strip()[:3].title() for d in a.weekend.split(",") if d.strip()]
    files, other = gather(a.inputs, tmp); tabs = {k: [] for k in ("cycles", "sleeps", "workouts", "journal", "unknown")}; info = []; TOMAP = []
    for fp, label in files:
        try:
            df = read(fp)
        except Exception as e:
            info.append([label, "UNREADABLE", 0, 0, str(e)[:60]]); continue
        k = kind_of(df.columns); tabs[k].append((label, df))
        raw = [c for c in df.columns if "[" not in c and (k == "unknown" or NONASCII(c))]  # an unrecognised file: every header
        if raw:
            TOMAP.append(dict(file=label, detected_as=k, columns=[dict(header=c, sample=[str(x) for x in df[c].dropna().unique()[:3]]) for c in raw]))
        note = "headers translated (originals kept in [brackets])" if any("[" in c for c in df.columns) else ""
        info.append([label, k, len(df), df.shape[1], (note + "; " if note else "") + f"{len(raw)} header(s) not in English - see headers_to_map.json" if raw else note])
    TB = {}
    for k, lst in tabs.items():
        if k != "unknown" and lst:
            cols = list(dict.fromkeys(c for _, d in lst for c in d.columns))
            df = pd.concat([d.reindex(columns=cols) for _, d in lst], ignore_index=True); n0 = len(df); df = df.drop_duplicates(); TB[k] = (df, n0 - len(df))
    H("1. Files received and how they were read"); T(["File", "Detected as", "Rows", "Columns", "Note"], info)
    if TOMAP:
        with open(os.path.join(out, "headers_to_map.json"), "w", encoding="utf-8") as fh:
            json.dump(dict(how="Give each header the matching English WHOOP header from english_headers (or null if none fits), and each yes/no answer "
                               "word its English yes/no in values; save as header_map.json and rerun with --map header_map.json",
                           english_headers=ENGLISH_HEADERS, files=TOMAP, values={}), fh, ensure_ascii=False, indent=1)
        P(f"**CHECK: {sum(len(t['columns']) for t in TOMAP)} header(s) are in a language the engine does not translate by itself.** "
          f"They are listed in headers_to_map.json; map them and rerun with --map, or the analysis misses them.")
        print(f"ACTION NEEDED: headers in another language -> fill {out}/headers_to_map.json into header_map.json and rerun with --map header_map.json")
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
        key.append(s); return re.sub(r"[\u0600-\u06ff\u064b-\u0652]+", "", s).strip(" :?") + f" [A{len(key)}]"
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
