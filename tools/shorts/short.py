"""Carousel -> YouTube Short (1080x1920, 30 fps, swipe transitions, progress bar, end card).
Usage: python3 short.py spec.json OUT.mp4
spec = {"slides":[{"img":path,"dur":3.4},...], "end":{"img":path,"dur":3.0} (optional),
        "kicker":"ALBANIAN WITH ELISA", "audio_seed":1}
"""
import sys, json, subprocess, os, tempfile, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
BG = (236, 228, 216); INK = (27, 27, 27); RED = (179, 20, 27)
CW, CH = 960, 1200; CX, CY = (W - CW) // 2, 330; RADIUS = 34
TRANS = 0.45; FADE = 0.5
spec = json.load(open(sys.argv[1])); OUT = sys.argv[2]
FONT = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-SemiBold.otf', 26)
HERE = os.path.dirname(os.path.abspath(__file__))

def ease(x): return 4*x*x*x if x < .5 else 1 - (-2*x + 2) ** 3 / 2

# background with soft grain + gentle top light
rng = np.random.default_rng(7)
bg = np.zeros((H, W, 3), np.float32) + BG
yy = np.linspace(1, 0, H)[:, None, None]
bg += yy * 8
bg += rng.normal(0, 2.2, (H, W, 1))
BGI = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))

mask = Image.new('L', (CW, CH), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, CW - 1, CH - 1], RADIUS, fill=255)
sh = Image.new('L', (CW + 160, CH + 160), 0); ImageDraw.Draw(sh).rounded_rectangle([80, 80 + 18, 80 + CW, 80 + CH + 18], RADIUS, fill=70)
SHADOW = sh.filter(ImageFilter.GaussianBlur(28))

slides = [Image.open(s['img']).convert('RGB') for s in spec['slides']]
durs = [float(s['dur']) for s in spec['slides']]
end = spec.get('end'); endimg = Image.open(end['img']).convert('RGB').resize((W, H)) if end else None
kicker = spec.get('kicker', 'ALBANIAN WITH ELISA')

def card(i, zoom):
    im = slides[i]
    w, h = int(CW * zoom), int(CH * zoom)
    big = im.resize((w, h), Image.BICUBIC)
    l, t = (w - CW) // 2, (h - CH) // 2
    return big.crop((l, t, l + CW, t + CH))

def base(prog_i, prog_f):
    f = BGI.copy(); d = ImageDraw.Draw(f)
    d.text((60, 196), ' '.join(kicker), font=FONT, fill=(90, 84, 80))
    n = len(slides); gap = 10; x0, x1, y = 60, 1020, 252
    sw = (x1 - x0 - gap * (n - 1)) / n
    for k in range(n):
        a = x0 + k * (sw + gap)
        d.rounded_rectangle([a, y, a + sw, y + 6], 3, fill=(214, 204, 192))
        fill = 1 if k < prog_i else (prog_f if k == prog_i else 0)
        if fill > 0: d.rounded_rectangle([a, y, a + max(6, sw * fill), y + 6], 3, fill=RED)
    return f

def put(f, im, x):
    shadow_layer = Image.new('RGB', SHADOW.size, (120, 100, 80))
    f.paste(shadow_layer, (int(x) - 80, CY - 80), SHADOW)
    f.paste(im, (int(x), CY), mask)

total = sum(durs) + (end['dur'] if end else 0)
nfr = int(round(total * FPS))
tmpwav = tempfile.mktemp(suffix='.wav')
subprocess.run(['python3', os.path.join(HERE, 'pad.py'), str(total), tmpwav, str(spec.get('audio_seed', 1))], check=True, stdout=subprocess.DEVNULL)
ff = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-i', tmpwav, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
                       '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
starts = np.cumsum([0] + durs)
last_carousel = None
for fi in range(nfr):
    t = fi / FPS
    if t < starts[-1]:
        i = int(np.searchsorted(starts, t, side='right') - 1); i = min(i, len(slides) - 1)
        lt = t - starts[i]; d = durs[i]
        f = base(i, min(1, lt / d))
        z = 1.0 + 0.018 * (lt / d)
        if i > 0 and lt < TRANS:          # swipe in from the right
            p = ease(lt / TRANS)
            put(f, card(i - 1, 1.018), CX - p * 1100)
            put(f, card(i, z), CX + (1 - p) * 1100)
        else:
            put(f, card(i, z), CX)
        last_carousel = f
    else:
        lt = t - starts[-1]
        zz = 1.0 + 0.04 * (lt / end['dur'])
        w, h = int(W * zz), int(H * zz)
        e = endimg.resize((w, h), Image.BICUBIC).crop(((w - W) // 2, (h - H) // 2, (w - W) // 2 + W, (h - H) // 2 + H))
        if lt < FADE: f = Image.blend(last_carousel, e, ease(lt / FADE))
        else: f = e
    ff.stdin.write(f.tobytes())
ff.stdin.close(); ff.wait(); os.remove(tmpwav)
print('wrote', OUT, round(total, 2), 's')
