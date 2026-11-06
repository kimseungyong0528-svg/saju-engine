"""결제 전 화면 목차의 '이 장에 들어 있는 쪽' 줄이 실제 리포트 목차와 같은지(사장님 2026-11-06 저녁 5-2, 제1조항)."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_toc_pages_json_matches_report_outline():
    spec = importlib.util.spec_from_file_location("make_toc_pages", ROOT / "site" / "tools" / "make_toc_pages.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    saved = json.loads((ROOT / "site" / "public" / "assets" / "free" / "toc-pages.json").read_text(encoding="utf-8"))
    assert saved == mod.build(), "리포트 목차가 바뀌었으면 python site/tools/make_toc_pages.py 를 다시 돌린다"
    assert set(saved) >= {"lifetime", "romance", "newyear", "wealth", "career", "business", "health", "intimate", "reunion", "reunion-solo"}
    # 상대 생일 없는 재회사주는 5·6장이 내 사주로 바뀐 쪽이다(화면 목차 RV_SOLO_TOC 와 같은 리포트)
    assert saved["reunion-solo"]["5"] != saved["reunion"]["5"]
