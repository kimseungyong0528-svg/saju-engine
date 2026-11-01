"""사장님이 보고 "올려" 한 그날 영상 2개 + 인스타 캡처 게시글·페북 글을 관리 사이트에 넣고 승인한다
(사장님 2026-11-01 "당장 오늘꺼 영상 2개 만들어 스레드 캡쳐한 게시글, 페북은 텍스트글은 이미 스레드 업로드된 1탄과 내일 아침에 올릴 2탄으로").

    python -m saju.marketing.formula.today_videos --date 2026-11-02 --src video-samples --picks "1탄,2탄" [--dry]

- 인스타 캡처 게시글·페북 글: --picks 의 글(스레드에 올린 그대로의 글)을 12:30(점심글)·21:00(밤글)에 하나씩.
  흰 배경 캡처는 여기서 찍는다. 이렇게 넣은 칸은 meta.run 이 전날 인기 글 고르기(pick.py) 대신 이 글을 올린다.

- 영상은 다시 만들지 않는다. 영상 견본(video-samples 브랜치)에 올라간, 사장님이 본 파일을 그대로 쓴다.
- 그날 스레드 글은 지금 묶음에 있는 그대로(승인·번호 그대로) 옮겨 담는다. 그래서 그날 스레드는 그대로 올라간다.
- 묶음 이름은 그 날짜 하루치. 관리 사이트는 그날이 들어 있는 가장 최근 묶음을 쓰므로, 다음 날부터는 원래 주 묶음을 쓴다.
- 영상은 approved_by=claude (사장님 "올려" 뒤에만 돌린다, CLAUDE.md 제2조항·ask-before-studio-upload).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path

from .. import publish
from . import text as T
from ..__main__ import WEEKDAYS
from .__main__ import VIDEO_AM, VIDEO_PM, _videos
from .pick import IG_CAPTION_MAX, body

PICK_TIMES = (("점심글", "12:30"), ("밤글", "21:00"))


class _Shown:
    """스레드에 올라간 글을 캡처용 모양으로. 긴 장은 빈 줄 단위로 끊어 한 사진에 18줄 안쪽으로 담는다 (글씨가 작아지지 않게)."""
    LINES = 18

    def __init__(self, parts: list[str]):
        pages = []
        for p in parts:
            cur: list[str] = []
            for block in p.strip().split("\n\n"):
                if cur and len("\n\n".join(cur + [block]).split("\n")) > self.LINES:
                    pages.append(["\n\n".join(cur)])
                    cur = []
                cur.append(block)
            if cur:
                pages.append(["\n\n".join(cur)])
        self.pages = pages[:10]   # 인스타 여러 장 게시글은 10장까지
        self.shown = self.pages


def find_post(plans: list[dict], mark: str) -> dict:
    """'1탄'처럼 글 속 표시로 스레드 글을 찾는다 (올라간 글 그대로)."""
    for plan in plans:
        for it in plan.get("items", []):
            if it["channel"] == "threads" and f"- {mark}" in body(it):
                return it
    raise SystemExit(f"'{mark}' 스레드 글을 못 찾았어요")


def pick_items(C, week: Path, date: dt.date, posts: list[dict]) -> list[dict]:
    tag, out = f"{date:%m-%d}", []
    for (slot, time), it in zip(PICK_TIMES, posts):
        stem = f"{tag}_{slot}_{it['material']}"
        imgs = [f"인스타/{f.name}" for f in C.thread_cards(_Shown(list(it["texts"].values())), week / "인스타", stem)]
        text = body(it)
        for ch, sfx in (("instagram-cards", "cards"), ("facebook-post", "fbpost")):
            out.append({"id": f"{tag}_{slot}-{sfx}", "channel": ch, "time": time, "slot": slot, "material": it["material"],
                        "format": it.get("format", ""), "title": it.get("title", ""), "score": 0, "approved_by": "claude",
                        "images": imgs if ch == "instagram-cards" else [],
                        "texts": {"캡션": text[:IG_CAPTION_MAX]} if ch == "instagram-cards" else {"본문": text}})
    return out


def build(date: dt.date, src: Path, out: Path, today: dict, posts: list[dict] | None = None) -> dict:
    d = T.plan(date, 1, set())[0]      # 영상 견본과 같은 계산 (video-samples.yml: plan(start, days, set()))
    tag = f"{date:%m-%d}"
    week = out / date.isoformat()
    shutil.rmtree(week, ignore_errors=True)
    week.mkdir(parents=True)
    vids = _videos(None, week, d.morning, tag, "오전", "아침영상", VIDEO_AM, 1, src=src)
    if d.video2:
        vids += _videos(None, week, d.video2, tag, "저녁", "저녁영상", VIDEO_PM, 2, src=src)
    # 유튜브는 아직 계정이 없어서 넣지 않는다 (사장님 2026-11-01 "유튜브는 아직 계정 안만들었으니까 올리지말고 인스타 페북만")
    vids = [it for it in vids if it["channel"] != "youtube"]
    for it in vids:
        it["approved_by"] = "claude"
    keep = [it for it in today.get("items", []) if it["channel"] == "threads"]
    picks = []
    if posts:
        from .render import Renderer
        C = Renderer(out / "_work")
        try:
            picks = pick_items(C, week, date, posts)
        finally:
            C.close()
    items = sorted(keep + vids + picks, key=lambda it: it["time"])
    used = [d.morning.key] + ([d.video2.key] if d.video2 else []) + [it["material"] for it in keep]
    return {"week": week.name, "start": date.isoformat(), "days": [{"date": date.isoformat(), "weekday": WEEKDAYS[date.weekday()], "items": items}],
            "used": used, "problems": [], "videos_approved_by": "claude", "from_week": today.get("week")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", default="오늘영상")
    ap.add_argument("--picks", default="", help="인스타 캡처·페북 글로 올릴 스레드 글 표시 (예 '1탄,2탄': 12:30, 21:00 순서)")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    date = dt.date.fromisoformat(a.date)
    get = lambda d: publish._call("GET", f"/api/internal/studio/today?date={d.isoformat()}")
    today = {"items": []} if a.dry else get(date)
    posts = []
    if a.picks and not a.dry:
        plans = [get(date - dt.timedelta(days=1)), today]
        posts = [find_post(plans, x.strip()) for x in a.picks.split(",")]
    man = build(date, Path(a.src), Path(a.out), today, posts)
    folder = Path(a.out) / man["week"]
    (folder / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    its = man["days"][0]["items"]
    th = sum(it["channel"] == "threads" for it in its)
    for it in its:
        print(f"  {it['time']} {it['channel']:16} {it['id']} {it.get('approved_by', '')}")
    print(f"{date} 묶음: 스레드 {th}개(그대로) + 나머지 {len(its) - th}개(승인)")
    if not a.dry:
        if th == 0:
            raise SystemExit("그날 스레드 글을 못 찾았어요. 스레드가 빠지면 안 되므로 올리지 않아요.")
        publish.upload_week(folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
