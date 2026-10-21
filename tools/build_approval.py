#!/usr/bin/env python3
"""Build the weekly approval page. Usage: python3 build_approval.py week.json OUTDIR
week.json = {"title": "Week of 26 October",
  "days": {"YYYY-MM-DD": {"weekday": "Monday", "theme": "..."}},
  "posts": [{"date","time","kind","platforms":["instagram","facebook","threads","reddit","tiktok"],"text","images":["YYYY-MM-DD/slide-1.jpg"],"label"?,"title"?,
             "aspect"?: "story" (9:16 thumbnails), "videos"?: ["YYYY-MM-DD/clip.mp4"], "status"?: "new"|"approved"|"changed", "note"?: "..."}],
  optional page texts: "eyebrow", "lead", "facts": [".."], "end" (html)}
Images must already be in OUTDIR/img/<date>/... Writes OUTDIR/index.html; publish it with the images as files img/... ."""
import json, sys, html, pathlib
DATA = json.load(open(sys.argv[1])); OUT = pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
NICE = {"instagram": "Instagram", "threads": "Threads", "facebook": "Facebook", "reddit": "Reddit", "tiktok": "TikTok", "ig_story": "Instagram story", "fb_story": "Facebook story"}
STAT = {"new": ("Needs your go", "st-new"), "approved": ("Already approved", "st-ok"), "changed": ("Changed · needs your go", "st-new")}
posts = sorted(DATA["posts"], key=lambda p: (p["date"], p["time"]))
LB = '\n<div class="lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="Image preview">\n<img id="lb-img" alt="">\n<div class="lb-row"><button id="lb-prev" aria-label="Previous image">‹ Prev</button><span class="lb-n" id="lb-n"></span><button id="lb-next" aria-label="Next image">Next ›</button><button id="lb-close">Close</button></div>\n</div>\n<script>\n(function(){\n  const lb=document.getElementById("lb"), im=document.getElementById("lb-img"), n=document.getElementById("lb-n");\n  let list=[], i=0, x0=null;\n  function show(k){ i=(k+list.length)%list.length; im.src=list[i].src; im.alt=list[i].alt; n.textContent=(i+1)+" / "+list.length; }\n  document.querySelectorAll(".strip").forEach(strip=>{\n    const imgs=[...strip.querySelectorAll("img")];\n    imgs.forEach((el,k)=>{ el.tabIndex=0; el.setAttribute("role","button");\n      const open=()=>{ list=imgs; show(k); lb.hidden=false; document.getElementById("lb-close").focus(); };\n      el.addEventListener("click",open); el.addEventListener("keydown",e=>{ if(e.key==="Enter"||e.key===" "){ e.preventDefault(); open(); } }); });\n  });\n  document.getElementById("lb-prev").onclick=()=>show(i-1);\n  document.getElementById("lb-next").onclick=()=>show(i+1);\n  document.getElementById("lb-close").onclick=()=>{ lb.hidden=true; };\n  lb.addEventListener("click",e=>{ if(e.target===lb) lb.hidden=true; });\n  document.addEventListener("keydown",e=>{ if(lb.hidden) return; if(e.key==="Escape") lb.hidden=true; if(e.key==="ArrowRight") show(i+1); if(e.key==="ArrowLeft") show(i-1); });\n  lb.addEventListener("touchstart",e=>{ x0=e.touches[0].clientX; },{passive:true});\n  lb.addEventListener("touchend",e=>{ if(x0===null) return; const dx=e.changedTouches[0].clientX-x0; if(Math.abs(dx)>40) show(dx<0?i+1:i-1); x0=null; });\n})();\n</script>'
days = {}
for p in posts: days.setdefault(p["date"], []).append(p)
themes = {k: (v["weekday"], v["theme"]) for k, v in DATA["days"].items()}
E = html.escape
TXT = lambda p: f'<p class="txt">{E(p["text"])}</p>' if p.get("text") else ""

def fmt_day(date):
    import datetime
    dt = datetime.date.fromisoformat(date); return dt.strftime("%a %-d %b")

