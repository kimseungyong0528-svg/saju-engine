"""대본 한 줄씩 목소리 파일(wav)로 만든다.

타입캐스트 열쇠(TYPECAST_API_KEY)가 있으면 타입캐스트로 읽는다 (사장님 2026-11-01 "타입캐스트 존나 자연스러운걸로").
없으면 Supertonic, 그것도 없으면 길이만 맞춘 무음을 만든다."""

from __future__ import annotations

import json
import os
import re
import urllib.request
import wave
from pathlib import Path

VOICE = os.environ.get("SAJU_VOICE", "F2")   # 여자1~5 = F1~F5, 남자1~5 = M1~M5
SPEED = float(os.environ.get("SAJU_VOICE_SPEED", "1.1"))   # 쇼츠가 1분 안에 끝나도록 조금 빠르게
SR = 44100
_tts = None
_style = None
_failed = ""


def clean(text: str) -> str:
    """읽기 좋게: 한자 괄호, 따옴표, 번호 매기기를 뺀다."""
    t = re.sub(r"\([㐀-鿿·\s]+\)", "", text)
    t = re.sub(r"[㐀-鿿]+", "", t)
    t = re.sub(r"^\s*\d+\.\s*", "", t, flags=re.M)
    t = t.replace("'", "").replace("\"", "").replace("ㅣ", ", ").replace("·", ", ").replace("—", ", ").replace("×", "와 ")
    return re.sub(r"\s+", " ", t).strip()


def sentences(text: str) -> list[str]:
    """문장 단위로 자른다(자막 한 장 = 목소리 한 번)."""
    parts = re.split(r"(?<=[.!?요다])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p and p.strip()]


def _engine():
    global _tts, _style, _failed
    if _tts is None and not _failed:
        if os.environ.get("SAJU_TTS") == "off":
            _failed = "목소리 끔(SAJU_TTS=off)"
        else:
            try:
                from supertonic import TTS
                _tts = TTS()
                _style = _tts.get_voice_style(VOICE)
            except Exception as e:  # 모델을 못 받는 곳(인터넷 막힘 등)에서는 무음으로 만든다
                _failed = f"목소리 엔진을 쓰지 못함: {type(e).__name__}"
    return _tts


def status() -> str:
    _engine()
    return f"목소리 {VOICE}" if _tts else _failed


def _silence(path: Path, sec: float) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"\0\0" * int(SR * sec))


TYPECAST = "https://api.typecast.ai/v1/text-to-speech"
TC_MODEL = os.environ.get("TYPECAST_MODEL", "ssfm-v31")


def typecast(text: str, path: Path, voice_id: str = "", prev: str = "", nxt: str = "", tempo: float = 0.0) -> Path:
    """타입캐스트로 읽는다. 앞뒤 문장을 같이 주면 감정을 문맥에 맞춰 넣는다(smart)."""
    prompt = {"emotion_type": "smart"}
    if prev:
        prompt["previous_text"] = prev
    if nxt:
        prompt["next_text"] = nxt
    body = {"text": text, "model": TC_MODEL, "voice_id": voice_id or os.environ["TYPECAST_VOICE"], "prompt": prompt,
            "output": {"audio_format": "wav", "target_lufs": -14.0, "audio_tempo": tempo or SPEED}}
    req = urllib.request.Request(TYPECAST, data=json.dumps(body, ensure_ascii=False).encode(), method="POST",
                                 headers={"X-API-KEY": os.environ["TYPECAST_API_KEY"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        Path(path).write_bytes(r.read())
    return path


def typecast_voices(model: str = "") -> list[dict]:
    req = urllib.request.Request(f"https://api.typecast.ai/v3/voices?model={model or TC_MODEL}",
                                 headers={"X-API-KEY": os.environ["TYPECAST_API_KEY"]})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def speak(text: str, path: Path, prev: str = "", nxt: str = "") -> Path:
    said = clean(text)
    if os.environ.get("TYPECAST_API_KEY") and os.environ.get("TYPECAST_VOICE"):
        return typecast(said, path, prev=clean(prev), nxt=clean(nxt))
    tts = _engine()
    if tts is None:
        _silence(path, max(1.2, len(said) / (8.0 * SPEED)))
        return path
    wav, _ = tts.synthesize(said, voice_style=_style, lang="ko", total_steps=16, speed=SPEED)
    tts.save_audio(wav, str(path))
    return path
