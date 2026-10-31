"""SNS 게시 규칙 (사장님 2026-10-31, 못 박음). 원본은 site/public/studio/rules.json 하나다.

스튜디오 화면과 이 프로그램이 같은 파일을 읽는다. 규칙을 바꾸려면 그 파일만 고친다.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

FILE = Path(__file__).resolve().parents[2] / "site" / "public" / "studio" / "rules.json"


def load() -> dict:
    return json.loads(FILE.read_text(encoding="utf-8"))


def slot(name: str) -> dict:
    return next(s for s in load()["slots"] if s["slot"] == name)


def morning_format(day: dt.date) -> str:
    """그날 아침 영상 형식. 날마다 돌아가므로 이틀 연속 같은 형식이 나오지 않는다."""
    keys = [f["key"] for f in slot("아침")["formats"]]
    return keys[day.toordinal() % len(keys)]
