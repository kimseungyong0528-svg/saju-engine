"""줄마다 읽은 목소리 파일들 → 하나로 잇고 시간표(plan.json) 만들기 → 배경음 깔기.
python mix.py 목소리폴더 접두어 자막.json 배경음.wav 출력폴더"""
import json, subprocess, sys, pathlib
vdir, prefix, capf, bgm, out = sys.argv[1:6]
out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
caps = json.load(open(capf, encoding="utf-8"))
files = sorted(pathlib.Path(vdir).glob(f"{prefix}_L*.mp3"))
dur = lambda f: float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))
GAP, LEAD = 0.35, 0.4
t, lines, parts = LEAD, [], []
for f, c in zip(files, caps):
    d = dur(f); lines.append({"s": round(t, 2), "e": round(t + d + GAP, 2), "cap": c}); parts.append((f, t)); t += d + GAP
total = round(t + 1.6, 2)
json.dump({"lines": lines, "total": total}, open(out / "plan.json", "w"), ensure_ascii=False)
inputs, flt = [], []
for i, (f, s) in enumerate(parts):
    inputs += ["-i", str(f)]; flt.append(f"[{i}]adelay={int(s*1000)}|{int(s*1000)},aformat=channel_layouts=mono[v{i}]")
n = len(parts)
inputs += ["-i", bgm]
flt.append("".join(f"[v{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,loudnorm=I=-15:TP=-1.5,aresample=44100,apad,asplit=2[voice][voice2]")
flt.append(f"[{n}]atrim=0:{total},volume=0.13,aformat=channel_layouts=mono,aresample=44100[bg]")
flt.append("[bg][voice]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=400[duck]")
flt.append("[duck][voice2]amix=inputs=2:normalize=0[a]")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(flt), "-map", "[a]", "-t", str(total), "-b:a", "160k", str(out / "audio.mp3")], check=True)
print(total)
