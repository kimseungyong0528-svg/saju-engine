"""마케팅 게시물 재료: 띠별 2027 운세와 방법·시기 글을 채널별 글로 바꾼다.

사주 근거(띠와 그해의 합·충, 삼재)는 엔진이 계산하고, 글은 data/*.json에 미리 써 둔 것을 쓴다.
API를 부르지 않는다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..analysis import branch_relation
from ..constants import BRANCHES, BRANCHES_HANJA, STEMS, STEMS_HANJA, ZODIAC_ANIMALS
from ..report.newyear import samjae, year_branch

DATA = Path(__file__).parent / "data"

SITE_URL = "https://unmyeong-saju.com"
BRAND = "운명서재"
YEAR = 2027
# 띠별 운세 올리는 순서: 합·충이 있는 띠(반응이 큰 띠)를 앞에 둔다
DDI_ORDER = ["말", "소", "토끼", "개", "쥐", "양", "돼지", "호랑이", "용", "뱀", "원숭이", "닭"]
EMOJI = {"쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰", "용": "🐲", "뱀": "🐍", "말": "🐴",
         "양": "🐑", "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"}
BASE_TAGS = ["#2027운세", "#2027신년운세", "#정미년", "#신년운세", "#사주", "#띠별운세", "#운명서재"]


@dataclass
class Post:
    kind: str                 # "ddi" | "topic" | "summary"
    key: str                  # 띠 이름 또는 주제 id
    title: str                # 표지·쇼츠 제목
    hook: str                 # 표지 큰 글씨
    sub: str                  # 표지 작은 글씨
    slides: list[dict]        # [{"head", "body"}] 표지와 마지막 장 사이의 본문 장
    remember: str
    tags: list[str]
    facts: dict = field(default_factory=dict)
    ask: str = ""             # 스레드 끝 질문 (댓글 받기)
    keywords: list[str] = field(default_factory=list)   # 뜬 주제와 맞춰 볼 낱말
    reel_hook: str = ""       # 인스타 릴스 첫 화면 한 줄


def _load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def year_ganzhi_hanja(year: int) -> str:
    s, b = (year - 4) % 10, (year - 4) % 12
    return f"{STEMS[s]}{BRANCHES[b]}({STEMS_HANJA[s]}{BRANCHES_HANJA[b]})"


def birth_years(animal: str, lo: int = 1950, hi: int = 2008) -> list[int]:
    i = ZODIAC_ANIMALS.index(animal)
    return [y for y in range(lo, hi + 1) if (y - 4) % 12 == i]


def ddi_facts(animal: str, year: int = YEAR) -> dict:
    """엔진으로 띠 글자와 그해 지지의 관계, 삼재를 계산한다."""
    i = ZODIAC_ANIMALS.index(animal)
    yb = BRANCHES.index(year_branch(year))
    rels = branch_relation(i, yb)
    sj = samjae(BRANCHES[i], year)
    return {"animal": animal, "branch": BRANCHES[i], "hanja": BRANCHES_HANJA[i],
            "relations": [r.split("(")[0] for r in rels], "samjae": sj["kind"],
            "years": birth_years(animal)}


def _years_text(years: list[int]) -> str:
    return "·".join(f"{y % 100:02d}" for y in years) + "년생"


def ddi_posts(year: int = YEAR) -> list[Post]:
    items = {d["animal"]: d for d in _load("ddi_2027.json")["items"]}
    gz = year_ganzhi_hanja(year)
    out = []
    for animal in DDI_ORDER:
        d = items[animal]
        f = ddi_facts(animal, year)
        tags = [f"#{animal}띠운세", f"#{animal}띠", f"#{year}{animal}띠"] + BASE_TAGS
        rel = ("·".join(f["relations"]) if f["relations"]
               else "같은 띠 글자" if f["branch"] == year_branch(year) else "큰 부딪힘 없음")
        if f["samjae"]:
            rel += f" · {f['samjae']}"
        out.append(Post(
            kind="ddi", key=animal,
            title=f"{year}년 정미년 {animal}띠 운세ㅣ{_years_text(f['years'][-5:])}",
            hook=f"{year} {animal}띠 운세",
            sub=d["summary"],
            slides=[
                {"head": f"사주 근거: {f['branch']}({f['hanja']}) × 미(未) — {rel}", "body": d["basis"]},
                {"head": "이런 일이 생길 수 있어요", "body": d["scene"]},
                {"head": "이렇게 하세요", "body": "\n".join(f"{n}. {t}" for n, t in enumerate(d["todo"], 1))},
                {"head": "조심할 것", "body": d["caution"]},
            ],
            remember=d["remember"],
            tags=tags, facts=f | {"ganzhi": gz},
            ask=f"주변에 {animal}띠가 있나요? 이 글을 보여 주세요.",
            keywords=[f"{animal}띠"] + [f"{y % 100:02d}년생" for y in f["years"]],
            reel_hook=f"{animal}띠, {d['summary'].split('에게 ', 1)[-1]}",
        ))
    return out


def summary_post(year: int = YEAR) -> Post:
    """12띠 한눈에 보기: 띠별 글의 첫 줄만 모은다."""
    items = {d["animal"]: d for d in _load("ddi_2027.json")["items"]}
    lines = [f"{a}띠: {items[a]['summary'].split('에게 ', 1)[-1]}" for a in ZODIAC_ANIMALS]
    return Post(
        kind="summary", key="12띠",
        title=f"{year}년 정미년 12띠 운세 한눈에 보기",
        hook=f"{year} 12띠 운세 한눈에",
        sub="쥐띠부터 돼지띠까지 2027년을 한 줄씩 정리했어요.",
        slides=[{"head": "쥐띠 ~ 호랑이띠", "body": "\n".join(lines[0:3])},
                {"head": "토끼띠 ~ 말띠", "body": "\n".join(lines[3:7])},
                {"head": "양띠 ~ 돼지띠", "body": "\n".join(lines[7:12])}],
        remember="띠는 태어난 해 하나만 본 것이에요. 생년월일 전체를 보면 내 2027년이 정확히 보여요.",
        tags=["#12띠운세"] + BASE_TAGS,
        ask="여러분 띠는 어떤 해인가요? 댓글로 띠를 알려 주세요.",
        keywords=["12띠", "띠별운세", "대박띠"],
        reel_hook="2027년, 12띠를 한 줄씩 정리했어요",
    )


def topic_posts() -> list[Post]:
    out = []
    for t in _load("topics.json")["items"]:
        out.append(Post(
            kind="topic", key=t["id"], title=t["title"], hook=t["hook"], sub=t["title"],
            slides=t["slides"], remember=t["remember"],
            tags=["#사주공부", "#사주풀이", "#명리학"] + BASE_TAGS,
            ask=t["ask"], keywords=t["keywords"], reel_hook=t["hook"],
        ))
    return out


# ── 채널별 포장 ─────────────────────────────────────────────
# 재료(Post)는 하나, 포장은 채널마다 그 채널 1위 계정 방식으로 다르게 한다.
#   유튜브 쇼츠: 도화도르 — 제목에 "보는 법·시기", 출생연도 나열, 설명란 링크
#   인스타 릴스·카드: 도화도르·포스텔러 — 첫 화면 큰 한 줄, 짧은 캡션, 저장 유도, 팔로우 유도
#   스레드: 사주장인 — 긴 설명을 이어 쓰기(한 칸 500자), 질문으로 시작하고 질문으로 끝내 댓글 받기
#   당근: 사주대가 — 주 1회 소식, 상품·가격 안내

THREADS_LIMIT = 500


def youtube(p: Post) -> dict:
    if p.kind == "ddi":
        rest = p.sub.split("에게 ", 1)[-1].rstrip(".")
        title = f"{p.title}, {rest.removesuffix('예요')}"
    else:
        title = f"{p.title}ㅣ2027 정미년 사주 쉽게 보기"
    desc = [p.sub, ""]
    for s in p.slides:
        desc.append(f"▪ {s['head']}")
    desc += ["", f"기억할 한 줄: {p.remember}", "", f"내 생년월일로 보는 2027 신년운세 👉 {SITE_URL}", "",
             " ".join(p.tags[:6]) + " #shorts"]
    return {"제목": title[:100], "설명": "\n".join(desc)}


def _ig_tags(p: Post) -> str:
    return " ".join(p.tags[:9])


def instagram_reel(p: Post) -> dict:
    cap = [p.reel_hook, "", p.sub, "", f"기억할 한 줄: {p.remember}", "",
           "저장해 두고 2027년에 다시 꺼내 보세요.", "매일 띠별 운세 올려요. 놓치기 싫으면 팔로우 해 두세요.", "",
           _ig_tags(p)]
    return {"캡션": "\n".join(cap)}


def facebook_reel(p: Post) -> dict:
    """페이스북 페이지 릴스: 40~60대가 많이 보므로 해시태그를 줄이고 차분한 설명으로 쓴다 (인스타와 문장이 다르게)."""
    cap = [p.title, "", p.sub, ""]
    cap += [f"▪ {s['head']}" for s in p.slides[:3]]
    cap += ["", f"오늘 기억할 한 줄: {p.remember}", "",
            "띠는 태어난 해 하나만 본 것이에요. 생년월일과 태어난 시간까지 보면 내 운의 흐름이 더 자세히 나와요.", "", "매일 띠별 운세 올려요. 놓치기 싫으면 팔로우 해 두세요.", "",
            " ".join(p.tags[:3])]
    return {"캡션": "\n".join(cap)}


def instagram_cards(p: Post) -> dict:
    cap = [p.hook, "", p.sub, "", "👉 옆으로 넘겨서 보세요.", "", f"기억할 한 줄: {p.remember}", "",
           "저장해 두면 필요할 때 바로 꺼내 볼 수 있어요.", "매일 띠별 운세 올려요. 놓치기 싫으면 팔로우 해 두세요.", "",
           _ig_tags(p)]
    return {"캡션": "\n".join(cap)}


def _split(blocks: list[str], limit: int = THREADS_LIMIT) -> list[str]:
    """스레드 한 칸은 500자까지라서, 문단을 깨지 않고 여러 칸으로 나눈다."""
    parts, cur = [], ""
    for b in blocks:
        nxt = f"{cur}\n\n{b}" if cur else b
        if len(nxt) <= limit:
            cur = nxt
        else:
            if cur:
                parts.append(cur)
            cur = b
    if cur:
        parts.append(cur)
    return parts


def threads(p: Post) -> dict:
    first = f"{p.hook}\n\n{p.sub}"
    blocks = [first] + [f"{s['head']}\n{s['body']}" for s in p.slides]
    blocks += [f"기억할 한 줄: {p.remember}", f"{p.ask}\n\n내 생년월일로 보는 2027 신년운세: {SITE_URL}"]
    parts = _split(blocks)
    n = len(parts)
    return {f"{i}/{n}": t for i, t in enumerate(parts, 1)}


def daangn(week_posts: list[Post]) -> dict:
    """당근 비즈프로필 소식: 한 주에 한 번, 그 주의 띠를 묶어서 올린다."""
    ddis = [p for p in week_posts if p.kind == "ddi"]
    lines = ["2027년 정미년 띠별 운세 (이번 주)", ""]
    for p in ddis:
        lines.append(f"{EMOJI[p.key]} {p.key}띠: {p.sub}")
    lines += ["", "띠는 태어난 해 하나만 본 것이에요.",
              "생년월일과 태어난 시간으로 2027년 12달 흐름, 돈·일·연애·건강을 한 권(PDF 약 60쪽)으로 정리해 드려요.",
              "2027 신년운세 29,800원", "", f"신청: {SITE_URL}"]
    return {"소식": "\n".join(lines)}
