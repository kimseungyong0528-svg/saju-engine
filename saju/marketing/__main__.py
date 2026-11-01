"""일주일치 SNS 게시물 묶음 만들기 (재료 하나, 포장은 채널별).

    python -m saju.marketing --start 2026-10-19 --out 게시물 [--trends] [--publish]

하루 재료 2개: 오전 = 띠별 2027 운세, 저녁 = 사주 상식(보는 법·시기).
  유튜브 쇼츠 2: 오전 = 목소리 입힌 이야기형(오전 재료), 저녁 = 띠 순위형(ranking.py, 엔진 계산)
  인스타 릴스 1 (오전 쇼츠와 같은 영상), 인스타 카드뉴스 1 (저녁 재료),
  스레드 2 (오전·저녁 재료), 페이스북은 인스타에서 같이 공유, 당근은 주 1회 소식.
재료 순서는 그 주 레퍼런스 계정에서 뜬 주제(trends)와 겹치는 것부터, 이미 쓴 재료는 뒤로.
결과: <out>/<첫날>/ 아래 채널별 폴더, manifest.json(관리 사이트가 읽음), 일정표.csv, 검사결과.txt
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import shutil
from pathlib import Path

from . import cards, trends as tr
from .checks import check_post, check_rank
from .ranking import rank_posts, youtube_rank
from .content import (daangn, ddi_posts, facebook_reel, instagram_cards, instagram_reel, summary_post, threads,
                      topic_posts, youtube)

WEEKDAYS = "월화수목금토일"
# 출근길·퇴근길 (사장님 2026-10-31). 인스타·페북·스레드는 승인한 것만 이 시각에 자동으로 올라간다(meta.py).
AM, PM = "07:30", "18:00"
CHANNEL_NAMES = {"youtube": "유튜브 쇼츠", "instagram-reel": "인스타 릴스", "facebook-reel": "페이스북 릴스",
                 "instagram-cards": "인스타 카드뉴스",
                 "threads": "스레드", "daangn": "당근 소식"}


def pick(days: int, trends: dict | None, used: set[str]) -> list[tuple]:
    """하루치 (오전 재료, 저녁 재료) 짝을 days개 고른다. 재료가 모자라면 오래전에 쓴 것부터 다시 쓴다."""
    am = tr.order(ddi_posts() + [summary_post()], trends, used)
    pm = tr.order(topic_posts(), trends, used)
    return [(am[i % len(am)], pm[i % len(pm)]) for i in range(days)]


def pick_ranks(start: dt.date, days: int, used: set[str]) -> list:
    pool = rank_posts(start)
    pool = [p for p in pool if p.key not in used] + [p for p in pool if p.key in used]
    return [pool[i % len(pool)] for i in range(days)]


def _thumb(video: Path, at: float, out: Path) -> None:
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{at:.2f}", "-i", str(video), "-frames:v", "1", str(out)],
                   check=True)


def _jpgs(pngs: list[Path]) -> list[Path]:
    """인스타 API는 사진을 JPEG만 받는다. 카드 PNG를 JPEG로 바꾼다 (ffmpeg 이 없으면 PNG 그대로)."""
    import shutil as sh
    import subprocess
    if not sh.which("ffmpeg"):
        return pngs
    out = []
    for p in pngs:
        j = p.with_suffix(".jpg")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(p), "-q:v", "2", str(j)], check=True)
        p.unlink()
        out.append(j)
    return out


def build(start: dt.date, days: int, out: Path, trends: dict | None = None, used: set[str] | None = None,
          video: bool = True) -> dict:
    used = used or set()
    if video:
        from .video import render as vr
    week = out / start.isoformat()
    week.mkdir(parents=True, exist_ok=True)
    manifest = {"week": start.isoformat(), "createdAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
                "days": [], "problems": [], "trends": trends or {"items": [], "notes": ["뜬 주제 모으기를 하지 않음"]},
                "used": []}
    rows, posts = [], []
    ranks = pick_ranks(start, days, used)

    def save(rel: str, text: str) -> str:
        (week / rel).parent.mkdir(parents=True, exist_ok=True)
        (week / rel).write_text(text, encoding="utf-8")
        return rel

    for d, ((am, am_score), (pm, pm_score)) in enumerate(pick(days, trends, used)):
        day = start + dt.timedelta(days=d)
        tag = f"{day:%m-%d}"
        entry = {"date": day.isoformat(), "weekday": WEEKDAYS[day.weekday()], "items": []}
        for p, score, slot, time in ((am, am_score, "오전", AM), (pm, pm_score, "저녁", PM)):
            posts.append(p)
            manifest["used"].append(p.key)
            base = f"{tag}_{slot}"
            packs = {"youtube": youtube(p), "threads": threads(p)}
            (week / "유튜브").mkdir(exist_ok=True)
            if slot == "오전":
                # 유튜브 쇼츠: 목소리 입힌 이야기형. 인스타 릴스도 같은 영상을 쓴다
                vid, thumb = f"유튜브/{base}_{p.key}.mp4", f"유튜브/{base}_{p.key}_표지.jpg"
                if video:
                    info = vr.make_talk(p, week / vid, seed=d * 2 + 1, day=day.isoformat())
                    manifest["voice"] = info["voice"]
                    manifest["art"] = f"{vr.images.status()} · 그린 장면 {info['art']}장"
                    _thumb(week / vid, 1.2, week / thumb)
                else:
                    thumb = ""
                entry["items"].append({"id": f"{base}-youtube", "channel": "youtube", "time": time, "slot": slot,
                                       "material": p.key, "title": packs["youtube"]["제목"], "score": score,
                                       "video": vid if video else "", "thumb": thumb, "texts": packs["youtube"]})
                packs["instagram-reel"] = instagram_reel(p)
                entry["items"].append({"id": f"{base}-reel", "channel": "instagram-reel", "time": time, "slot": slot,
                                       "material": p.key, "title": p.reel_hook, "score": score,
                                       "video": vid if video else "", "thumb": thumb,
                                       "texts": packs["instagram-reel"]})
                packs["facebook-reel"] = facebook_reel(p)
                entry["items"].append({"id": f"{base}-fbreel", "channel": "facebook-reel", "time": time, "slot": slot,
                                       "material": p.key, "title": p.title, "score": score,
                                       "video": vid if video else "", "thumb": thumb,
                                       "texts": packs["facebook-reel"]})
            else:
                # 유튜브 쇼츠: 띠 순위형 (엔진이 매긴 순위)
                rp = ranks[d]
                manifest["used"].append(rp.key)
                ypack = youtube_rank(rp)
                vid, thumb = f"유튜브/{base}_{rp.key}.mp4", f"유튜브/{base}_{rp.key}_표지.jpg"
                if video:
                    info = vr.make_rank(rp, week / vid, seed=d * 2 + 2)
                    manifest["voice"] = info["voice"]
                    _thumb(week / vid, info["seconds"] - 3.0, week / thumb)
                else:
                    thumb = ""
                entry["items"].append({"id": f"{base}-youtube", "channel": "youtube", "time": time, "slot": slot,
                                       "material": rp.key, "title": ypack["제목"], "score": 0,
                                       "video": vid if video else "", "thumb": thumb, "texts": ypack})
                save(f"유튜브/{base}_youtube_{rp.key}.txt", "\n\n".join(f"[{kk}]\n{vv}" for kk, vv in ypack.items()))
                manifest["problems"] += [f"{tag} {slot} {rp.key}: {i}" for i in check_rank(rp, ypack)]
                del packs["youtube"]
            if slot == "저녁":
                # 인스타 카드뉴스 (페북은 인스타에서 같이 공유)
                packs["instagram-cards"] = instagram_cards(p)
                imgs = _jpgs(cards.render_pngs(p, "feed", week / "인스타" / f"{base}_카드_{p.key}", "카드"))
                entry["items"].append({"id": f"{base}-cards", "channel": "instagram-cards", "time": time, "slot": slot,
                                       "material": p.key, "title": p.hook, "score": score,
                                       "images": [str(i.relative_to(week)) for i in imgs],
                                       "texts": packs["instagram-cards"]})
            entry["items"].append({"id": f"{base}-threads", "channel": "threads", "time": time, "slot": slot,
                                   "material": p.key, "title": p.reel_hook, "score": score, "texts": packs["threads"]})
            for k, v in packs.items():
                save(f"{CHANNEL_NAMES[k].split()[0]}/{base}_{k}_{p.key}.txt",
                     "\n\n".join(f"[{kk}]\n{vv}" for kk, vv in v.items()))
            manifest["problems"] += [f"{tag} {slot} {p.key}: {i}" for i in check_post(p, packs)]
            for it in entry["items"]:
                if it["slot"] == slot:
                    rows.append([f"{day.isoformat()} {time}", CHANNEL_NAMES[it["channel"]], it["title"], it["id"]])
        manifest["days"].append(entry)
    manifest["daangn"] = daangn(posts)
    save("당근/이번주_소식.txt", manifest["daangn"]["소식"])
    rows.append([f"{start.isoformat()} 아무 때", "당근 소식", "이번 주 띠별 운세", "daangn"])
    shutil.rmtree(week / "_작업", ignore_errors=True)
    with open(week / "일정표.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["올릴 시각", "채널", "제목", "번호"])
        w.writerows(rows)
    (week / "검사결과.txt").write_text("\n".join(manifest["problems"]) or "문제 없음", encoding="utf-8")
    (week / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"folder": week, "manifest": manifest}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SNS 게시물 묶음 만들기")
    ap.add_argument("--start", required=True, help="첫날 (YYYY-MM-DD)")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out", default="게시물")
    ap.add_argument("--trends", action="store_true", help="레퍼런스 계정에서 뜬 주제를 먼저 모은다 (키 필요)")
    ap.add_argument("--used", default="", help="이미 쓴 재료 이름들 (쉼표로)")
    ap.add_argument("--publish", action="store_true", help="다 만든 뒤 관리 사이트에 올린다 (SITE_URL, WORKER_SECRET)")
    ap.add_argument("--no-video", action="store_true")
    a = ap.parse_args(argv)
    start = dt.date.fromisoformat(a.start)
    used = set(filter(None, a.used.split(",")))
    from . import publish
    if a.publish:
        publish.status(start.isoformat(), "running", "만드는 중")
        used |= publish.used_keys()
    t = tr.collect() if a.trends else None
    try:
        r = build(start, a.days, Path(a.out), t, used, video=not a.no_video)
    except Exception as e:
        if a.publish:
            publish.status(start.isoformat(), "failed", f"만들기 실패: {type(e).__name__}")
        raise
    m = r["manifest"]
    print(f"{sum(len(d['items']) for d in m['days'])}개 게시물 → {r['folder']}")
    for p in m["problems"]:
        print("  검사:", p)
    if a.publish:
        publish.upload_week(r["folder"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
