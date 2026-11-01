"""SNS 게시물을 공식으로 만든다 (사장님 2026-11-01 "전부 공식으로, 무한 발행 고퀄리티로").

    python -m saju.marketing.formula --start 2026-11-02 --days 1 --out 게시물 [--publish] [--no-video]

하루에
  아침 07:30  영상 1개 (5가지 형식을 날마다 돌림) → 유튜브 쇼츠·인스타 릴스·페북 릴스
  저녁 18:00  스레드 글 1개 (첫 장은 본글, 나머지는 내 댓글로 이어 쓰기) + 같은 글 캡처 영상 → 인스타 릴스
이미 쓴 재료(관리 사이트의 used 목록)는 다시 고르지 않는다. 결과 묶음은 /studio 가 읽는 manifest.json 모양 그대로다.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path

from ..__main__ import AM, CHANNEL_NAMES, PM, WEEKDAYS
from ..content import SITE_URL
from . import text as T

FMT_NAMES = {"tier": "천복식 띠 순위", "hidden": "가림식 띠 순위", "sinbi": "띠별 운세 표", "forceteller": "오행 그림",
             "solo": "풍경 2줄 제목"}
STYLE_NAMES = {"jangin": "사주장인식 (댓글로 이어 쓰기)", "salgu": "살구식 ○탄", "dohwa": "도화도르식 한 줄"}


def problems(m: T.Morning, e: T.Evening) -> list[str]:
    out = []
    txt = T.all_text(m, e)
    out += [f"금지어 '{w}'" for w in T.BANNED if w in txt]
    out += [f"스레드 {i}장이 500자를 넘어요" for i, p in enumerate(e.parts, 1) if len(p) > 500]
    if m.title and len(m.title) != 3:
        out.append("제목이 3줄이 아니에요")
    return out


def _thumb(video: Path, at: float, out: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{at:.2f}", "-i", str(video), "-frames:v", "1", str(out)], check=True)


def build(start: dt.date, days: int, out: Path, used: set[str] | None = None, video: bool = True) -> dict:
    week = out / start.isoformat()
    (week / "유튜브").mkdir(parents=True, exist_ok=True)
    (week / "인스타").mkdir(parents=True, exist_ok=True)
    manifest = {"week": start.isoformat(), "createdAt": dt.datetime.now(dt.UTC).isoformat(timespec="minutes"),
                "maker": "formula", "days": [], "problems": [], "used": [],
                "trends": {"items": [], "notes": ["공식으로 만든 묶음: 엔진 순위 + 글 재료 창고(banks.json)"]}}
    R = None
    if video:
        from .render import Renderer
        R = Renderer(week / "_작업")
    rows = []
    try:
        for i, (day, m, e) in enumerate(T.plan(start, days, used)):
            tag = f"{day:%m-%d}"
            entry = {"date": day.isoformat(), "weekday": WEEKDAYS[day.weekday()], "items": []}
            manifest["used"] += [m.key, e.key]
            manifest["problems"] += [f"{tag} {p}" for p in problems(m, e)]
            # 아침 영상 1개 → 세 채널
            vid, thumb = f"유튜브/{tag}_오전_{m.key}.mp4", f"유튜브/{tag}_오전_{m.key}_표지.jpg"
            if R:
                R.morning(m, week / vid, seed=i * 2 + 1)
                _thumb(week / vid, 2.5, week / thumb)
            mt = m.texts()
            title = " ".join(m.title).replace("“", "").replace("”", "") if m.title else mt["youtube"]["제목"]
            for ch, sfx in (("youtube", "youtube"), ("instagram-reel", "reel"), ("facebook-reel", "fbreel")):
                entry["items"].append({"id": f"{tag}_오전-{sfx}", "channel": ch, "time": AM, "slot": "오전", "material": m.key,
                                       "format": FMT_NAMES[m.fmt], "title": title, "score": 0,
                                       "video": vid if R else "", "thumb": thumb if R else "", "texts": mt[ch]})
            # 저녁 스레드 글 + 캡처 영상
            et = e.texts()
            cap = f"인스타/{tag}_저녁_{e.key}.mp4"
            if R:
                R.threads(e, week / cap, seed=i * 2 + 2)
            first = e.pages[0][0] if e.pages and e.pages[0] else e.key
            entry["items"].append({"id": f"{tag}_저녁-threads", "channel": "threads", "time": PM, "slot": "저녁", "material": e.key,
                                   "format": STYLE_NAMES[e.style], "title": first, "score": 0, "texts": et["threads"]})
            entry["items"].append({"id": f"{tag}_저녁-reel", "channel": "instagram-reel", "time": PM, "slot": "저녁", "material": e.key,
                                   "format": "스레드 글 캡처", "title": first, "score": 0, "video": cap if R else "",
                                   "thumb": "", "texts": et["instagram-reel"]})
            for it in entry["items"]:
                rows.append([f"{day.isoformat()} {it['time']}", CHANNEL_NAMES[it["channel"]], it["format"], it["title"], it["id"]])
            manifest["days"].append(entry)
            print(f"{day} 아침 {m.key} / 저녁 {e.key}")
    finally:
        if R:
            R.close()
    titles = [it["title"] for d in manifest["days"] for it in d["items"] if it["channel"] == "youtube"]
    manifest["daangn"] = {"소식": "\n".join(["이번 주 띠별 운세", ""] + [f"▪ {t}" for t in titles] +
                                         ["", "띠는 태어난 해 하나만 본 것이에요.", "생년월일과 태어난 시간으로 보는 내 운세는 운명서재에서", SITE_URL])}
    shutil.rmtree(week / "_작업", ignore_errors=True)
    with open(week / "일정표.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["올릴 시각", "채널", "형식", "제목", "번호"])
        w.writerows(rows)
    (week / "검사결과.txt").write_text("\n".join(manifest["problems"]) or "문제 없음", encoding="utf-8")
    (week / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"folder": week, "manifest": manifest}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SNS 게시물 공식으로 만들기")
    ap.add_argument("--start", required=True)
    ap.add_argument("--days", type=int, default=1)
    ap.add_argument("--out", default="게시물")
    ap.add_argument("--used", default="", help="이미 쓴 재료 이름들 (쉼표로)")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--no-video", action="store_true")
    a = ap.parse_args(argv)
    start = dt.date.fromisoformat(a.start)
    used = set(filter(None, a.used.split(",")))
    from .. import publish
    if a.publish:
        publish.status(start.isoformat(), "running", "만드는 중")
        used |= publish.used_keys()
    try:
        r = build(start, a.days, Path(a.out), used, video=not a.no_video)
    except Exception as e:
        if a.publish:
            publish.status(start.isoformat(), "failed", f"만들기 실패: {type(e).__name__}")
        raise
    for p in r["manifest"]["problems"]:
        print("  검사:", p)
    if a.publish:
        publish.upload_week(r["folder"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
