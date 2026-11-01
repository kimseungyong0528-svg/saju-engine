"""SNS 게시물 공식: 날짜만 넣으면 그날 아침 영상·저녁 스레드 글 재료가 나온다 (사장님 2026-11-01 "공식으로, 무한 발행").

- 순위·띠·합충·출생연도는 모두 엔진 계산(ranking.rank, analysis.branch_relation)에서 나온다 (제1조항).
- 문장은 banks.json 재료를 엔진 결과에 맞춰 고른다. 이미 쓴 재료(key)는 건너뛴다.
- 아침 형식은 rules.json 의 5가지를 날마다 돌린다. 저녁은 사주장인식(댓글로 이어 쓰기)·살구식·도화도르식을 돌린다.
"""

from __future__ import annotations

import datetime as dt
import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

from ...analysis import branch_relation
from ...constants import (
    BRANCH_ELEMENT,
    BRANCHES,
    BRANCHES_HANJA,
    ELEMENTS,
    STEM_ELEMENT,
    STEMS,
    STEMS_HANJA,
    ZODIAC_ANIMALS,
)
from ...pillars import day_pillar_for_date
from .. import rules
from ..content import birth_years
from ..ranking import KINDS, Period, Row, _god, month_period, rank, year_period

B = json.loads((Path(__file__).with_name("banks.json")).read_text(encoding="utf-8"))
KIND_ORDER = ["money", "love", "care", "work", "help", "study", "move"]
# 잘 터지는 돈·연애를 더 자주 (돈 3, 연애 3, 조심 2, 나머지 1)
KIND_ROT = ["money", "love", "care", "money", "work", "love", "help", "money", "care", "love", "study", "move"]
BANNED = ("보장", "확정", "참고용", "재미로", "재회", "무조건")
Y_LO, Y_HI = 1960, 2007
EL_HANJA = {e: B["elements"][e]["hanja"] for e in ELEMENTS}
GH = B["god_hanja"]


# ── 말 다듬기 ──
def _batchim(word: str) -> bool:
    w = word.split("(")[0].strip()
    c = w[-1] if w else "가"
    if "가" <= c <= "힣":
        return (ord(c) - 0xAC00) % 28 != 0
    return c in "0136781L"  # 숫자·영문 끝 (일, 삼, 육, 칠, 팔, 십)


def josa(word: str, a: str, b: str) -> str:
    """받침 있으면 a(이·은·과·을), 없으면 b(가·는·와·를)."""
    return word + (a if _batchim(word) else b)


def fill(s: str, **kw) -> str:
    for k, v in kw.items():
        s = s.replace("{" + k + "}", str(v))
    return s


def years(ddi: str) -> list[int]:
    return sorted((y for y in birth_years(ddi) if Y_LO <= y <= Y_HI), reverse=True)


def years_short(ddi: str) -> str:
    return ", ".join(f"{y % 100:02d}" for y in years(ddi))


def years_full(ddi: str) -> str:
    return ", ".join(str(y) for y in years(ddi))


def ddi(a: str) -> str:
    return a + "띠"


def target_month(day: dt.date) -> tuple[int, int]:
    """20일부터는 다음 달 이야기를 한다."""
    if day.day >= 20:
        n = day.replace(day=28) + dt.timedelta(days=5)
        return n.year, n.month
    return day.year, day.month


def periods(day: dt.date) -> list[Period]:
    """이번(20일부터는 다음) 달, 그다음 달, 다가올 해."""
    y, m = target_month(day)
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return [month_period(y, m), month_period(ny, nm), year_period(day.year + 1 if day.month >= 9 else day.year)]


def _rot(seq: list, n: int) -> list:
    n %= len(seq)
    return seq[n:] + seq[:n]


# ── 엔진 근거를 사람 말로 ──
def why_key(kind: str, text: str) -> str:
    for r in ("육합", "반합", "원진", "충", "형", "파", "해"):
        if f"{r}이에요" in text or f"{r}예요" in text:
            return f"move:{r}" if kind == "move" and f"move:{r}" in B["rel"] else r
    return text


def why_bank(kind: str, text: str) -> dict:
    k = why_key(kind, text)
    if k in B["rel"]:
        d = dict(B["rel"].get(k.split(":")[-1], {}))
        d.update(B["rel"][k])
        d["tag"] = fill(d["tag"], n=B["kinds"][kind]["noun"])
        return d
    return B["why"].get(text, {"short": [text], "long": [text], "tag": text})


def main_whys(r: Row) -> list[tuple[float, str]]:
    """점수에 가장 크게 보탠 근거부터."""
    return sorted(r.why, key=lambda x: -x[0])


def pick_unique(options: list[str], used: set[str]) -> str:
    for o in options:
        if o not in used:
            used.add(o)
            return o
    return options[0]


# ── 제목 ──
def titles(kind: str, p: Period) -> list[list[str]]:
    k = B["kinds"][kind]
    lab = p.label
    out = []
    for lines in rules.load()["titles"].get(kind, []):
        out.append([t.replace("11월", lab).replace("이번 달", lab) for t in lines])
    for sc in k["scenes"]:
        out.append([sc, f"{lab} {k['verb']} 띠", "1위부터 12위"])
        out.append([sc, f"{lab} {k['alt']} 띠", "1위부터 12위"])
    return out


# ── 아침 ──
@dataclass
class Morning:
    key: str
    fmt: str
    kind: str = ""
    period: Period | None = None
    title: list[str] = field(default_factory=list)
    rows: list[Row] = field(default_factory=list)
    data: dict = field(default_factory=dict)

    def texts(self) -> dict[str, dict]:
        return morning_texts(self)


def _forceteller_variants() -> list[tuple[str, str, str]]:
    out = []
    for e in ELEMENTS:
        out += [("lack", e, ""), ("much", e, ""), ("pair", e, ELEMENTS[(ELEMENTS.index(e) + 1) % 5])]
    out += [("stem", STEMS[i], "") for i in range(10)]
    return out


def forceteller_data(tpl: str, e: str, c: str, p: Period) -> dict:
    E = B["elements"][e]
    lab = f"{e}({E['hanja']})"
    if tpl == "lack":
        head = [f"<em>{e} 없는 사주</em>가", "꼭 만나야 하는 사람"]
        say = [f"태어날 때 받은 여덟 글자 안에\n{josa(lab, '이', '가')} 없으면"] + E["lack"]
    elif tpl == "much":
        head = [f"<em>{e} 많은 사주</em>가", "조심해야 할 한 가지"]
        say = [f"태어날 때 받은 여덟 글자 안에\n{josa(lab, '이', '가')} 많으면"] + E["much"]
    else:
        C = B["elements"][c]
        head = [f"<em>{e} 많은 사람</em>과", f"{c} 많은 사람이 만나면"]
        say = [f"{e} 많은 사람은\n{E['who']}", f"{c} 많은 사람은\n{C['who']}",
               f"{josa(e + '(' + E['hanja'] + ')', '이', '가')} {josa(c + '(' + C['hanja'] + ')', '을', '를')} 키워 주는\n상생(相生) 사이예요",
               f"{c} 쪽이 받기만 하지 않게\n고마움을 말로 표현하세요"]
    cta = f"내 사주에 {josa(e, '이', '가')} 얼마나 있는지 궁금하면\n댓글에 '{e}' 남겨 주세요"
    return {"tpl": tpl, "el": e, "pair": c, "head": head, "say": say + [cta]}


def forceteller_stem(st: str) -> dict:
    i = STEMS.index(st)
    j = (i + 5) % 10
    name, partner = STEM_NAMES[i].split("(")[0], STEM_NAMES[j].split("(")[0]
    trait, weak, gain = B["stems"][st]
    a, c = sorted((i, j))
    return {"tpl": "stem", "el": ELEMENTS[STEM_ELEMENT[i]], "pair": ELEMENTS[STEM_ELEMENT[j]],
            "head": [f"<em>{name} 일간</em>이", "꼭 만나야 하는 사람"],
            "say": [f"{name} 일간은\n{trait}", weak, f"{partner} 일간을 만나면\n{gain}", f"{STEMS[a]}{STEMS[c]}합(合)\n서로 손을 잡는 사이예요",
                    "내 일간이 뭔지 모르면\n프로필 링크에서 생년월일만 넣어 보세요"]}


