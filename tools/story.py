#!/usr/bin/env python3
"""Render Instagram/Facebook Story frames (1080x1920 PNG) for Albanian with Elisa.
Usage: python3 story.py frames.json OUTDIR FONTDIR
frames.json = {"frames":[{...}, ...]}  Frame types:
  photo : {"type":"photo","bg":"path.jpg","kicker":"","title":"html","sub":"","hand":"handwritten accent","pos":"bottom|center|top","dim":0.0-1}
  count : {"type":"count","bg":"path.jpg","n":"6","unit":"days","line":"Wednesday 28 October · 10:00","hand":"..."}
  phone : {"type":"phone","shot":"screenshot.png","blur":0-40,"kicker":"","title":"html","sub":"","tone":"cream|red|ink","crop":"top|center"}
  text  : {"type":"text","tone":"cream|red|ink","kicker":"","title":"html","sub":"","hand":""}
Safe zone: nothing important above y=250 or below y=1560 (Instagram UI).
"""
import json, sys, html, pathlib, base64, mimetypes
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).parent))
data = json.load(open(sys.argv[1]))
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
FD = pathlib.Path(sys.argv[3])
fd64 = lambda n: "data:font/woff2;base64," + base64.b64encode((FD / n).read_bytes()).decode()
def img64(p):
    p = pathlib.Path(p); mt = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    return f"data:{mt};base64," + base64.b64encode(p.read_bytes()).decode()
E = lambda s: html.escape(s or "")

# logo markup shared with the carousel renderer
src = (pathlib.Path(__file__).parent / "render.py").read_text()
HALF = src.split('HALF = "', 1)[1].split('"', 1)[0]
LOGO = ('<span class="logo"><svg class="mk" viewBox="12 4 76 90" aria-hidden="true"><defs><clipPath id="c"><circle cx="50" cy="56" r="36"/></clipPath>'
        f'<path id="h" d="{HALF}"/><g id="e"><use href="#h"/><use href="#h" transform="matrix(-1 0 0 1 640 0)"/><path d="M318.8 140H321.2V384H318.8Z"/></g></defs>'
        '<circle cx="50" cy="56" r="36" fill="none" stroke="currentColor" stroke-width="2.2"/>'
        '<path d="M0 100V84L22 69L31 75L47 58L58 68L66 63L100 87V100Z" fill="currentColor" clip-path="url(#c)"/>'
        '<g transform="translate(50 5) scale(.2) translate(-320 -93.3)"><use href="#e" stroke-width="15" stroke-linejoin="round" style="fill:var(--mk-g);stroke:var(--mk-g)"/><use href="#e" fill="currentColor"/></g></svg>'
        '<span class="wm"><b>Albanian</b><i>with Elisa</i></span></span>')

