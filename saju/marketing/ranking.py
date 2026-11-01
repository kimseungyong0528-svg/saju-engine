"""띠 순위 쇼츠 재료: 그해(또는 그달)의 천간·지지와 띠 글자의 관계로 12띠 점수를 매긴다.

점수 근거 (엔진 계산만 쓴다)
- 오행 관계: 띠 지지의 오행과 그 기간 천간·지지 오행이 비겁(같음)·식상(띠가 낳음)·재성(띠가 이김)·관성(띠를 누름)·인성(띠를 낳음) 중 무엇인지
- 지지 관계: 띠 글자와 그 기간 지지의 육합·반합·충·형·파·해·원진 (saju.analysis.branch_relation)
- 삼재: 해 단위 순위에서만 (saju.report.newyear.samjae)
순위 종류마다 위 항목에 주는 무게가 다르다. 같은 점수는 좋은 근거가 많은 띠, 그다음 자축인묘 순서로 나눈다.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from ..analysis import branch_relation
from ..constants import (
    BRANCH_ELEMENT,
    BRANCHES,
    BRANCHES_HANJA,
    STEM_ELEMENT,
    STEMS,
    STEMS_HANJA,
    ZODIAC_ANIMALS,
)
from ..report.newyear import samjae
from .content import SITE_URL, birth_years

GODS = ["비겁", "식상", "재성", "관성", "인성"]
REL_NAMES = ["육합", "반합", "충", "형", "파", "해", "원진"]

# 종류: 이름, 제목 문구, 십신 무게(비겁·식상·재성·관성·인성), 지지 관계 무게, 삼재 무게(들·눌, 날)
KINDS = {
    "money": {"name": "재물운", "head": "돈이 가장 많이 들어오는 띠", "gods": (-1, 1.5, 3, -0.5, 0),
              "rel": {"육합": 2, "반합": 1.5, "충": -2, "형": -1, "파": -1, "해": -0.5, "원진": -1}, "samjae": (-1, -0.5)},
    "love": {"name": "인연운", "head": "좋은 사람을 만나는 띠", "gods": (0.5, 1, 0.5, 0.5, 0),
             "rel": {"육합": 3, "반합": 2, "충": -2, "형": -1, "파": -0.5, "해": -1, "원진": -2}, "samjae": (0, 0)},
    "work": {"name": "일·승진운", "head": "일에서 인정받는 띠", "gods": (-0.5, -0.5, 1, 3, 1.5),
             "rel": {"육합": 1, "반합": 1, "충": -1, "형": -1, "파": -0.5, "해": -0.5, "원진": -0.5}, "samjae": (-0.5, 0)},
    "study": {"name": "시험·문서운", "head": "시험과 계약이 잘 풀리는 띠", "gods": (0, -0.5, -1, 1, 3),
              "rel": {"육합": 1, "반합": 1, "충": -1, "형": -0.5, "파": -1, "해": -0.5, "원진": -0.5}, "samjae": (-0.5, 0)},
    "help": {"name": "귀인운", "head": "도와주는 사람이 나타나는 띠", "gods": (1, 0, 0, 0.5, 3),
             "rel": {"육합": 2, "반합": 1.5, "충": -1.5, "형": -1, "파": -0.5, "해": -1, "원진": -1.5}, "samjae": (-0.5, 0)},
    "move": {"name": "이동·변화운", "head": "이사·이직 기회가 들어오는 띠", "gods": (0.5, 1, 0, 0, 0),
             "rel": {"육합": -0.5, "반합": 0, "충": 3, "형": 1.5, "파": 1, "해": 0.5, "원진": 0}, "samjae": (1, 0.5)},
    "care": {"name": "조심운", "head": "가장 조심해야 할 띠", "gods": (0.5, 0, 0, 1.5, 0),
             "rel": {"육합": -1, "반합": -1, "충": 3, "형": 2, "파": 1.5, "해": 1, "원진": 1.5}, "samjae": (2, 1)},
}
YEAR_KINDS = ["money", "love", "work", "help", "study", "move", "care"]
MONTH_KINDS = ["money", "love", "care"]

# 근거 문장 (쉬운 말). 순위 종류마다 같은 십신도 다르게 읽는다
GOD_TEXT = {
    "money": {"비겁": "돈을 나눌 사람이 생겨요", "식상": "돈 버는 활동이 늘어요", "재성": "돈 기운이 들어와요",
              "관성": "책임이 커져서 돈이 나가요"},
    "love": {"비겁": "친구와 모임이 늘어요", "식상": "마음을 표현하기 쉬워져요", "재성": "남성에게는 이성 인연이 들어와요",
             "관성": "여성에게는 이성 인연이 들어와요"},
    "work": {"비겁": "경쟁자가 생겨요", "식상": "윗사람과 부딪히기 쉬워요", "재성": "성과가 돈으로 이어져요",
             "관성": "자리와 책임이 들어와요", "인성": "윗사람이 밀어 줘요"},
    "study": {"식상": "집중이 흩어지기 쉬워요", "재성": "공부보다 돈 일이 먼저 생겨요", "관성": "자격과 직함이 따라와요",
              "인성": "공부와 문서 기운이 들어와요"},
    "help": {"비겁": "편이 되어 주는 친구가 생겨요", "관성": "나를 끌어 주는 윗사람이 생겨요", "인성": "도와주는 어른이 나타나요"},
    "move": {"비겁": "함께 움직일 사람이 생겨요", "식상": "새 일을 벌이고 싶어져요"},
    "care": {"비겁": "돈 문제로 다투기 쉬워요", "관성": "부담과 압박이 커져요"},
}
REL_TEXT = {"육합": "짝처럼 잘 맞는 육합이에요", "반합": "힘을 보태 주는 반합이에요", "충": "정면으로 부딪히는 충이에요",
            "형": "일을 다시 손봐야 하는 형이에요", "파": "계획이 깨지기 쉬운 파예요", "해": "작은 손해가 생기기 쉬운 해예요",
            "원진": "마음이 어긋나기 쉬운 원진이에요"}
SAMJAE_TEXT = {"들삼재": "삼재가 시작되는 들삼재예요", "눌삼재": "삼재 한가운데인 눌삼재예요", "날삼재": "삼재가 끝나는 날삼재예요"}


@dataclass
class Period:
    key: str          # "2027" | "2026-11"
    label: str        # "2027년" | "11월"
    long: str         # "2027 정미년" | "2026년 11월"
    stem: int
    branch: int
    year: int | None  # 삼재를 볼 해 (해 단위만)

    @property
    def ganzhi(self) -> str:
        return f"{STEMS[self.stem]}{BRANCHES[self.branch]}({STEMS_HANJA[self.stem]}{BRANCHES_HANJA[self.branch]})"


def year_period(year: int) -> Period:
    s, b = (year - 4) % 10, (year - 4) % 12
    return Period(str(year), f"{year}년", f"{year} {STEMS[s]}{BRANCHES[b]}년", s, b, year)


def month_period(year: int, month: int) -> Period:
    """그달 15일이 속한 절기 달의 간지. 1월(축월)은 아직 지난해 간지에 속한다."""
    b = month % 12                                 # 1월 축, 2월 인, …, 11월 해, 12월 자
    sy = year - 1 if month == 1 else year
    first = ((sy - 4) % 10 % 5 * 2 + 2) % 10       # 인월 천간 (갑기년 병인, 을경년 무인 …)
    s = (first + (b - 2) % 12) % 10
    return Period(f"{year}-{month:02d}", f"{month}월", f"{year}년 {month}월", s, b, None)


def _god(ddi_el: int, el: int) -> str:
    d = (el - ddi_el) % 5
    return {0: "비겁", 1: "식상", 2: "재성", 3: "관성", 4: "인성"}[d]


@dataclass
class Row:
    ddi: str
    branch: str
    score: float
    why: list[tuple[float, str]] = field(default_factory=list)   # (무게, 근거 문장)
    years: str = ""
    rank: int = 0

    @property
    def good(self) -> list[str]:
        return [t for w, t in sorted(self.why, key=lambda x: -x[0]) if w > 0]

    @property
    def bad(self) -> list[str]:
        return [t for w, t in sorted(self.why, key=lambda x: x[0]) if w < 0]


def rank(kind: str, period: Period) -> list[Row]:
    k = KINDS[kind]
    els = {STEM_ELEMENT[period.stem], BRANCH_ELEMENT[period.branch]}
    rows = []
    for i, (b, animal) in enumerate(zip(BRANCHES, ZODIAC_ANIMALS)):
        r = Row(animal, b, 0.0)
        for el in sorted(els):
            g = _god(BRANCH_ELEMENT[i], el)
            w = k["gods"][GODS.index(g)]
            txt = GOD_TEXT.get(kind, {}).get(g)
            if w and txt:
                r.score += w
                r.why.append((w, txt))
        for name in branch_relation(i, period.branch):
            n = name.split("(")[0]
            w = k["rel"].get(n, 0)
            if w:
                r.score += w
                r.why.append((w, f"띠와 {period.label}이 {REL_TEXT[n]}"))
        if period.year:
            sj = samjae(b, period.year)["kind"]
            if sj:
                w = k["samjae"][1 if sj == "날삼재" else 0]
                if w:
                    r.score += w
                    r.why.append((w, SAMJAE_TEXT[sj]))
        ys = birth_years(animal)
        r.years = "·".join(f"{y % 100:02d}" for y in ys[-4:-1])
        rows.append(r)
    rows.sort(key=lambda r: (-r.score, -len(r.good), BRANCHES.index(r.branch)))
    for n, r in enumerate(rows, 1):
        r.rank = n
    return rows


@dataclass
class RankPost:
    key: str
    kind: str
    period: Period
    rows: list[Row]
    title: str
    lines: list[str]          # 읽을 대본 (한 줄 = 목소리 한 번)
    caps: list[str]           # 화면 자막
    reveal_from: int          # lines[reveal_from] 가 12위
    tags: list[str]

    @property
    def name(self) -> str:
        return KINDS[self.kind]["name"]


def rank_post(kind: str, period: Period) -> RankPost:
    k = KINDS[kind]
    rows = rank(kind, period)
    top = rows[0]
    head = k["head"]
    intro = f"{period.label} {head}, 순위로 알려 드릴게요. 12위부터 갈게요."
    lines, caps = [intro], [f"{period.long} {k['name']} 띠 순위"]
    for r in reversed(rows[3:]):
        lines.append(f"{r.rank}위, {r.ddi}띠.")
        caps.append(f"{r.rank}위 {r.ddi}띠")
    for r in reversed(rows[:3]):
        why = (r.good or r.bad)[:1]
        tail = f" {why[0]}." if why else ""
        if r.rank == 1:
            why2 = (r.good + r.bad)[:2]
            tail = " " + " ".join(f"{w}." for w in why2) if why2 else ""
            lines.append(f"대망의 1위는 {r.ddi}띠예요!{tail}")
        else:
            lines.append(f"{r.rank}위는 {r.ddi}띠예요.{tail}")
        caps.append(f"{r.rank}위 {r.ddi}띠")
    lines.append("더 궁금한 사주는 프로필 링크에서 확인해 보세요.")
    caps.append("더 궁금한 사주는 프로필 링크에서")
    title = f"{period.label} {head} 순위ㅣ1위는 {top.ddi}띠 ({top.years}년생)"
    tags = [f"#{period.label}운세", f"#{k['name'].replace('·', '')}", "#띠별운세", "#띠순위", "#사주", "#운명서재"]
    return RankPost(f"rank-{kind}-{period.key}", kind, period, rows, title, lines, caps, 1, tags)


def youtube_rank(p: RankPost) -> dict:
    k = KINDS[p.kind]
    lst = "\n".join(f"{r.rank}위 {r.ddi}띠 ({r.years}년생)" for r in p.rows)
    why = "\n".join(f"{r.rank}위 {r.ddi}띠: " + ", ".join((r.good + r.bad)[:3]) for r in p.rows[:3])
    basis = (f"{p.period.long}의 간지는 {p.period.ganzhi}이에요. 띠 글자와 {p.period.label} 글자의 오행 관계, "
             f"그리고 합·충 같은 지지 관계로 12띠의 {k['name']} 점수를 매겼어요.")
    desc = "\n\n".join([f"{p.period.label} {k['head']} 순위", lst, "상위 3띠 근거\n" + why, basis,
                        "띠는 태어난 해 하나만 본 것이에요. 내 생년월일 전체로 보는 운세는 운명서재에서 확인하세요.\n" + SITE_URL,
                        " ".join(p.tags)])
    return {"제목": p.title[:100], "설명": desc}


def rank_posts(today: dt.date) -> list[RankPost]:
    """쓸 수 있는 순위 재료: 다음 해 7종 + 이번(또는 다음) 달 3종."""
    year = today.year + 1 if today.month >= 9 else today.year
    m = today if today.day < 15 else (today.replace(day=1) + dt.timedelta(days=32))
    out = [rank_post(k, year_period(year)) for k in YEAR_KINDS]
    out += [rank_post(k, month_period(m.year, m.month)) for k in MONTH_KINDS]
    return out
