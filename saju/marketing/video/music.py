"""저작권 걱정 없는 잔잔한 배경음을 직접 만든다(가야금 비슷한 뜯는 소리 + 낮은 울림)."""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100
SCALE = [293.66, 329.63, 392.0, 440.0, 493.88, 587.33, 659.25]   # D 오음계 비슷하게


def _pluck(f: float, dur: float = 2.4) -> np.ndarray:
    tt = np.arange(int(SR * dur)) / SR
    tone = sum(np.sin(2 * np.pi * f * k * tt) / k ** 1.6 for k in range(1, 7))
    env = np.exp(-tt * 2.6) * (1 - np.exp(-tt * 300))
    bend = np.sin(2 * np.pi * f * tt * (1 + 0.006 * np.exp(-tt * 4)))   # 줄을 누르는 느낌
    return (0.7 * tone + 0.3 * bend) * env


def ambient(sec: float, out: Path, seed: int = 7) -> Path:
    rng = np.random.default_rng(seed)
    n = int(SR * sec)
    t = np.arange(n) / SR
    mix = np.zeros(n)
    for f, a in ((73.42, .10), (110.0, .07), (146.83, .04)):      # 낮은 울림(드론)
        mix += a * np.sin(2 * np.pi * f * t) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 9 + f))
    pos = 0.8
    while pos < sec - 2.5:
        p = _pluck(SCALE[rng.integers(len(SCALE))]) * (0.16 + 0.08 * rng.random())
        i = int(pos * SR)
        mix[i:i + len(p)] += p[: n - i]
        if rng.random() < .35:                                         # 이어 뜯기
            p2 = _pluck(SCALE[rng.integers(len(SCALE))]) * .1
            j = i + int(SR * .25)
            mix[j:j + len(p2)] += p2[: max(0, n - j)]
        pos += rng.choice([1.2, 1.6, 2.0, 2.4])
    for d, g in ((.11, .3), (.23, .2), (.37, .12)):                    # 잔향 비슷하게
        k = int(SR * d)
        mix[k:] += g * mix[:-k]
    fade = np.minimum(1, np.minimum(t / 1.5, (sec - t) / 2.0))
    mix = mix * fade
    mix = mix / (np.max(np.abs(mix)) or 1) * .7
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    return out
