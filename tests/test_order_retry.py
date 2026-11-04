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
