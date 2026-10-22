"""Soft original ambient bed for Shorts. Usage: python3 pad.py SECONDS OUT.wav [seed]"""
import sys, numpy as np, wave

SR = 44100
dur = float(sys.argv[1]); out = sys.argv[2]; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
rng = np.random.default_rng(seed)
n = int(dur * SR) + SR * 3
t = np.arange(n) / SR
L = np.zeros(n); R = np.zeros(n)

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
# F major, warm and calm: Fmaj7 - Am7 - Bbmaj7 - C(add9)
chords = [[53, 57, 60, 64], [57, 60, 64, 67], [58, 62, 65, 69], [48, 55, 62, 64]]
roots = [41, 45, 46, 48]
bar = 4.0

def env(length, a, r):
    e = np.ones(length)
    ai, ri = int(a * SR), int(r * SR)
    e[:ai] = np.linspace(0, 1, ai) ** 2
    e[-ri:] *= np.linspace(1, 0, ri) ** 1.5
    return e

k = 0; start = 0.0
while start < dur + 2:
    ch = chords[k % 4]; rt = roots[k % 4]
    s0 = int(start * SR); ln = int((bar + 1.6) * SR)
    s1 = min(n, s0 + ln); ln = s1 - s0
    if ln <= 0: break
    tt = np.arange(ln) / SR
    e = env(ln, 1.1, 1.6)
    for m in ch:
        f = hz(m)
        for side, det in ((L, -0.0018), (R, 0.0018)):
            ff = f * (1 + det)
            w = np.sin(2*np.pi*ff*tt) + 0.22*np.sin(4*np.pi*ff*tt) + 0.06*np.sin(6*np.pi*ff*tt)
            side[s0:s1] += 0.055 * w * e * (1 + 0.04*np.sin(2*np.pi*0.3*tt))
    fb = hz(rt)
    bass = 0.09 * np.sin(2*np.pi*fb*tt) * env(ln, 0.6, 1.4)
    L[s0:s1] += bass; R[s0:s1] += bass
    # two soft bell notes per bar
    for off, m in ((0.5, ch[2] + 12), (2.5, ch[3] + 12)):
        b0 = s0 + int(off * SR); bl = int(2.2 * SR); b1 = min(n, b0 + bl)
        if b1 <= b0: continue
        tb = np.arange(b1 - b0) / SR; f = hz(m)
        bell = (np.sin(2*np.pi*f*tb) + 0.3*np.sin(2*np.pi*2.01*f*tb)) * np.exp(-tb * 2.2) * np.minimum(1, tb / 0.01)
        pan = rng.uniform(0.35, 0.65)
        L[b0:b1] += 0.035 * bell * (1 - pan) * 2; R[b0:b1] += 0.035 * bell * pan * 2
    k += 1; start += bar

def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); acc = 0.0
    # vectorised one-pole via scipy-free cumulative trick (chunked)
    from numpy.lib.stride_tricks import sliding_window_view  # noqa (keeps numpy-only)
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y

try:
    from scipy.signal import lfilter, fftconvolve
    a = np.exp(-2*np.pi*3200/SR)
    L = lfilter([1-a], [1, -a], L); R = lfilter([1-a], [1, -a], R)
    conv = fftconvolve
    from scipy.signal import butter
    bh, ah = butter(2, 70/(SR/2), 'highpass')
    HP = lambda x: lfilter(bh, ah, x)
except Exception:
    L = lowpass(L, 3200); R = lowpass(R, 3200)
    HP = lambda x: x
    conv = lambda x, h, mode='full': np.fft.irfft(np.fft.rfft(x, len(x)+len(h)) * np.fft.rfft(h, len(x)+len(h)))[:len(x)+len(h)-1]

ir_len = int(2.6 * SR); ti = np.arange(ir_len) / SR
irL = rng.standard_normal(ir_len) * np.exp(-ti * 2.4); irR = rng.standard_normal(ir_len) * np.exp(-ti * 2.4)
irL /= np.sqrt((irL**2).sum()); irR /= np.sqrt((irR**2).sum())
wL = conv(L, irL)[:n]; wR = conv(R, irR)[:n]
L = 0.75 * L + 0.45 * wL; R = 0.75 * R + 0.45 * wR

m = int(dur * SR); L = HP(L)[:m]; R = HP(R)[:m]
fi, fo = int(0.6 * SR), int(1.4 * SR)
for x in (L, R):
    x[:fi] *= np.linspace(0, 1, fi); x[-fo:] *= np.linspace(1, 0, fo) ** 1.3
st = np.stack([L, R], 1)
rms = np.sqrt((st**2).mean()); st *= (10 ** (-18.5 / 20)) / max(rms, 1e-9)
pk = np.abs(st).max()
if pk > 0.7: st *= 0.7 / pk
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype('<i2').tobytes())
print('wrote', out, round(dur, 2), 's')