def forceteller_month(tpl: str, p: Period) -> dict:
    e = ELEMENTS[BRANCH_ELEMENT[p.branch]]
    E = B["elements"][e]
    lab = f"{e}({E['hanja']})"
    intro = f"{josa(p.label, '은', '는')} {BRANCHES[p.branch]}월({BRANCHES_HANJA[p.branch]}月)\n{lab} 기운이 강한 달이에요"
    if tpl == "mlack":
        say = [intro, f"태어날 때 받은 여덟 글자 안에\n{josa(lab, '이', '가')} 없던 사람은\n이 달에 그 기운을 빌려 써요", E["borrow"], E["lack"][2]]
        head = [f"<em>{p.label}, {e}의 달</em>", f"{e} 없는 사주는 이렇게"]
    else:
        say = [intro, f"태어날 때 받은 여덟 글자 안에\n{josa(lab, '이', '가')} 많은 사람은\n같은 기운이 겹쳐 넘치기 쉬워요", E["much"][1], E["much"][2]]
        head = [f"<em>{p.label}, {e}의 달</em>", f"{e} 많은 사주는 이렇게"]
    cta = f"내 사주에 {josa(e, '이', '가')} 얼마나 있는지 궁금하면\n댓글에 '{e}' 남겨 주세요"
    return {"tpl": tpl, "el": e, "pair": "", "head": head, "say": say + [cta]}


def sinbi_data(day: dt.date) -> dict:
    p = day_pillar_for_date(day)
    per = Period(day.isoformat(), "오늘", f"{day.month}월 {day.day}일", p.stem, p.branch, None)
    allw: dict[str, list] = {}
    for kind in ("money", "love", "care", "work", "help"):
        for r in rank(kind, per):
            allw.setdefault(r.ddi, []).extend((w, kind, t) for w, t in r.why)
    used: set[str] = set()
    txt = {}
    for a in ZODIAC_ANIMALS:
        hit = None
        for w, kind, t in sorted(allw.get(a, []), key=lambda x: -abs(x[0])):
            longs = _rot(why_bank(kind, t)["long"], day.toordinal())
            hit = next((s for s in longs if s not in used), None)
            if hit:
                used.add(hit)
                break
        txt[a] = hit or "큰 변화 없이 흘러가는 날이에요. 하던 일을 마무리하세요."
    return {"date": day.isoformat(), "ganzhi": f"{STEMS[p.stem]}{BRANCHES[p.branch]}", "text": txt}


