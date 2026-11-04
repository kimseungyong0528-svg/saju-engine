"""깃허브 Actions에서 주문 하나를 처리한다.

예) SITE_URL=https://unmyeong-saju.com WORKER_SECRET=... ANTHROPIC_API_KEY=... python -m saju.order 주문번호
    SAJU_DRAFT=1 이면 AI 없이 초안 글로 만든다(시험용, API 비용 없음).
기록(로그)에는 이름·생일 같은 개인정보를 남기지 않는다.
"""

import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from . import blocking, make_pdf
from ..report.verify import summary


def _call(method: str, path: str, body: bytes | None = None, content_type: str = "application/json"):
    url = os.environ.get("SITE_URL", "https://unmyeong-saju.com").rstrip("/") + path
    req = urllib.request.Request(url, data=body, method=method, headers={
        "X-Worker-Secret": os.environ["WORKER_SECRET"], "Content-Type": content_type, "User-Agent": "unmyeong-worker"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")


def status(order_id: str, value: str, note: str = "") -> None:
    try:
        _call("POST", f"/api/internal/orders/{order_id}/status", json.dumps({"status": value, "note": note}).encode())
    except urllib.error.URLError as e:
        print(f"상태 보내기 실패: {value} {e}")


def writer():
    from ..report import ClaudeWriter, DraftWriter
    if os.environ.get("SAJU_DRAFT") == "1" or not os.environ.get("ANTHROPIC_API_KEY"):
        return DraftWriter()
    return ClaudeWriter()


def usage_line(usage: list[dict] | None) -> str:
    """글쓰기 AI가 쓴 토큰을 모델별로 더한다(입력·출력·캐시 읽기·캐시 쓰기). 재무가 1권당 원가를 실측하는 데 쓴다."""
    if not usage:
        return "없음"
    tot: dict[str, dict[str, int]] = {}
    for u in usage:
        t = tot.setdefault(u.get("model", "?"), {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "calls": 0})
        for k in ("input", "output", "cache_read", "cache_write"):
            t[k] += int(u.get(k) or 0)
        t["calls"] += 1
    return " / ".join(f"{m} 호출 {t['calls']} 입력 {t['input']} 출력 {t['output']} 캐시읽기 {t['cache_read']} 캐시쓰기 {t['cache_write']}"
                      for m, t in tot.items())


TRIES = 4  # 검사를 통과할 때까지 처음부터 다시 쓴다(한 번에 AI 비용 약 500원). 4번 다 막히면 보류하고 사장님께 알린다.


def build(job: dict) -> tuple[bytes | None, str]:
    """PDF를 만든다. 글 검사에서 막히거나 작성이 실패하면 통과할 때까지 다시 만든다(최대 TRIES번).

    사장님 2026-11-04: "보내질 때까지 계속 검수하고 스스로 고치고 하게 해".
    """
    last = ""
    for attempt in range(1, TRIES + 1):
        try:
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / "report.pdf"
                w = writer()
                r = make_pdf(job, out, w)
                bad = blocking(r["issues"])
                print(f"{attempt}번째: {job['productId']} {r['pages']}쪽, 검사 문제 {len(r['issues'])}곳(막는 문제 {len(bad)}곳), 글 {type(w).__name__}")
                print(f"{attempt}번째 남은 문제 종류: {summary(r['issues'])}")  # 종류별 개수만(개인정보 없음), 품질검수 표본용
                print(f"{attempt}번째 AI 사용량: {usage_line(getattr(w, 'usage', None))}")  # 모델별 토큰 합(재무 원가 실측용, 개인정보 없음)
                if not bad:
                    return out.read_bytes(), ""
                # 개인정보 없이 어떤 검사에 막혔는지만 남긴다
                last = "글 검사: " + ", ".join(sorted({i['kind'] for i in bad}))
                print(f"{attempt}번째 막힘 → {last}")
        except Exception as e:  # 개인정보가 섞일 수 있는 내용은 남기지 않고 종류만 남긴다
            last = f"PDF 작성 실패: {type(e).__name__}"
            print(f"{attempt}번째 작성 실패: {type(e).__name__}")
        if attempt < TRIES:
            status(job["orderId"], "retry", last)
    return None, last


def run(order_id: str) -> int:
    job = _call("GET", f"/api/internal/orders/{order_id}")
    if job["status"] not in ("queued", "processing", "retry", "held"):
        print(f"처리할 상태가 아님: {job['status']}")
        return 0
    status(order_id, "processing")
    pdf, problem = build(job)
    if pdf is None:
        status(order_id, "held", problem)
        return 1
    for attempt in (1, 2, 3):  # 보내기만 다시 한다(글은 다시 쓰지 않음)
        try:
            _call("POST", f"/api/internal/orders/{order_id}/result", pdf, "application/pdf")
            print("PDF 보냄, 이메일 발송 요청됨")
            return 0
        except urllib.error.HTTPError as e:
            print(f"PDF 보내기 실패: HTTP {e.code}")
            if e.code < 500:
                break
        except urllib.error.URLError as e:
            print(f"PDF 보내기 실패: {e.reason}")
        time.sleep(10 * attempt)
    status(order_id, "held", "PDF 보내기 실패")
    return 1


if __name__ == "__main__":
    sys.exit(run(sys.argv[1]))
