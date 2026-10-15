"""올리기 전 검사표: 금지어, 과장 약속, 채널별 글자 수, 사이트 주소, 사주 근거와 엔진 계산이 맞는지."""

from __future__ import annotations

import re

from ..report.verify import HEDGE
from .content import THREADS_LIMIT, Post, SITE_URL

# 과장 약속: 표시광고 문제가 될 수 있고 신뢰를 깎는다
HYPE = re.compile(r"돈벼락|수백억|수억|일확천금|인생역전|딱\s*1번|두\s*번\s*다시\s*없|100\s*%|무조건|반드시\s*대박|초대박|로또")
REL_TERMS = ["육합", "반합", "충", "형", "파", "해", "원진"]
SLIDE_BODY_MAX = 190   # 카드 한 장 본문 글자 수 (넘으면 글씨가 작아지거나 넘친다)
LIMITS = {"youtube.제목": 100, "youtube.설명": 5000, "instagram.캡션": 2200}
IG_TAGS_MAX = 30


def _quoted_terms(text: str) -> set[str]:
    return {t for t in REL_TERMS if f"'{t}'" in text}


def check_post(p: Post, packs: dict[str, dict[str, str]]) -> list[str]:
    """packs: {"youtube": {"제목": .., "설명": ..}, "instagram": {"캡션": ..}, "threads": {"1/2": .., ...}}"""
    issues = []
    texts = [t for pack in packs.values() for t in pack.values()]
    every = "\n".join([p.hook, p.sub, p.remember, p.reel_hook, *(s["head"] + s["body"] for s in p.slides), *texts])
    if m := HEDGE.search(every):
        issues.append(f"금지어(참고용·재미로 등): {m.group(0)}")
    if m := HYPE.search(every):
        issues.append(f"과장 약속: {m.group(0)}")
    for s in p.slides:
        if len(s["body"]) > SLIDE_BODY_MAX:
            issues.append(f"카드 글이 깁니다({len(s['body'])}자 > {SLIDE_BODY_MAX}): {s['head']}")
    for ch, pack in packs.items():
        for k, t in pack.items():
            lim = THREADS_LIMIT if ch == "threads" else LIMITS.get(f"{ch.split('-')[0]}.{k}")
            if lim and len(t) > lim:
                issues.append(f"{ch} {k} 글자 수 초과: {len(t)} > {lim}")
        if ch.startswith("instagram") and sum(t.count("#") for t in pack.values()) > IG_TAGS_MAX:
            issues.append(f"{ch} 해시태그가 {IG_TAGS_MAX}개를 넘습니다")
    if "youtube" in packs and SITE_URL not in packs["youtube"]["설명"]:
        issues.append("유튜브 설명에 사이트 주소가 없습니다")
    if "threads" in packs and SITE_URL not in list(packs["threads"].values())[-1]:
        issues.append("스레드 마지막 칸에 사이트 주소가 없습니다")
    if p.kind == "ddi":
        f = p.facts
        basis = p.slides[0]["body"]
        said, real = _quoted_terms(basis), set(f["relations"])
        if said != real:
            issues.append(f"사주 근거가 엔진 계산과 다릅니다: 글={sorted(said)}, 엔진={sorted(real)}")
        if f["samjae"] and f["samjae"] not in basis:
            issues.append(f"{f['samjae']}인데 글에 없습니다")
        if not f["samjae"] and "삼재" in basis:
            issues.append("삼재가 아닌데 글에 삼재가 나옵니다")
    return issues


def check_rank(p, pack: dict[str, str]) -> list[str]:
    """띠 순위 쇼츠: 금지어·과장, 제목 길이, 사이트 주소, 12띠가 모두 한 번씩 들어갔는지."""
    issues = []
    every = "\n".join([*p.lines, *pack.values()])
    if m := HEDGE.search(every):
        issues.append(f"금지어(참고용·재미로 등): {m.group(0)}")
    if m := HYPE.search(every):
        issues.append(f"과장 약속: {m.group(0)}")
    if len(pack["제목"]) > LIMITS["youtube.제목"]:
        issues.append(f"유튜브 제목 글자 수 초과: {len(pack['제목'])}")
    if SITE_URL not in pack["설명"]:
        issues.append("유튜브 설명에 사이트 주소가 없습니다")
    if sorted(r.ddi for r in p.rows) != sorted(set(r.ddi for r in p.rows)) or len(p.rows) != 12:
        issues.append("순위에 12띠가 한 번씩 들어가지 않았습니다")
    return issues
