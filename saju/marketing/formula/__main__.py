"""SNS 게시물을 공식으로 만든다 (사장님 2026-11-01 "전부 공식으로, 무한 발행 고퀄리티로").

    python -m saju.marketing.formula --start 2026-11-02 --days 1 --out 게시물 [--publish] [--no-video]

하루에 (사장님 2026-11-01)
  스레드 글 6개: 사주장인식 07:30·18:00, 도화도르식 12:00·21:00, 살구식 15:00·23:00 (첫 장은 본글, 나머지는 내 댓글로 이어 쓰기)
  영상 2개 (5가지 형식을 날마다 돌림, 아침·저녁 형식이 다름) → 인스타 릴스·페북 릴스·유튜브 쇼츠 모두 08:00, 19:00
  인스타 게시글(캡처)·페북 글 2개는 묶음 밖: 매일 전날 반응 좋은 스레드 글 2개를 12:30, 21:00 (formula/pick.py)
이미 쓴 재료(관리 사이트의 used 목록)는 다시 고르지 않는다. 결과 묶음은 /studio 가 읽는 manifest.json 모양 그대로다.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import shutil
import subprocess
from pathlib import Path

from ..__main__ import CHANNEL_NAMES, WEEKDAYS
from ..content import SITE_URL
from . import text as T
from . import script as S

FMT_NAMES = {"tier": "천복식 띠 순위", "hidden": "가림식 띠 순위", "sinbi": "띠별 운세 표", "forceteller": "오행 그림",
             "solo": "풍경 2줄 제목"}
STYLE_NAMES = {"jangin": "사주장인식", "salgu": "살구식", "dohwa": "도화도르식"}
VIDEO_AM, VIDEO_PM = "08:00", "19:00"   # 사장님 2026-11-01: 영상은 세 SNS 모두 아침 8시·저녁 7시


def problems(m: T.Morning, *es: T.Evening) -> list[str]:
    out = []
    txt = T.all_text(m, *es)
    out += [f"금지어 '{w}'" for w in T.BANNED if w in txt]
    out += [f"스레드 {e.key} {i}장이 500자를 넘어요" for e in es for i, p in enumerate(e.parts, 1) if len(p) > 500]
    if m.title and len(m.title) != 3:
        out.append("제목이 3줄이 아니에요")
    return out


def _thumb(video: Path, at: float, out: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{at:.2f}", "-i", str(video), "-frames:v", "1", str(out)], check=True)


TH_SLOTS = [("오전", "07:30"), ("점심", "12:00"), ("오후", "15:00"), ("저녁", "18:00"), ("밤", "21:00"), ("늦은밤", "23:00")]


def shift_threads(manifest: dict, frm: str) -> int:
    """스레드 글을 한 칸씩 뒤로 미룬다 (사장님 2026-11-01 "스레드는 한개씩 미루자").

    frm 은 '2026-11-01 늦은밤' 처럼 날짜와 칸. 그 칸부터 뒤의 스레드 글이 모두 다음 칸으로 간다.
    번호(id)는 그대로 둔다. 사장님이 /studio 에서 누른 승인 표시가 번호에 붙어 있기 때문이다.
    마지막 글은 다음 날 아침 칸으로 가고, 그 날이 묶음에 없으면 새로 만든다. 옮긴 글 수를 돌려준다.
    """
    d0, s0 = frm.split()
    order = [s for s, _ in TH_SLOTS]
    key0 = (d0, order.index(s0))
    moved = []
    for day in manifest["days"]:
        keep = []
        for it in day["items"]:
            if it["channel"] == "threads" and (day["date"], order.index(it["slot"])) >= key0:
                moved.append((day["date"], order.index(it["slot"]), it))
            else:
                keep.append(it)
        day["items"] = keep
    for date, i, it in moved:
        j = i + 1
        nd = dt.date.fromisoformat(date) + dt.timedelta(days=j // len(TH_SLOTS))
        it["slot"], it["time"] = TH_SLOTS[j % len(TH_SLOTS)]
        day = next((d for d in manifest["days"] if d["date"] == nd.isoformat()), None)
        if day is None:
            day = {"date": nd.isoformat(), "weekday": WEEKDAYS[nd.weekday()], "items": []}
            manifest["days"].append(day)
        day["items"].append(it)
    for day in manifest["days"]:
        day["items"].sort(key=lambda it: it["time"])
    return len(moved)


def move_items(manifest: dict, moves: str) -> int:
    """게시물 하나를 다른 날·칸으로 옮긴다 (사장님 2026-11-01 "내일 3탄 올릴 시간에 ... 못올리는거 그 중에서 괜찮은거 하나로 대체해").

    moves 는 '11-01_점심-threads=2026-11-02 저녁' 처럼 '번호=날짜 칸', 여러 개는 쉼표로. 번호(id)는 그대로라 승인·올림 표시가 남는다.
    그 칸에 있던 글은 지우지 않는다. 이미 올라간 글은 올림 표시가 있어 다시 올라가지 않는다. 옮긴 글 수를 돌려준다.
    """
    slots = dict(TH_SLOTS)
    n = 0
    for mv in filter(None, (x.strip() for x in moves.split(","))):
        iid, where = mv.split("=")
        date, slot = where.split()
        it = None
        for day in manifest["days"]:
            for x in day["items"]:
                if x["id"] == iid:
                    it = x
            if it is not None and it in day["items"]:
                day["items"].remove(it)
                break
        if it is None:
            raise SystemExit(f"옮길 게시물이 없어요: {iid}")
        it["slot"], it["time"] = slot, slots[slot]
        day = next((d for d in manifest["days"] if d["date"] == date), None)
        if day is None:
            nd = dt.date.fromisoformat(date)
            day = {"date": date, "weekday": WEEKDAYS[nd.weekday()], "items": []}
            manifest["days"].append(day)
        day["items"].append(it)
        day["items"].sort(key=lambda x: x["time"])
        n += 1
    return n


SFX = {"instagram-reel": "reel", "facebook-reel": "fbreel", "youtube": "youtube"}


def _with_cta(texts: dict, line: str) -> dict:
    """설명글 끝 팔로우 말을 곳마다 다른 밑에 글로 바꾼다 (사장님 2026-11-01: 유튜브 구독 · 인스타·페북 팔로우)."""
    out = {}
    for k, v in texts.items():
        if k == "제목":
            out[k] = v
            continue
        for old in (T.FOLLOW_AM, T.FOLLOW_AM.replace("팔로우 해 두세요", "구독해 두세요")):
            v = v.replace(old, line)
        if "댓글" in line:   # 인스타: 댓글 부탁이 두 번 나오지 않게 (영상 심사 팔로우 항목 '두 번 조름')
            v = "\n".join(x for x in v.split("\n") if not x.startswith("💬"))
            while "\n\n\n" in v:
                v = v.replace("\n\n\n", "\n\n")
        out[k] = v if line in v else v.replace("\n\n#", f"\n\n{line}\n\n#", 1) if "\n\n#" in v else v + "\n\n" + line
    return out


# 영상 올리는 곳: 인스타 릴스만 (사장님 2026-11-03 "페북은 운영하지 말자 인스타만 해", 유튜브는 계정 없음)
VIDEO_CHANNELS = ("instagram-reel",)


def _videos(R, week: Path, m, tag: str, part: str, slot: str, time: str, seed: int, src: Path | None = None) -> list[dict]:
    """영상 7초 하나를 세 곳에 (사장님 2026-11-01). 가림식은 레퍼런스처럼 화면 밑 글이 곳마다 달라서 영상도 세 개.
    src: 이미 만들어 사장님께 보여 드린 영상 폴더 (video-samples). 주면 다시 만들지 않고 그 파일을 그대로 쓴다."""
    if not R and not src:   # 영상 없이 만들면 영상 게시물은 넣지 않는다 ("영상은 올리지마 확실히 될때까지")
        return []
    cta, mt = S.cta(m), m.texts()
    title = " ".join(m.title).replace("“", "").replace("”", "") if m.title else mt["youtube"]["제목"]
    made: dict[str, tuple[str, str]] = {}
    items = []
    for ch in VIDEO_CHANNELS:
        own = m.fmt in S.ON_SCREEN_CTA
        key = ch if own else "all"
        if key not in made:
            stem = f"{tag}_{part}_{m.key}" + (f"_{SFX[ch]}" if own else "")
            vid, thumb = f"유튜브/{stem}.mp4", f"유튜브/{stem}_표지.jpg"
            if src:
                (week / vid).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src / f"{stem}.mp4", week / vid)
            else:
                R.morning(m, week / vid, seed=seed, cta=cta[ch] if own else "")
                if os.environ.get("TYPECAST_API_KEY"):
                    R.voiceover(week / vid, S.script(m), seed=seed)
            _thumb(week / vid, 2.5, week / thumb)
            made[key] = (vid, thumb)
        vid, thumb = made[key]
        items.append({"id": f"{tag}_{part}-{SFX[ch]}", "channel": ch, "time": time, "slot": slot, "material": m.key,
                      "format": FMT_NAMES[m.fmt], "title": title, "score": 0, "video": vid, "thumb": thumb,
                      "voice": S.script(m), "cta": cta[ch], "texts": _with_cta(mt[ch], cta[ch])})
    return items


def build(start: dt.date, days: int, out: Path, used: set[str] | None = None, video: bool = True, shift: str = "",
          approve_threads: bool = False, move: str = "", approve_videos: bool = False, cards: bool = False) -> dict:
    week = out / start.isoformat()
    (week / "유튜브").mkdir(parents=True, exist_ok=True)
    (week / "인스타").mkdir(parents=True, exist_ok=True)
    manifest = {"week": start.isoformat(), "createdAt": dt.datetime.now(dt.UTC).isoformat(timespec="minutes"),
                "maker": "formula", "days": [], "problems": [], "used": [],
                "trends": {"items": [], "notes": ["공식으로 만든 묶음: 엔진 순위 + 글 재료 창고(banks.json)"]}}
    R = C = None
    if video or cards:
        from .render import Renderer
        C = Renderer(week / "_작업")
        R = C if video else None
    rows = []
    try:
        for i, dd in enumerate(T.plan(start, days, used)):
            day, m, e = dd
            tag = f"{day:%m-%d}"
            entry = {"date": day.isoformat(), "weekday": WEEKDAYS[day.weekday()], "items": []}
            manifest["used"] += [m.key] + [x.key for _, _, x in dd.threads]
            manifest["problems"] += [f"{tag} {p}" for p in problems(m, *[x for _, _, x in dd.threads])]
            # 아침 영상 1개 → 세 채널
            entry["items"] += _videos(R, week, m, tag, "오전", "아침영상", VIDEO_AM, i * 2 + 1)
            # 스레드 글 5개
            for slot, tm, x in dd.threads:
                first = x.pages[0][0] if x.pages and x.pages[0] else x.key
                it = {"id": f"{tag}_{slot}-threads", "channel": "threads", "time": tm, "slot": slot, "material": x.key,
                      "format": STYLE_NAMES[x.style], "title": first, "score": 0, "texts": x.texts()["threads"]}
                if C:
                    # 이 글이 전날 인기 글로 뽑히면 인스타 게시글로 그대로 쓴다 (흰 배경 캡처, formula/pick.py)
                    stem = f"{tag}_{slot}_{x.key}"
                    it["images"] = [f"인스타/{f.name}" for f in C.thread_cards(x, week / "인스타", stem)]
                entry["items"].append(it)
            # 저녁 영상 1개 (아침과 다른 형식) → 인스타·페북 릴스·유튜브 쇼츠 19:00 (사장님 2026-11-01 "영상은 아침 8시, 오후 7시")
            if dd.video2:
                entry["items"] += _videos(R, week, dd.video2, tag, "저녁", "저녁영상", VIDEO_PM, i * 2 + 2)
            # 인스타 게시글(캡처)·페북 글은 묶음에 넣지 않는다. 매일 전날 반응 좋은 스레드 글 2개를 골라 12:30·21:00 에 올린다 (formula/pick.py).
            entry["items"].sort(key=lambda it: it["time"])
            for it in entry["items"]:
                rows.append([f"{day.isoformat()} {it['time']}", CHANNEL_NAMES[it["channel"]], it["format"], it["title"], it["id"]])
            manifest["days"].append(entry)
            print(f"{day} 아침 {m.key} / 스레드 " + ", ".join(x.key for _, _, x in dd.threads))
    finally:
        if C:
            C.close()
    titles = [it["title"] for d in manifest["days"] for it in d["items"] if it["channel"] == "youtube"]
    manifest["daangn"] = {"소식": "\n".join(["이번 주 띠별 운세", ""] + [f"▪ {t}" for t in titles] +
                                         ["", "띠는 태어난 해 하나만 본 것이에요.", "생년월일과 태어난 시간으로 보는 내 운세는 운명서재에서", SITE_URL])}
    shutil.rmtree(week / "_작업", ignore_errors=True)
    if approve_threads:
        # 심사원 50명 심사를 통과한 주만 이 표시를 단다 (CLAUDE.md 제2조항). 표시가 있으면 /studio 승인 없이 시간 맞춰 올라간다.
        n = 0
        for d in manifest["days"]:
            for it in d["items"]:
                if it["channel"] == "threads":
                    it["approved_by"] = "claude"
                    n += 1
        manifest["threads_approved_by"] = "claude"
        print(f"스레드 글 {n}개 클로드 승인 (심사 통과)")
    if approve_videos:
        # 사장님 2026-11-01 "릴스랑 유튜브도 1주치씩 미리": 사장님이 대화방에서 "올려" 한 주만 영상도 클로드가 한 번에 승인한다.
        n = 0
        for d in manifest["days"]:
            for it in d["items"]:
                if it["channel"] in VIDEO_CHANNELS:
                    it["approved_by"] = "claude"
                    n += 1
        manifest["videos_approved_by"] = "claude"
        print(f"영상 {n}개 클로드 승인 (사장님 '올려')")
    if shift:
        print(f"스레드 글 {shift_threads(manifest, shift)}개를 한 칸씩 미뤘어요 ({shift}부터)")
    if move:
        print(f"게시물 {move_items(manifest, move)}개를 옮겼어요 ({move})")
    if shift or move:
        rows = [[f"{d['date']} {it['time']}", CHANNEL_NAMES[it["channel"]], it["format"], it["title"], it["id"]]
                for d in manifest["days"] for it in d["items"]]
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
    ap.add_argument("--no-cards", action="store_true", help="스레드 글 캡처(인스타 게시글용)를 찍지 않는다")
    ap.add_argument("--approve-threads", action="store_true", help="심사 통과한 주: 스레드 글을 클로드가 한 번에 승인")
    ap.add_argument("--approve-videos", action="store_true", help="사장님이 '올려' 한 주: 인스타·페북·유튜브 영상을 클로드가 한 번에 승인")
    ap.add_argument("--shift-threads", default="", help="'2026-11-01 늦은밤' 처럼: 그 칸부터 스레드 글을 한 칸씩 미룬다")
    ap.add_argument("--move", default="", help="'11-01_점심-threads=2026-11-02 저녁' 처럼: 게시물 하나를 다른 날·칸으로 옮긴다 (미루기 뒤에)")
    a = ap.parse_args(argv)
    start = dt.date.fromisoformat(a.start)
    used = set(filter(None, a.used.split(",")))
    from .. import publish
    if a.publish:
        publish.status(start.isoformat(), "running", "만드는 중")
        used |= publish.used_keys(before=start.isoformat())
    try:
        r = build(start, a.days, Path(a.out), used, video=not a.no_video, shift=a.shift_threads, approve_threads=a.approve_threads,
                  move=a.move, approve_videos=a.approve_videos, cards=not a.no_cards)
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
