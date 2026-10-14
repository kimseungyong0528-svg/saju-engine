"""올리기 전 검사표: 금지어, 과장 약속, X 글자 수, 사주 근거와 엔진 계산이 맞는지."""

from __future__ import annotations

import re
import unicodedata

from ..report.verify import HEDGE
from .content import Post, SITE_URL

# 과장 약속: 표시광고 문제가 될 수 있고 신뢰를 깎는다
HYPE = re.compile(r"돈벼락|수백억|수억|일확천금|인생역전|딱\s*1번|두\s*번\s*다시\s*없|100\s*%|무조건|반드시\s*대박|초대박|로또")
REL_TERMS = ["육합", "반합", "충", "형", "파", "해", "원진"]
SLIDE_BODY_MAX = 190   # 카드 한 장 본문 글자 수 (넘으면 글씨가 작아지거나 넘친다)
X_LIMIT = 280          # X 가중 글자 수 (한글 2, 링크 23)
URL_RE = re.compile(r"https?://\S+")


def x_weight(text: str) -> int:
    n = 0
    for part in URL_RE.split(text):
        for ch in part:
            n += 2 if unicodedata.east_asian_width(ch) in ("W", "F") or ord(ch) > 0x2E80 else 1
    return n + 23 * len(URL_RE.findall(text))


def _quoted_terms(text: str) -> set[str]:
    return {t for t in REL_TERMS if f"'{t}'" in text}


def check_post(p: Post, texts: dict[str, str]) -> list[str]:
    issues = []
    every = "\n".join([p.hook, p.sub, p.remember, *(s["head"] + s["body"] for s in p.slides), *texts.values()])
    if HEDGE.search(every):
        issues.append(f"금지어(참고용·재미로 등): {HEDGE.search(every).group(0)}")
    if m := HYPE.search(every):
        issues.append(f"과장 약속: {m.group(0)}")
    for s in p.slides:
        if len(s["body"]) > SLIDE_BODY_MAX:
            issues.append(f"카드 글이 깁니다({len(s['body'])}자 > {SLIDE_BODY_MAX}): {s['head']}")
    if "X" in texts and x_weight(texts["X"]) > X_LIMIT:
        issues.append(f"X 글자 수 초과: {x_weight(texts['X'])} > {X_LIMIT}")
    for name, t in texts.items():
        if name != "인스타" and SITE_URL not in t:
            issues.append(f"{name}: 사이트 주소가 없습니다")
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
