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


def _ding(f: float, dur: float, bright: float = 1.0) -> np.ndarray:
    tt = np.arange(int(SR * dur)) / SR
    tone = sum(np.sin(2 * np.pi * f * k * tt) * (bright / k ** 1.3) for k in (1, 2, 3, 4.2))   # 종소리 비슷한 배음
    return tone * np.exp(-tt * 5) * (1 - np.exp(-tt * 800))


def _whoosh(dur: float = 0.5, seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    noise = rng.standard_normal(n)
    sm = np.convolve(noise, np.ones(40) / 40, mode="same")        # 거친 소리를 부드럽게
    tt = np.arange(n) / SR
    env = np.sin(np.pi * tt / dur) ** 2
    return sm * env * 0.6


def sfx(total: float, events: list[tuple[float, str]], out: Path) -> Path:
    """효과음 트랙: ding(순위 공개), big(상위 3위), crown(1위), whoosh(장면 바뀜)."""
    n = int(SR * (total + 1))
    mix = np.zeros(n)
    for t, kind in events:
        if kind == "ding":
            s = _ding(880, 0.6) * 0.35
        elif kind == "big":
            a = _ding(660, 1.0) * 0.45
            b = np.pad(_ding(990, 0.92) * 0.3, (int(SR * .08), 0), mode="constant")[: len(a)]
            s = a + np.pad(b, (0, len(a) - len(b)))
        elif kind == "crown":
            parts = [np.pad(_ding(f, 1.6) * 0.4, (int(SR * d), 0)) for f, d in ((523.25, 0), (659.25, .12), (783.99, .24), (1046.5, .36))]
            m = max(len(p) for p in parts)
            s = sum(np.pad(p, (0, m - len(p))) for p in parts)
        else:
            s = _whoosh()
        i = int(t * SR)
        if i < n:
            mix[i:i + len(s)] += s[: n - i]
    peak = np.max(np.abs(mix)) or 1
    mix = mix / peak * 0.8
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    return out


BGM_DIR = Path(__file__).parent / "bgm"


def tracks() -> list[Path]:
    """배경음악 10곡 (사장님 2026-11-01 "유행하는거 저작권 괜찮은거 10개 가져와 랜덤돌리게"). 목록·출처는 bgm/bgm.json."""
    import json
    f = BGM_DIR / "bgm.json"
    if not f.exists():
        return []
    return [BGM_DIR / t["file"] for t in json.loads(f.read_text(encoding="utf-8"))["tracks"] if (BGM_DIR / t["file"]).exists()]


def bgm(sec: float, out: Path, seed: int = 7) -> Path:
    """10곡 중 하나를 seed 로 골라 영상 길이만큼 자르고 앞뒤를 부드럽게 줄인다. 곡이 없으면 직접 만든 배경음을 쓴다."""
    import subprocess
    ts = tracks()
    if not ts:
        return ambient(sec, out, seed=seed)
    src = ts[np.random.default_rng(seed).integers(len(ts))]
    fo = max(0.0, sec - 1.5)
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", str(src), "-t", f"{sec:.2f}",
                    "-af", f"afade=t=in:d=0.4,afade=t=out:st={fo:.2f}:d=1.5,volume=0.85", "-ac", "2", "-ar", "44100", str(out)],
                   check=True)
    return out