CSS = f"""
@font-face{{font-family:F;src:url({fd64("playfair-display-latin-600-normal.woff2")});font-weight:600}}
@font-face{{font-family:F;src:url({fd64("playfair-display-latin-400-italic.woff2")});font-weight:400;font-style:italic}}
@font-face{{font-family:I;src:url({fd64("inter-latin-500-normal.woff2")});font-weight:500}}
@font-face{{font-family:I;src:url({fd64("inter-latin-600-normal.woff2")});font-weight:600}}
@font-face{{font-family:P;src:url({fd64("pinyon-script-latin-400-normal.woff2")});font-weight:400}}
@font-face{{font-family:J;src:url({fd64("jost-latin-500-normal.woff2")});font-weight:500}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;position:relative;font-family:I;color:#FBF7F1;background:#1B1B1B;
  font-variant-ligatures:none;font-feature-settings:"liga" 0,"calt" 0,"clig" 0}}
.bg{{position:absolute;inset:0;background-size:cover;background-position:center}}
.shade{{position:absolute;inset:0}}
.logo{{position:absolute;top:150px;left:80px;display:inline-flex;align-items:center;gap:14px;color:#FBF7F1;--mk-g:transparent}}
.logo .mk{{height:92px;width:auto;filter:drop-shadow(0 2px 8px rgba(0,0,0,.25))}}
.logo .wm{{display:flex;flex-direction:column;align-items:center;line-height:1;text-shadow:0 2px 10px rgba(0,0,0,.25)}}
.logo b{{font:400 56px/1 P;padding:0 8px 0 2px;margin-top:-6px}}
.logo i{{font:500 15px/1 J;font-style:normal;letter-spacing:.44em;padding-left:.44em;text-transform:uppercase;margin-top:5px}}
.box{{position:absolute;left:80px;right:80px;display:flex;flex-direction:column;gap:30px}}
.pos-bottom{{bottom:380px}} .pos-center{{top:50%;transform:translateY(-50%)}} .pos-top{{top:330px}}
.kick{{align-self:flex-start;font:600 24px I;letter-spacing:.2em;text-transform:uppercase;padding:14px 24px;border-radius:999px;
  background:rgba(251,247,241,.16);border:2px solid rgba(251,247,241,.55);backdrop-filter:blur(6px)}}
.t{{font:600 104px/1.03 F;letter-spacing:-.02em;text-shadow:0 4px 30px rgba(0,0,0,.25);text-wrap:balance}}
.t em{{font-style:italic;font-weight:400}}
.s{{font:500 40px/1.4 I;opacity:.95;max-width:880px;text-shadow:0 2px 16px rgba(0,0,0,.3)}}
.hand{{font:400 92px/1 P;color:#FBF7F1;margin-top:6px;text-shadow:0 2px 16px rgba(0,0,0,.3)}}
.stamp{{position:absolute;bottom:250px;left:80px;right:80px;display:flex;justify-content:space-between;font:500 24px I;letter-spacing:.16em;text-transform:uppercase;opacity:.85}}
/* countdown */
.num{{font:400 560px/0.8 F;font-style:italic;letter-spacing:-.04em;text-shadow:0 8px 60px rgba(0,0,0,.35)}}
.unit{{font:600 60px I;letter-spacing:.3em;text-transform:uppercase;margin-top:130px}}
.line{{font:500 40px I;margin-top:40px;padding:22px 34px;border-radius:999px;background:#B3141B;align-self:flex-start}}
/* tones */
body.cream{{background:#F5EFE6;color:#1B1B1B}} body.cream .logo{{color:#1B1B1B}} body.cream .kick{{background:#fff;border-color:#E4DCD0;color:#B3141B}}
body.cream .t,body.cream .s,body.cream .hand{{text-shadow:none}} body.cream .t em{{color:#B3141B}} body.cream .s{{color:#4A4540}} body.cream .hand{{color:#B3141B}}
body.red{{background:#B3141B;color:#FBF7F1}} body.ink{{background:#1B1B1B;color:#FBF7F1}} body.red .t,body.ink .t,body.red .s,body.ink .s{{text-shadow:none}}
body.red .kick{{background:rgba(255,255,255,.12)}}
/* phone mockup */
.phone{{position:absolute;left:50%;transform:translateX(-50%);top:330px;width:560px;height:1100px;border-radius:72px;background:#111;padding:18px;
  box-shadow:0 40px 90px rgba(0,0,0,.28),0 0 0 2px rgba(0,0,0,.08)}}
.phone .scr{{width:100%;height:100%;border-radius:56px;overflow:hidden;background:#fff;position:relative}}
.phone .scr img{{width:100%;display:block}}
.phone .notch{{position:absolute;top:30px;left:50%;transform:translateX(-50%);width:150px;height:40px;border-radius:30px;background:#111;z-index:2}}
body.withphone .box{{bottom:250px;gap:18px}}
body.withphone .t{{font-size:76px}} body.withphone .s{{font-size:34px}}
"""
FIT = """<script>
document.querySelectorAll('.t').forEach(el=>{let s=parseFloat(getComputedStyle(el).fontSize);while(el.scrollHeight>(document.body.classList.contains('withphone')?260:620)&&s>50){s-=2;el.style.fontSize=s+'px'}});
</script>"""

