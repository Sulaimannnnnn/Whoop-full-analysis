#!/usr/bin/env python3
# whoop-full-analysis brief v1.3
# One-page visual brief from a JSON spec: python3 brief.py brief.json --out whoop_out [--font FILE ...] [--no-fetch] [--width 720]
# Writes brief.html (self-contained), plus brief.png (phone-friendly image) and brief.pdf when a headless Chromium (Playwright) is available.
# Any language: "lang" in the spec (ar and en built in). Other languages: add "chips" {clear, possible, between, nodata}, "legend_text"
# {same keys}, "plan_title" and "alerts_label" in that language; right-to-left follows the language (ar, fa, ur, he...) or "dir".
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
RTL_LANGS = {"ar", "fa", "ur", "he", "iw", "ps", "ckb", "ku", "yi", "dv", "sd", "ug"}
RTL_CH = re.compile(r"[\u0590-\u08ff\ufb1d-\ufdff\ufe70-\ufefc]")  # Hebrew and Arabic-script letters
ALERT = ('<svg viewBox="0 0 24 24"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" fill="#fab219"/>'
         '<path d="M12 9v4.5M12 17.2v.1" stroke="#0b0b0b" stroke-width="2.2" stroke-linecap="round"/></svg>')
CHIPS = dict(clear=("علاقة واضحة", "solid"), possible=("إشارة محتملة", "outline"), between=("تظهر بين الفترات فقط", "muted"),
             nodata=("البيانات ما تكفي للحكم", "muted"))
LEG = dict(clear="قوية وثابتة داخل نفس الشهر", possible="تحتاج تأكيد", nodata="مو معناها ما فيه تأثير",
           between="تظهر لما نقارن فترات وتختفي داخل الشهر، فسببها غالباً شي ثاني")
CHIPS_EN = dict(clear=("clear link", "solid"), possible=("possible signal", "outline"), between=("between periods only", "muted"), nodata=("not enough data", "muted"))
LEG_EN = dict(clear="strong, and it holds inside the same month", possible="needs confirming", nodata="not the same as no effect",
              between="shows when comparing periods and fades inside a month, so something else likely changed")
RTL = True  # set by build() from "lang" / "dir": left-to-right for every language that is not written right to left
TONES = dict(good="#0ca30c", warn="#fab219", bad="#d03b3b", neutral="#898781")  # status colours always come with a word (tag)
SUB = dict(arabic="U+0600-06FF, U+0750-077F, U+0870-08FF, U+FB50-FDFF, U+FE70-FEFC",
           latin="U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+20AC, U+2122, U+2190-2193, U+2212, U+2215")
