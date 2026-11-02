"""승인한 게시물을 인스타·페이스북·스레드에 올린다 (메타 공식 API, 무료).

    python -m saju.marketing.meta --slot 오전        # 오늘 오전 게시물 중 승인한 것만 올린다
                                                   # 시간대: 오전 07:30 · 점심 12:00 · 오후 15:00 · 저녁 18:00 · 밤 21:00 · 늦은밤 23:00
                                                   # 영상: 아침영상 08:00 · 저녁영상 19:00, 인스타 게시글·페북 글: 점심글 12:30 · 밤글 21:00
    python -m saju.marketing.meta --slot 저녁 --dry   # 올리지 않고 무엇을 올릴지만 보여 준다

순서: 관리 사이트(/studio)에서 오늘 게시물과 승인 표시를 받는다 → 채널별로 올린다 → 결과(주소·실패 이유)를 사이트에 남긴다.
한 채널이 실패해도 나머지는 올린다. 이미 올라간 것은 다시 올리지 않는다.
영상·사진은 관리 사이트의 서명된 주소로 메타가 직접 가져간다.

환경 변수: IG_ACCESS_TOKEN, FB_PAGE_TOKEN, THREADS_TOKEN (GitHub 비밀), SITE_URL, WORKER_SECRET.
SNS_SITE_LINK=on 이 아니면 글에서 사이트 주소 줄을 뺀다 (토스 정식 결제 전에는 시험 결제로 리포트를 받아 가지 못하게).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from . import publish
from .content import SITE_URL

G = "https://graph.facebook.com/v23.0"
T = "https://graph.threads.net/v1.0"
IG_USER_ID = os.environ.get("IG_USER_ID") or "17841476113870391"       # unmyeong_saju.kr
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") or "1359319530606113"        # 금월선녀 - 운명서재 사주·운세
AUTO = ("instagram-reel", "instagram-cards", "facebook-reel", "facebook-post", "threads")
KST = dt.timezone(dt.timedelta(hours=9))
# 스레드 6칸(formula.text.THREAD_SLOTS 와 같은 시간대) + 영상 2칸 + 인스타 게시글·페북 글 2칸 (사장님 2026-11-01)
SLOTS = ["오전", "아침영상", "점심", "점심글", "오후", "저녁", "저녁영상", "밤", "밤글", "늦은밤"]
SLOT_TIME = {"오전": "07:30", "아침영상": "08:00", "점심": "12:00", "점심글": "12:30", "오후": "15:00", "저녁": "18:00",
             "저녁영상": "19:00", "밤": "21:00", "밤글": "21:00", "늦은밤": "23:00"}
PICK_SLOTS = {"점심글": 0, "밤글": 1}   # 전날 반응 1등은 12:30, 2등은 21:00 (formula/pick.py)
LATE_MIN = 60   # 예약 실행이 이보다 늦게 시작하면 올리지 않는다
THREAD_GAP_MIN = 60   # 스레드 글은 이 시간 안에 두 개 올리지 않는다 (사장님 2026-11-02 "스레드 두개 한번에올리지마")


def scheduled_date(slot: str, now: dt.datetime) -> tuple[str, int]:
    """예약 실행이 몇 시간씩 늦게 시작해도 날짜를 잘못 잡지 않게 한다 (2026-11-01 사고).

    GitHub 예약 실행이 6시간 40분 늦게(한국 00:28) 시작해서 '오늘'이 다음 날로 넘어갔고,
    다음 날 18:00 글(3탄)이 2탄보다 먼저 올라갔다. 그래서 날짜는 지금 시각이 아니라
    '그 칸 시각이 가장 최근에 지난 날'로 잡고, 몇 분 늦었는지 같이 돌려준다."""
    hh, mm = map(int, SLOT_TIME[slot].split(":"))
    now = now.astimezone(KST)
    at = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if at - now > dt.timedelta(minutes=30):   # 칸 시각보다 30분 넘게 이르면 어제 칸이다
        at -= dt.timedelta(days=1)
    return at.date().isoformat(), int((now - at).total_seconds() // 60)
REFRESH_DAYS = 7          # 스레드 열쇠는 60일짜리라 일주일마다 새것으로 바꿔 둔다


class MetaError(Exception):
    pass


def _http(method: str, url: str, data: dict | None = None, headers: dict | None = None, timeout: int = 120) -> dict:
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers={"User-Agent": "unmyeong-sns", **(headers or {})})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")[:400]
            if e.code >= 500 and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            try:
                msg = json.loads(text).get("error", {})
                text = msg.get("error_user_msg") or msg.get("message") or text
            except (ValueError, AttributeError):
                pass
            raise MetaError(f"{e.code}: {text}") from None
        except urllib.error.URLError as e:
            if attempt == 2:
                raise MetaError(f"연결 실패: {e.reason}") from None
            time.sleep(5 * (attempt + 1))
    return {}


def media_url(week: str, path: str) -> str:
    """메타가 영상·사진을 가져갈 주소. WORKER_SECRET 로 서명해서 아무나 파일을 못 보게 한다."""
    sig = hmac.new(os.environ["WORKER_SECRET"].encode(), f"pub:{week}/{path}".encode(), hashlib.sha256).hexdigest()
    base = os.environ.get("SITE_URL", SITE_URL).rstrip("/")
    return f"{base}/api/studio/pub/{week}?path={urllib.parse.quote(path)}&sig={sig}"


def clean(text: str) -> str:
    """토스 정식 결제 전에는 사이트 주소가 든 줄을 뺀다."""
    if os.environ.get("SNS_SITE_LINK") == "on":
        return text
    lines = [ln for ln in text.split("\n") if "unmyeong-saju.com" not in ln]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


# ── 인스타 ──
def _ig_wait(cid: str, tok: str, tries: int = 40) -> None:
    for _ in range(tries):
        st = _http("GET", f"{G}/{cid}?fields=status_code,status&access_token={tok}")
        if st.get("status_code") == "FINISHED":
            return
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise MetaError(f"인스타 처리 실패: {st.get('status', '')}")
        time.sleep(10)
    raise MetaError("인스타가 영상 처리를 끝내지 못했어요 (7분 넘음)")


def _ig_publish(cid: str, tok: str) -> str:
    mid = _http("POST", f"{G}/{IG_USER_ID}/media_publish", {"creation_id": cid, "access_token": tok})["id"]
    return _http("GET", f"{G}/{mid}?fields=permalink&access_token={tok}").get("permalink", "")


def ig_reel(week: str, it: dict) -> str:
    tok = os.environ["IG_ACCESS_TOKEN"]
    cid = _http("POST", f"{G}/{IG_USER_ID}/media", {
        "media_type": "REELS", "video_url": media_url(week, it["video"]), "caption": clean(it["texts"]["캡션"]),
        "share_to_feed": "true", "access_token": tok})["id"]
    _ig_wait(cid, tok)
    return _ig_publish(cid, tok)


def ig_cards(week: str, it: dict) -> str:
    tok = os.environ["IG_ACCESS_TOKEN"]
    kids = []
    for p in it["images"][:10]:
        kids.append(_http("POST", f"{G}/{IG_USER_ID}/media", {
            "image_url": media_url(week, p), "is_carousel_item": "true", "access_token": tok})["id"])
    for k in kids:
        _ig_wait(k, tok, tries=12)
    cid = _http("POST", f"{G}/{IG_USER_ID}/media", {
        "media_type": "CAROUSEL", "children": ",".join(kids), "caption": clean(it["texts"]["캡션"]), "access_token": tok})["id"]
    _ig_wait(cid, tok, tries=12)
    return _ig_publish(cid, tok)


# ── 페이스북 페이지 릴스 ──
def _page_token() -> str:
    for pg in _http("GET", f"{G}/me/accounts?fields=id,access_token&access_token={os.environ['FB_PAGE_TOKEN']}").get("data", []):
        if pg["id"] == FB_PAGE_ID:
            return pg["access_token"]
    raise MetaError("페이스북 페이지 열쇠를 찾지 못했어요")


def fb_reel(week: str, it: dict) -> str:
    tok = _page_token()
    start = _http("POST", f"{G}/{FB_PAGE_ID}/video_reels", {"upload_phase": "start", "access_token": tok})
    vid = start["video_id"]
    up = start.get("upload_url") or f"https://rupload.facebook.com/video-upload/v23.0/{vid}"
    _http("POST", up, None, {"Authorization": f"OAuth {tok}", "file_url": media_url(week, it["video"])}, timeout=300)
    _http("POST", f"{G}/{FB_PAGE_ID}/video_reels", {
        "upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
        "description": clean(it["texts"]["캡션"]), "access_token": tok})
    return f"https://www.facebook.com/reel/{vid}"


def fb_post(week: str, it: dict) -> str:
    """페이스북 페이지에 스레드 긴 글을 그대로 올린다 (사장님 2026-11-01 "페북도 스레드에 있는 긴 글 발행")."""
    tok = _page_token()
    r = _http("POST", f"{G}/{FB_PAGE_ID}/feed", {"message": clean(it["texts"]["본문"]), "access_token": tok})
    return f"https://www.facebook.com/{r['id']}"


# ── 스레드 ──
def threads_token() -> str:
    """사이트에 저장해 둔 새 열쇠가 있으면 그것을, 없으면 GitHub 비밀을 쓴다. 일주일 지나면 새 열쇠로 바꾼다."""
    saved = {}
    try:
        saved = publish._call("GET", "/api/internal/studio/meta/threads-token")
    except Exception as e:  # noqa: BLE001 - 저장된 열쇠가 없어도 비밀 열쇠로 올린다
        print(f"[스레드] 저장된 열쇠 받기 실패: {e}")
    tok = saved.get("token") or os.environ["THREADS_TOKEN"]
    at = saved.get("refreshedAt")
    if not at or dt.datetime.now(dt.UTC) - dt.datetime.fromisoformat(at) > dt.timedelta(days=REFRESH_DAYS):
        try:
            new = _http("GET", f"{T}/refresh_access_token?grant_type=th_refresh_token&access_token={tok}")["access_token"]
            publish._call("POST", "/api/internal/studio/meta/threads-token",
                          json.dumps({"token": new, "refreshedAt": dt.datetime.now(dt.UTC).isoformat()}).encode())
            tok = new
            print("[스레드] 열쇠를 새것으로 바꿨어요")
        except Exception as e:  # noqa: BLE001
            print(f"[스레드] 열쇠 바꾸기 실패 (지금 열쇠로 계속): {e}")
    return tok


def _th_post(text: str, tok: str, reply_to: str = "") -> str:
    data = {"media_type": "TEXT", "text": text, "access_token": tok}
    if reply_to:
        data["reply_to_id"] = reply_to
    cid = _http("POST", f"{T}/me/threads", data)["id"]
    time.sleep(5)
    return _http("POST", f"{T}/me/threads_publish", {"creation_id": cid, "access_token": tok})["id"]


FOLLOW_LINK = "운명서재에서 내 사주 보기 👉 https://unmyeong-saju.com"


def with_link(parts: list[str]) -> list[str]:
    """토스 정식 결제가 연결되면(SNS_SITE_LINK=on) 마지막 장 팔로우 말 뒤에 사이트 주소 한 줄을 붙인다 (사장님 2026-11-01)."""
    if os.environ.get("SNS_SITE_LINK") != "on" or not parts or "unmyeong-saju.com" in parts[-1]:
        return parts
    return parts[:-1] + [parts[-1].rstrip() + "\n" + FOLLOW_LINK]


def threads(week: str, it: dict) -> str:
    tok = threads_token()
    parts = with_link([clean(t) for t in it["texts"].values()])
    first = prev = _th_post(parts[0], tok)
    for t in parts[1:]:
        time.sleep(3)
        prev = _th_post(t, tok, prev)
    return _http("GET", f"{T}/{first}?fields=permalink&access_token={tok}").get("permalink", "")


POSTERS = {"instagram-reel": ig_reel, "instagram-cards": ig_cards, "facebook-reel": fb_reel, "facebook-post": fb_post, "threads": threads}


def _thread_gap(plan: dict, posted: dict, now: dt.datetime | None = None) -> int | None:
    """THREAD_GAP_MIN 안에 올라간 스레드 글이 있으면 몇 분 전인지 돌려준다."""
    now = now or dt.datetime.now(dt.timezone.utc)
    ids = {it["id"] for it in plan.get("items", []) if it["channel"] == "threads"}
    for pid, p in posted.items():
        if pid in ids and p.get("ok") and p.get("at"):
            ago = (now - dt.datetime.fromisoformat(p["at"].replace("Z", "+00:00"))).total_seconds() / 60
            if 0 <= ago < THREAD_GAP_MIN:
                return int(ago)
    return None


def run(slot: str, date: str, dry: bool = False) -> int:
    plan = publish._call("GET", f"/api/internal/studio/today?date={date}")
    if slot in PICK_SLOTS and not any(it["slot"] == slot for it in plan.get("items", [])):
        # 사장님이 고른 글을 넣어 둔 날(formula/today_videos.py --picks)은 그 글을, 아니면 전날 인기 글을 고른다
        from .formula import pick
        return pick.run(PICK_SLOTS[slot], date, dry)
    if not plan.get("week"):
        print(f"{date} 게시물 묶음이 없어요")
        return 0
    week, approved, posted = plan["week"], plan.get("approved", {}), plan.get("posted", {})
    fails = 0
    for it in plan["items"]:
        if it["slot"] != slot or it["channel"] not in AUTO:
            continue
        # 스레드는 클로드가 심사원 50명 심사(CLAUDE.md 제2조항)를 마친 주를 한 번에 승인한다 (사장님 2026-11-01 "스레드는 승인 없이 한 번에 다 일주일치 클로드에서 승인")
        if not approved.get(it["id"]) and it.get("approved_by") != "claude":
            print(f"건너뜀 (승인 안 됨): {it['id']}")
            continue
        if posted.get(it["id"], {}).get("ok"):
            print(f"건너뜀 (이미 올림): {it['id']}")
            continue
        if it["channel"] == "threads" and (gap := _thread_gap(plan, posted)) is not None:
            print(f"건너뜀 (스레드 글이 {gap}분 전에 올라가서, 한 번에 두 개 안 올림): {it['id']}")
            continue
        if dry:
            print(f"올릴 것: {it['id']} {it['title']}")
            continue
        try:
            url = POSTERS[it["channel"]](week, it)
            result = {"ok": True, "url": url}
            print(f"올림: {it['id']} → {url}")
        except Exception as e:  # noqa: BLE001 - 한 채널이 실패해도 나머지는 올린다
            fails += 1
            result = {"ok": False, "error": str(e)[:300]}
            print(f"실패: {it['id']} → {e}")
        publish._call("POST", f"/api/internal/studio/{week}/posted",
                      json.dumps({"id": it["id"], **result}, ensure_ascii=False).encode())
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="승인한 게시물을 인스타·페이스북·스레드에 올린다")
    ap.add_argument("--slot", choices=SLOTS, required=True)
    ap.add_argument("--date", default="", help="날짜 (기본: 한국 시각 오늘)")
    ap.add_argument("--dry", action="store_true", help="올리지 않고 목록만 본다")
    ap.add_argument("--scheduled", action="store_true", help="예약 실행: 날짜를 칸 시각으로 잡고, 너무 늦게 시작했으면 올리지 않는다")
    a = ap.parse_args(argv)
    if a.date:
        return run(a.slot, a.date, a.dry)
    date, late = scheduled_date(a.slot, dt.datetime.now(KST))
    if a.scheduled and late > LATE_MIN:
        print(f"{date} {a.slot} 칸 예약 실행이 {late}분 늦게 시작해서 올리지 않았어요 (순서가 꼬이지 않게)")
        return 0
    return run(a.slot, date, a.dry)


if __name__ == "__main__":
    raise SystemExit(main())
