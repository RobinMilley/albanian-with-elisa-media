#!/usr/bin/env python3
"""Render a vertical (1080x1920, 30 fps) motion piece for Albanian with Elisa, frame by frame.
Usage: python3 motion.py spec.json OUT.mp4 FONTDIR
spec = {"fps":30, "scenes":[ scene, ... ], "fade":0.25}
Scene (all have "dur" in seconds and optional kicker/title(html)/sub/hand):
  photo : {"type":"photo","bg":"x.jpg","focus":"center","pos":"bottom|center|top","dim":0.2,"zoom":[1,1.08]}
  phone : {"type":"phone","tone":"cream|red|ink","media":{...}}  media is one of
          {"clip":"frames_dir","fps":30,"start":0.0,"speed":1.0}   (frames_dir holds 00001.jpg ...)
          {"slides":["a.png","b.png"],"each":1.2}
          {"still":"a.png","zoom":[1,1.04],"y":[0,0]}              (y = scroll offset in screenshot px, start->end)
  text  : {"type":"text","tone":"red|cream|ink"}
  end   : {"type":"end","url":"albanian-withelisa.com","pill":"Link in bio","tone":"red"}
Safe zone: titles live between y=250 and y=640; nothing important below y=1500.
"""
import json, sys, html, pathlib, subprocess, threading, http.server, functools, os, shutil
from playwright.sync_api import sync_playwright

spec = json.load(open(sys.argv[1])); OUT = pathlib.Path(sys.argv[2]); FD = pathlib.Path(sys.argv[3]).resolve()
FPS = spec.get("fps", 30); FADE = spec.get("fade", 0.25)
E = lambda s: html.escape(s or "")
ROOT = pathlib.Path("/")

# serve the whole filesystem read-only on a local port so the page can load images by absolute path
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Q, directory="/"))
threading.Thread(target=srv.serve_forever, daemon=True).start()
PORT = srv.server_address[1]
U = lambda p: f"http://127.0.0.1:{PORT}{pathlib.Path(p).resolve()}"

src = (pathlib.Path(__file__).parent / "render.py").read_text()
HALF = src.split('HALF = "', 1)[1].split('"', 1)[0]
def LOGO(cls="logo"):
    return (f'<span class="{cls}"><svg class="mk" viewBox="12 4 76 90" aria-hidden="true"><defs><clipPath id="c"><circle cx="50" cy="56" r="36"/></clipPath>'
        f'<path id="h" d="{HALF}"/><g id="e"><use href="#h"/><use href="#h" transform="matrix(-1 0 0 1 640 0)"/><path d="M318.8 140H321.2V384H318.8Z"/></g></defs>'
        '<circle cx="50" cy="56" r="36" fill="none" stroke="currentColor" stroke-width="2.2"/>'
        '<path d="M0 100V84L22 69L31 75L47 58L58 68L66 63L100 87V100Z" fill="currentColor" clip-path="url(#c)"/>'
        '<g transform="translate(50 5) scale(.2) translate(-320 -93.3)"><use href="#e" stroke-width="15" stroke-linejoin="round" style="fill:var(--mk-g);stroke:var(--mk-g)"/><use href="#e" fill="currentColor"/></g></svg>'
        '<span class="wm"><b>Albanian</b><i>with Elisa</i></span></span>')

