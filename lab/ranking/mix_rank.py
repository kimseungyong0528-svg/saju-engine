"""순위 대본을 줄마다 읽은 목소리 → 공개 시간표(plan.json) + 배경음 깐 audio.mp3.
python mix_rank.py 목소리폴더 접두어 배경음.wav 출력폴더   (예: 접두어 supertonic_F3_rank)"""
import json, subprocess, sys, pathlib
vdir, prefix, bgm, out = sys.argv[1:5]
out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
here = pathlib.Path(__file__).parent
plan = json.load(open(here / "plan.json", encoding="utf-8"))
lines = [l.strip() for l in open(here.parent / "tts/script_rank.txt", encoding="utf-8") if l.strip()]
files = sorted(pathlib.Path(vdir).glob(f"{prefix}_L*.mp3"))
assert len(files) == len(lines) == 14, (len(files), len(lines))
dur = lambda f: float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))
LEAD, GAP = 0.3, 0.25
t, starts = LEAD, []
for f in files:
    starts.append(t); t += dur(f) + GAP
ends = starts[1:] + [t]
# 2~13번째 줄이 12위~1위 공개
plan["reveal"] = [round(starts[13 - r], 2) for r in range(1, 13)]   # reveal[0]=1위 … reveal[11]=12위
plan["crownAt"] = round(starts[12] + 2.0, 2)
caps = [{"s": round(starts[0], 2), "e": round(ends[0], 2), "text": "2027년 재물운 띠 순위, 12위부터 공개할게요"}]
for i in range(1, 13):
    caps.append({"s": round(starts[i], 2), "e": round(ends[i], 2), "text": lines[i].rstrip(".!")})
caps.append({"s": round(starts[13], 2), "e": round(ends[13], 2), "text": "내 사주로 보는 2027 재물운, 운명서재"})
plan["caps"] = caps
plan["total"] = round(t + 1.0, 2)
json.dump(plan, open(out / "plan.json", "w", encoding="utf-8"), ensure_ascii=False)
inputs, flt = [], []
for i, (f, s) in enumerate(zip(files, starts)):
    inputs += ["-i", str(f)]; flt.append(f"[{i}]adelay={int(s*1000)}|{int(s*1000)},aformat=channel_layouts=mono[v{i}]")
n = len(files); total = plan["total"]
inputs += ["-i", bgm]
flt.append("".join(f"[v{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,loudnorm=I=-15:TP=-1.5,aresample=44100,asplit=2[voice][voice2]")
flt.append(f"[{n}]atrim=0:{total},volume=0.16,aformat=channel_layouts=mono,aresample=44100[bg]")
flt.append("[bg][voice]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=400[duck]")
flt.append("[duck][voice2]amix=inputs=2:normalize=0[a]")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(flt), "-map", "[a]", "-t", str(total), "-b:a", "160k", str(out / "audio.mp3")], check=True)
print(total)
