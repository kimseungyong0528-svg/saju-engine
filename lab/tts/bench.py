"""한국어 목소리 비교 시험: 대본 두 개(말띠 운세, 재물 순위)를 줄마다 읽혀 out/ 에 남긴다.
파일 이름: {엔진}_{목소리}_{대본}_L01.mp3"""
import json, sys, time, subprocess, pathlib, traceback
OUT = pathlib.Path("lab/tts/out"); OUT.mkdir(parents=True, exist_ok=True)
SCRIPTS = {name: [l.strip() for l in pathlib.Path(f"lab/tts/{f}").read_text(encoding="utf-8").splitlines() if l.strip()]
           for name, f in [("horse", "script.txt"), ("rank", "script_rank.txt")]}
engine = sys.argv[1]
res = {}

def mp3(wav, name):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-ac", "1", "-b:a", "96k", str(OUT / f"{name}.mp3")], check=True)
    pathlib.Path(wav).unlink()

def run(tag, say):
    """say(text, wav_path) 로 모든 줄을 읽힌다."""
    t0, n = time.time(), 0
    for sname, lines in SCRIPTS.items():
        for i, line in enumerate(lines, 1):
            say(line, "/tmp/x.wav"); mp3("/tmp/x.wav", f"{tag}_{sname}_L{i:02d}"); n += 1
    res[tag] = {"sec": round(time.time() - t0, 1), "lines": n}

try:
    if engine == "supertonic":
        from supertonic import TTS
        tts = TTS()
        for v in ["F1", "F2", "F3", "F4", "F5", "M1", "M2", "M3", "M4", "M5"]:
            style = tts.get_voice_style(v)
            def say(text, path, style=style):
                wav, _ = tts.synthesize(text, voice_style=style, lang="ko", total_steps=16, speed=1.0)
                tts.save_audio(wav, path)
            run(f"supertonic_{v}", say)
    elif engine == "qwen":
        import torch, soundfile as sf
        from qwen_tts import Qwen3TTSModel
        torch.set_num_threads(4)
        m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice", dtype=torch.float32, device_map="cpu")
        res["speakers"] = m.get_supported_speakers()
        def say(text, path):
            wavs, sr = m.generate_custom_voice(text=text, language="korean", speaker="sohee",
                                               instruct="차분하고 따뜻한 목소리로, 또박또박 읽어 주세요.")
            sf.write(path, wavs[0], sr)
        run("qwen_sohee", say)
    elif engine == "melo":
        from melo.api import TTS
        m = TTS(language="KR", device="cpu")
        run("melo_kr", lambda text, path: m.tts_to_file(text, m.hps.data.spk2id["KR"], path, speed=1.05))
except Exception:
    res["error"] = traceback.format_exc()[-1500:]
(OUT / f"result_{engine}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1))
