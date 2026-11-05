"""주문 처리: 글 검사에 막히면 통과할 때까지 다시 쓴다(사장님 2026-11-04)."""
from pathlib import Path

import saju.order.__main__ as M


def _job():
    return {"orderId": "x", "productId": "wealth", "payload": {}}


def test_rebuilds_until_check_passes(monkeypatch):
    calls, sent = [], []
    def fake(job, out, w):
        calls.append(1)
        Path(out).write_bytes(b"%PDF")
        bad = [{"kind": "점수"}] if len(calls) < 3 else []
        return {"pages": 70, "issues": bad}
    monkeypatch.setattr(M, "make_pdf", fake)
    monkeypatch.setattr(M, "status", lambda *a: sent.append(a))
    pdf, problem = M.build(_job())
    assert pdf == b"%PDF" and problem == "" and len(calls) == 3
    assert [a[1] for a in sent] == ["retry", "retry"]


def test_holds_after_all_tries(monkeypatch):
    calls = []
    def fake(job, out, w):
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("boom")
        return {"pages": 70, "issues": [{"kind": "연도"}]}
    monkeypatch.setattr(M, "make_pdf", fake)
    monkeypatch.setattr(M, "status", lambda *a: None)
    pdf, problem = M.build(_job())
    assert pdf is None and len(calls) == M.TRIES >= 4
    assert problem == "글 검사: 연도"


def test_usage_line_sums_tokens_by_model():
    """발송 로그에 모델별 토큰 합을 남긴다(재무 원가 실측, 개인정보 없음)."""
    line = M.usage_line([
        {"model": "a", "input": 10, "output": 5, "cache_read": 1, "cache_write": 0},
        {"model": "a", "input": 2, "output": 1},
        {"model": "b", "input": 7, "output": 3, "cache_read": 0, "cache_write": 4},
    ])
    assert line == "a 호출 2 입력 12 출력 6 캐시읽기 1 캐시쓰기 0 / b 호출 1 입력 7 출력 3 캐시읽기 0 캐시쓰기 4"
    assert M.usage_line(None) == "없음"


def test_stops_quietly_when_refunded_before_send(monkeypatch):
    """작업 중 환불되면 서버가 409 ORDER_REFUNDED로 막고, 작업은 보류로 남기지 않고 끝낸다(P-VC-3)."""
    import io
    import urllib.error
    sent = []
    def call(method, path, body=None, content_type="application/json"):
        if method == "GET":
            return {"orderId": "x", "productId": "wealth", "status": "queued", "payload": {}}
        raise urllib.error.HTTPError(path, 409, "Conflict", {}, io.BytesIO(b'{"code":"ORDER_REFUNDED"}'))
    monkeypatch.setattr(M, "_call", call)
    monkeypatch.setattr(M, "build", lambda job: (b"%PDF", ""))
    monkeypatch.setattr(M, "status", lambda *a: sent.append(a[1]))
    assert M.run("x") == 0
    assert sent == ["processing"]


def test_skips_refunded_job(monkeypatch):
    monkeypatch.setattr(M, "_call", lambda *a, **k: {"orderId": "x", "productId": "wealth", "status": "refunded"})
    monkeypatch.setattr(M, "status", lambda *a: (_ for _ in ()).throw(AssertionError("상태를 보내면 안 됨")))
    assert M.run("x") == 0