def shade(dim, pos):
    a = max(0.0, min(1.0, dim))
    if pos == "center":
        return f"background:rgba(0,0,0,{0.28 + 0.4 * a})"
    if pos == "top":
        return f"background:linear-gradient(180deg,rgba(0,0,0,{0.55 + 0.3 * a}) 0%,rgba(0,0,0,{0.15 + 0.2 * a}) 45%,rgba(0,0,0,0) 70%,rgba(0,0,0,.25) 100%)"
    return f"background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,{0.1 + 0.2 * a}) 45%,rgba(0,0,0,{0.62 + 0.3 * a}) 100%)"

frames = data["frames"]
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    for i, f in enumerate(frames, 1):
        t = f["type"]; cls = ""; stamp = f'<div class="stamp"><span>{E(f.get("foot","Mëso shqip me Elisën"))}</span><span>{E(f.get("foot_r",""))}</span></div>'
        kick = f'<span class="kick">{E(f["kicker"])}</span>' if f.get("kicker") else ""
        hand = f'<div class="hand">{E(f["hand"])}</div>' if f.get("hand") else ""
        sub = f'<div class="s">{E(f["sub"])}</div>' if f.get("sub") else ""
        if t == "photo":
            pos = f.get("pos", "bottom")
            bg = f'<div class="bg" style="background-image:url({img64(f["bg"])});background-position:{f.get("focus","center")}"></div><div class="shade" style="{shade(f.get("dim",0.2),pos)}"></div>'
            body = f'{bg}{LOGO}<div class="box pos-{pos}">{kick}<div class="t">{f.get("title","")}</div>{sub}{hand}</div>{stamp}'
        elif t == "count":
            bg = f'<div class="bg" style="background-image:url({img64(f["bg"])});background-position:{f.get("focus","center")}"></div><div class="shade" style="{shade(f.get("dim",0.5),"center")}"></div>'
            body = (f'{bg}{LOGO}<div class="box pos-center" style="gap:0">{kick}<div class="num">{E(f["n"])}</div><div class="unit">{E(f.get("unit","days"))}</div>'
                    f'<div class="line">{E(f.get("line",""))}</div>{hand}</div>{stamp}')
        elif t == "phone":
            cls = (f.get("tone") or "cream") + " withphone"
            blur = f.get("blur", 0); crop = f.get("crop", "top")
            sh = f'<img src="{img64(f["shot"])}" style="filter:blur({blur}px);transform:scale({1.08 if blur else 1});{"margin-top:-" + str(f.get("offset",0)) + "px" if f.get("offset") else ""}">'
            body = (f'{LOGO}<div class="phone"><div class="notch"></div><div class="scr">{sh}</div></div>'
                    f'<div class="box" style="bottom:250px">{kick}<div class="t">{f.get("title","")}</div>{sub}</div>')
            stamp = ""
        elif t == "art":
            cls = f.get("tone") or "cream"
            st = f.get("art_style", "position:absolute;left:50%;transform:translateX(-50%);bottom:-330px;width:980px")
            body = (f'{LOGO}<img src="{img64(f["art"])}" style="{st}">'
                    f'<div class="box pos-top">{kick}<div class="t">{f.get("title","")}</div>{sub}{hand}</div>')
        else:
            cls = f.get("tone") or "cream"
            body = f'{LOGO}<div class="box pos-center">{kick}<div class="t">{f.get("title","")}</div>{sub}{hand}</div>{stamp}'
        if cls.startswith("cream"):
            body = body.replace('class="logo"', 'class="logo" style="color:#1B1B1B"')
        doc = f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body class="{cls}">{body}{FIT}</body></html>'
        pg.set_content(doc, wait_until="load"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(200)
        name = f.get("name") or f"story-{i}"
        pg.screenshot(path=str(out / f"{name}.png"))
        print("wrote", out / f"{name}.png")
    b.close()
