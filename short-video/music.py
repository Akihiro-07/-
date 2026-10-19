# Synthesizes an original, royalty-free "sunny stroll" backing track.
# Fingerpicked guitar, whistle melody, pizzicato walking bass, light snaps.
# Usage: python3 music.py [seconds] [out.wav]
import sys
import wave
import numpy as np

SR = 44100
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 34.0
OUT = sys.argv[2] if len(sys.argv) > 2 else 'music.wav'
BPM = 100
BEAT = 60 / BPM
BAR = BEAT * 4
SWING = 0.58          # gentle shuffle: offbeat 8ths land a little late
N = int(SR * DUR)
L = np.zeros(N)
R = np.zeros(N)
rng = np.random.default_rng(3)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def at(bar, beat):
    """Time of a (possibly fractional) beat, with swung offbeat 8ths."""
    whole = np.floor(beat)
    frac = beat - whole
    if abs(frac - 0.5) < 1e-6:
        frac = SWING
    return bar * BAR + (whole + frac) * BEAT


def put(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= N or i < 0:
        return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2)
    R[i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2)


_gcache = {}


def guitar(m, length=1.2):
    # Karplus-Strong plucked string: warm, acoustic-guitar-like
    key = (m, length)
    if key not in _gcache:
        f = hz(m)
        n = int(SR * length)
        p = int(round(SR / f))
        buf = np.convolve(rng.uniform(-1, 1, p), [0.5, 0.5], 'same')
        reps = n // p + 1
        out = np.empty(reps * p)
        for r in range(reps):
            out[r * p:(r + 1) * p] = buf
            buf = 0.996 * 0.5 * (buf + np.roll(buf, -1))
        _gcache[key] = out[:n] * 0.6
    return _gcache[key]


def whistle(m, length):
    n = int(SR * length)
    t = np.arange(n) / SR
    f = hz(m) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(t / 0.25, 1))
    f = f * (1 - 0.02 * np.exp(-t / 0.03))   # tiny upward scoop, like a real whistle
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    breath = np.convolve(rng.uniform(-1, 1, n), np.ones(30) / 30, 'same') * 0.05
    a = np.minimum(t / 0.04, 1) * np.clip((length - t) / 0.08, 0, 1)
    return (s + breath) * a


def pizz(m, length=0.5):
    n = int(SR * length)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    return s * np.minimum(t / 0.004, 1) * np.exp(-t / 0.22)


def snap():
    n = int(SR * 0.08)
    t = np.arange(n) / SR
    s = np.diff(rng.uniform(-1, 1, n), prepend=0)
    return s * np.exp(-t / 0.012)


def shaker():
    n = int(SR * 0.07)
    t = np.arange(n) / SR
    s = np.diff(rng.uniform(-1, 1, n), prepend=0)
    return s * np.sin(np.pi * t / t[-1])


# G - Em - C - D  (walking bass per beat, guitar voicing low->high)
CHORDS = [
    ([43, 47, 50, 52], [55, 59, 62, 67]),   # G
    ([40, 43, 47, 45], [52, 59, 64, 67]),   # Em
    ([36, 40, 43, 45], [48, 55, 60, 64]),   # C
    ([38, 42, 45, 42], [50, 57, 62, 66]),   # D
]
# 4-bar whistle tune (bar, beat, midi, beats); answered by a variation
TUNE_A = [(0, 0, 74, 1.5), (0, 1.5, 76, .5), (0, 2, 79, 1), (0, 3, 76, 1),
          (1, 0, 74, 2), (1, 2.5, 71, .5), (1, 3, 74, 1),
          (2, 0, 72, 1.5), (2, 1.5, 74, .5), (2, 2, 76, 1), (2, 3, 79, 1),
          (3, 0, 78, 2.5), (3, 3, 74, 1)]
TUNE_B = [(0, 0, 79, 1.5), (0, 1.5, 81, .5), (0, 2, 83, 1), (0, 3, 79, 1),
          (1, 0, 76, 2), (1, 2.5, 74, .5), (1, 3, 76, 1),
          (2, 0, 72, 1), (2, 1, 76, 1), (2, 2, 74, 1), (2, 3, 72, 1),
          (3, 0, 71, 1.5), (3, 1.5, 69, .5), (3, 2, 67, 2)]

nbars = int(np.ceil(DUR / BAR))
for b in range(nbars):
    bass, voice = CHORDS[b % 4]
    # fingerpicking: bass string on 1 & 3, treble notes rolling on the 8ths
    for beat, k in [(0, 0), (0.5, 2), (1, 1), (1.5, 3), (2, 0), (2.5, 2), (3, 1), (3.5, 3)]:
        put(guitar(voice[k], 1.4), at(b, beat), pan=-0.3, gain=0.5 if k == 0 else 0.32)
    if b >= 1:
        for q in range(4):
            put(pizz(bass[q]), at(b, q), gain=0.55)
        for q in (1, 3):
            put(snap(), at(b, q), pan=0.25, gain=0.35)
        for e in range(8):
            put(shaker(), at(b, e / 2), pan=0.45, gain=0.05 if e % 2 == 0 else 0.08)
    # whistle tune from bar 3: A phrase, then B phrase, then repeat
    if b >= 2 and (b - 2) % 4 == 0:
        tune = TUNE_A if ((b - 2) // 4) % 2 == 0 else TUNE_B
        for bb, beat, m, ln in tune:
            put(whistle(m, ln * BEAT * 0.95), at(b + bb, beat), pan=0.15, gain=0.22)

# light room reverb (a few short echoes)
for delay, g in ((0.031, 0.25), (0.053, 0.18), (0.089, 0.12), (0.13, 0.08)):
    d = int(SR * delay)
    L[d:] += L[:-d] * g
    R[d:] += R[:-d] * g * 0.9

t = np.arange(N) / SR
fade = np.minimum(t / 0.2, 1) * np.clip((DUR - t) / 2.0, 0, 1)
L *= fade
R *= fade
peak = max(np.abs(L).max(), np.abs(R).max())
mix = np.stack([L, R], axis=1) / peak * 0.9
mix = np.tanh(mix * 1.1) / np.tanh(1.1)

with wave.open(OUT, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', OUT)