FONT_PKG, FONT_FILE = "@fontsource/ibm-plex-sans-arabic@5", "ibm-plex-sans-arabic-{s}-{w}-normal.woff2"
CSS = """
:root{--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--ring:rgba(11,11,11,.10);--blue:#2a78d6;--blue6:#184f95;
--blue7:#0d366b;--blue1:#cde2fb;--wash:#eaf2fc;--track:#f0efec;--good:#0ca30c}
*{box-sizing:border-box;margin:0;padding:0}
html{background:var(--page)}
body{width:__W__px;padding:26px;font-family:"WBrief","IBM Plex Sans Arabic","Noto Kufi Arabic","Noto Sans Arabic","Tajawal","Cairo",system-ui,-apple-system,"Segoe UI","Geeza Pro",
"Noto Sans","Noto Sans CJK JP","Noto Sans JP","Hiragino Sans","PingFang SC","Microsoft YaHei","Apple SD Gothic Neo","Malgun Gothic","Noto Sans Hebrew","Arial Hebrew",
"Noto Sans Devanagari","Kohinoor Devanagari","Noto Sans Thai","Thonburi","DejaVu Sans",sans-serif;
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
    if not RTL:  # left-to-right brief: bold only, so the text wraps normally
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
    elif RTL_CH.search(u):  # a right-to-left unit follows the number in reading order
        val = f"{v} <small>{rich(u)}</small>"
    else:
        val = f'<span dir="ltr">{v}<small>{" " if u.isalpha() else ""}{rich(u)}</small></span>'
    tone = TONES.get(k.get("tone", "neutral"), TONES["neutral"])
    tag = f'<div class="tag"><i style="background:{tone}"></i>{rich(k["tag"])}</div>' if k.get("tag") else ""
    return f'<div class="kpi"><div class="l">{rich(k.get("label", ""))}</div><div class="v">{val}</div><div class="nt">{rich(k.get("note", ""))}</div>{tag}</div>'


def card(c):
    ic = c.get("icon", "pulse"); fl = " class=flip" if ic in FLIP and RTL else ""
    svg = f'<svg viewBox="0 0 24 24"{fl}>{ICONS.get(ic, ICONS["pulse"])}</svg>'
    chip = ""
    if c.get("chip"):
        txt, sty = CHS.get(c["chip"], (c["chip"], "muted")); chip = f'<span class="chip {sty}">{rich(txt)}</span>'
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


CHS = dict(CHIPS)


def build(S, fcss, W):
    global RTL, CHS
    lang = str(S.get("lang", "ar")).strip().lower() or "ar"; base = re.split(r"[-_]", lang)[0]
    RTL = S.get("dir") == "rtl" or (S.get("dir") != "ltr" and base in RTL_LANGS)
    CH0, LG = (CHIPS, dict(LEG)) if base == "ar" else (CHIPS_EN, dict(LEG_EN))
    CHS = {k: ((S.get("chips") or {}).get(k) or CH0[k][0], CH0[k][1]) for k in CH0}; LG.update({k: v for k, v in (S.get("legend_text") or {}).items() if v})
    if base not in ("ar", "en"):
        miss = [f"chips.{k}" for k in CH0 if not (S.get("chips") or {}).get(k)] + [f"legend_text.{k}" for k in CH0 if not (S.get("legend_text") or {}).get(k)]
        miss += [k for k in ("plan_title", "alerts_label") if not S.get(k)]
        if miss:
            print(f"brief: no '{lang}' text for {', '.join(miss)} - English used. Add them to the spec and render again.")
    CH, en_ui = CHS, base != "ar"
    kp = "".join(kpi(k) for k in S.get("kpis", []))
    cards = "".join(card(c) for c in S.get("cards", []))
    plan = ""
    if S.get("plan"):
        items = "".join(f'<li><b class="pl">{rich(p.get("lead", ""))}</b>' + (f'<span class="pt">{rich(p["text"])}</span>' if p.get("text") else "") + "</li>" for p in S["plan"])
        plan = (f'<section class="plan"><div class="ch"><div class="ico"><svg viewBox="0 0 24 24">{ICONS["check"]}</svg></div>'
                f'<h2>{rich(S.get("plan_title", "Your plan" if en_ui else "خطتك العملية"))}</h2></div><ol>{items}</ol></section>')
    alert = ""
    if S.get("alerts"):
        lbl = f'<b class="lbl">{rich(S.get("alerts_label", "Note" if en_ui else "انتبه"))}:</b> '
        ps = "".join(f"<p>{lbl if i == 0 else ''}{rich(x)}</p>" for i, x in enumerate(S["alerts"]))
        alert = f'<section class="alert">{ALERT}<div>{ps}</div></section>'
    keys = S.get("legend") or list(dict.fromkeys(c.get("chip") for c in S.get("cards", []) if c.get("chip") in CHIPS))
    legend = "".join(f'<span><span class="chip {CH[k][1]}">{CH[k][0]}</span>{LG[k]}</span>' for k in keys if k in CHIPS)
    legend = f'<div class="legend">{legend}</div>' if legend else ""
    foot = "".join(f"<p>{rich(x)}</p>" for x in S.get("footer", []))
    hd = f'<div class="head">{rich(S["headline"])}</div>' if S.get("headline") else ""
    return (f'<!DOCTYPE html><html lang="{html.escape(lang)}" dir="{"rtl" if RTL else "ltr"}"><head><meta charset="utf-8"><meta name="viewport" content="width={W}">'
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
        print("web font not available - the system font is used (install one, or pass --font)")
    if re.search(r"[\u0e00-\u0e7f\u0900-\u097f\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af\u0590-\u05ff]", json.dumps(S, ensure_ascii=False)) and not a.font:
        print("note: the spec uses a script the bundled font does not cover (CJK, Korean, Thai, Devanagari or Hebrew) - it is drawn with the "
              "system font; check brief.png for empty boxes and pass --font with a Noto Sans file for that script if you see any")
    hp, png, pdf, h = render(build(S, face_css(fl), a.width), a.out, a.width)
    print("Done:", ", ".join(x for x in (png, pdf, hp) if x) + (f" ({a.width}x{h} px at 2x)" if h else ""))


if __name__ == "__main__":
    main()
