# Synthesizes an original, royalty-free bright house backing track:
# four-on-the-floor kick, offbeat open hats, clap, shaker, house piano stabs,
# offbeat bass and a pluck hook, with a filter sweep opening the intro.
# Usage: python3 music.py [seconds] [out.wav]
import sys
import wave
import numpy as np

SR = 44100
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 34.0
OUT = sys.argv[2] if len(sys.argv) > 2 else 'music.wav'
BPM = 122
BEAT = 60 / BPM
BAR = BEAT * 4
N = int(SR * DUR)
rng = np.random.default_rng(21)
# two buses so the intro sweep only filters the music, not the kick
BUS = {k: [np.zeros(N), np.zeros(N)] for k in ('drums', 'music')}


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def at(bar, beat):
    return bar * BAR + beat * BEAT


def put(sig, t, pan=0.0, gain=1.0, bus='music'):
    i = int(t * SR)
    if i >= N or i < 0:
        return
    sig = sig[: N - i] * gain
    Lb, Rb = BUS[bus]
    Lb[i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2)
    Rb[i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2)


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, 'same')


def piano(m, length=0.5):
    """Bright house-piano stab: hammer click + a few decaying partials."""
    n = int(SR * length)
    t = np.arange(n) / SR
    f = hz(m)
    s = sum(np.sin(2 * np.pi * f * k * t * (1 + 0.0004 * k * k)) * np.exp(-t * (3 + 2.5 * k)) / k
            for k in range(1, 7))
    click = rng.uniform(-1, 1, n) * np.exp(-t / 0.003) * 0.15
    return (s + click) * np.minimum(t / 0.002, 1) * np.clip((length - t) / 0.05, 0, 1)


def pluck(m, length=0.3):
    n = int(SR * length)
    t = np.arange(n) / SR
    ph = 2 * np.pi * hz(m) * t
    saw = sum(np.sin(k * ph) / k for k in range(1, 9))
    bright = np.exp(-t / 0.05)
    s = saw * bright + np.sin(ph) * (1 - bright)
    return s * np.minimum(t / 0.002, 1) * np.exp(-t / 0.14)


def bass(m, length):
    n = int(SR * length)
    t = np.arange(n) / SR
    ph = 2 * np.pi * hz(m) * t
    s = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)
    a = np.minimum(t / 0.004, 1) * np.clip((length - t) / 0.02, 0, 1) * np.exp(-t / 0.25)
    return np.tanh(1.3 * s * a)


def kick():
    n = int(SR * 0.32)
    t = np.arange(n) / SR
    f = 50 + 120 * np.exp(-t / 0.025)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.13)
    return np.tanh(1.5 * body) + rng.uniform(-1, 1, n) * np.exp(-t / 0.002) * 0.2


def clap():
    n = int(SR * 0.22)
    t = np.arange(n) / SR
    noise = np.diff(rng.uniform(-1, 1, n), prepend=0)
    burst = sum((t >= d) * np.exp(-np.maximum(t - d, 0) / 0.008) for d in (0, 0.009, 0.018))
    return noise * (0.6 * burst + np.exp(-t / 0.07))


def hat(open_=False):
    n = int(SR * (0.16 if open_ else 0.035))
    t = np.arange(n) / SR
    s = np.diff(np.diff(rng.uniform(-1, 1, n), prepend=0), prepend=0) * 0.5
    return s * np.exp(-t / (0.06 if open_ else 0.01))


# F - G - Em - Am  (uplifting, 4-bar loop): bass root, piano voicing
CHORDS = [(41, [60, 64, 65, 69]), (43, [62, 65, 67, 71]), (40, [59, 62, 64, 67]), (45, [60, 64, 67, 69])]
# syncopated house-piano rhythm (beat positions)
STABS = [0, 0.75, 1.5, 2.5, 3.0, 3.75]
# catchy 2-bar pluck hook (bar, beat, midi)
HOOK = [(0, 0.5, 76), (0, 1, 77), (0, 1.75, 79), (0, 2.5, 77), (0, 3, 76),
        (1, 0.5, 74), (1, 1, 76), (1, 1.75, 79), (1, 2.5, 81), (1, 3.25, 79)]

nbars = int(np.ceil(DUR / BAR))
for b in range(nbars):
    root, voice = CHORDS[b % 4]
    full = b >= 2
    last = b >= nbars - 1
    # drums
    for q in range(4):
        put(kick(), at(b, q), gain=0.85, bus='drums')
        if full or b == 1:
            put(hat(open_=True), at(b, q + 0.5), pan=0.25, gain=0.2, bus='drums')
        if full and q in (1, 3):
            put(clap(), at(b, q), pan=-0.05, gain=0.35, bus='drums')
    if full:
        for s16 in range(16):
            if s16 % 4 != 2:
                put(hat(), at(b, s16 / 4), pan=-0.4, gain=0.07 if s16 % 2 == 0 else 0.11, bus='drums')
    # piano stabs every bar (filtered open over the intro)
    for k, pos in enumerate(STABS):
        for j, m in enumerate(voice):
            put(piano(m, 0.45), at(b, pos) + j * 0.003, pan=0.1 - j * 0.07, gain=0.13)
    # offbeat bass from bar 2
    if full and not last:
        for e in range(4):
            put(bass(root if e != 3 else root + 7, BEAT * 0.42), at(b, e + 0.5), gain=0.5)
    # hook from bar 6
    if b >= 6 and b % 2 == 0 and b < nbars - 1:
        for bb, beat, m in HOOK:
            put(pluck(m + 12), at(b + bb, beat), pan=0.3, gain=0.14)
            put(pluck(m + 12), at(b + bb, beat) + BEAT * 0.75, pan=-0.3, gain=0.04)   # echo

# intro sweep: music bus goes from muffled to open over the first 2 bars
t = np.arange(N) / SR
open_k = np.clip(t / (BAR * 2), 0, 1) ** 1.5
for ch in range(2):
    x = BUS['music'][ch]
    BUS['music'][ch] = lowpass(x, 60) * (1 - open_k) + x * open_k
# simple sidechain-style pump on the music bus, ducking on each kick
phase = (t % BEAT) / BEAT
duck = 1 - 0.35 * np.exp(-phase / 0.18)
for ch in range(2):
    BUS['music'][ch] *= duck

L = BUS['drums'][0] + BUS['music'][0]
R = BUS['drums'][1] + BUS['music'][1]
for delay, g in ((0.021, 0.15), (0.043, 0.1), (0.071, 0.06)):
    d = int(SR * delay)
    L[d:] += L[:-d] * g
    R[d:] += R[:-d] * g * 0.9

fade = np.minimum(t / 0.05, 1) * np.clip((DUR - t) / 2.0, 0, 1)
mix = np.stack([L * fade, R * fade], axis=1)
mix = mix / np.abs(mix).max()
mix = np.tanh(mix * 1.3) / np.tanh(1.3) * 0.89

with wave.open(OUT, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', OUT)
