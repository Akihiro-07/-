# Synthesizes an original, royalty-free "honwaka / puppu" style backing track:
# bouncy tuba oom-pah, recorder melody, pizzicato strings, glockenspiel, woodblock.
# Usage: python3 music.py [seconds] [out.wav]
import sys
import wave
import numpy as np

SR = 44100
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 34.0
OUT = sys.argv[2] if len(sys.argv) > 2 else 'music.wav'
BPM = 116
BEAT = 60 / BPM
BAR = BEAT * 4
N = int(SR * DUR)
L = np.zeros(N)
R = np.zeros(N)
rng = np.random.default_rng(5)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def at(bar, beat):
    return bar * BAR + beat * BEAT


def put(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= N or i < 0:
        return
    sig = sig[: N - i] * gain
    L[i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2)
    R[i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2)


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, 'same')


def tuba(m, length, slide=0.0):
    """Round, slightly comic brass 'pu'. slide>0 bends the pitch up (for the 'puu')."""
    n = int(SR * length)
    t = np.arange(n) / SR
    f = hz(m) * (1 - 0.04 * np.exp(-t / 0.02)) * (1 + slide * np.clip(t / length, 0, 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph) + 0.1 * np.sin(4 * ph)
    a = np.minimum(t / 0.018, 1) * np.clip((length - t) / 0.04, 0, 1)
    return lowpass(s * a, 6)


def recorder(m, length):
    n = int(SR * length)
    t = np.arange(n) / SR
    f = hz(m) * (1 + 0.005 * np.sin(2 * np.pi * 5 * t) * np.clip((t - 0.15) / 0.2, 0, 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.12 * np.sin(3 * ph) + 0.04 * np.sin(2 * ph)
    breath = lowpass(rng.uniform(-1, 1, n), 12) * 0.08 * np.exp(-t / 0.05)
    a = np.minimum(t / 0.015, 1) * np.clip((length - t) / 0.03, 0, 1)
    return (s + breath) * a


def pizz(m, length=0.35):
    n = int(SR * length)
    t = np.arange(n) / SR
    ph = 2 * np.pi * hz(m) * t
    s = np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)
    return s * np.minimum(t / 0.003, 1) * np.exp(-t / 0.09)


def glock(m, length=1.0):
    n = int(SR * length)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.08)
    return s * np.minimum(t / 0.001, 1) * np.exp(-t / 0.45)


def woodblock(pitch=900):
    n = int(SR * 0.06)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * pitch * t) * np.exp(-t / 0.012)


def kick():
    n = int(SR * 0.2)
    t = np.arange(n) / SR
    f = 55 + 70 * np.exp(-t / 0.02)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.08)


# 8-bar loop in F: F Bb C F | Dm Bb C F   -> (tuba root, tuba fifth, pizz chord)
PROG = [(41, 48, [65, 69, 72]), (46, 41, [65, 70, 74]), (48, 43, [64, 67, 72]), (41, 48, [65, 69, 72]),
        (38, 45, [65, 69, 74]), (46, 41, [65, 70, 74]), (48, 43, [64, 67, 72]), (41, 48, [65, 69, 72])]
# bouncy 8-bar melody (bar, beat, midi, beats)
MELODY = [
    (0, 0, 81, .5), (0, .5, 84, .5), (0, 1, 81, .5), (0, 1.5, 77, .5), (0, 2, 79, .5), (0, 2.5, 81, .5), (0, 3, 79, 1),
    (1, 0, 82, .5), (1, .5, 81, .5), (1, 1, 79, .5), (1, 1.5, 77, .5), (1, 2, 74, 1), (1, 3, 77, 1),
    (2, 0, 79, .5), (2, .5, 81, .5), (2, 1, 82, .5), (2, 1.5, 84, .5), (2, 2, 86, .5), (2, 2.5, 84, .5), (2, 3, 82, 1),
    (3, 0, 81, 1.5), (3, 2, 77, .5),
    (4, 0, 77, .5), (4, .5, 81, .5), (4, 1, 86, 1), (4, 2, 84, .5), (4, 2.5, 81, .5), (4, 3, 77, 1),
    (5, 0, 74, .5), (5, .5, 77, .5), (5, 1, 82, 1), (5, 2, 81, .5), (5, 2.5, 79, .5), (5, 3, 77, 1),
    (6, 0, 76, .5), (6, .5, 79, .5), (6, 1, 84, .5), (6, 1.5, 82, .5), (6, 2, 81, .5), (6, 2.5, 79, .5), (6, 3, 76, 1),
    (7, 0, 77, 1.5), (7, 2, 72, .5),
]

nbars = int(np.ceil(DUR / BAR))
for b in range(nbars):
    root, fifth, chord = PROG[0] if b == 0 else PROG[(b - 1) % 8]
    # oom-pah: tuba on 1 and 3, pizzicato chord on 2 and 4
    put(tuba(root, BEAT * 0.55), at(b, 0), gain=0.55)
    put(tuba(fifth, BEAT * 0.55), at(b, 2), gain=0.48)
    for q in (1, 3):
        for j, m in enumerate(chord):
            put(pizz(m), at(b, q) + j * 0.004, pan=-0.3, gain=0.16)
    # light pulse + woodblock "tick-tock" on the offbeats
    if b >= 1:
        for q in (0, 2):
            put(kick(), at(b, q), gain=0.35)
        for e in range(4):
            put(woodblock(1000 if e % 2 else 800), at(b, e + 0.5), pan=0.35, gain=0.16)
    # melody: recorder from bar 1, glockenspiel joins on the repeat
    if b >= 1 and (b - 1) % 8 == 0:
        second = (b - 1) // 8 >= 1
        for bb, beat, m, ln in MELODY:
            dur = ln * BEAT * (0.6 if ln <= 0.5 else 0.85)   # short and bouncy
            put(recorder(m, dur), at(b + bb, beat), pan=0.15, gain=0.24)
            if second:
                put(glock(m + 12), at(b + bb, beat), pan=0.4, gain=0.07)
        # the "pu-ppuu" answer at the end of each 4-bar line
        for line in (3, 7):
            put(tuba(53, BEAT * 0.3), at(b + line, 3), gain=0.5)
            put(tuba(57, BEAT * 0.9, slide=0.06), at(b + line, 3.5), gain=0.5)

# small room
for delay, g in ((0.027, 0.2), (0.047, 0.14), (0.081, 0.09)):
    d = int(SR * delay)
    L[d:] += L[:-d] * g
    R[d:] += R[:-d] * g * 0.9

t = np.arange(N) / SR
fade = np.minimum(t / 0.1, 1) * np.clip((DUR - t) / 1.8, 0, 1)
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