sec = []
for date, ps in days.items():
    wd, th = themes[date]
    cards = []
    for p in ps:
        chips = "".join(f'<span class="chip">{NICE[x]}</span>' for x in p["platforms"])
        imgs = ""
        if p.get("images"):
            sc = "strip story" if p.get("aspect") == "story" else "strip"
            imgs = f'<div class="{sc}">' + "".join(f'<img src="img/{x}" alt="{E(p["kind"])} image {i+1}" loading="lazy">' for i, x in enumerate(p["images"])) + "</div>"
        if p.get("videos"):
            imgs += '<div class="vids">' + "".join(f'<video src="img/{v}" controls playsinline preload="metadata"' + (f' poster="img/{v.rsplit(".", 1)[0]}.jpg"' if (OUT / "img" / (v.rsplit(".", 1)[0] + ".jpg")).exists() else "") + '></video>' for v in p["videos"]) + "</div>"
        st = STAT.get(p.get("status", ""))
        stc = f'<span class="st {st[1]}">{st[0]}</span>' if st else ""
        note = f'<p class="note">{E(p["note"])}</p>' if p.get("note") else ""
        title = f'<p class="rtitle">{E(p["title"])}</p>' if p.get("title") else ""
        lab = f'<span class="lab">{E(p["label"])}</span>' if p.get("label") else ""
        cards.append(f'''<article class="post"><div class="when"><span class="t">{p["time"]}</span></div>
<div class="body"><div class="meta"><b>{E(p["kind"])}</b>{lab}<span class="chips">{chips}</span>{stc}</div>{note}{imgs}{title}{TXT(p)}</div></article>''')
    sec.append(f'''<section class="day" id="d{date[-2:]}"><header class="dh"><h2>{wd}</h2><span class="date">{fmt_day(date)}</span><span class="theme">{E(th)}</span><span class="cnt">{len(ps)} items</span></header>{"".join(cards)}</section>''')

