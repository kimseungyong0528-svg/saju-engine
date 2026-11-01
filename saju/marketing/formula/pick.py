"""전날 반응 좋은 스레드 글 2개를 인스타 게시글(흰 배경 캡처 여러 장)과 페북 글로 올린다 (사장님 2026-11-01).

    python -m saju.marketing.meta --slot 점심글   # 12:30, 어제 1등
    python -m saju.marketing.meta --slot 밤글     # 21:00, 어제 2등 (점심에 올린 글은 빼고 고른다)

고르는 기준 (사장님 2026-11-01 "어제 반응 좋은 글"): 어제 올라간 스레드 글의 좋아요 + 댓글 + 리포스트 + 인용 수.
스레드 공식 API 인사이트로 읽는다. 못 읽으면 어제 사주장인식 글을 시간 순으로 고른다.
캡처 사진은 묶음을 만들 때 스레드 글마다 미리 찍어 둔다(formula/__main__.py, item["images"]).
올린 결과는 어제 묶음의 올림 기록에 '{오늘}_pick-{재료}-cards' / '-fbpost' 로 남겨서 같은 날 두 번 고르지 않는다.

SNS_PICK=on (GitHub 변수) 이 아니면 아무것도 올리지 않는다. 사장님이 견본을 보고 "올려" 한 뒤에 켠다.
"""

from __future__ import annotations

import datetime as dt
import json
import os

from .. import meta, publish

JANGIN = "사주장인식"
IG_CAPTION_MAX = 2200
METRICS = ("likes", "replies", "reposts", "quotes")


def body(it: dict) -> str:
    """스레드 본글과 이어 쓴 댓글을 한 글로 붙인다 (페북 글·인스타 설명)."""
    return "\n\n".join(t.strip() for t in it["texts"].values())


def candidates(plan: dict) -> list[dict]:
    """어제 실제로 올라간 스레드 글 중 캡처 사진이 있는 것."""
    posted = plan.get("posted", {})
    out = []
    for it in plan.get("items", []):
        p = posted.get(it["id"], {})
        if it["channel"] == "threads" and p.get("ok") and it.get("images"):
            out.append({**it, "url": p.get("url", "")})
    return out


def scores(items: list[dict], tok: str) -> dict[str, int] | None:
    """글마다 좋아요+댓글+리포스트+인용. 인사이트 권한이 없거나 실패하면 None."""
    try:
        mine = meta._http("GET", f"{meta.T}/me/threads?fields=id,permalink&limit=100&access_token={tok}").get("data", [])
        ids = {m.get("permalink", "").rstrip("/"): m["id"] for m in mine}
        out = {}
        for it in items:
            mid = ids.get(it["url"].rstrip("/"))
            if not mid:
                continue
            data = meta._http("GET", f"{meta.T}/{mid}/insights?metric={','.join(METRICS)}&access_token={tok}").get("data", [])
            out[it["id"]] = sum(int((d.get("values") or [{}])[0].get("value", 0)) for d in data if d.get("name") in METRICS)
        return out if out else None
    except Exception as e:  # noqa: BLE001 - 못 읽으면 사주장인식으로 고른다
        print(f"[고르기] 스레드 반응 수를 못 읽었어요 (사주장인식으로 고름): {e}")
        return None


def rank(items: list[dict], sc: dict[str, int] | None) -> list[dict]:
    if sc is None:
        return sorted(items, key=lambda it: (it.get("format") != JANGIN, it["time"]))
    return sorted(items, key=lambda it: (-sc.get(it["id"], -1), it.get("format") != JANGIN, it["time"]))


def run(k: int, date: str, dry: bool = False, tok: str | None = None) -> int:
    if os.environ.get("SNS_PICK") != "on" and not dry:
        print("인스타 게시글·페북 글 자동 올리기는 아직 꺼져 있어요 (GitHub 변수 SNS_PICK=on 이면 켜짐)")
        return 0
    yday = (dt.date.fromisoformat(date) - dt.timedelta(days=1)).isoformat()
    plan = publish._call("GET", f"/api/internal/studio/today?date={yday}")
    if not plan.get("week"):
        print(f"{yday} 스레드 묶음이 없어요")
        return 0
    week, posted = plan["week"], plan.get("posted", {})
    done = {pid.split("_pick-", 1)[1].rsplit("-", 1)[0] for pid, p in posted.items()
            if pid.startswith(f"{date}_pick-") and p.get("ok")}
    items = [it for it in candidates(plan) if it["material"] not in done]
    if not items:
        print(f"{yday} 에 올라간 스레드 글 중 고를 것이 없어요")
        return 0
    sc = scores(items, tok or meta.threads_token())
    best = rank(items, sc)[0]
    print(f"{'1' if k == 0 else '2'}번째 고른 글: {best['id']} ({best.get('format')}, 반응 {sc.get(best['id']) if sc else '못 읽음'})")
    text = body(best)
    fails = 0
    for ch, sfx in (("instagram-cards", "cards"), ("facebook-post", "fbpost")):
        pid = f"{date}_pick-{best['material']}-{sfx}"
        if posted.get(pid, {}).get("ok"):
            print(f"건너뜀 (이미 올림): {pid}")
            continue
        if dry:
            print(f"올릴 것: {pid} 사진 {len(best['images'])}장" if ch == "instagram-cards" else f"올릴 것: {pid} 글 {len(text)}자")
            continue
        it = {"id": pid, "images": best["images"], "texts": {"캡션": text[:IG_CAPTION_MAX], "본문": text}}
        try:
            url = meta.POSTERS[ch](week, it)
            result = {"ok": True, "url": url}
            print(f"올림: {pid} → {url}")
        except Exception as e:  # noqa: BLE001 - 인스타가 실패해도 페북은 올린다
            fails += 1
            result = {"ok": False, "error": str(e)[:300]}
            print(f"실패: {pid} → {e}")
        publish._call("POST", f"/api/internal/studio/{week}/posted", json.dumps({"id": pid, **result}, ensure_ascii=False).encode())
    return 1 if fails else 0
