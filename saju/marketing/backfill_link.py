"""이미 올라간 스레드 글 중 사이트 링크가 없는 글에 링크 줄을 내 댓글로 달아 둔다 (사장님 2026-11-02 "여태까지 안붙인건 넣어놔").

    python -m saju.marketing.backfill_link          # 목록만 보기
    python -m saju.marketing.backfill_link --go     # 실제로 달기

글마다 내가 단 마지막 댓글(없으면 본글) 아래에 meta.FOLLOW_LINK 한 줄을 단다.
이미 그 글 줄기 어디에든 unmyeong-saju.com 이 있으면 건너뛴다. 스레드는 API로 글 고치기가 안 돼서 새 댓글로 단다.
"""

from __future__ import annotations

import argparse
import time

from . import meta

MARK = "unmyeong-saju.com"


def roots(tok: str) -> list[dict]:
    out, url = [], f"{meta.T}/me/threads?fields=id,text,timestamp,permalink,username,is_reply&limit=100&access_token={tok}"
    while url and len(out) < 300:
        r = meta._http("GET", url)
        out += r.get("data", [])
        url = r.get("paging", {}).get("next")
    return [p for p in out if not p.get("is_reply")]


def mine_in_thread(root: dict, tok: str) -> list[dict]:
    r = meta._http("GET", f"{meta.T}/{root['id']}/conversation?fields=id,text,timestamp,username&reverse=false&access_token={tok}")
    me = root.get("username")
    return [c for c in r.get("data", []) if c.get("username") == me]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()
    tok = meta.threads_token()
    todo = []
    for p in sorted(roots(tok), key=lambda x: x.get("timestamp", "")):
        mine = mine_in_thread(p, tok)
        texts = [p.get("text") or ""] + [c.get("text") or "" for c in mine]
        first = (p.get("text") or "").split("\n")[0][:40]
        if any(MARK in t for t in texts):
            print(f"이미 있음: {p.get('timestamp')} {first}")
            continue
        last = sorted(mine, key=lambda c: c.get("timestamp", ""))[-1] if mine else p
        todo.append((p, last, first))
        print(f"달 곳: {p.get('timestamp')} {first} → 댓글 {len(mine)}개 중 마지막 아래")
    print(f"모두 {len(todo)}개")
    if not a.go:
        return 0
    bad = 0
    for p, last, first in todo:
        try:
            meta._th_post(meta.FOLLOW_LINK, tok, last["id"])
            print(f"달았음: {first}")
        except meta.MetaError as e:
            bad += 1
            print(f"실패: {first} — {e}")
        time.sleep(4)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