nav = "".join(f'<a href="#d{d[-2:]}">{themes[d][0][:3]}</a>' for d in days)
total = sum(len(p["platforms"]) for p in posts)
LEAD = "Every post that goes out Monday to Sunday, in the order it goes out. Times are Paris time. Tap any image to see it full size, then use the arrows or swipe through the slides."
FACTS = DATA.get("facts") or [f"{total} posts", "Instagram · Facebook · Threads · TikTok · Reddit", "Elisa: check every Albanian word and pronunciation"]
FACTS_HTML = "".join(f'<span class="fact{" warn" if i == len(FACTS) - 1 else ""}">{E(f)}</span>' for i, f in enumerate(FACTS))
END_DEF = "<b>When you're both happy:</b> reply <b>go</b> in the chat, plus anything to change (for example \"Friday quiz: swap qershi for another word\"). Nothing is scheduled before that."
END = DATA.get("end") or END_DEF
page = f'''<title>{DATA["title"]}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=Manrope:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
/* Layout: a running order. One column per day, each post a row with its air time on the left. */
:root{{--bg:#F7F5F2;--surface:#FFFFFF;--ink:#1C1A19;--muted:#6F6862;--line:#E4DFDA;--accent:#B3141B;--soft:#F6E3E2;
--display:"Playfair Display",Georgia,serif;--body:"Manrope",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#141312;--surface:#1D1B1A;--ink:#F1EDE9;--muted:#A39B94;--line:#33302D;--accent:#F0646A;--soft:#3A1F20;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#141312;--surface:#1D1B1A;--ink:#F1EDE9;--muted:#A39B94;--line:#33302D;--accent:#F0646A;--soft:#3A1F20;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--ink);font:15px/1.55 var(--body);padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:28px 64px}}
.wrap{{max-width:820px;margin:0 auto;display:flex;flex-direction:column;gap:28px}}
.top{{display:flex;flex-direction:column;gap:12px}}
.eyebrow{{font:500 12px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}}
h1{{font:600 clamp(30px,6vw,44px)/1.1 var(--display);margin:0;text-wrap:balance}}
.lead{{margin:0;color:var(--muted);max-width:62ch}}
.facts{{display:flex;flex-wrap:wrap;gap:8px}}
.fact{{font-size:13px;padding:6px 10px;border-radius:999px;background:var(--surface);border:1px solid var(--line)}}
.fact.warn{{background:var(--soft);border-color:transparent}}
nav{{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;display:flex;gap:6px;flex-wrap:wrap;padding:10px 0;background:var(--bg);border-bottom:1px solid var(--line)}}
nav a{{font:500 13px var(--mono);color:var(--ink);text-decoration:none;padding:5px 10px;border:1px solid var(--line);border-radius:8px;background:var(--surface)}}
nav a:focus-visible,nav a:hover{{border-color:var(--accent);outline:none}}
.day{{display:flex;flex-direction:column;gap:12px;scroll-margin-top:64px}}
.dh{{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 12px;padding-bottom:8px;border-bottom:2px solid var(--ink)}}
.dh h2{{font:600 26px/1.2 var(--display);margin:0}}
.date{{font:500 13px var(--mono);color:var(--muted)}}
.theme{{font-weight:600}}
.cnt{{margin-left:auto;font:500 12px var(--mono);color:var(--muted)}}
.post{{display:grid;grid-template-columns:64px minmax(0,1fr);gap:14px;padding:14px 0;border-bottom:1px solid var(--line)}}
.t{{font:500 15px var(--mono);color:var(--accent);font-variant-numeric:tabular-nums}}
.body{{display:flex;flex-direction:column;gap:10px;min-width:0}}
.meta{{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px}}
.lab{{color:var(--muted);font-size:14px}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}}
.chip{{font-size:12px;padding:2px 8px;border-radius:6px;background:var(--surface);border:1px solid var(--line);color:var(--muted)}}
.strip{{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px}}
.strip img{{flex:none;width:160px;aspect-ratio:4/5;object-fit:cover;border-radius:6px;border:1px solid var(--line);cursor:zoom-in}}
.strip.story img{{width:132px;aspect-ratio:9/16}}
.vids{{display:flex;gap:10px;overflow-x:auto;padding-bottom:4px}}
.vids video{{flex:none;width:220px;aspect-ratio:9/16;border-radius:8px;background:#000;border:1px solid var(--line)}}
.vids video.wide{{width:420px;aspect-ratio:16/9}}
.st{{font:600 11px var(--mono);letter-spacing:.04em;text-transform:uppercase;padding:3px 8px;border-radius:6px}}
.st-new{{background:var(--soft);color:var(--accent)}} .st-ok{{background:var(--surface);color:var(--muted);border:1px solid var(--line)}}
.note{{margin:0;font-size:14px;color:var(--muted)}}
.strip img:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
.lb{{position:fixed;inset:0;z-index:20;background:rgba(0,0,0,.9);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:calc(12px + env(safe-area-inset-top,0px)) max(12px,env(safe-area-inset-right,0px)) calc(12px + env(safe-area-inset-bottom,0px)) max(12px,env(safe-area-inset-left,0px))}}
.lb img{{max-height:82vh;max-width:100%;border-radius:8px}}
.lb-row{{display:flex;gap:10px;align-items:center}}
.lb-row button{{background:#fff;color:#111;border:0;border-radius:999px;padding:9px 18px;font:600 14px var(--body);cursor:pointer}}
.lb-n{{color:#ddd;font:500 13px var(--mono);min-width:56px;text-align:center}}
[hidden]{{display:none!important}}
.rtitle{{margin:0;font-weight:700}}
.txt{{margin:0;white-space:pre-wrap;overflow-wrap:anywhere;padding:12px 14px;border-radius:10px;background:var(--surface);border:1px solid var(--line)}}
.end{{padding:18px;border-radius:14px;background:var(--surface);border:1px solid var(--line)}}
.end p{{margin:0}}
@media (max-width:520px){{.post{{grid-template-columns:1fr;gap:6px}}}}
</style>
<div class="wrap">
<header class="top">
<span class="eyebrow">{E(DATA.get("eyebrow", "For approval · Albanian with Elisa"))}</span>
<h1>{DATA["title"]}</h1>
<p class="lead">{E(DATA.get("lead", LEAD))}</p>
<div class="facts">{FACTS_HTML}</div>
</header>
<nav aria-label="Days">{nav}</nav>
{"".join(sec)}
<section class="end"><p>{END}</p></section>
</div>'''
page = page + LB
(OUT / "index.html").write_text(page)
print("wrote", OUT / "index.html", "posts:", total)