CSS = f"""
@font-face{{font-family:F;src:url({U(FD/"playfair-display-latin-600-normal.woff2")});font-weight:600}}
@font-face{{font-family:F;src:url({U(FD/"playfair-display-latin-400-italic.woff2")});font-weight:400;font-style:italic}}
@font-face{{font-family:I;src:url({U(FD/"inter-latin-500-normal.woff2")});font-weight:500}}
@font-face{{font-family:I;src:url({U(FD/"inter-latin-600-normal.woff2")});font-weight:600}}
@font-face{{font-family:P;src:url({U(FD/"pinyon-script-latin-400-normal.woff2")});font-weight:400}}
@font-face{{font-family:J;src:url({U(FD/"jost-latin-500-normal.woff2")});font-weight:500}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;overflow:hidden;position:relative;font-family:I;background:#1B1B1B;font-variant-ligatures:none;font-feature-settings:"liga" 0,"calt" 0,"clig" 0}}
.sc{{position:absolute;inset:0;overflow:hidden;opacity:0;color:#FBF7F1}}
.sc.cream{{background:#F5EFE6;color:#1B1B1B}} .sc.red{{background:#B3141B}} .sc.ink{{background:#1B1B1B}}
.bg{{position:absolute;inset:-2px;background-size:cover;background-position:center;will-change:transform}}
.shade{{position:absolute;inset:0}}
.logo{{position:absolute;top:150px;left:80px;display:inline-flex;align-items:center;gap:14px;color:currentColor;--mk-g:transparent}}
.logo .mk{{height:80px;width:auto}} .logo .wm{{display:flex;flex-direction:column;align-items:center;line-height:1}}
.logo b{{font:400 50px/1 P;padding:0 8px 0 2px;margin-top:-6px}} .logo i{{font:500 13px/1 J;font-style:normal;letter-spacing:.44em;padding-left:.44em;text-transform:uppercase;margin-top:5px}}
.box{{position:absolute;left:80px;right:110px;display:flex;flex-direction:column;gap:26px}}
.pos-bottom{{bottom:430px}} .pos-center{{top:50%;transform:translateY(-50%)}} .pos-top{{top:300px}}
.a{{opacity:0;will-change:transform,opacity}}
.kick{{align-self:flex-start;font:600 24px I;letter-spacing:.2em;text-transform:uppercase;padding:14px 24px;border-radius:999px;background:rgba(251,247,241,.16);border:2px solid rgba(251,247,241,.55)}}
.t{{font:600 100px/1.03 F;letter-spacing:-.02em;text-wrap:balance}} .t em{{font-style:italic;font-weight:400}}
.s{{font:500 40px/1.4 I;opacity:.95}}
.hand{{font:400 88px/1 P}}
.photo .t,.photo .s,.photo .hand{{text-shadow:0 4px 30px rgba(0,0,0,.3)}}
.cream .kick{{background:#fff;border-color:#E4DCD0;color:#B3141B}} .cream .t em{{color:#B3141B}} .cream .s{{color:#4A4540}} .cream .hand{{color:#B3141B}}
.red .kick,.ink .kick{{background:rgba(255,255,255,.12)}}
.phone{{position:absolute;left:50%;top:700px;width:660px;height:1430px;margin-left:-330px;border-radius:84px;background:#111;padding:20px;
  box-shadow:0 50px 110px rgba(0,0,0,.28),0 0 0 2px rgba(0,0,0,.08);will-change:transform}}
.scr{{width:100%;height:100%;border-radius:66px;overflow:hidden;background:#fff;position:relative}}
.scr img{{position:absolute;left:0;top:0;width:100%;display:block}}
.notch{{position:absolute;top:34px;left:50%;transform:translateX(-50%);width:170px;height:46px;border-radius:30px;background:#111;z-index:2}}
.phone-sc .box{{top:250px;bottom:auto;gap:20px}} .phone-sc .t{{font-size:84px}} .phone-sc .s{{font-size:36px}}
.end{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:56px;text-align:center}}
.end .big{{display:inline-flex;flex-direction:column;align-items:center;gap:22px;--mk-g:transparent}}
.end .big .mk{{height:260px;width:auto}} .end .big .wm{{display:flex;flex-direction:column;align-items:center;line-height:1}}
.end .big b{{font:400 150px/1 P}} .end .big i{{font:500 30px/1 J;font-style:normal;letter-spacing:.44em;padding-left:.44em;text-transform:uppercase;margin-top:12px}}
.end .url{{font:600 52px I;letter-spacing:.01em}}
.end .pill{{font:600 34px I;letter-spacing:.16em;text-transform:uppercase;padding:22px 40px;border-radius:999px;background:#FBF7F1;color:#B3141B}}
.end.cream .pill{{background:#B3141B;color:#FBF7F1}}
"""

def shade(dim, pos):
    a = max(0.0, min(1.0, dim))
    if pos == "center": return f"background:rgba(0,0,0,{0.28 + 0.4 * a})"
    if pos == "top": return f"background:linear-gradient(180deg,rgba(0,0,0,{0.5 + 0.3 * a}) 0%,rgba(0,0,0,{0.12 + 0.2 * a}) 45%,rgba(0,0,0,0) 70%,rgba(0,0,0,.3) 100%)"
    return f"background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,{0.1 + 0.2 * a}) 45%,rgba(0,0,0,{0.62 + 0.3 * a}) 100%)"

def textblock(s, pos):
    k = f'<span class="kick a">{E(s["kicker"])}</span>' if s.get("kicker") else ""
    t = f'<div class="t a">{s["title"]}</div>' if s.get("title") else ""
    sub = f'<div class="s a">{E(s["sub"])}</div>' if s.get("sub") else ""
    hd = f'<div class="hand a">{E(s["hand"])}</div>' if s.get("hand") else ""
    return f'<div class="box pos-{pos}">{k}{t}{sub}{hd}</div>'

