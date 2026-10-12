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


def build(job: dict) -> tuple[bytes | None, str]:
    """PDF를 만든다. 실패하면 한 번만 다시 만든다(다시 만들면 API 비용이 또 든다)."""
    last = ""
    for attempt in (1, 2):
        try:
            with tempfile.TemporaryDirectory() as d:
                out = Path(d) / "report.pdf"
                w = writer()
                r = make_pdf(job, out, w)
                bad = blocking(r["issues"])
                print(f"{job['productId']}: {r['pages']}쪽, 검사 문제 {len(r['issues'])}곳(막는 문제 {len(bad)}곳), 글 {type(w).__name__}")
                if bad:
                    return None, "글 검사: " + ", ".join(sorted({i['kind'] for i in bad}))
                return out.read_bytes(), ""
        except Exception as e:  # 개인정보가 섞일 수 있는 내용은 남기지 않고 종류만 남긴다
            last = type(e).__name__
            print(f"{attempt}번째 작성 실패: {last}")
            if attempt == 1:
                status(job["orderId"], "retry", last)
    return None, f"PDF 작성 실패: {last}"


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
