"""일주일치 SNS 게시물 묶음 만들기.

    python -m saju.marketing --start 2026-10-19 --days 7 --out 게시물

하루 2번(오전 띠별 운세, 저녁 방법·시기 글) 순서대로 채운다.
게시물마다 인스타·페북·스레드·X·유튜브 쇼츠용 파일을 만들고, 일정표와 검사 결과를 남긴다.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path

from . import cards
from .checks import check_post
from .content import (caption_facebook, caption_instagram, ddi_posts, summary_post, text_daangn,
                      text_shorts, text_threads, text_x, topic_posts)

SLOTS = (("오전", "08:00"), ("저녁", "20:00"))
WEEKDAYS = "월화수목금토일"


def schedule() -> list[tuple]:
    """(오전 글, 저녁 글) 하루치 짝의 전체 목록. 오전은 띠별 12개 + 12띠 한눈에, 저녁은 방법·시기 글."""
    am = ddi_posts() + [summary_post()]
    pm = topic_posts()
    n = max(len(am), len(pm))
    return [(am[i] if i < len(am) else None, pm[i] if i < len(pm) else None) for i in range(n)]


def build(start: dt.date, days: int, offset: int, out: Path, video: bool = True) -> dict:
    plan = schedule()[offset:offset + days]
    week = out / f"{start.isoformat()}_시작"
    week.mkdir(parents=True, exist_ok=True)
    rows, problems, posts = [], [], []
    for d, pair in enumerate(plan):
        day = start + dt.timedelta(days=d)
        for (slot, time), p in zip(SLOTS, pair):
            if p is None:
                continue
            posts.append(p)
            label = f"{p.key}띠" if p.kind == "ddi" else p.key if p.kind == "summary" else p.title.replace(" ", "")
            name = f"{day:%m-%d}({WEEKDAYS[day.weekday()]})_{slot}_{label}"
            folder = week / name
            folder.mkdir(exist_ok=True)
            texts = {"인스타": caption_instagram(p), "페북": caption_facebook(p), "스레드": text_threads(p),
                     "X": text_x(p), "쇼츠": text_shorts(p)}
            files = {"인스타": "인스타_캡션.txt", "페북": "페북_캡션.txt", "스레드": "스레드_글.txt",
                     "X": "X_글.txt", "쇼츠": "쇼츠_제목_설명.txt"}
            for k, fn in files.items():
                (folder / fn).write_text(texts[k], encoding="utf-8")
            cards.render_pngs(p, "feed", folder, "카드")
            if video:
                tall = cards.render_pngs(p, "shorts", folder / "_세로", "세로")
                cards.render_video(tall, folder / "쇼츠_영상.mp4")
            issues = check_post(p, texts)
            problems += [f"{name}: {i}" for i in issues]
            when = f"{day.isoformat()} {time}"
            for ch, what in (("인스타그램", "카드_01~ 이미지 + 인스타_캡션"), ("페이스북", "카드 이미지 + 페북_캡션"),
                             ("스레드", "스레드_글 (+카드_01 이미지)"), ("X", "X_글 (+카드_01 이미지)"),
                             ("유튜브 쇼츠", "쇼츠_영상.mp4 + 쇼츠_제목_설명")):
                rows.append([when, ch, p.title, name, what])
    (week / "당근_비즈프로필_소식.txt").write_text(text_daangn(posts), encoding="utf-8")
    with open(week / "일정표.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["올릴 시각", "채널", "제목", "폴더", "올릴 파일"])
        w.writerows(rows)
        w.writerow([f"{start.isoformat()} 아무 때", "당근", "이번 주 띠별 운세", "", "당근_비즈프로필_소식.txt"])
    (week / "검사결과.txt").write_text("\n".join(problems) if problems else "문제 없음", encoding="utf-8")
    return {"folder": week, "posts": len(posts), "problems": problems}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SNS 게시물 묶음 만들기")
    ap.add_argument("--start", required=True, help="첫날 (YYYY-MM-DD)")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--offset", type=int, default=0, help="전체 순서에서 몇 번째 날부터 (2주차는 7)")
    ap.add_argument("--out", default="게시물")
    ap.add_argument("--no-video", action="store_true")
    a = ap.parse_args(argv)
    r = build(dt.date.fromisoformat(a.start), a.days, a.offset, Path(a.out), video=not a.no_video)
    print(f"{r['posts']}개 게시물 → {r['folder']}")
    for p in r["problems"]:
        print("  검사:", p)
    return 1 if r["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
