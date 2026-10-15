"""저작권 걱정 없는 잔잔한 배경음을 직접 만든다(가야금 비슷한 뜯는 소리 + 낮은 울림). python ambient.py 초 출력.wav"""
import sys, numpy as np, wave
SR = 44100
sec = float(sys.argv[1]); out = sys.argv[2]; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 7
rng = np.random.default_rng(seed)
n = int(SR * sec); t = np.arange(n) / SR
mix = np.zeros(n)
# 낮은 울림(드론): D 와 A 를 느리게 숨쉬듯
for f, a in ((73.42, .10), (110.0, .07), (146.83, .04)):
    mix += a * np.sin(2 * np.pi * f * t) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 9 + f))
def pluck(f, dur=2.4):
    m = int(SR * dur); tt = np.arange(m) / SR
    tone = sum(np.sin(2 * np.pi * f * k * tt) / k ** 1.6 for k in range(1, 7))
    env = np.exp(-tt * 2.6) * (1 - np.exp(-tt * 300))
    bend = np.sin(2 * np.pi * f * tt * (1 + 0.006 * np.exp(-tt * 4)))  # 줄을 누르는 느낌
    return (0.7 * tone + 0.3 * bend) * env
scale = [293.66, 329.63, 392.0, 440.0, 493.88, 587.33, 659.25]  # D 오음계 비슷하게
pos = 0.8
while pos < sec - 2.5:
    f = scale[rng.integers(len(scale))]
    p = pluck(f) * (0.16 + 0.08 * rng.random())
    i = int(pos * SR); mix[i:i + len(p)] += p[: n - i]
    if rng.random() < .35:  # 이어 뜯기
        p2 = pluck(scale[rng.integers(len(scale))]) * .1; j = i + int(SR * .25); mix[j:j + len(p2)] += p2[: max(0, n - j)]
    pos += rng.choice([1.2, 1.6, 2.0, 2.4])
# 잔향 비슷하게
for d, g in ((.11, .3), (.23, .2), (.37, .12)):
    k = int(SR * d); mix[k:] += g * mix[:-k]
fade = np.minimum(1, np.minimum(t / 1.5, (sec - t) / 2.0))
mix = mix * fade; mix = mix / np.max(np.abs(mix)) * .7
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
