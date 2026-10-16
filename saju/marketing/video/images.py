"""장면 그림을 매일 새로 그린다 (Cloudflare Workers AI, FLUX.1 schnell, 하루 무료 사용량 안).

열쇠 두 개가 환경 변수에 있어야 한다: CF_ACCOUNT_ID, CF_API_TOKEN.
열쇠가 없거나 그리기에 실패하면 None 을 돌려주고, 부르는 쪽은 고정 그림을 쓴다.
같은 얼굴을 매번 똑같이 그리지 못하므로 사람 얼굴은 그리지 않는다 (금월선녀는 고정 그림).
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

MODEL = "@cf/black-forest-labs/flux-1-schnell"
STYLE = ("cinematic photorealistic scene in Joseon dynasty Korea, traditional hanok architecture, "
         "rich warm colors, dramatic soft lighting, highly detailed, vertical composition, "
         "dark and simple lower third, no people, no faces, no text, no letters, no watermark")

ANIMAL = {
    "쥐": "a white mouse in front of a snowy palace granary",
    "소": "a calm brown ox beside a thatched house and spring rice fields",
    "호랑이": "a majestic tiger sitting on a rock in a misty pine forest at dawn",
    "토끼": "a white rabbit in a palace garden under a full moon",
    "용": "a blue dragon rising through dark clouds above palace roofs",
    "뱀": "a golden snake on a rock by a lotus pond",
    "말": "a white horse galloping across a palace courtyard at sunset",
    "양": "white sheep on a green hill near a hanok village, clear day",
    "원숭이": "a monkey on a persimmon tree beside an autumn palace wall",
    "닭": "a red rooster on a thatched roof at sunrise",
    "개": "a loyal yellow dog guarding a palace gate lit by lanterns",
    "돼지": "a plump happy pig beside sacks of harvested grain in golden light",
}

# 장면 제목·본문에 이 낱말이 있으면 그 장면 모습을 그린다 (앞에 있는 것이 먼저).
MOTIF = [
    (("조심", "주의", "충돌", "상충", "삼재", "구설", "다툼", "손실", "손해"),
     "a palace under dark storm clouds with lightning, rain at night"),
    (("재물", "돈", "재성", "수입", "투자", "금전", "부자"),
     "a treasure room piled with gold coins and gold bars, candlelight"),
    (("연애", "사랑", "인연", "결혼", "배우자", "짝", "궁합", "육합", "삼합"),
     "a lantern-lit wooden bridge with red threads tied to the railings, night"),
    (("직장", "일터", "승진", "관성", "직업", "사업", "이직", "명예"),
     "a royal government office with a desk, official seal and documents"),
    (("공부", "시험", "합격", "인성", "자격", "문서", "계약"),
     "a quiet seodang study room with brush, inkstone and old books on a low desk"),
    (("건강", "몸", "휴식", "잠", "체력", "병"),
     "a traditional herbal medicine room with drawers of herbs and a steaming clay pot"),
    (("이사", "이동", "여행", "변화", "역마"),
     "a stone road leading out of the palace with a wooden palanquin at dawn"),
    (("귀인", "사람", "도움", "관계", "친구", "가족"),
     "two warm lanterns meeting at an open palace gate, welcoming light"),
]
SEASON = ["spring cherry blossoms", "summer green leaves", "autumn red maple leaves", "winter fresh snow"]
TIME = ["golden sunset light", "soft morning mist", "moonlit night with lanterns", "bright clear afternoon"]


def _cf() -> bool:
    return bool(os.environ.get("CF_ACCOUNT_ID") and os.environ.get("CF_API_TOKEN"))


def _free() -> bool:
    # 시험용: 열쇠 없이 쓰는 공개 그림 AI (Pollinations, FLUX). 매일 영상에는 Cloudflare 를 쓴다.
    return os.environ.get("SAJU_ART") == "free"


def ready() -> bool:
    return _cf() or _free()


def status() -> str:
    if _cf():
        return "그림 AI 켜짐 (Cloudflare FLUX)"
    return "그림 AI 시험 (Pollinations FLUX)" if _free() else "그림 AI 꺼짐 (CF 열쇠 없음, 고정 그림 사용)"


def _draw_free(prompt: str, out: Path, seed: int) -> Path | None:
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
           + f"?width=768&height=1344&seed={seed}&nologo=true&model=flux")
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "saju-engine"}), timeout=180) as r:
                data = r.read()
            if len(data) > 10_000:
                out.write_bytes(data)
                return out
        except Exception as e:  # noqa: BLE001
            print(f"[그림] 다시 시도 {i + 1}: {e}")
        time.sleep(15)
    return None


def _seed(*parts: str) -> int:
    return zlib.crc32("|".join(parts).encode()) & 0x7FFFFFFF


def scene_prompt(text: str, day: str, n: int, animal: str = "") -> str:
    """장면 글(제목+본문)과 날짜로 그림 주문서를 만든다. 날짜가 바뀌면 계절·시간 모습도 바뀐다."""
    motif = next((m for words, m in MOTIF if any(w in text for w in words)), "")
    if not motif or (animal and n % 2 == 0):
        motif = ANIMAL.get(animal, "") or motif or "a grand Joseon palace courtyard"
    s = _seed(day, str(n))
    return f"{motif}, {SEASON[s % 4]}, {TIME[(s // 4) % 4]}, {STYLE}"


def draw(prompt: str, out: Path, seed: int) -> Path | None:
    if not ready():
        return None
    if not _cf():
        return _draw_free(prompt, out, seed)
    url = (f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CF_ACCOUNT_ID']}/ai/run/{MODEL}")
    body = json.dumps({"prompt": prompt, "steps": 8, "seed": seed}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {os.environ['CF_API_TOKEN']}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read())
        img = (data.get("result") or {}).get("image")
        if not img:
            print(f"[그림] 실패: {str(data)[:200]}")
            return None
        out.write_bytes(base64.b64decode(img))
        return out
    except Exception as e:  # noqa: BLE001 - 그림이 없어도 영상은 만든다
        print(f"[그림] 실패: {e}")
        return None
