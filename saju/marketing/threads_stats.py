"""스레드에 올라간 글마다 조회수·반응을 읽어 형식(사주장인·도화도르·살구)별로 비교한다 (사장님 2026-11-05 "어떤 폼이 좋고 낮은지").

    python -m saju.marketing.threads_stats --since 2026-11-01

글의 형식은 관리 사이트 묶음(올림 기록의 주소)에서 찾는다. 읽기만 하고 아무것도 올리지 않는다.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json

from . import meta, publish

METRICS = ("views", "likes", "replies", "reposts", "quotes", "shares")
KST = dt.timezone(dt.timedelta(hours=9))


def formats(since: dt.date, until: dt.date) -> dict[str, dict]:
    """올라간 글 주소 → 묶음 속 칸 (형식·시간·첫 줄)."""
    out = {}
    d = since
    while d <= until:
        try:
            plan = publish._call("GET", f"/api/internal/studio/today?date={d.isoformat()}")
        except Exception as e:  # noqa: BLE001
            print(f"[{d}] 묶음을 못 읽음: {e}")
            plan = {}
        posted = plan.get("posted", {})
        for it in plan.get("items", []):
            p = posted.get(it["id"], {})
            if it.get("channel") == "threads" and p.get("ok") and p.get("url"):
                out[p["url"].rstrip("/")] = {"format": it.get("format", "?"), "slot": it.get("time", ""), "title": it.get("title", "")}
        d += dt.timedelta(days=1)
    return out


def comments(tok: str, word: str) -> int:
    """첫 줄에 word 가 든 글마다 달린 댓글(대댓글 포함)을 모두 보여 준다. 읽기만 한다."""
    url = f"{meta.T}/me/threads?fields=id,text,timestamp,permalink,is_reply&limit=100&access_token={tok}"
    posts = []
    while url and len(posts) < 300:
        r = meta._http("GET", url)
        posts += r.get("data", [])
        url = r.get("paging", {}).get("next")
    hit = [p for p in posts if not p.get("is_reply") and word in (p.get("text") or "").split("\n")[0]]
    for p in hit:
        print(f"\n=== {p['timestamp']} {p.get('permalink')} ===\n{(p.get('text') or '')[:80]}")
        u = f"{meta.T}/{p['id']}/conversation?fields=id,text,username,timestamp,replied_to&reverse=false&limit=100&access_token={tok}"
        n = 0
        while u:
            r = meta._http("GET", u)
            for c in r.get("data", []):
                n += 1
                print(f"- [{c.get('timestamp', '')}] @{c.get('username', '?')} (답글 대상 {(c.get('replied_to') or {}).get('id', '')}): {c.get('text', '')}")
            u = r.get("paging", {}).get("next")
        print(f"댓글 {n}개")
    if not hit:
        print("그런 글을 못 찾음")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-11-01")
    ap.add_argument("--comments", default="", help="이 말이 첫 줄에 든 글의 댓글을 모두 읽는다 (예 9탄)")
    a = ap.parse_args()
    since = dt.date.fromisoformat(a.since)
    tok = meta.threads_token()
    if a.comments:
        return comments(tok, a.comments)
    fm = formats(since - dt.timedelta(days=1), dt.datetime.now(KST).date())
    posts, url = [], f"{meta.T}/me/threads?fields=id,text,timestamp,permalink,is_reply&limit=100&access_token={tok}"
    while url and len(posts) < 300:
        r = meta._http("GET", url)
        posts += r.get("data", [])
        url = r.get("paging", {}).get("next")
    rows = []
    now = dt.datetime.now(dt.UTC)
    for p in posts:
        if p.get("is_reply"):
            continue
        t = dt.datetime.fromisoformat(p["timestamp"].replace("+0000", "+00:00"))
        if t.astimezone(KST).date() < since:
            continue
        try:
            data = meta._http("GET", f"{meta.T}/{p['id']}/insights?metric={','.join(METRICS)}&access_token={tok}").get("data", [])
        except Exception as e:  # noqa: BLE001
            print(f"인사이트 실패 {p['id']}: {e}")
            continue
        m = {d["name"]: int((d.get("values") or [{}])[0].get("value", d.get("total_value", {}).get("value", 0)) or 0) for d in data}
        info = fm.get((p.get("permalink") or "").rstrip("/"), {})
        rows.append({"at": t.astimezone(KST).strftime("%m-%d %H:%M"), "hours": round((now - t).total_seconds() / 3600, 1),
                     "format": info.get("format", "모름"), "first": (p.get("text") or "").split("\n")[0][:40], **m})
    rows.sort(key=lambda r: r["at"])
    print("\n=== 글마다 ===")
    for r in rows:
        print(f"{r['at']} | {r['format']:6} | 조회 {r.get('views', 0):6} | 좋아요 {r.get('likes', 0):3} | 댓글 {r.get('replies', 0):3} | "
              f"리포스트 {r.get('reposts', 0):2} | 공유 {r.get('shares', 0):2} | {r['hours']}h | {r['first']}")
    print("\n=== 형식별 (평균) ===")
    g = collections.defaultdict(list)
    for r in rows:
        g[r["format"]].append(r)
    for f, rs in sorted(g.items(), key=lambda x: -sum(r.get("views", 0) for r in x[1]) / len(x[1])):
        n = len(rs)
        avg = lambda k: sum(r.get(k, 0) for r in rs) / n  # noqa: E731
        print(f"{f:6} 글 {n:2}개 | 평균 조회 {avg('views'):7.0f} | 중간값 조회 {sorted(r.get('views', 0) for r in rs)[n // 2]:6} | "
              f"평균 좋아요 {avg('likes'):5.1f} | 평균 댓글 {avg('replies'):4.1f} | 평균 공유 {avg('shares'):4.1f}")
    print("\n=== 시간대별 (평균 조회) ===")
    h = collections.defaultdict(list)
    for r in rows:
        h[r["at"][6:]].append(r.get("views", 0))
    for k in sorted(h):
        print(f"{k} 글 {len(h[k])}개 평균 조회 {sum(h[k]) / len(h[k]):.0f}")
    print("\nJSON " + json.dumps(rows, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