def morning_candidates(fmt: str, day: dt.date):
    n = day.toordinal()
    if fmt == "sinbi":
        yield Morning(f"sinbi-{day.isoformat()}", fmt, data=sinbi_data(day))
        return
    if fmt == "forceteller":
        p = periods(day)[0]
        for tpl in ("mlack", "mmuch"):
            yield Morning(f"forceteller-{tpl}-{p.key}", fmt, period=p, data=forceteller_month(tpl, p))
        for tpl, e, c in _rot(_forceteller_variants(), n // 5):
            data = forceteller_stem(e) if tpl == "stem" else forceteller_data(tpl, e, c, p)
            yield Morning(f"forceteller-{tpl}-{e}", fmt, period=p, data=data)
        return
    for kind in dict.fromkeys(_rot(KIND_ROT, n // 5)):
        for p in periods(day):
            rows = rank(kind, p)
            ts = titles(kind, p)
            m = Morning(f"{fmt}-{kind}-{p.key}", fmt, kind, p, ts[n % len(ts)], rows)
            if fmt == "hidden":
                used: set[str] = set()
                m.data["phrase"] = {r.ddi: pick_unique(
                    [s for _, t in (main_whys(r) if r.score > 0 else sorted(r.why)) for s in why_bank(kind, t)["short"]] or ["평소처럼 흘러가요"], used) for r in rows}
            if fmt == "solo":
                bgs = B["backgrounds"]
                m.data["bg"] = bgs[(n // 5) % len(bgs)]
                m.data["lines"] = [fill(x, p=p.label) for x in B["kinds"][kind]["solo"]]
            yield m


def morning(day: dt.date, used: set[str]) -> Morning:
    fmt = rules.morning_format(day)
    cands = list(morning_candidates(fmt, day))
    return next((c for c in cands if c.key not in used), cands[0])


def _rank_lines(rows: list[Row], upto: int = 12) -> list[str]:
    return [f"{r.rank}위 {ddi(r.ddi)} ({years_short(r.ddi)}년생)" for r in rows[:upto]]


def morning_texts(m: Morning) -> dict[str, dict]:
    tags = "#사주 #운세 #띠별운세 #띠순위 #운명서재"
    if m.fmt == "sinbi":
        d = dt.date.fromisoformat(m.data["date"])
        head = f"{d.month}월 {d.day}일 띠별 운세"
        body = "\n".join(f"{ddi(a)}: {t}" for a, t in m.data["text"].items())
        lines = [head, "", body, "", f"오늘 일진은 {m.data['ganzhi']}일이에요. 띠 글자와 오늘 글자의 관계로 풀었어요.", "",
                 "저장해 두고 오늘 하루 한 번 더 보세요.", "내 생년월일로 보는 운세는 프로필 링크에서", "", tags]
        cap = "\n".join(lines)
        return {"youtube": {"제목": f"{head} | 오늘의 운세 #shorts", "설명": cap},
                "instagram-reel": {"캡션": cap}, "facebook-reel": {"캡션": cap}}
    if m.fmt == "forceteller":
        e = m.data["el"]
        head = " ".join(x.replace("<em>", "").replace("</em>", "") for x in m.data["head"])
        cap = "\n".join([head, ""] + [s.replace("\n", " ") for s in m.data["say"]] + ["", f"#오행 #{e} #사주 #궁합 #운명서재"])
        return {"youtube": {"제목": f"{head} | 오행 쉽게 보기 #shorts", "설명": cap},
                "instagram-reel": {"캡션": cap}, "facebook-reel": {"캡션": cap}}
    k = KINDS[m.kind]
    lab = m.period.label
    title = " ".join(m.title).replace("“", "").replace("”", "")
    basis = (f"{m.period.long} 간지는 {copula(m.period.ganzhi)}. 띠 글자와 {lab} 글자의 오행 관계, "
             f"합·충 같은 지지 관계로 12띠 {k['name']} 점수를 매겼어요.")
    if m.fmt == "solo":
        top = m.rows[:3]
        cap = "\n".join([" ".join(m.data["lines"]), "", *[f"✅ {r.rank}위 {ddi(r.ddi)} ({years_short(r.ddi)}년생)" for r in top], "",
                         "💬 댓글에 본인 띠 남겨 주세요", "", basis, "", tags])
    elif m.fmt == "hidden":
        rest = [f"{r.rank}위 {ddi(r.ddi)} 👉 {m.data['phrase'][r.ddi]}" for r in reversed(m.rows[3:])]
        top = [f"{r.rank}위 {ddi(r.ddi)} ({years_short(r.ddi)}년생) 👉 {m.data['phrase'][r.ddi]}" for r in reversed(m.rows[:3])]
        cap = "\n".join([title, "", *rest, "", "1~3위는 맨 아래에 👇", "", "💬 댓글에 내 띠 남기기", "", basis, "", tags,
                         "", ".", ".", ".", *top])
    else:
        cap = "\n".join([title, "", *_rank_lines(m.rows), "", basis, "", "💬 내 띠는 몇 위인지 댓글로 남겨 주세요", "", tags])
    yt = f"{lab} {k['name']} 띠 순위 | 1위 {ddi(m.rows[0].ddi)} ({years_short(m.rows[0].ddi)}년생) #shorts"
    return {"youtube": {"제목": yt[:100], "설명": cap}, "instagram-reel": {"캡션": cap}, "facebook-reel": {"캡션": cap}}


# ── 저녁 ──
@dataclass
class Evening:
    key: str
    style: str
    pages: list[list[str]]
    dark: bool = False   # 스레드 글은 전부 흰 배경 (사장님 2026-11-01)
    topic: str = ""      # 도화도르식 틀 글의 주제: 한 주에 같은 주제를 두 번 쓰지 않는다
    facts: tuple = ()    # (대상, 기간 key, 주제, +/-): 한 주 안에서 같은 대상을 좋다·조심 양쪽으로 쓰지 않는다 (제1조항)

    @property
    def frame(self) -> str:
        """글 틀 이름 (같은 틀을 이틀 연속 같은 시간대에 쓰지 않는다)."""
        k = self.key
        for pre in ("jangin-double", "jangin-stem", "jstem", "jone", "dohwa-d", "dohwa-s", "salgu"):
            if k.startswith(pre):
                return pre
        return k.split("-")[0] + ("-list" if k.startswith("jangin-") else "")

    @property
    def kind(self) -> str:
        """주제 (money·love·…). 목록 글·한 장 글만, 나머지는 빈칸."""
        k = self.key.split("-")
        if k[0] in ("jone", "jstem"):
            return k[1]
        if k[0] == "jangin" and k[1] not in ("double",):
            return k[2] if k[1] == "stem" else k[1]
        return ""

    @property
    def is_list(self) -> bool:
        return self.key.startswith("jangin-")

    @property
    def parts(self) -> list[str]:
        """스레드에 올릴 글: 첫 장은 본글, 나머지는 내 댓글로 이어 쓴다."""
        return ["\n".join(p).strip() for p in self.pages]

    def texts(self) -> dict[str, dict]:
        n = len(self.parts)
        th = {f"{i}/{n}": t for i, t in enumerate(self.parts, 1)}
        cap = "\n\n".join(self.parts) + "\n\n#사주 #운세 #띠별운세 #사주스레드 #운명서재"
        return {"threads": th, "instagram-reel": {"캡션": cap[:2100]}}


def _branch(i: int) -> str:
    return f"{BRANCHES[i]}({BRANCHES_HANJA[i]})"


def _stem(i: int) -> str:
    return f"{STEMS[i]}({STEMS_HANJA[i]})"


def ira(word: str) -> str:
    """'이라/라'를 받침에 맞춰 붙인다."""
    return word + ("이라" if _batchim(word) else "라")


def copula(word: str) -> str:
    """'이에요/예요'를 받침에 맞춰 붙인다."""
    return word + ("이에요" if _batchim(word) else "예요")


REL_NAMES7 = ("육합", "반합", "충", "형", "파", "해", "원진")


def _basis(kind: str, p: Period, r: Row, t: str) -> list[str]:
    """엔진 근거 한 개를 '무슨 글자가 어떻게 만나는지' 줄로 바꾼다."""
    bi = BRANCHES.index(r.branch)
    key = why_key(kind, t).split(":")[-1]
    if key in REL_NAMES7:
        h = B["rel"][key]["hanja"]
        return [josa(f"{p.label} {_branch(p.branch)}", "과", "와"), josa(f"{ddi(r.ddi)} {_branch(bi)}", "이", "가"),
                copula(f"{key}({h})"), B["rel"][key]["mean"]]
    from ..ranking import GOD_TEXT
    for e in (STEM_ELEMENT[p.stem], BRANCH_ELEMENT[p.branch]):
        g = _god(BRANCH_ELEMENT[bi], e)
        if GOD_TEXT.get(kind, {}).get(g) == t:
            return [f"{p.label} {p.ganzhi}의 {ELEMENTS[e]}({EL_HANJA[ELEMENTS[e]]}) 기운은",
                    f"{ddi(r.ddi)}에게 {copula(f'{g}({GH[g]})')}", t]
    return [t]


def jangin_card(kind: str, p: Period, r: Row, k: int, tags: set[str]) -> list[str]:
    """띠 한 장: 꼬리표와 근거는 같은 이유에서 나온다 (꼬리표만 다른 이유를 쓰면 글이 어긋난다)."""
    whys = main_whys(r)
    good = [t for w, t in whys if w > 0]
    cand = good if (good and kind != "care") else [t for _, t in whys]
    main = next((t for t in cand if why_bank(kind, t)["tag"] not in tags), cand[0])
    tag = why_bank(kind, main)["tag"]
    tags.add(tag)
    lines = [f"{ddi(r.ddi)} ({years_full(r.ddi)})", f"- {tag}", ""]
    lines += _basis(kind, p, r, main)
    feel = why_bank(kind, main).get("feel") or B["feel"][kind][k % len(B["feel"][kind])]
    lines += ["", feel[0], feel[1]]
    return lines


STEM_NAMES = [f"{STEMS[i]}{ELEMENTS[STEM_ELEMENT[i]]}({STEMS_HANJA[i]}{EL_HANJA[ELEMENTS[STEM_ELEMENT[i]]]})" for i in range(10)]
HAP_W = {"money": 1, "love": 2, "care": 0, "work": 1, "help": 1.5, "study": 1, "move": 0}


@dataclass
class StemRow:
    stem: int
    score: float = 0.0
    why: list = field(default_factory=list)   # (무게, 근거 문장, 기운 오행, 십신)


def stem_rank(kind: str, p: Period) -> list[StemRow]:
    """일간(태어난 날 첫 글자) 10개를 그 기간 글자와의 십신·천간합으로 매긴다. 띠 순위와 같은 무게(ranking.KINDS)를 쓴다."""
    from ..ranking import GOD_TEXT
    k = KINDS[kind]
    rows = []
    for i in range(10):
        r = StemRow(i)
        for e in sorted({STEM_ELEMENT[p.stem], BRANCH_ELEMENT[p.branch]}):
            g = _god(STEM_ELEMENT[i], e)
            w = k["gods"][["비겁", "식상", "재성", "관성", "인성"].index(g)]
            t = GOD_TEXT.get(kind, {}).get(g)
            if w and t:
                r.score += w
                r.why.append((w, t, e, g))
        if (i - p.stem) % 10 == 5 and HAP_W[kind]:
            r.score += HAP_W[kind]
            r.why.append((HAP_W[kind], "천간합", None, None))
        rows.append(r)
    rows.sort(key=lambda r: (-r.score, -len([w for w in r.why if w[0] > 0]), r.stem))
    return rows


# ── 사주장인식 목록 글 (상위 레퍼런스 90개를 보고 다시 짬, 2026-11-01) ──
# 본글: 장면 제목 → 1·2·3 (엔진 순위) → 미리 축하. 댓글: ※질문 머리 카드 → 신호 → 할 일 → 다음 해 → 끝맺음.
LB = B["list"]
_TERM: dict = {}


def start_label(p: Period) -> str:
    """기간이 시작하는 절기와 날짜 (예: 입동(11/7)). 엔진 절기 계산(astro.solar_terms)을 한국 시간으로 쓴다."""
    from ...astro import solar_terms
    y = int(p.key[:4])
    m = 2 if p.year else int(p.key[5:])
    name = B["jeolgi"][str(m)]
    if (y, name) not in _TERM:
        t = next(t for t, _, nm in solar_terms(y) if nm == name)
        k = t + dt.timedelta(hours=9)
        _TERM[(y, name)] = f"{name}({k.month}/{k.day})"
    return _TERM[(y, name)]


def period_intro(p: Period, n: int = 0) -> list[str]:
    """이 기간이 무슨 글자로 시작하는지 두 줄 (절기 날짜·간지·오행은 엔진 계산, 말투만 돌린다)."""
    d = start_label(p)
    e = ELEMENTS[BRANCH_ELEMENT[p.branch]]
    gz = f"{STEMS[p.stem]}{BRANCHES[p.branch]}"
    gzh = f"{STEMS_HANJA[p.stem]}{BRANCHES_HANJA[p.branch]}{'年' if p.year else '月'}"
    tpl = LB["intro"][n % len(LB["intro"])]
    kw = {"d": d, "gz": gz, "gzh": gzh, "unit": "년" if p.year else "월", "e": e, "eh": EL_HANJA[e], "ew": B["elements"][e]["word"],
          "b": BRANCHES[p.branch], "bh": BRANCHES_HANJA[p.branch], "bj": josa(_branch(p.branch), "이", "가"),
          "un": "해" if p.year else "달이", "lab": p.label}
    out = [fill(x, **kw) for x in tpl]
    return [x.replace(f"{d}이 지나면", josa(d, "이", "가") + " 지나면").replace(f"{p.label}은", josa(p.label, "은", "는"))
            .replace(f"{gz}년로", f"{gz}년으로").replace(f"{gz}월로", f"{gz}월로") for x in out]


def this_year(p: Period) -> Period:
    """'올해': 해 글이면 그 앞 해, 달 글이면 그 달이 속한 해 (1월은 아직 지난해)."""
    y = int(p.key[:4])
    if p.year:
        return year_period(y - 1)
    return year_period(y - 1 if int(p.key[5:]) == 1 else y)


def next_year(p: Period) -> Period | None:
    if p.year:
        return None
    y, m = int(p.key[:4]), int(p.key[5:])
    return year_period(y + 1 if m >= 2 else y)


def pain_ddi(a: str, p: Period, n: int = 0) -> str:
    """올해 버거웠던 이유 (엔진: 올해 지지와 띠의 충·형·파·해·원진, 없으면 올해 천간이 띠에게 무슨 십신인지)."""
    Y = this_year(p)
    b = ZODIAC_ANIMALS.index(a)
    yn = f"{STEMS[Y.stem]}{BRANCHES[Y.branch]}년"
    for x in branch_relation(b, Y.branch):
        rel = x.split("(")[0]
        if rel in LB["pain_rel"]:
            v = LB["pain_rel"][rel]
            return f"- 올해 {yn}엔 {ira(BRANCHES[b] + BRANCHES[Y.branch] + rel)} {v[n % len(v)]}"
    g = _god(BRANCH_ELEMENT[b], STEM_ELEMENT[Y.stem])
    if g in LB["pain_god"]:
        e = ELEMENTS[STEM_ELEMENT[Y.stem]]
        v = LB["pain_god"][g]
        return f"- 올해 {yn} {josa(f'{e}({EL_HANJA[e]})', '이', '가')} {ira(f'{g}({GH[g]})')} {v[n % len(v)]}"
    return ""


def pain_stem(s: int, p: Period, n: int = 0) -> str:
    Y = this_year(p)
    g = _god(STEM_ELEMENT[s], STEM_ELEMENT[Y.stem])
    if g not in LB["pain_god"]:
        return ""
    e = ELEMENTS[STEM_ELEMENT[Y.stem]]
    v = LB["pain_god"][g]
    return f"- 올해 {STEMS[Y.stem]}{BRANCHES[Y.branch]}년 {josa(f'{e}({EL_HANJA[e]})', '이', '가')} {ira(f'{g}({GH[g]})')} {v[n % len(v)]}"


def basis_ddi(kind: str, p: Period, r: Row, t: str) -> list[str]:
    """엔진 근거 한 개를 두 줄로: 무슨 글자가 어떻게 만나는지 / 그래서 무슨 일이 생기는지."""
    ls = [x.replace(f"{p.label} {p.ganzhi}의 ", "이 해 " if p.year else "이 달 ") for x in _basis(kind, p, r, t)]
    if len(ls) == 4:
        rel = why_key(kind, t).split(":")[-1]
        return [f"- {ls[0]} {ls[1]} {ls[2]}", f"- {LB['rel_mean'].get(kind, {}).get(rel, ls[3])}"]
    if len(ls) == 3:
        return [f"- {ls[0].replace(' 기운은', ' 기운이')} {ls[1]}", f"- {ls[2]}"]
    return [f"- {ls[0]}"]


def basis_stem(kind: str, p: Period, r: "StemRow", w: tuple) -> list[str]:
    _w, t, e, g = w
    short = STEM_NAMES[r.stem].split("(")[0]
    if t == "천간합":
        a, c = sorted((r.stem, p.stem))
        return [f"- {p.label} {josa(_stem(p.stem), '과', '와')} {short} 일간이 {STEMS[a]}{STEMS[c]}합(合)이에요",
                f"- {LB['rel_mean'].get(kind, {}).get('천간합', B['stem_hap']['mean'])}"]
    return [f"- {'이 해' if p.year else '이 달'} {ELEMENTS[e]}({EL_HANJA[ELEMENTS[e]]}) 기운이 {short} 일간에게 {copula(f'{g}({GH[g]})')}", f"- {t}"]


def next_lines(kind: str, ny: Period, place: int, total: int, unit: str, n: int = 0) -> tuple[list[str], str]:
    """다음 해에도 이어지는지 (엔진 순위 그대로). 돌려주는 부호는 글의 사실(facts)에 들어간다."""
    name = KINDS[kind]["name"]
    if kind == "care":
        if place <= 4:
            return [f"- {ny.long}에도 조심운 {total}{unit} 중 {place}위예요", "- 큰 결정은 내년에도 한 번 더 보고 하세요"], "-"
        if place > total // 2:
            return [f"- {ny.long}엔 조심운 {total}{unit} 중 {place}위로 내려가요", "- 이 달만 잘 넘기면 숨통이 트여요"], ""
        return [f"- {ny.long}엔 조심운 {total}{unit} 중 {place}위로 보통이에요", "- 무리만 안 하면 괜찮아요"], ""
    if place <= 4:
        return [f"- {ny.long}에도 {name} {total}{unit} 중 {place}위예요", LB["next_go"][n % 3]], "+"
    if place > total - (4 if total == 12 else 3):
        return [f"- {ny.long}엔 {name} {total}{unit} 중 {place}위로 흐름이 바뀌어요", LB["next_keep"][n % 3]], "-"
    return [f"- {ny.long}엔 {name} {total}{unit} 중 {place}위로 보통이에요", "- 지금 만든 걸 꾸준히 이어 가세요"], ""


def _alike(line: str, text: str) -> bool:
    """신호 줄이 이미 앞 장에 나온 말과 겹치는지 (낱말 두 개 이상 같으면 겹친다고 본다)."""
    ws = {w for w in re.findall(r"[가-힣]{2,}", line) if w not in ("생겨요", "나와요", "쉬워요", "이에요")}
    return sum(1 for w in ws if w in text) >= 2


def list_post(key: str, kind: str, p: Period, n: int, W: str, items: list[dict], facts: list) -> Evening:
    """items: {"name": 카드 제목, "line": 본글 줄, "pain": 올해 줄, "basis": 근거 두 줄, "next": (줄, 부호), "subj": 사실 대상}"""
    K = B["kinds"][kind]
    q = LB["q"][kind]
    d = start_label(p)
    hooks = LB["hooks"][kind]
    hi = n + int(p.key[5:] if not p.year else 0) + len(W)     # 같은 주제를 다른 달·다른 대상으로 다시 쓸 때 제목이 겹치지 않게
    hook = [fill(x, d=d, p=p.label, W=W, **{"W는": josa(W, "은", "는")}) for x in hooks[hi % len(hooks)]]
    pr = LB["promise"][kind]
    care = kind == "care"
    p1 = hook + [""] + [x["line"] for x in items] + ["",
          f"이 세 {W}{'는' if not _batchim(W) else '은'} {p.label} 한 달만 천천히 가세요." if care else f"이 세 {ira(W)}면 미리 축하드려요.",
          pr[hi % len(pr)]]
    scenes = _rot(LB["scenes"][kind], n)
    p2 = [q[0]] + period_intro(p, n)
    for i, x in enumerate(items):
        p2 += ["", x["name"]] + ([x["pain"]] if x["pain"] else []) + x["basis"]
    if sum(len(s) + 1 for s in p2) + 40 * len(items) < 470:      # 자리가 남으면 생활 장면 한 줄씩
        p2 = [q[0]] + period_intro(p, n)
        for i, x in enumerate(items):
            p2 += ["", x["name"]] + ([x["pain"]] if x["pain"] else []) + x["basis"] + [scenes[i]]
    sig_pool = LB["signals"].get(kind) or B["signals"][kind]["good"]
    if isinstance(sig_pool, dict):
        sig_pool = sig_pool["good"]
    shown = " ".join(p1 + p2)
    sigs = [x for x in _rot(sig_pool, n) if not _alike(x, shown)][:4]
    sh = LB["sign_head_bad" if care else "sign_head"]
    p3 = [q[1], sh[n % len(sh)], "",
          *sigs, "", LB["sign_tail"][kind]]
    p4 = [q[2], fill(LB["do_head"][n % 3], d=d, k="네"), "", *_rot(LB["actions"][kind], n)[:4], "", LB["act_tail"][kind]]
    pages = [p1, p2, p3, p4]
    ny = next_year(p)
    if ny and any(x["next"][1] == ("" if care else "+") and (not care or "내려가요" in x["next"][0][0]) for x in items):
        # 내년 이야기는 좋은 소식(좋은 글은 4위 안, 조심 글은 순위가 내려가는 띠)이 하나라도 있을 때만 쓴다
        p5 = [f"※ {ny.long}{'엔 풀릴까' if care else '에도 이어질까'}"]
        for x in items:
            lines, sign = x["next"]
            p5 += ["", x["name"], *lines]
            if sign:
                facts.append((x["subj"], ny.key, kind, sign))
        pages.append(p5)
    burn = LB["burning"][kind][n % len(LB["burning"][kind])]
    same = "같은 일간이라도" if W == "일간" else ("같은 해에 태어났어도" if W == "해" else "같은 띠라도")
    rest = "나머지 일곱 글자에 따라" if W == "일간" else "나머지 여섯 글자에 따라"
    end = [q[3], same, rest, f"{K['where']} 달라요", "그건 따로 봐야 알아요", "", *burn, "", *LB["find_me"][n % 3],
           LB["close"][n % len(LB["close"])]]
    pages.append(end)
    return Evening(key, "jangin", pages, facts=tuple(facts))


def jangin(kind: str, p: Period, n: int) -> Evening:
    rows = rank(kind, p)[:3]
    ny = next_year(p)
    nyr = {r.ddi: r.rank for r in rank(kind, ny)} if ny else {}
    tags: set[str] = set()
    items = []
    for i, r in enumerate(rows, 1):
        whys = main_whys(r)
        good = [t for w, t in whys if w > 0]
        cand = good if (good and kind != "care") else [t for _, t in whys]
        main = next((t for t in cand if why_bank(kind, t)["tag"] not in tags), cand[0])
        tags.add(why_bank(kind, main)["tag"])
        bi = BRANCHES.index(r.branch)
        items.append({"name": ddi(r.ddi), "line": f"{i}. {ddi(r.ddi)} [{BRANCHES_HANJA[bi]}] - ({years_full(r.ddi)})",
                      "pain": "" if kind == "care" else pain_ddi(r.ddi, p, n + i), "basis": basis_ddi(kind, p, r, main),
                      "next": next_lines(kind, ny, nyr[r.ddi], 12, "띠", n + i) if ny else ([], ""), "subj": r.ddi})
    sign = "-" if kind == "care" else "+"
    return list_post(f"jangin-{kind}-{p.key}", kind, p, n, "띠", items, [(r.ddi, p.key, kind, sign) for r in rows])


def jangin_stem(kind: str, p: Period, n: int) -> Evening | None:
    rows = [r for r in stem_rank(kind, p) if r.score > 0][:3]
    if len(rows) < 3:
        return None
    ny = next_year(p)
    nyr = {r.stem: i for i, r in enumerate(stem_rank(kind, ny), 1)} if ny else {}
    items = []
    for i, r in enumerate(rows, 1):
        w = sorted(r.why, key=lambda x: -x[0])[0]
        short = STEM_NAMES[r.stem].split("(")[0]
        items.append({"name": f"{short} 일간", "line": f"{i}. {STEM_NAMES[r.stem]} 일간",
                      "pain": "" if kind == "care" else pain_stem(r.stem, p, n + i), "basis": basis_stem(kind, p, r, w),
                      "next": next_lines(kind, ny, nyr[r.stem], 10, "일간", n + i) if ny else ([], ""), "subj": STEMS[r.stem]})
    sign = "-" if kind == "care" else "+"
    return list_post(f"jangin-stem-{kind}-{p.key}", kind, p, n, "일간", items, [(STEMS[r.stem], p.key, kind, sign) for r in rows])


DOUBLE_GOOD = ["계약서에 도장이 찍히기 쉬워요", "기다리던 답이 오기 쉬워요", "도와주는 사람이 생기기 쉬워요",
               "문서와 합격 소식이 오기 쉬워요", "가족에게 반가운 소식이 오기 쉬워요", "직함이 오르고 인정받기 쉬워요"]


def double_years(p: Period) -> list[dict]:
    """천간도 좋게, 지지도 좋게 만나는 출생 해 (겹경사). 엔진 글자 관계만 쓴다."""
    out = []
    for y in range(Y_HI, Y_LO - 1, -1):
        s, b = (y - 4) % 10, (y - 4) % 12
        if (s - p.stem) % 10 == 5:
            a, c = sorted((s, p.stem))
            stem_txt, score = f"{josa(_stem(p.stem), '과', '와')} {_stem(s)}{'이' if _batchim(STEMS[s]) else '가'} {STEMS[a]}{STEMS[c]}합이에요", 2
        elif (STEM_ELEMENT[s] - STEM_ELEMENT[p.stem]) % 5 == 1:
            stem_txt, score = f"{josa(_stem(p.stem), '이', '가')} {josa(_stem(s), '을', '를')} 생해요", 1
        else:
            continue
        rel = [x.split("(")[0] for x in branch_relation(b, p.branch)]
        if any(x in rel for x in ("충", "형", "파", "해", "원진")):
            continue
        hit = next((x for x in ("육합", "반합") if x in rel), None)
        if not hit:
            continue
        out.append({"year": y, "ddi": ZODIAC_ANIMALS[b], "gz": f"{STEMS[s]}{BRANCHES[b]}", "stem": stem_txt,
                    "branch": f"{josa(_branch(p.branch), '과', '와')} {_branch(b)}{'이' if _batchim(BRANCHES[b]) else '가'} {hit}이에요",
                    "both": score == 2, "score": score + (1 if hit == "육합" else 0)})
    out.sort(key=lambda d: (-d["score"], -d["year"]))
    return out[:3]


def double(p: Period, n: int) -> Evening | None:
    ys = double_years(p)
    if len(ys) < 2:
        return None
    d = start_label(p)
    p1 = [f"<{p.label}, 겹경사 터지는 사람>", ""] + [f"{i}. {x['year']}년생 {ddi(x['ddi'])}" for i, x in enumerate(ys, 1)]
    p1 += ["", "이 해에 태어났다면 미리 축하드려요.", "좋은 일이 한 번에 두 개씩 겹쳐 와요."]
    gz = f"{STEMS[p.stem]}{BRANCHES[p.branch]}({STEMS_HANJA[p.stem]}{BRANCHES_HANJA[p.branch]})"
    p2 = ["겹경사인 이유", "", f"{d}부터 들어오는 {gz} 두 글자가", "태어난 해 두 글자와", "둘 다 좋게 만나요"]   # reason_short
    cards = []
    for i, x in enumerate(ys):
        g = _rot(DOUBLE_GOOD, n + i * 2)[:2]
        cards.append([f"{x['year']}년생 {ddi(x['ddi'])} - {x['gz']}년생", "", "- 천간", x["stem"], "", "- 지지", x["branch"], "",
                      "천간도 합, 지지도 합이라 천합지합이에요" if x["both"] else "생과 합이 같이 들어와요", "",
                      f"- {g[0]}", f"- {g[1]}"])
    by: dict[str, list[int]] = {}
    for x in ys:
        by.setdefault(x["ddi"], []).append(x["year"])
    same = ["※ 같은 띠인데 왜 나는 아닐까"] + [f"같은 {ddi(a)}라도 {', '.join(map(str, v))}년생이에요" for a, v in by.items()]
    same += ["같은 띠라도 천간이 다른 해에 태어났으면", "겹경사는 아니에요", "", "좋은 일이 겹칠수록", "계약서와 약속은 한 번 더 읽고 도장 찍으세요"]
    end = ["※ 경사는 어디로 올까", "태어난 해는 여덟 글자 중 두 글자예요", "나머지 여섯 글자에 따라", "경사가 어디로 오는지 달라요", "그건 따로 봐야 알아요", "",
           "이 겹경사가 돈으로 올지 사람으로 올지", "그간 버틴 고생은 언제 보상받을지", "", *LB["find_me"][n % 3], LB["close"][n % len(LB["close"])]]
    return Evening(f"jangin-double-{p.key}", "jangin", [p1, p2, *cards, same, end], facts=tuple((x["ddi"], p.key, "double", "+") for x in ys))


def dohwa(day: dt.date, t: int) -> Evening:
    y, m = target_month(day)
    p = month_period(y, m)
    E = ELEMENTS[BRANCH_ELEMENT[p.branch]]
    i = ELEMENTS.index(E)
    M, C, K, P2 = ELEMENTS[(i - 1) % 5], ELEMENTS[(i + 1) % 5], ELEMENTS[(i - 2) % 5], ELEMENTS[(i + 2) % 5]
    st = lambda e: B["elements"][e]["stems"]
    kw = {"p": p.label, "E": E, "EH": EL_HANJA[E], "Ew": B["elements"][E]["word"], "M": M, "C": C, "CS": st(C), "K": K, "KS": st(K), "P2": P2,
              "P2S": st(P2), "MS": st(M), "ES": st(E), "B": BRANCHES[p.branch], "BH": BRANCHES_HANJA[p.branch], "Ega": josa(E, "이", "가"), "EEHga": josa(f"{E}({EL_HANJA[E]})", "이", "가"), "Creul": josa(C, "을", "를"), "jeol": start_label(p)}
    body = [fill(x, **kw) for x in B["dohwa"][t]]
    body = [x.replace(f"{p.label}은", josa(p.label, "은", "는")).replace(f"{p.label}이 ", josa(p.label, "이", "가") + " ") for x in body]
    reply = [fill(x, p=p.label) for x in B["dohwa_reply"][t % len(B["dohwa_reply"])]]
    topic = B["dohwa_topic"][t]
    facts = ()
    if ":" in topic:      # 어느 일간에게 좋은 말인지도 사실로 남긴다 (제1조항: 같은 주에 같은 일간을 조심으로 쓰지 않게)
        who, kind = topic.split(":")
        el = ELEMENTS.index({"C": C, "K": K, "P2": P2, "M": M, "E": E}[who])
        facts = tuple((STEMS[s_], p.key, kind, "+") for s_ in range(10) if STEM_ELEMENT[s_] == el)
    return Evening(f"dohwa-{t}-{p.key}", "dohwa", [body, reply], facts=facts, topic=f"{topic.split(':')[0]}-{topic.split(':')[-1]}")


# ── 하루 6개 (사장님 2026-11-01): 사주장인식·도화도르식·살구식을 번갈아 두 번씩 ──
ONE_KINDS = ["money", "love", "work", "help"]
_RANK: dict = {}


def _rank(kind: str, p: Period) -> list[Row]:
    k = (kind, p.key)
    if k not in _RANK:
        _RANK[k] = rank(kind, p)
    return _RANK[k]


def _action(kind: str, t: str) -> str:
    return why_bank(kind, t)["long"][0].split(". ")[-1].rstrip(".")


def _month_periods(day: dt.date) -> list[Period]:
    return [p for p in periods(day) if not p.year]


def _lead(r: Row) -> tuple[bool, str]:
    whys = main_whys(r)
    good = [t for w, t in whys if w > 0]
    bad = [t for w, t in sorted(r.why) if w < 0]
    if r.score > 0 and good:
        return True, good[0]
    return False, (bad[0] if bad else "")


def _heart(kind: str, good: bool, n: int, who: str, kw: dict) -> list[str]:
    """첫 줄: 읽는 사람의 마음·장면 → '○월 ○○띠는 ~' (thread_rules heart_first)."""
    hs = B["heart_hooks"][kind]["good" if good else "bad"]
    end = fill(B["heart_ends"]["good" if good else "bad"], **{**kw, "D": who})
    return [*hs[n % len(hs)], josa_fix(end, who)]


def josa_fix(line: str, who: str) -> str:
    return line.replace(f"{who}는", josa(who, "은", "는"))


def one_pages(kind: str, p: Period, n: int, good: bool, p1: list[str], feel: list[str], pain: str, basis: list[str], W: str) -> list[list[str]]:
    """사주장인식 한 장 글의 댓글 4장: ※왜 지금 → ※신호 → ※할 일 → 끝맺음 (상위 레퍼런스 틀)."""
    d = start_label(p)
    qk, qb = LB["q"][kind], LB["q"]["care"]
    p2 = [f"※ 왜 {d}부터일까" if good else f"※ 왜 {d}부터 천천히 가야 할까", feel[0]]
    if pain and good:
        p2.append(pain[2:])
    p2 += ["", *period_intro(p, n), "", *basis, "", feel[1]]
    sig = [x for x in _rot(B["signals"][kind]["good" if good else "bad"], n) if not _alike(x, " ".join(p1 + p2))][:3]
    sh = LB["sign_head" if good else "sign_head_bad"]
    p3 = [qk[1] if good else qb[1], sh[n % len(sh)], "", *sig, "",
          LB["sign_tail"][kind if good else "care"]]
    acts = [x for x in _rot(LB["actions" if good else "bad_actions"][kind], n) if not _alike(x, " ".join(p1 + p2 + sig))][:3]
    p4 = [qk[2] if good else qb[2], fill(LB["do_head"][n % 3], d=d, k="세"), "", *acts, "", B["good_end"][kind] if good else B["bad_end"][kind]]
    burn = LB["burning"][kind][n % len(LB["burning"][kind])]
    same = "같은 일간이라도" if W == "일간" else "같은 띠라도"
    rest = "나머지 일곱 글자에 따라" if W == "일간" else "나머지 여섯 글자에 따라"
    end = [qk[3], same, rest, f"{B['kinds'][kind]['where']} 달라요", "그건 따로 봐야 알아요", "", *burn, "", *LB["find_me"][n % 3],
           LB["close"][n % len(LB["close"])]]
    return [p1, p2, p3, p4, end]


def jangin_one(kind: str, p: Period, a: str, n: int) -> Evening | None:
    """사주장인식 띠 한 장 글: 첫 줄(마음·장면) → 띠·출생연도 → ※왜 지금(올해 고생 + 근거) → ※신호 → ※할 일 → 끝맺음.
    12띠 중 앞 4개(좋은 쪽)와 뒤 3개(조심 쪽)만 쓴다. 순위는 엔진 그대로."""
    r = next(x for x in _rank(kind, p) if x.ddi == a)
    good, lead = _lead(r)
    if not lead or not ((good and r.rank <= 4) or (not good and r.rank >= 10)):
        return None
    L = B["one_lines"][kind]
    kw = {"p": p.label, "D": ddi(a), "Y": years_short(a), "r": r.rank, "name": KINDS[kind]["name"], "verb": B["kinds"][kind]["verb"],
          "gl": L["gl"], "bl": L["bl"], "fix": _action(kind, lead)}
    p1 = _heart(kind, good, n + ZODIAC_ANIMALS.index(a), ddi(a), kw)    # 피드백 heart_first
    p1 += ["", f"{ddi(a)} ({years_full(a)})", ""] + ([f"이 글 본 {ira(ddi(a))}면 그냥 넘기지 마세요.", _rot(LB["promise_one"][kind], n + ZODIAC_ANIMALS.index(a))[0]] if good else
                                                    [f"이 글 본 {ira(ddi(a))}면 {p.label} 한 달만 천천히 가세요."])   # no_scary_tag
    pool = B["feel"][kind] if good else B["bad_feel"][kind]
    feel = why_bank(kind, lead).get("feel") or pool[(n + r.rank) % len(pool)]
    pages = one_pages(kind, p, n + ZODIAC_ANIMALS.index(a), good, p1, feel, pain_ddi(a, p, n), basis_ddi(kind, p, r, lead), "띠")
    return Evening(f"jone-{kind}-{a}-{p.key}", "jangin", pages, facts=((a, p.key, kind, "+" if good else "-"),))


def jangin_stem_one(kind: str, p: Period, s: int, n: int) -> Evening | None:
    """사주장인식 일간 한 장 글 (10일간 중 앞 3개, 뒤 2개). 순위는 stem_rank 그대로."""
    rows = stem_rank(kind, p)
    rk = next(i for i, r in enumerate(rows, 1) if r.stem == s)
    r = rows[rk - 1]
    good = r.score > 0
    if not r.why or not ((good and rk <= 3) or (r.score < 0 and rk >= 9)):
        return None
    short = STEM_NAMES[s].split("(")[0]
    L = B["one_lines"][kind]
    ws = sorted(r.why, key=lambda x: -x[0] if good else x[0])
    p1 = _heart(kind, good, n + s, f"{short} 일간", {"p": p.label, "gl": L["gl"], "bl": L["bl"]})   # 피드백 heart_first
    p1 += ["", f"태어난 날 첫 글자가 {STEMS[s]}({STEMS_HANJA[s]})인 사람", ""] + (
        [f"이 글 본 {short} 일간이라면 그냥 넘기지 마세요.", _rot(LB["promise_one"][kind], n + s)[0]] if good else
        [f"이 글 본 {short} 일간이라면 {p.label} 한 달만 천천히 가세요."])
    t0 = ws[0][1]
    pool = B["feel"][kind] if good else B["bad_feel"][kind]
    feel = (why_bank(kind, t0).get("feel") if t0 != "천간합" else None) or pool[(n + s) % len(pool)]
    pages = one_pages(kind, p, n + s, good, p1, feel, pain_stem(s, p, n), basis_stem(kind, p, r, ws[0]), "일간")
    return Evening(f"jstem-{kind}-{s}-{p.key}", "jangin", pages, facts=((STEMS[s], p.key, kind, "+" if good else "-"),))


def _end(kind: str, n: int) -> list[str]:
    K = B["kinds"][kind]
    return [fill(x, where=K["where"]) for x in B["ending"]] + [""] + K["ask"][:2] + ["", B["cta"][n % len(B["cta"])]]


def dohwa_ddi(kind: str, p: Period, a: str, n: int) -> Evening | None:
    """도화도르식 한두 줄 (띠): 좋은 소식만, 엔진 순위 4위 안만 (thread_rules dohwa_short_good)."""
    r = next(x for x in _rank(kind, p) if x.ddi == a)
    good, lead = _lead(r)
    if not lead or not good or r.rank > 4:
        return None
    wb = why_bank(kind, lead)
    tpl = B["dohwa_one"]["good"]
    line = fill(tpl[n % len(tpl)], D=ddi(a), Y=years_short(a).replace(", ", "·"), p=p.label, name=KINDS[kind]["name"],
                r=r.rank, short=wb["short"][n % len(wb["short"])])
    line = line.replace(f"{ddi(a)}는", josa(ddi(a), "은", "는"))
    reply = [fill(x, p=p.label) for x in B["dohwa_reply"][(n + 1) % len(B["dohwa_reply"])]]
    return Evening(f"dohwa-d-{kind}-{a}-{p.key}", "dohwa", [line.split("|"), reply], facts=((a, p.key, kind, "+"),))


def dohwa_stem(kind: str, p: Period, s: int, n: int) -> Evening | None:
    """도화도르식 한두 줄 (일간): 좋은 소식만, stem_rank 3위 안만."""
    rows = stem_rank(kind, p)
    rk = next(i for i, r in enumerate(rows, 1) if r.stem == s)
    r = rows[rk - 1]
    ws = [w for w in sorted(r.why, key=lambda x: -x[0]) if w[1] != "천간합" and w[0] > 0]
    if not ws or rk > 3 or r.score <= 0:
        return None
    _w, t, _e, g = ws[0]
    tpl = B["dohwa_one"]["stem_good"]
    line = fill(tpl[n % len(tpl)], S=STEM_NAMES[s].split("(")[0], p=p.label, gname=f"{g}({GH[g]})", why=t.rstrip("."),
                name=KINDS[kind]["name"], r=rk)
    reply = [fill(x, p=p.label) for x in B["dohwa_reply"][1]]
    return Evening(f"dohwa-s-{kind}-{s}-{p.key}", "dohwa", [line.split("|"), reply], facts=((STEMS[s], p.key, kind, "+"),))


SALGU_ROT = ["love", "self", "love", "money", "love", "self", "love", "flow"]   # 연애·결혼 절반 (salgu_one_theme)


def salgu_theme(t: str) -> str:
    if re.search(r"여자|남자|연애|결혼|배우자|일지|남편|아내|궁합|인연|부부|연락|짝|띠와|띠·|사이|홍염|도화|원진", t):
        return "love"
    if re.search(r"돈|재성|통장|비상금|재물|지갑|부업|재테크|암록", t):
        return "money"
    if re.search(r"대운|세운|월운|개운|운이|운을|운에|운도|운은", t):
        return "flow"
    return "self"


def _salgu_stream(group: tuple[str, ...]):
    """주제 묶음의 재료 줄: 긴 이야기(salgu_long, 레퍼런스 말투)를 먼저 섞어 쓰고, 그다음 짧은 재료. 다 쓰면 다른 순서로 다시."""
    long_ = [t for t in B["salgu_long"] if salgu_theme(t) in group]
    short = [t for t in B["salgu"] if salgu_theme(t) in group]
    cyc = 0
    while True:
        a, b = long_[:], short[:]
        random.Random(f"{group}-{cyc}-l").shuffle(a)
        random.Random(f"{group}-{cyc}-s").shuffle(b)
        yield from a + b
        cyc += 1


def _salgu_chunks(group: tuple[str, ...], n_tan: int, head_len: int):
    """한 탄에 들어갈 만큼(본글 500자 안, 3~6개)씩 잘라 n_tan 번째 묶음까지 돌려준다."""
    st = _salgu_stream(group)
    out, cur = [], []
    for t in st:
        size = head_len + sum(len(x) + 5 for x in cur) + len(t) + 5
        if cur and (size > 480 or len(cur) == 6):
            out.append(cur)
            if len(out) == n_tan:
                return out
            cur = []
        if t not in cur:
            cur.append(t)


def salgu_tan(day: dt.date, n_tan: int) -> Evening:
    """○탄: 한 탄에 주제 하나(연애·결혼 절반). 레퍼런스처럼 한 줄이 길고 말투가 센 이야기를 본글 500자 안에서 3~6개."""
    th = SALGU_ROT[(n_tan - 1) % len(SALGU_ROT)]
    group = ("money", "flow") if th in ("money", "flow") else (th,)   # 돈·운 흐름은 재료가 적어서 같이 쓴다
    j = sum(1 for i in range(n_tan) if SALGU_ROT[i % len(SALGU_ROT)] in group)
    head = f"흥미로운 사주 이야기들 (금월선녀 ver.) - {n_tan}탄"
    six = _salgu_chunks(group, j, len(head) + 2)[-1]
    p1 = [head, ""] + [f"{i}. {t}" for i, t in enumerate(six, 1)]
    return Evening(f"salgu-{n_tan}", "salgu", [p1, B["salgu_end"][n_tan % len(B["salgu_end"])]])


def jangin_pool(day: dt.date):
    n = day.toordinal()
    ps = periods(day)
    if (n // 4) % 3 == 0:
        for p in ps:
            d = double(p, n)
            if d:
                yield d
    for kind in dict.fromkeys(_rot(KIND_ROT, n // 4)):
        for p in ps:
            subj = (jangin, jangin_stem) if (n // 4) % 2 == 0 else (jangin_stem, jangin)
            for f in subj:
                ev = f(kind, p, n)
                if ev:
                    yield ev


def jangin_card_pool(day: dt.date, off: int = 0):
    n = day.toordinal()
    for p in _month_periods(day):
        for kind in _rot(ONE_KINDS, n + off):
            for a in _rot(list(ZODIAC_ANIMALS), n * 5 + off * 3):
                ev = jangin_one(kind, p, a, n)
                if ev:
                    yield ev
            for s in _rot(list(range(10)), n * 3 + off):
                ev = jangin_stem_one(kind, p, s, n)
                if ev:
                    yield ev


DOHWA_KINDS = ["money", "love", "work", "study", "help", "move"]   # 조심(care)은 도화도르식에 안 쓴다


def dohwa_pool(day: dt.date, off: int = 0):
    """12:00 은 오행 팁 틀 글 먼저, 21:00 은 엔진 순위 띠·일간 한두 줄 먼저 (한 주에 같은 주제를 두 번 쓰지 않게 섞는다)."""
    n = day.toordinal()

    def tips():
        for t in _rot(list(range(len(B["dohwa"]))), n // 3 + off):
            yield dohwa(day, t)

    def ones():
        for p in periods(day):
            for kind in _rot(DOHWA_KINDS, n + off):
                for a in _rot(list(ZODIAC_ANIMALS), n * 7 + off * 5):
                    ev = dohwa_ddi(kind, p, a, n)
                    if ev:
                        yield ev
                for s in _rot(list(range(10)), n * 3 + off):
                    ev = dohwa_stem(kind, p, s, n)
                    if ev:
                        yield ev

    if off:
        yield from ones()
        yield from tips()
    else:
        yield from tips()
        yield from ones()


def salgu_pool(day: dt.date, used: set[str]):
    yield salgu_tan(day, sum(1 for k in used if k.startswith("salgu-") and k.split("-")[1].isdigit()) + 1)


def evening_candidates(day: dt.date, used: set[str]):
    """18:00 대표 글 (캡처 영상도 이 글로 만든다): 사주장인식 목록 글."""
    yield from jangin_pool(day)
    yield from jangin_card_pool(day)


# 스레드 시간대 (사장님 2026-11-01): 사주장인 → 도화도르 → 살구 순서로 번갈아 두 번씩, 하루 6개
THREAD_SLOTS = [("오전", "07:30", "jangin"), ("점심", "12:00", "dohwa"), ("오후", "15:00", "salgu"),
                ("저녁", "18:00", "jangin"), ("밤", "21:00", "dohwa"), ("늦은밤", "23:00", "salgu")]


def slot_candidates(day: dt.date, slot: str, used: set[str]):
    style = next(st for s, _, st in THREAD_SLOTS if s == slot)
    if slot == "저녁":
        yield from evening_candidates(day, used)
    elif style == "jangin":
        yield from jangin_card_pool(day)
        yield from jangin_pool(day)
    elif style == "dohwa":
        yield from dohwa_pool(day, 0 if slot == "점심" else 2)
    else:
        yield from salgu_pool(day, used)
    # 같은 글 틀에서 못 찾으면 사주장인식으로
    yield from jangin_card_pool(day, 1)
    yield from jangin_pool(day)


def clash(e: Evening, facts: dict) -> bool:
    """한 주 안에서 같은 대상(띠·일간)·같은 기간을 한쪽은 좋다, 한쪽은 조심으로 쓰면 모순이다 (제1조항).
    조심(care) 글은 그 기간 모든 좋은 글과 부딪힌다."""
    for subj, pk, kind, sign in e.facts:
        for k2, s2 in facts.get((subj, pk), []):
            if s2 != sign and (k2 == kind or "care" in (k2, kind) or "double" in (k2, kind)):
                return True
    return False


def pick(cands, used: set[str], facts: dict | None = None, today: set[str] | None = None,
         avoid_frames: set[str] = frozenset(), ok=None, style: str = "") -> Evening:
    """안 쓴 재료 중 첫 장(본글)도 처음 나오는 것을 고른다.
    facts: 이번 주에 쓴 (대상, 기간) → [(주제, +/-)]. today: 오늘 이미 나온 대상. avoid_frames: 어제 이 시간대에 쓴 틀.
    ok: 한 주 다양성 규칙(같은 주제·대상 반복 금지). 그 시간대 글 틀(style) 안에서 다양성 규칙을 지키는 것 → 틀만 지키는 것 → 아무거나 순."""
    facts, today = facts or {}, today or set()
    cands = list(cands)
    tries = [(True, True), (True, False), (False, True), (False, False)] if style else [(False, True), (False, False)]
    for same_style, strict in tries:
        for c in cands:
            if same_style and c.style != style:
                continue
            if c.key in used or "first:" + c.parts[0] in used:
                continue
            if clash(c, facts) or c.frame in avoid_frames or any(f[0] in today for f in c.facts):
                continue
            if strict and ok and not ok(c):
                continue
            return c
    return cands[0]


def evening(day: dt.date, used: set[str]) -> Evening:
    return pick(evening_candidates(day, used), used)


@dataclass
class Day:
    date: dt.date
    morning: Morning
    threads: list[tuple[str, str, Evening]]   # (시간대, 시각, 글)

    @property
    def evening(self) -> Evening:
        """18:00 대표 글 (캡처 영상으로도 올린다)."""
        return next(e for s, _, e in self.threads if s == "저녁")

    def __iter__(self):   # d, m, e = day
        return iter((self.date, self.morning, self.evening))


def plan(start: dt.date, days: int, used: set[str] | None = None) -> list[Day]:
    """며칠치를 한 번에 고른다. 앞에서 고른 재료는 뒤에서 다시 쓰지 않는다.
    한 주 안에 같은 대상을 좋다·조심 양쪽으로 쓰지 않고, 같은 날 같은 띠·일간을 두 번 쓰지 않고,
    같은 시간대에 어제와 같은 틀을 쓰지 않는다."""
    used = set(used or ())
    out = []
    facts: dict = {}
    frames: dict[str, str] = {}
    lists: list[tuple[int, str]] = []      # (날, 주제): 목록 글 주제는 이틀 연속, 한 주에 세 번 쓰지 않는다
    ones: list[tuple[int, str]] = []       # (날, 대상): 한 장 글 대상은 한 주에 한 번만
    topics: list[tuple[int, str]] = []     # (날, 주제): 도화도르식 틀 글 주제는 한 주에 한 번만
    promises: list[tuple[int, str]] = []   # (날, 본글 줄): 같은 약속 줄을 한 주에 두 번 쓰지 않는다

    def ok(i: int):
        def f(c: Evening) -> bool:
            if c.is_list and c.kind:
                ks = [k for j, k in lists if i - j < 7]
                if c.kind in [k for j, k in lists if j == i - 1] or ks.count(c.kind) >= (1 if c.kind == "care" else 2):
                    return False
            if c.key.startswith(("jone-", "jstem-", "dohwa-d-", "dohwa-s-")):
                if c.facts[0][0] in [a for j, a in ones if i - j < 7]:
                    return False
            if c.topic and c.topic in [x for j, x in topics if i - j < 7]:
                return False
            return True
        return f

    for i in range(days):
        d = start + dt.timedelta(days=i)
        m = morning(d, used)
        used.add(m.key)
        ths, today, new_frames = [], set(), {}
        for s, t, _st in sorted(THREAD_SLOTS, key=lambda x: x[0] != "저녁"):   # 대표 글(저녁)을 먼저 고른다
            avoid = {frames[s]} if s in frames and _st == "jangin" else set()
            e = pick(slot_candidates(d, s, used), used, facts, today, avoid, ok(i), _st)
            _vary_promise(e, [x for j, x in promises if i - j < 7])
            promises += [(i, x) for x in e.pages[0]]
            used |= {e.key, "first:" + e.parts[0]}
            if e.is_list and e.kind:
                lists.append((i, e.kind))
            if e.key.startswith(("jone-", "jstem-", "dohwa-d-", "dohwa-s-")):
                ones.append((i, e.facts[0][0]))
            if e.topic:
                topics.append((i, e.topic))
            for subj, pk, kind, sign in e.facts:
                facts.setdefault((subj, pk), []).append((kind, sign))
                today.add(subj)
            new_frames[s] = e.frame
            ths.append((s, t, e))
        frames = new_frames
        ths.sort(key=lambda x: x[1])
        out.append(Day(d, m, ths))
    _teasers(out)
    return out


def _vary_promise(e: Evening, recent: list[str]) -> None:
    """본글의 약속 줄(promise)이 이번 주에 이미 나왔으면 같은 주제의 다른 줄로 바꾼다 (뜻은 같고 말만 다르다)."""
    if not e.kind or e.style != "jangin":
        return
    opts = LB["promise"].get(e.kind, [])
    p1 = e.pages[0]
    for i, x in enumerate(p1):
        if x in opts and x in recent:
            alt = next((o for o in opts if o not in recent), None)
            if alt:
                e.pages[0] = p1[:i] + [alt] + p1[i + 1:]
            return


ONE_NOUN = {"money": "돈", "love": "인연", "work": "일", "help": "귀인"}
SLOT_SAY = {"07:30": "아침 7시 반", "12:00": "낮 12시", "15:00": "오후 3시", "18:00": "저녁 6시", "21:00": "밤 9시", "23:00": "밤 11시"}


def title_of(e: Evening) -> str:
    """본글 제목 (번호 목록 앞 줄들)."""
    ls = []
    for x in e.pages[0]:
        if not x.strip() or re.match(r"^\d\. ", x):
            break
        ls.append(x.strip("<>").rstrip(","))
    return " ".join(ls)


def _teasers(days: list[Day]) -> None:
    """사주장인식 끝장에 다음 사주장인식 글 예고 한 줄 (팔로우 이유, 실제로 잡힌 글만). 같은 주 안에서만."""
    seq = [(d.date, t, e) for d in days for _, t, e in d.threads if e.style == "jangin"]
    for j, ((d0, t0, e0), (d1, t1, e1)) in enumerate(zip(seq, seq[1:])):
        when = ("오늘 " if d1 == d0 else "내일 ") + SLOT_SAY[t1]
        if d1 - d0 > dt.timedelta(days=1):
            continue
        if e1.key.startswith(("jone-", "jstem-")):
            subj, pk = e1.facts[0][0], e1.facts[0][1]
            who = ddi(subj) if subj in ZODIAC_ANIMALS else f"{STEM_NAMES[STEMS.index(subj)].split('(')[0]} 일간"
            what = f"{who} {int(pk[5:])}월 {ONE_NOUN[e1.kind]} 이야기"
        else:
            what = f"'{title_of(e1)}'"
        e0.pages[-1] = e0.pages[-1] + ["", f"{when}엔 {what} 올려요", LB["follow"][j % len(LB["follow"])]]


def all_text(m: Morning, *es: Evening) -> str:
    parts = [json.dumps(m.texts(), ensure_ascii=False), *[json.dumps(e.texts(), ensure_ascii=False) for e in es], " ".join(m.title),
             json.dumps(m.data, ensure_ascii=False)]
    return "\n".join(parts)
