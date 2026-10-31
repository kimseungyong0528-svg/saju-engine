import json

from saju.marketing import trends as tr
from saju.marketing.__main__ import build, pick
from saju.marketing.checks import check_post
from saju.marketing.content import (SITE_URL, THREADS_LIMIT, daangn, ddi_facts, ddi_posts, instagram_cards,
                                    instagram_reel, summary_post, threads, topic_posts, youtube)


def _packs(p):
    return {"youtube": youtube(p), "instagram-reel": instagram_reel(p), "instagram-cards": instagram_cards(p),
            "threads": threads(p)}


def _all_posts():
    return ddi_posts() + [summary_post()] + topic_posts()


def test_ddi_facts_match_engine():
    assert ddi_facts("말")["relations"] == ["육합"]
    assert set(ddi_facts("소")["relations"]) == {"충", "형"}
    assert ddi_facts("토끼")["samjae"] == "날삼재"
    assert ddi_facts("호랑이")["relations"] == [] and ddi_facts("호랑이")["samjae"] == ""
    assert ddi_facts("쥐")["years"][-1] == 2008


def test_all_posts_pass_checks():
    posts = _all_posts()
    assert len(posts) == 27
    for p in posts:
        assert check_post(p, _packs(p)) == [], p.key


def test_threads_split_under_limit_and_end_with_site():
    for p in _all_posts():
        parts = list(threads(p).values())
        assert all(len(t) <= THREADS_LIMIT for t in parts), p.key
        assert SITE_URL in parts[-1]


def test_check_catches_wrong_basis_and_hype():
    p = ddi_posts()[0]                     # 말띠
    p.slides[0]["body"] = p.slides[0]["body"].replace("'육합'", "'충'")
    assert any("엔진 계산과 다릅니다" in i for i in check_post(p, _packs(p)))
    p.sub = "돈벼락 맞는 해예요"
    assert any("과장" in i for i in check_post(p, _packs(p)))


def test_trend_score_puts_hot_topic_first_and_used_last():
    topics = topic_posts()
    hot = {"items": [{"title": "삼재 띠 총정리", "ratio": 5.0, "value": 1}]}
    ranked = tr.order(topics, hot)
    assert ranked[0][0].key == "samjae" and ranked[0][1] == 5.0
    ranked = tr.order(topics, hot, used={"samjae"})
    assert ranked[-1][0].key == "samjae"


def test_pick_two_materials_a_day():
    days = pick(7, None, set())
    assert len(days) == 7
    assert all(am.kind in ("ddi", "summary") and pm.kind == "topic" for (am, _), (pm, _) in days)
    assert len({am.key for (am, _), _ in days}) == 7


def test_collect_without_keys_skips():
    t = tr.collect(env={})
    assert t["items"] == [] and any("건너뜀" in n for n in t["notes"])


def test_daangn_mentions_site():
    assert SITE_URL in daangn(ddi_posts()[:2])["소식"]


def test_build_one_day_manifest(tmp_path):
    r = build(__import__("datetime").date(2026, 10, 19), 1, tmp_path, video=False)
    m = json.loads((r["folder"] / "manifest.json").read_text(encoding="utf-8"))
    chans = [it["channel"] for it in m["days"][0]["items"]]
    assert sorted(chans) == sorted(["youtube", "instagram-reel", "facebook-reel", "threads", "youtube",
                                         "instagram-cards", "threads"])
    assert m["problems"] == []
    for it in m["days"][0]["items"]:
        for f in [it.get("thumb"), *it.get("images", [])]:
            if f:
                assert (r["folder"] / f).exists()


def test_build_cards_are_jpeg_for_instagram(tmp_path):
    import shutil
    if not shutil.which("ffmpeg"):
        return
    r = build(__import__("datetime").date(2026, 10, 19), 1, tmp_path, video=False)
    m = json.loads((r["folder"] / "manifest.json").read_text(encoding="utf-8"))
    imgs = [f for it in m["days"][0]["items"] for f in it.get("images", [])]
    assert imgs and all(f.endswith(".jpg") for f in imgs)


def test_meta_clean_removes_site_link_until_toss_live(monkeypatch):
    from saju.marketing import meta
    text = "질문이에요?\n\n내 생년월일로 보는 2027 신년운세: https://unmyeong-saju.com"
    monkeypatch.delenv("SNS_SITE_LINK", raising=False)
    assert meta.clean(text) == "질문이에요?"
    monkeypatch.setenv("SNS_SITE_LINK", "on")
    assert meta.clean(text) == text


def test_meta_media_url_signature_matches_site(monkeypatch):
    import hashlib
    import hmac
    from saju.marketing import meta
    monkeypatch.setenv("WORKER_SECRET", "worker-secret")
    url = meta.media_url("2026-11-02", "인스타/a.jpg")
    sig = hmac.new(b"worker-secret", "pub:2026-11-02/인스타/a.jpg".encode(), hashlib.sha256).hexdigest()
    assert url.endswith(f"&sig={sig}") and "/api/studio/pub/2026-11-02?path=" in url


def test_meta_run_posts_only_approved_and_unposted(monkeypatch):
    from saju.marketing import meta
    calls = []
    plan = {"week": "2026-11-02", "approved": {"a": "t", "b": "t", "d": "t"}, "posted": {"b": {"ok": True}},
            "items": [{"id": "a", "slot": "오전", "channel": "threads", "title": "", "texts": {}},
                      {"id": "b", "slot": "오전", "channel": "threads", "title": "", "texts": {}},
                      {"id": "c", "slot": "오전", "channel": "threads", "title": "", "texts": {}},
                      {"id": "d", "slot": "저녁", "channel": "threads", "title": "", "texts": {}},
                      {"id": "e", "slot": "오전", "channel": "youtube", "title": "", "texts": {}}]}

    def fake_call(method, path, body=None, content_type=""):
        calls.append((method, path, body))
        return plan if path.startswith("/api/internal/studio/today") else {}
    monkeypatch.setattr(meta.publish, "_call", fake_call)
    monkeypatch.setitem(meta.POSTERS, "threads", lambda week, it: f"https://threads.net/{it['id']}")
    assert meta.run("오전", "2026-11-02") == 0
    posted = [json.loads(b)["id"] for m_, p, b in calls if p.endswith("/posted")]
    assert posted == ["a"]


def test_sns_rules_fixed():
    """사장님이 못 박은 SNS 게시 규칙 (2026-10-31). 지우거나 바꾸면 이 검사가 빨간불이 된다."""
    import datetime as dt
    from saju.marketing import rules
    from saju.marketing.__main__ import AM, PM
    r = rules.load()
    am, pm = rules.slot("아침"), rules.slot("저녁")
    assert (am["time"], pm["time"]) == (AM, PM) == ("07:30", "18:00")
    assert {f["key"] for f in am["formats"]} >= {"solo", "forceteller", "sinbi", "tier"}
    assert [f["key"] for f in pm["formats"]] == ["threads-capture"]
    assert "salgusaju" in pm["formats"][0]["ref"] and "taebaek_saju" in pm["formats"][0]["ref"]
    assert any("엔진 계산" in t for t in r["always"]) and any("승인" in t for t in r["always"])
    days = [dt.date(2026, 11, 1) + dt.timedelta(days=i) for i in range(60)]
    fmts = [rules.morning_format(d) for d in days]
    assert all(a != b for a, b in zip(fmts, fmts[1:]))
