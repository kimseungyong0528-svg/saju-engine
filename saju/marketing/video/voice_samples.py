"""타입캐스트 목소리 후보를 골라 같은 문장을 읽힌다 (사장님 2026-11-01). 손으로만 돌린다: Actions → 목소리 견본."""
import json
import os
import sys
from pathlib import Path

from saju.marketing.video import voice

# 사장님 2026-11-01 "5문장 정도로 해"
LINE = os.environ.get("VOICE_LINE") or (
    "11월에 먼저 연락 오는 사람 생길 띠, 1위는 호랑이띠예요. "
    "98년생, 86년생, 74년생, 62년생이라면 그냥 넘기지 마세요. "
    "입동이 지나면 물 기운이 세지는 기해월이 시작돼요. "
    "이 달 글자 해와 호랑이띠 글자 인이 짝처럼 잘 맞는 육합이라, 곁에 앉고 싶은 사람이 생겨요. "
    "내 띠는 몇 위였는지 댓글로 남겨 주세요.")
out = Path(sys.argv[1] if len(sys.argv) > 1 else "voice-samples")
out.mkdir(parents=True, exist_ok=True)
vs = voice.typecast_voices()
want = os.environ.get("VOICE_IDS", "")
if want:
    pick = [v for v in vs if v["voice_id"] in want.split(",")]
else:
    # 사장님 2026-11-01: "가장 유명하고 자연스러운 20~30대 여성 목소리" → 여자·젊은 어른, 쇼츠/대화용 먼저
    fem = [v for v in vs if v.get("gender") == "female" and v.get("age") == "young_adult"]
    uses = lambda v: " ".join(v.get("use_cases", []))
    fem.sort(key=lambda v: ("Shorts" not in uses(v), "Conversational" not in uses(v)))
    pick = fem[:8]
rows = []
for v in pick:
    name = (v.get("voice_name") or {}).get("kor") or (v.get("voice_name") or {}).get("eng") or v["voice_id"]
    f = out / f"{name}_{v['voice_id']}.wav"
    voice.typecast(LINE, f, voice_id=v["voice_id"], tempo=1.0)
    rows.append({"name": name, "id": v["voice_id"], "gender": v.get("gender"), "age": v.get("age"), "use_cases": v.get("use_cases"), "file": f.name})
    print(name, v["voice_id"], v.get("gender"), v.get("age"))
(out / "voices.json").write_text(json.dumps({"line": LINE, "voices": rows, "all": len(vs)}, ensure_ascii=False, indent=1), encoding="utf-8")
