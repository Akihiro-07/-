# Synthesizes an original upbeat backing track (no samples, royalty-free).
# Usage: python3 music.py [seconds] [out.wav]
import sys
import wave
import numpy as np

SR = 44100
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 34.0
OUT = sys.argv[2] if len(sys.argv) > 2 else 'music.wav'
BPM = 120
BEAT = 60 / BPM
BAR = BEAT * 4
N = int(SR * DUR)
L = np.zeros(N)
R = np.zeros(N)
rng = np.random.default_rng(1)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def put(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * (1 - pan) / 2 * 2 ** 0.5
    R[i:i + len(sig)] += sig * (1 + pan) / 2 * 2 ** 0.5


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1) * np.exp(-t / d)


def pluck(m, length=0.5, decay=0.18):
    # ukulele-ish: bright triangle-like stack with fast decay
    n = int(SR * length)
    t = np.arange(n) / SR
    f = hz(m)
    s = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.6 for k in range(1, 7))
    return s * env(n, 0.003, decay)


def marimba(m, length=0.45):
    n = int(SR * length)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t / 0.03)
    return s * env(n, 0.002, 0.16)


def bass(m, length):
    n = int(SR * length)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) + 0.1 * np.sin(2 * np.pi * 3 * f * t)
    return s * env(n, 0.005, length * 0.7)


def kick():
    n = int(SR * 0.3)
    t = np.arange(n) / SR
    f = 50 + 110 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)


def clap():
    n = int(SR * 0.2)
    t = np.arange(n) / SR
    noise = rng.uniform(-1, 1, n)
    burst = sum(np.exp(-np.maximum(t - d, 0) / 0.012) * (t >= d) for d in (0, 0.01, 0.02))
    s = noise * (burst * 0.4 + np.exp(-t / 0.06))
    return np.diff(s, prepend=0) * 0.8   # crude high-pass


def hat(open_=False):
    n = int(SR * (0.12 if open_ else 0.04))
    t = np.arange(n) / SR
    s = np.diff(rng.uniform(-1, 1, n), prepend=0)
    return s * np.exp(-t / (0.04 if open_ else 0.012))


def shaker():
    n = int(SR * 0.06)
    t = np.arange(n) / SR
    s = np.diff(rng.uniform(-1, 1, n), prepend=0)
    return s * np.sin(np.pi * t / t[-1]) * 0.5


# C - G - Am - F  (roots, chord tones)
CHORDS = [(48, [60, 64, 67, 72]), (43, [59, 62, 67, 71]), (45, [60, 64, 69, 72]), (41, [60, 65, 69, 72])]
# 2-bar melody phrases in C major pentatonic, (beat offset, midi, length in beats)
MEL_A = [(0, 76, .5), (.5, 79, .5), (1, 81, .5), (1.5, 79, .5), (2, 76, 1), (3, 74, .5), (3.5, 76, .5),
         (4, 79, .5), (4.5, 76, .5), (5, 74, .5), (5.5, 72, .5), (6, 74, 1.5)]
MEL_B = [(0, 72, .5), (.5, 74, .5), (1, 76, .5), (1.5, 79, .5), (2, 81, .75), (2.75, 79, .25), (3, 76, 1),
         (4, 81, .5), (4.5, 84, .5), (5, 81, .5), (5.5, 79, .5), (6, 76, .5), (6.5, 79, .5), (7, 84, 1)]

nbars = int(np.ceil(DUR / BAR))
for b in range(nbars):
    t0 = b * BAR
    root, tones = CHORDS[b % 4]
    full = b >= 2
    # ukulele strum pattern: down on beats, quick up-strums on offbeats
    for k, off in enumerate([0, 1, 1.5, 2.5, 3, 3.5]):
        st = t0 + off * BEAT
        for j, m in enumerate(tones if k % 2 == 0 else tones[::-1]):
            put(pluck(m, 0.45, 0.16 if k % 2 else 0.22), st + j * 0.012, pan=-0.35, gain=0.11 if k % 2 else 0.14)
    if full:
        for e in range(8):
            put(bass(root if e % 4 != 3 else root + 7, BEAT * 0.45), t0 + e * BEAT / 2, gain=0.42 if e % 2 == 0 else 0.3)
        for q in range(4):
            if q in (0, 2):
                put(kick(), t0 + q * BEAT, gain=0.85)
            else:
                put(clap(), t0 + q * BEAT, pan=0.1, gain=0.32)
        for e in range(8):
            put(hat(open_=(e % 4 == 3)), t0 + e * BEAT / 2 + 0.25 * BEAT * 0, pan=0.4, gain=0.12)
        for s16 in range(16):
            put(shaker(), t0 + s16 * BEAT / 4, pan=-0.5, gain=0.05 if s16 % 2 else 0.08)
    else:
        for q in (1, 3):
            put(clap(), t0 + q * BEAT, gain=0.25)
    # melody enters on bar 3, alternates phrases every 2 bars, rests on the outro
    if full and b % 2 == 0 and b < nbars - 1:
        phrase = MEL_A if (b // 2) % 2 == 1 else MEL_B
        for off, m, ln in phrase:
            put(marimba(m, max(ln * BEAT, 0.3)), t0 + off * BEAT, pan=0.3, gain=0.24)
            put(marimba(m + 12, 0.25), t0 + off * BEAT + 0.006, pan=0.3, gain=0.05)

# simple echo on the whole mix for space
d = int(SR * BEAT * 0.75)
for ch in (L, R):
    ch[d:] += ch[:-d] * 0.18

# fade in/out, normalize
t = np.arange(N) / SR
fade = np.minimum(t / 0.15, 1) * np.clip((DUR - t) / 1.5, 0, 1)
L *= fade
R *= fade
peak = max(np.abs(L).max(), np.abs(R).max())
mix = np.stack([L, R], axis=1) / peak * 0.89
mix = np.tanh(mix * 1.1) / np.tanh(1.1)

with wave.open(OUT, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', OUT)
