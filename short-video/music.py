# Synthesizes an original, royalty-free gentle lo-fi hip hop backing track:
# swung soft drums, electric-piano jazz chords, warm bass, vinyl crackle, tape wobble.
# Usage: python3 music.py [seconds] [out.wav]
import sys
import wave
import numpy as np

SR = 44100
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 34.0
OUT = sys.argv[2] if len(sys.argv) > 2 else 'music.wav'
BPM = 80
BEAT = 60 / BPM
BAR = BEAT * 4
SWING = 0.6          # lazy swung 8ths
N = int(SR * DUR)
L = np.zeros(N)
R = np.zeros(N)
rng = np.random.default_rng(11)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def at(bar, beat):
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


def lowpass(x, k):
    return np.convolve(x, np.ones(k) / k, 'same')


def epiano(m, length):
    """Soft Rhodes-like tine: sine body + short bell partial + slow tremolo."""
    n = int(SR * length)
    t = np.arange(n) / SR
    f = hz(m) * (1 + 0.0015 * rng.standard_normal())
    s = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t / 0.4)
    s += 0.12 * np.sin(2 * np.pi * f * 7.1 * t) * np.exp(-t / 0.04)
    trem = 1 + 0.12 * np.sin(2 * np.pi * 4.2 * t)
    a = np.minimum(t / 0.006, 1) * np.exp(-t / 1.6) * np.clip((length - t) / 0.15, 0, 1)
    return s * a * trem


def bass(m, length):
    n = int(SR * length)
    t = np.arange(n) / SR
    s = np.tanh(1.6 * np.sin(2 * np.pi * hz(m) * t))
    a = np.minimum(t / 0.01, 1) * np.exp(-t / 0.9) * np.clip((length - t) / 0.06, 0, 1)
    return lowpass(s * a, 10)


def kick():
    n = int(SR * 0.35)
    t = np.arange(n) / SR
    f = 48 + 60 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.14)


def snare():
    n = int(SR * 0.25)
    t = np.arange(n) / SR
    noise = lowpass(rng.uniform(-1, 1, n), 4) * np.exp(-t / 0.07)
    body = np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.04) * 0.5
    return noise + body


def hat(soft=1.0):
    n = int(SR * 0.05)
    t = np.arange(n) / SR
    s = np.diff(rng.uniform(-1, 1, n), prepend=0)
    return lowpass(s, 2) * np.exp(-t / 0.015) * soft


# Fmaj9 - Em7 - Dm9 - Cmaj9   (bass, voicing)
CHORDS = [(41, [57, 64, 67, 72]), (40, [55, 62, 64, 71]), (38, [53, 60, 64, 69]), (36, [52, 59, 62, 67])]
# sparse, sleepy top line over 4 bars (bar, beat, midi, beats)
TOP = [(0, 1.5, 76, 1), (0, 3, 79, 1.5), (1, 1, 76, 1), (1, 2.5, 74, 1.5),
       (2, 1.5, 72, 1), (2, 3, 76, 1), (3, 0.5, 74, 2.5)]

nbars = int(np.ceil(DUR / BAR))
for b in range(nbars):
    root, voice = CHORDS[b % 4]
    last = b == nbars - 1
    # chords: lazy roll, held for the bar, re-touched softly on the "and" of 3
    for j, m in enumerate(voice):
        put(epiano(m, BAR * 1.0), at(b, 0) + j * 0.025, pan=-0.15 + j * 0.1, gain=0.17)
    for j, m in enumerate(voice[1:]):
        put(epiano(m, BEAT * 1.3), at(b, 2.5) + j * 0.02, pan=0.1, gain=0.08)
    if b >= 1 and not last:
        put(bass(root, BEAT * 2.4), at(b, 0), gain=0.5)
        put(bass(root + 7, BEAT * 1.0), at(b, 2.5), gain=0.35)
        put(bass(root + 12 if b % 2 else root + 5, BEAT * 0.8), at(b, 3.5), gain=0.25)
        # boom-bap: kick 1 and the "and" of 2, snare on 2 and 4, swung hats
        put(kick(), at(b, 0), gain=0.75)
        put(kick(), at(b, 1.5), gain=0.5)
        if b % 2:
            put(kick(), at(b, 2.5), gain=0.45)
        for q in (1, 3):
            put(snare(), at(b, q) + 0.012, pan=0.05, gain=0.28)
        for e in range(8):
            put(hat(), at(b, e / 2), pan=0.35, gain=0.1 if e % 2 == 0 else 0.06)
    if b >= 2 and (b - 2) % 4 == 0:
        for bb, beat, m, ln in TOP:
            if b + bb < nbars - 1:
                put(epiano(m, ln * BEAT * 1.2), at(b + bb, beat), pan=0.25, gain=0.14)

# tape wobble: slow pitch drift via a varying read position
t = np.arange(N) / SR
wob = t + 0.0018 * np.sin(2 * np.pi * 0.55 * t) + 0.0006 * np.sin(2 * np.pi * 3.1 * t)
L = np.interp(wob, t, L)
R = np.interp(wob, t, R)
# warm, slightly dull tone
L = 0.6 * lowpass(L, 7) + 0.4 * L
R = 0.6 * lowpass(R, 7) + 0.4 * R
# room
for delay, g in ((0.035, 0.22), (0.061, 0.15), (0.097, 0.1), (0.15, 0.06)):
    d = int(SR * delay)
    L[d:] += L[:-d] * g
    R[d:] += R[:-d] * g * 0.9
# vinyl: faint hiss and random crackles
hiss = lowpass(rng.uniform(-1, 1, N), 3) * 0.004
crackle = np.zeros(N)
idx = rng.choice(N, size=int(DUR * 9), replace=False)
crackle[idx] = rng.uniform(-1, 1, len(idx)) * rng.uniform(0.02, 0.09, len(idx))
crackle = lowpass(crackle, 3)
peak = max(np.abs(L).max(), np.abs(R).max())
L = L / peak * 0.85 + hiss + crackle
R = R / peak * 0.85 + hiss + np.roll(crackle, 37)

fade = np.minimum(t / 0.6, 1) * np.clip((DUR - t) / 2.5, 0, 1)
mix = np.stack([L * fade, R * fade], axis=1)
mix = np.tanh(mix * 1.15) / np.tanh(1.15)
mix = mix / np.abs(mix).max() * 0.89

with wave.open(OUT, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', OUT)