scenes = spec["scenes"]; t0 = 0.0; parts = []; meta = []
for i, s in enumerate(scenes):
    typ = s["type"]; dur = s["dur"]
    m = {"start": t0, "dur": dur, "type": typ}
    if typ == "photo":
        pos = s.get("pos", "bottom")
        inner = (f'<div class="bg" style="background-image:url({U(s["bg"])});background-position:{s.get("focus","center")}"></div>'
                 f'<div class="shade" style="{shade(s.get("dim",0.2),pos)}"></div>{LOGO()}{textblock(s,pos)}')
        cls = "photo"; m["zoom"] = s.get("zoom", [1.0, 1.08])
    elif typ == "phone":
        md = s["media"]; m["media"] = md
        if "clip" in md:
            n = len([f for f in os.listdir(md["clip"]) if f.endswith(".jpg")]); m["media"] = dict(md, n=n, base=U(md["clip"]))
            img = f'<img src="{U(md["clip"])}/00001.jpg">'
        elif "slides" in md:
            img = "".join(f'<img src="{U(p)}" style="opacity:{1 if j == 0 else 0}">' for j, p in enumerate(md["slides"]))
        else:
            img = f'<img src="{U(md["still"])}">' + (f'<img class="hdr" src="{U(md["top"])}" style="z-index:1">' if md.get("top") else "")
        inner = f'{textblock(s,"top")}<div class="phone"><div class="notch"></div><div class="scr">{img}</div></div>'
        cls = (s.get("tone") or "cream") + " phone-sc"
    elif typ == "end":
        inner = (f'<div class="sc-in end {s.get("tone","red")}" style="position:absolute;inset:0">{LOGO("big a")}'
                 f'<div class="url a">{E(s.get("url",""))}</div>' + (f'<div class="pill a">{E(s["pill"])}</div>' if s.get("pill") else "") + '</div>')
        cls = s.get("tone", "red") + " endsc"
    else:
        inner = f'{LOGO()}{textblock(s,"center")}'; cls = s.get("tone") or "red"
    if "cream" in cls.split()[0] and typ != "photo":
        inner = inner.replace('class="logo"', 'class="logo" style="color:#1B1B1B"')
    parts.append(f'<section class="sc {cls}" id="s{i}">{inner}</section>')
    meta.append(m); t0 += dur
TOTAL = t0

JS = """
const M = __META__, FADE = __FADE__;
const ease = x => x<0?0:x>1?1:1-Math.pow(1-x,3);
const io = x => x<0?0:x>1?1:(x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2);
function seek(t){
  const waits=[];
  M.forEach((m,i)=>{
    const el=document.getElementById('s'+i), lt=t-m.start;
    const vis = lt>=-0.0001 && lt < m.dur + FADE;
    el.style.display = vis ? 'block':'none'; if(!vis) return;
    el.style.zIndex = i;
    el.style.opacity = i===0 ? 1 : ease(lt/FADE);
    // staggered text
    el.querySelectorAll('.a').forEach((a,k)=>{const p=ease((lt-0.12-k*0.16)/0.5); a.style.opacity=p; a.style.transform='translateY('+((1-p)*36)+'px)';});
    if(m.type==='photo'){const z=m.zoom[0]+(m.zoom[1]-m.zoom[0])*(lt/(m.dur+FADE)); el.querySelector('.bg').style.transform='scale('+z+')';}
    if(m.type==='phone'){
      const ph=el.querySelector('.phone'); const p=ease(lt/0.6); ph.style.transform='translateY('+((1-p)*120)+'px)';
      const md=m.media, imgs=el.querySelectorAll('.scr img');
      if(md.clip){const fr=Math.min(md.n, Math.max(1, Math.floor(((md.start||0)+lt*(md.speed||1))*(md.fps||30))+1));
        const src=md.base+'/'+String(fr).padStart(5,'0')+'.jpg'; const im=imgs[0]; if(!im.src.endsWith(src)){im.src=src; waits.push(im.decode().catch(()=>0));}}
      else if(md.slides){const each=md.each||1.2; imgs.forEach((im,q)=>{im.style.opacity = q===0 ? 1 : io((lt-q*each)/0.25);});}
      else {const y=md.y||[0,0], z=md.zoom||[1,1]; const p2=io(Math.min(1,lt/(md.scroll_dur||m.dur))); imgs[0].style.transform='translateY('+(-(y[0]+(y[1]-y[0])*p2)*(620/1170))+'px) scale('+(z[0]+(z[1]-z[0])*p2)+')'; imgs[0].style.transformOrigin='50% 0';}
    }
    if(m.type==='end'){const b=el.querySelector('.big'); if(b){const p=ease(lt/0.7); b.style.transform='scale('+(0.92+0.08*p)+')';}}
  });
  return Promise.all(waits);
}
""".replace("__META__", json.dumps(meta)).replace("__FADE__", str(FADE))

doc = f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(parts)}<script>{JS}</script></body></html>'
tmp = OUT.with_suffix(".html"); tmp.write_text(doc)
nframes = int(round(TOTAL * FPS))
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-r", str(FPS), "-movflags", "+faststart", str(OUT)], stdin=subprocess.PIPE)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto(U(tmp)); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
    for f in range(nframes):
        pg.evaluate("t => seek(t)", f / FPS)
        ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
        if f % 150 == 0: print("frame", f, "/", nframes, flush=True)
    b.close()
ff.stdin.close(); ff.wait(); srv.shutdown()
print("wrote", OUT, f"{TOTAL:.1f}s")
