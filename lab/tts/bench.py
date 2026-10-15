"""한국어 목소리 비교 시험: 같은 대본을 여러 무료 엔진으로 읽힌다. 결과와 걸린 시간을 out/ 에 남긴다."""
import json, sys, time, subprocess, pathlib, traceback
OUT = pathlib.Path("lab/tts/out"); OUT.mkdir(parents=True, exist_ok=True)
TEXT = pathlib.Path("lab/tts/script.txt").read_text(encoding="utf-8").strip()
LINES = [l for l in TEXT.splitlines() if l.strip()]
engine = sys.argv[1]
res = {}

def mp3(wav, name):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-ac", "1", "-b:a", "96k", str(OUT / f"{name}.mp3")], check=True)
    pathlib.Path(wav).unlink()

def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]).decode())

try:
    if engine == "supertonic":
        from supertonic import TTS
        t0 = time.time(); tts = TTS(); res["load_s"] = round(time.time() - t0, 1)
        for v in ["F1", "F2", "F3", "F4", "F5", "M1", "M2", "M3", "M4", "M5"]:
            for steps in (8, 16):
                t0 = time.time()
                wav, _ = tts.synthesize(TEXT.replace("\n", " "), voice_style=tts.get_voice_style(v), lang="ko", total_steps=steps, speed=1.0)
                tts.save_audio(wav, f"/tmp/{v}.wav")
                name = f"supertonic_{v}_s{steps}"; mp3(f"/tmp/{v}.wav", name)
                res[name] = {"sec": round(time.time() - t0, 1), "audio": round(dur(OUT / f"{name}.mp3"), 1)}
    elif engine == "qwen":
        import torch, soundfile as sf
        from qwen_tts import Qwen3TTSModel
        torch.set_num_threads(4)
        t0 = time.time()
        m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice", dtype=torch.float32, device_map="cpu")
        res["load_s"] = round(time.time() - t0, 1)
        res["speakers"] = m.get_supported_speakers(); res["languages"] = sorted(m._supported_languages_set() or [])
        for spk, ins in [("sohee", ""), ("sohee", "차분하고 따뜻한 목소리로, 또박또박 읽어 주세요.")]:
            t0 = time.time()
            wavs, sr = m.generate_custom_voice(text=LINES, language=["korean"] * len(LINES), speaker=[spk] * len(LINES),
                                               instruct=[ins] * len(LINES) if ins else None)
            import numpy as np
            gap = np.zeros(int(sr * 0.35), dtype=np.float32)
            full = np.concatenate([x for w in wavs for x in (w.astype(np.float32), gap)])
            sf.write("/tmp/q.wav", full, sr)
            name = f"qwen06b_{spk}_{'instruct' if ins else 'plain'}"; mp3("/tmp/q.wav", name)
            res[name] = {"sec": round(time.time() - t0, 1), "audio": round(dur(OUT / f"{name}.mp3"), 1)}
    elif engine == "melo":
        from melo.api import TTS
        t0 = time.time(); m = TTS(language="KR", device="cpu"); res["load_s"] = round(time.time() - t0, 1)
        for spd in (1.0, 1.1):
            t0 = time.time()
            m.tts_to_file(TEXT.replace("\n", " "), m.hps.data.spk2id["KR"], "/tmp/m.wav", speed=spd)
            name = f"melo_kr_x{spd}"; mp3("/tmp/m.wav", name)
            res[name] = {"sec": round(time.time() - t0, 1), "audio": round(dur(OUT / f"{name}.mp3"), 1)}
    elif engine == "edge":
        import asyncio, edge_tts
        async def go(v, rate):
            t0 = time.time()
            await edge_tts.Communicate(TEXT.replace("\n", " "), v, rate=rate).save("/tmp/e.mp3")
            name = f"edge_{v.split('-')[2]}_{rate}"
            subprocess.run(["cp", "/tmp/e.mp3", OUT / f"{name}.mp3"], check=True)
            res[name] = {"sec": round(time.time() - t0, 1), "audio": round(dur(OUT / f"{name}.mp3"), 1)}
        for v in ["ko-KR-SunHiNeural", "ko-KR-InJoonNeural", "ko-KR-HyunsuMultilingualNeural"]:
            asyncio.run(go(v, "+0%"))
except Exception:
    res["error"] = traceback.format_exc()[-1500:]
(OUT / f"result_{engine}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1))
