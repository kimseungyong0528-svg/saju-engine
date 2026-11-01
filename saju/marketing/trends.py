"""그 주에 레퍼런스 계정에서 평소보다 많이 뜬 게시물을 모으고, 우리 재료 순서를 정한다.

- 유튜브: YouTube Data API (YOUTUBE_API_KEY). 레퍼런스 채널의 최근 영상 조회수 ÷ 그 채널 평소 조회수.
- 인스타: 메타 그래프 API 비즈니스 계정 조회 (IG_USER_ID, META_TOKEN). 최근 게시물 좋아요+댓글 ÷ 평소.
- 네이버: 데이터랩 검색어 트렌드 (NAVER_CLIENT_ID, NAVER_CLIENT_SECRET). 지난주 대비 이번 주 검색량.
- 스레드: 공식 API로 남의 계정을 볼 수 없어 지금은 사장님 캡처로 본다.
키가 없는 곳은 건너뛰고 notes에 적는다. 모두 무료 한도 안에서 쓴다.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import statistics
import urllib.parse
import urllib.request
from pathlib import Path

from .content import Post

REFS = json.loads((Path(__file__).parent / "data" / "references.json").read_text(encoding="utf-8"))
UA = {"User-Agent": "unmyeong-studio"}


def _get(url: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _post(url: str, body: dict, headers: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={**UA, "Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _ratio(v: float, avg: float) -> float:
    return round(v / avg, 2) if avg else 0.0


def youtube(key: str, now: dt.datetime) -> list[dict]:
    api = "https://www.googleapis.com/youtube/v3/"
    week_ago = now - dt.timedelta(days=7)
    out = []
    for ch in REFS["youtube"]:
        q = {"part": "contentDetails,snippet", "key": key}
        q |= {"id": ch["id"]} if "id" in ch else {"forHandle": ch["handle"]}
        items = _get(api + "channels?" + urllib.parse.urlencode(q)).get("items", [])
        if not items:
            continue
        uploads = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        pl = _get(api + "playlistItems?" + urllib.parse.urlencode(
            {"part": "contentDetails", "playlistId": uploads, "maxResults": 30, "key": key}))
        ids = [i["contentDetails"]["videoId"] for i in pl.get("items", [])]
        if not ids:
            continue
        vids = _get(api + "videos?" + urllib.parse.urlencode(
            {"part": "snippet,statistics", "id": ",".join(ids), "key": key})).get("items", [])
        views = [int(v["statistics"].get("viewCount", 0)) for v in vids]
        avg = statistics.median(views) if views else 0
        for v in vids:
            at = dt.datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
            if at < week_ago:
                continue
            n = int(v["statistics"].get("viewCount", 0))
            out.append({"source": "유튜브", "account": ch["name"], "title": v["snippet"]["title"], "value": n,
                        "unit": "조회수", "avg": int(avg), "ratio": _ratio(n, avg),
                        "url": f"https://www.youtube.com/watch?v={v['id']}", "at": at.date().isoformat()})
    for term in REFS["youtube_search"]:
        res = _get(api + "search?" + urllib.parse.urlencode(
            {"part": "snippet", "q": term, "type": "video", "order": "viewCount", "regionCode": "KR",
             "relevanceLanguage": "ko", "publishedAfter": week_ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
             "maxResults": 10, "key": key})).get("items", [])
        ids = [i["id"]["videoId"] for i in res]
        if not ids:
            continue
        for v in _get(api + "videos?" + urllib.parse.urlencode(
                {"part": "snippet,statistics", "id": ",".join(ids), "key": key})).get("items", []):
            n = int(v["statistics"].get("viewCount", 0))
            out.append({"source": "유튜브 검색", "account": v["snippet"]["channelTitle"], "title": v["snippet"]["title"],
                        "value": n, "unit": "조회수", "avg": 0, "ratio": 0.0, "query": term,
                        "url": f"https://www.youtube.com/watch?v={v['id']}",
                        "at": v["snippet"]["publishedAt"][:10]})
    return out


def instagram(ig_user: str, token: str, now: dt.datetime) -> list[dict]:
    week_ago = now - dt.timedelta(days=7)
    out = []
    for name in REFS["instagram"]:
        fields = (f"business_discovery.username({name})"
                  "{media.limit(30){caption,like_count,comments_count,timestamp,permalink,media_type}}")
        data = _get(f"https://graph.facebook.com/v21.0/{ig_user}?" + urllib.parse.urlencode(
            {"fields": fields, "access_token": token}))
        media = data.get("business_discovery", {}).get("media", {}).get("data", [])
        scores = [m.get("like_count", 0) + m.get("comments_count", 0) for m in media]
        avg = statistics.median(scores) if scores else 0
        for m, n in zip(media, scores):
            at = dt.datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
            if at < week_ago:
                continue
            out.append({"source": "인스타", "account": name, "title": (m.get("caption") or "")[:120], "value": n,
                        "unit": "좋아요+댓글", "avg": int(avg), "ratio": _ratio(n, avg), "url": m.get("permalink", ""),
                        "at": at.date().isoformat(), "type": m.get("media_type", "")})
    return out


def naver(cid: str, secret: str, now: dt.datetime) -> list[dict]:
    end = now.date() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=13)
    res = _post("https://openapi.naver.com/v1/datalab/search",
                {"startDate": start.isoformat(), "endDate": end.isoformat(), "timeUnit": "date",
                 "keywordGroups": REFS["naver_keywords"]},
                {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": secret})
    out = []
    for r in res.get("results", []):
        vals = [d["ratio"] for d in r.get("data", [])]
        last, prev = sum(vals[-7:]), sum(vals[-14:-7])
        out.append({"source": "네이버 검색", "account": "", "title": r["title"], "value": round(last, 1),
                    "unit": "검색량(상대값)", "avg": round(prev, 1), "ratio": _ratio(last, prev), "url": "", "at": end.isoformat()})
    return out


def collect(env=os.environ, now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    items, notes = [], []
    jobs = [("유튜브", ("YOUTUBE_API_KEY",), youtube),
            ("인스타", ("IG_USER_ID", "META_TOKEN"), instagram),
            ("네이버", ("NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"), naver)]
    for label, keys, fn in jobs:
        vals = [env.get(k, "") for k in keys]
        if not all(vals):
            notes.append(f"{label}: 키가 없어 건너뜀 ({', '.join(keys)})")
            continue
        try:
            got = fn(*vals, now)
            items += got
            notes.append(f"{label}: {len(got)}개 모음")
        except Exception as e:  # 한 곳이 막혀도 나머지는 계속
            notes.append(f"{label}: 가져오기 실패 ({type(e).__name__})")
    notes.append("스레드: 공식 API로 남의 계정을 볼 수 없어 캡처로 확인")
    items.sort(key=lambda x: (x["ratio"], x["value"]), reverse=True)
    return {"fetchedAt": now.isoformat(timespec="minutes"), "items": items, "notes": notes}


def score(p: Post, trends: dict) -> float:
    """우리 재료가 이번 주 뜬 게시물과 얼마나 겹치나. 겹친 게시물의 '평소 대비 배수'를 더한다."""
    total = 0.0
    for it in trends.get("items", []):
        title = it["title"]
        if any(k in title for k in p.keywords):
            total += it["ratio"] or 1.0
    return round(total, 2)


def order(posts: list[Post], trends: dict | None, used: set[str] | frozenset = frozenset()) -> list[tuple[Post, float]]:
    """안 쓴 재료를 먼저, 그 안에서 뜬 점수가 높은 순서로. 점수가 같으면 원래 순서(반응 큰 띠 먼저)."""
    ranked = [(p, score(p, trends or {}), i) for i, p in enumerate(posts)]
    ranked.sort(key=lambda x: (x[0].key in used, -x[1], x[2]))
    return [(p, s) for p, s, _ in ranked]
