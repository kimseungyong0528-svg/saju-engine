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
                    "이런 오행 이야기 계속 올려요\n놓치기 싫으면 팔로우 해 두세요"]}


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


def morning(day: dt.date, used: set[str], fmt: str = "") -> Morning:
    fmt = fmt or rules.morning_format(day)
    cands = list(morning_candidates(fmt, day))
    return next((c for c in cands if c.key not in used), cands[0])


def _rank_lines(rows: list[Row], upto: int = 12) -> list[str]:
    return [f"{r.rank}위 {ddi(r.ddi)} ({years_short(r.ddi)}년생)" for r in rows[:upto]]


FOLLOW_AM = "띠별 운세 계속 올려요. 놓치기 싫으면 팔로우 해 두세요."


def _am(cap: str) -> dict[str, dict]:
    """아침 캡션: 모든 형식에 팔로우 말 (유튜브는 '구독'으로). 사장님 2026-11-01."""
    if "팔로우" not in cap:
        cap = cap.replace("\n\n#", f"\n\n{FOLLOW_AM}\n\n#", 1)
    return {"yt": cap.replace("팔로우 해 두세요", "구독해 두세요"), "ig": cap}


def morning_texts(m: Morning) -> dict[str, dict]:
    tags = "#사주 #운세 #띠별운세 #띠순위 #운명서재"
    if m.fmt == "sinbi":
        d = dt.date.fromisoformat(m.data["date"])
        head = f"{d.month}월 {d.day}일 띠별 운세"
        body = "\n".join(f"{ddi(a)}: {t}" for a, t in m.data["text"].items())
        lines = [head, "", body, "", f"오늘 일진은 {m.data['ganzhi']}일이에요. 띠 글자와 오늘 글자의 관계로 풀었어요.", "",
                 "저장해 두고 오늘 하루 한 번 더 보세요.", FOLLOW_AM, "", tags]
        cap = "\n".join(lines)
        return {"youtube": {"제목": f"{head} | 오늘의 운세 #shorts", "설명": _am(cap)["yt"]},
                "instagram-reel": {"캡션": _am(cap)["ig"]}, "facebook-reel": {"캡션": _am(cap)["ig"]}}
    if m.fmt == "forceteller":
        e = m.data["el"]
        head = " ".join(x.replace("<em>", "").replace("</em>", "") for x in m.data["head"])
        cap = "\n".join([head, ""] + [s.replace("\n", " ") for s in m.data["say"]] + ["", f"#오행 #{e} #사주 #궁합 #운명서재"])
        return {"youtube": {"제목": f"{head} | 오행 쉽게 보기 #shorts", "설명": _am(cap)["yt"]},
                "instagram-reel": {"캡션": _am(cap)["ig"]}, "facebook-reel": {"캡션": _am(cap)["ig"]}}
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
    return {"youtube": {"제목": yt[:100], "설명": _am(cap)["yt"]}, "instagram-reel": {"캡션": _am(cap)["ig"]},
            "facebook-reel": {"캡션": _am(cap)["ig"]}}


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
        return [space_long_lists("\n".join(p).strip()) for p in self.shown]

    @property
    def shown(self) -> list[list[str]]:
        """사람에게 보이는 장들 (이모지 규칙을 입힌 것). 스레드 글과 캡처 영상이 같은 것을 쓴다."""
        return emojify(self)

    def texts(self) -> dict[str, dict]:
        n = len(self.parts)
        th = {f"{i}/{n}": t for i, t in enumerate(self.parts, 1)}
        cap = "\n\n".join(self.parts) + "\n\n#사주 #운세 #띠별운세 #사주스레드 #운명서재"
        return {"threads": th, "instagram-reel": {"캡션": cap[:2100]}}


NUM_LINE = re.compile(r"^(\d+\.|[❶❷❸❹❺❻❼❽❾❿])\s")
LONG_ITEM = 40  # 번호 줄의 평균 글자 수가 이보다 길면 '긴 글'이다 (사장님 2026-11-01 "존나 긴 글만")


def space_long_lists(text: str) -> str:
    """긴 번호 목록은 번호 사이에 빈 줄을 하나씩 넣는다 (사장님 2026-11-01 "각 번호 사이에 엔터 한번").
    '1. 1985년생 소띠' 처럼 짧은 번호 목록은 붙여 둔다 ("번호가 짧은건 여백 주지 말고 존나 긴 글만")."""
    lines = text.split("\n")
    out, i = [], 0
    while i < len(lines):
        if not NUM_LINE.match(lines[i]):
            out.append(lines[i])
            i += 1
            continue
        j = i
        while j < len(lines) and NUM_LINE.match(lines[j]):
            j += 1
        run = lines[i:j]
        if sum(map(len, run)) / len(run) > LONG_ITEM:
            for k, x in enumerate(run):
                out += ([""] if k else []) + [x]
        else:
            out += run
        i = j
    return "\n".join(out)


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


def glyph(p: Period, e: int) -> str:
    """이 달(해) 기운이 위 글자(천간)에서 온 건지 밝힌다. 다른 글에서 '11월은 수(水) 기운 달'이라 했는데
    여기서 '토(土) 기운'이라 하면 어긋나 보인다 (제1조항, 심사 2026-11-01)."""
    if e == STEM_ELEMENT[p.stem] and e != BRANCH_ELEMENT[p.branch]:
        return f"위 글자 {_stem(p.stem)}의 "
    return ""


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
            return [f"{p.label} {p.ganzhi}의 {glyph(p, e)}{ELEMENTS[e]}({EL_HANJA[ELEMENTS[e]]}) 기운은",
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
            h = B["rel"].get(rel, {}).get("hanja")   # 파(破)·해(害)처럼 한자와 쉬운 뜻을 붙인다 (달 이름 해(亥)와 헷갈리지 않게)
            word = BRANCHES[b] + BRANCHES[Y.branch] + rel + (f"({BRANCHES_HANJA[b]}{BRANCHES_HANJA[Y.branch]}{h})" if h else "")
            return f"- 올해 {yn}엔 {ira(word)} {v[n % len(v)]}"
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
    if len(ls) == 3:   # 십신은 띠 글자의 오행을 기준으로 본다는 걸 먼저 밝힌다 (전문성·신뢰 심사 2026-11-01)
        bi = BRANCHES.index(r.branch)
        el = ELEMENTS[BRANCH_ELEMENT[bi]]
        return [f"- {ddi(r.ddi)} 글자 {_branch(bi)}는 {el}({EL_HANJA[el]}) 기운이에요".replace(f"{_branch(bi)}는", josa(_branch(bi), "은", "는")),
                f"- {ls[0].replace(' 기운은', ' 기운이')} {ls[1]}", f"- {ls[2]}"]
    return [f"- {ls[0]}"]


def basis_stem(kind: str, p: Period, r: "StemRow", w: tuple) -> list[str]:
    _w, t, e, g = w
    short = STEM_NAMES[r.stem].split("(")[0]
    if t == "천간합":
        a, c = sorted((r.stem, p.stem))
        return [f"- {p.label} {josa(_stem(p.stem), '과', '와')} {short} 일간이 {STEMS[a]}{STEMS[c]}합(合)이에요",
                f"- {LB['rel_mean'].get(kind, {}).get('천간합', B['stem_hap']['mean'])}"]
    return [f"- {'이 해' if p.year else '이 달'} {glyph(p, e)}{ELEMENTS[e]}({EL_HANJA[ELEMENTS[e]]}) 기운이 {short} 일간에게 {copula(f'{g}({GH[g]})')}", f"- {t}"]


def next_lines(kind: str, ny: Period, place: int, total: int, unit: str, n: int = 0) -> tuple[list[str], str]:
    """다음 해에도 이어지는지 (엔진 순위 그대로). 돌려주는 부호는 글의 사실(facts)에 들어간다."""
    name = KINDS[kind]["name"]
    if kind == "care":
        if place <= 4:
            return [f"- {ny.long}에도 조심할 {'띠' if unit == '띠' else '일간'} {total}{unit} 중 {place}위예요", "- 큰 결정은 내년에도 한 번 더 보고 하세요"], "-"
        if place > total // 2:
            return [f"- {ny.long}엔 조심할 {'띠' if unit == '띠' else '일간'} 순위에서 {place}위로 빠져요", "- 이 달만 잘 넘기면 숨통이 트여요"], ""
        return [f"- {ny.long}엔 조심할 {'띠' if unit == '띠' else '일간'} 순위에서 {place}위로 보통이에요", "- 무리만 안 하면 괜찮아요"], ""
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
    end = [q[3], same, rest, f"{K['where']} 달라요", "그건 따로 봐야 알아요", "", *burn, "", LB["close"][n % len(LB["close"])],
           "", *LB["find_me"][n % 3]]
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


# 겹경사 카드의 좋은 일 두 줄은 들어오는 위 글자가 그 해 천간에게 무슨 십신인지로 고른다 (사주 검수원 2026-11-01:
# 정(丁)이 무(戊)를 생하면 인성이라 '문서·도움'이 맞고 '직함'(관성)은 틀림). sipsin_fact 의 십신 뜻 표와 같다.
DOUBLE_GOOD = {"인성": ["문서와 합격 소식이 오기 쉬워요", "도와주는 사람이 생기기 쉬워요", "배우던 일이 자격으로 남기 쉬워요"],
               "관성": ["직함이 오르고 인정받기 쉬워요", "맡은 자리에서 이름이 불리기 쉬워요", "미뤄진 결정에 답이 나오기 쉬워요"],
               "재성": ["계약서에 도장이 찍히기 쉬워요", "받을 돈이 들어오기 쉬워요", "가족에게 반가운 소식이 오기 쉬워요"],
               "식상": ["준비한 일이 결과물로 나오기 쉬워요", "하고 싶던 말을 꺼내기 쉬워요", "가족에게 반가운 소식이 오기 쉬워요"],
               "비겁": ["같이 뛰어 줄 사람이 생기기 쉬워요", "가족에게 반가운 소식이 오기 쉬워요", "오래 못 본 친구가 힘이 되기 쉬워요"]}


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
                    "god": _god(STEM_ELEMENT[s], STEM_ELEMENT[p.stem]),
                    "branch": f"{josa(_branch(p.branch), '과', '와')} {_branch(b)}{'이' if _batchim(BRANCHES[b]) else '가'} {hit}이에요",
                    "both": score == 2, "score": score + (1 if hit == "육합" else 0)})
    out.sort(key=lambda d: (-d["score"], -d["year"]))
    return out[:3]


DOUBLE_SAY = ["좋은 일이 한 번에 두 개씩 겹쳐 와요.", "기다리던 소식이 한 해에 두 번 찾아와요.", "한 가지 풀리면 다른 하나도 따라 풀려요."]


def double(p: Period, n: int) -> Evening | None:
    ys = double_years(p)
    if len(ys) < 2:
        return None
    d = start_label(p)
    p1 = [f"<{p.label}, 겹경사 터지는 사람>", ""] + [f"{i}. {x['year']}년생 {ddi(x['ddi'])}" for i, x in enumerate(ys, 1)]
    p1 += ["", "이 해에 태어났다면 미리 축하드려요.", DOUBLE_SAY[n % len(DOUBLE_SAY)]]
    gz = f"{STEMS[p.stem]}{BRANCHES[p.branch]}({STEMS_HANJA[p.stem]}{BRANCHES_HANJA[p.branch]})"
    p2 = ["겹경사인 이유", "", f"{d}부터 들어오는 {gz} 두 글자가", "태어난 해 두 글자와", "둘 다 좋게 만나요"]   # reason_short
    cards = []
    for i, x in enumerate(ys):
        g = _rot(DOUBLE_GOOD[x["god"]], n + i)[:2]
        cards.append([f"{x['year']}년생 {ddi(x['ddi'])} - {x['gz']}년생", "", "- 천간", x["stem"], "", "- 지지", x["branch"], "",
                      *(["위 글자도 손잡고, 아래 글자도 손잡아요", "이걸 천합지합이라고 해요. 겹경사 중에서도 제일 센 자리예요"] if x["both"] else
                        ["위 글자는 내 쪽으로 힘을 보태 주고, 아래 글자는 손을 잡아요", "생(生)은 기운을 보태 준다는 뜻이에요"]), "",
                      f"- {g[0]}", f"- {g[1]}"])
    by: dict[str, list[int]] = {}
    for x in ys:
        by.setdefault(x["ddi"], []).append(x["year"])
    same = ["※ 같은 띠인데 왜 나는 아닐까"] + [f"같은 {ddi(a)}라도 {', '.join(map(str, v))}년생이에요" for a, v in by.items()]
    same += ["같은 띠라도 천간이 다른 해에 태어났으면", "겹경사는 아니에요", "", "좋은 일이 겹칠수록", "계약서와 약속은 한 번 더 읽고 도장 찍으세요"]
    end = ["※ 경사는 어디로 올까", "태어난 해는 여덟 글자 중 두 글자예요", "나머지 여섯 글자에 따라", "경사가 어디로 오는지 달라요", "그건 따로 봐야 알아요", "",
           "이 겹경사가 돈으로 올지 사람으로 올지", "그간 버틴 고생은 언제 보상받을지", "", LB["close"][n % len(LB["close"])], "", *LB["find_me"][n % 3]]
    return Evening(f"jangin-double-{p.key}", "jangin", [p1, p2, *cards, same, end], facts=tuple((x["ddi"], p.key, "double", "+") for x in ys))


GOD_OF = {"E": "비겁", "M": "식상", "K": "재성", "P2": "관성", "C": "인성"}   # 이 달 기운(E)이 그 일간에게 무엇인지


def dohwa_month_lines(p: Period) -> list[str]:
    """이 달 기운 한 줄, 같은 사실을 말투만 바꿔서 (같은 줄이 한 주에 몰리지 않게 _vary_lines 가 돌려 쓴다)."""
    E = ELEMENTS[BRANCH_ELEMENT[p.branch]]
    e, b = f"{E}({EL_HANJA[E]})", _branch(p.branch)
    return [f"{p.label} {p.ganzhi}월은 {b}, {e} 기운이 센 달이에요",
            f"{p.label}은 {p.ganzhi}월이라 {b} 글자의 {e} 기운이 세요".replace(f"{p.label}은", josa(p.label, "은", "는")),
            f"{p.label}의 달 글자는 {copula(b)}. {e} 기운이에요",
            f"사주 달력으로 {p.label}은 {p.ganzhi}월이에요. {e} 기운이 들어와요".replace(f"{p.label}은", josa(p.label, "은", "는"))]


def _dohwa_tip_why(topic: str, p: Period, E: str, els: dict, n: int) -> list[str]:
    """도화도르식 팁 글 밑 사주 근거 (사장님 2026-11-01 "이게 끝임?"): 이 달 기운 → 그 사람에게 무엇인지 → 쉬운 뜻."""
    month = dohwa_month_lines(p)[0]
    who = topic.split(":")[0]
    if who in GOD_OF:
        X, g = els[who], GOD_OF[who]
        ls = [month, f"{E}({EL_HANJA[E]})는 {X}({B['elements'][X]['stems']}) 일간에게 {copula(f'{g}({GH[g]})')}".replace(f"{E}({EL_HANJA[E]})는", josa(f"{E}({EL_HANJA[E]})", "은", "는")),
              GOD_PLAIN[g][n % 2]]
    elif topic == "lack":
        ls = [month, f"태어날 때 받은 여덟 글자 안에 없던 {E}({EL_HANJA[E]}) 기운이 이 달엔 바깥에서 들어와요", "모자란 걸 채워 주니까 머리가 맑아지고 결정이 쉬워져요"]
    elif topic == "much":
        ls = [month, f"원래 많은 {E}({EL_HANJA[E]})에 바깥에서 들어오는 {E}({EL_HANJA[E]})가 더해져요", "그 기운이 가진 장점이 더 크게 드러나요"]
    elif topic == "good":
        ls = [month, "용신은 내 사주의 균형을 맞춰 주는 기운이에요", f"그 {E}({EL_HANJA[E]})가 이 달엔 바깥에서 들어오니까 막혔던 일이 풀려요"]
    elif topic == "jeol":
        ls = ["사주 달력은 1일이 아니라 절기에 달이 바뀌어요", f"{start_label(p)}부터 {p.ganzhi}월이고, {_branch(p.branch)}는 {E}({EL_HANJA[E]}) 기운이에요",
              "물(수) 기운 달은 생각이 많아지기 쉬워서, 먼저 움직인 사람이 앞서가요" if E == "수" else "달 기운이 바뀔 때 먼저 움직인 사람이 앞서가요"]
    else:
        return []
    return ["", DOHWA_WHY_HEAD[n % len(DOHWA_WHY_HEAD)], *ls]


NUMS = "❶❷❸❹❺"


def dohwa_list(day: dt.date, x: int, n: int) -> Evening:
    """도화도르식 목록 글 (레퍼런스 '○ 많은 사주가 해두면 좋은 것들(리마인드용) ❶~❺'): 이 달 기운이 그 오행에게 무슨 십신인지로 할 일 5개.
    사장님 2026-11-01 '얼마나 레퍼 따라한지' — 원문처럼 목록·근거·생활 예시를 꽉 채운다."""
    y, m = target_month(day)
    p = month_period(y, m)
    ei = BRANCH_ELEMENT[p.branch]
    E, X = ELEMENTS[ei], ELEMENTS[x]
    g = _god(x, ei)
    acts = B["dohwa_acts"][g]
    pick = [acts[(n + k) % len(acts)] for k in range(5)]
    # 사주 검수원 2026-11-01: 십신은 일간 기준이다. '사주에 토 많은 분'에게 수가 재성이라고 하면 틀린다 → 일간으로 콕 집는다.
    body = [f"{X}({B['elements'][X]['stems']}) 일간 분들 주목", f"{p.label}처럼 {E}({EL_HANJA[E]}) 기운 센 달에 해 두면 좋은 것들(리마인드용)🟡",
            *[f"{NUMS[k]} {a}" for k, a in enumerate(pick)], "",
            (f"같은 {E}({EL_HANJA[E]})끼리라 {X}({B['elements'][X]['stems']}) 일간에게 {copula(f'{g}({GH[g]})')}" if E == X else
             f"{E}({EL_HANJA[E]})는 {X}({B['elements'][X]['stems']}) 일간에게 {copula(f'{g}({GH[g]})')}".replace(f"{E}({EL_HANJA[E]})는", josa(f"{E}({EL_HANJA[E]})", "은", "는"))),
            GOD_PLAIN[g][n % 2]]
    reply = [fill(r, p=p.label) for r in B["dohwa_reply"][n % len(B["dohwa_reply"])]]
    return Evening(f"dohwa-list-{X}-{p.key}", "dohwa", [body, reply], topic=f"list-{X}")


def dohwa_ten(day: dt.date, n: int) -> Evening:
    """도화도르식 10일간 한 줄 스포 (레퍼런스 '갑목[甲] — …' 목록): 일간마다 이 달 십신에 맞는 할 일 하나."""
    y, m = target_month(day)
    p = month_period(y, m)
    ei = BRANCH_ELEMENT[p.branch]
    E = ELEMENTS[ei]
    body = [f"{p.label} 일간별로 하나씩만 미리 스포하자면,", f"{start_label(p)}부터 {p.ganzhi}월, 아래 글자 {_branch(p.branch)}의 {E}({EL_HANJA[E]}) 기운으로 봤어요", ""]
    for s_ in range(10):
        g = _god(STEM_ELEMENT[s_], ei)
        act = B["dohwa_acts"][g][(n + s_) % len(B["dohwa_acts"][g])].split(". ")[0]
        body.append(f"{STEMS[s_]}{ELEMENTS[STEM_ELEMENT[s_]]}[{STEMS_HANJA[s_]}] — {act} ({g} 달)")
    body += ["", "인성은 나를 받쳐 주는 기운, 관성은 자리 기운, 재성은 돈 기운,", "식상은 표현 기운, 비겁은 내 편 기운이에요"]
    reply = [fill(r, p=p.label) for r in B["dohwa_reply"][(n + 2) % len(B["dohwa_reply"])]]
    return Evening(f"dohwa-ten-{p.key}", "dohwa", [body, reply], topic="ten")


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
    body = body + _dohwa_tip_why(topic, p, E, {"C": C, "K": K, "P2": P2, "M": M, "E": E}, t)
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
    end = [qk[3], same, rest, f"{B['kinds'][kind]['where']} 달라요", "그건 따로 봐야 알아요", "", *burn, "", LB["close"][n % len(LB["close"])],
           "", *LB["find_me"][n % 3]]
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
    why = _dohwa_why(basis_ddi(kind, p, r, lead), n)
    return Evening(f"dohwa-d-{kind}-{a}-{p.key}", "dohwa", [line.split("|") + why, reply], facts=((a, p.key, kind, "+"),))


DOHWA_WHY_HEAD = ["사주로 보면", "왜 그러냐면", "사주 근거는 이거예요", "이유가 있어요", "사주로 풀면 이래요"]


GOD_PLAIN = {   # 십신을 처음 보는 사람도 알게 한 줄로 (쉬운 설명 심사). 같은 줄이 한 주에 몰리지 않게 두 가지씩
    "비겁": ["비겁은 나와 같은 기운이라, 같이 뛰어 줄 사람이 늘어요", "비겁(比劫)은 내 편 기운이에요. 혼자 하던 일에 손이 붙어요"],
    "식상": ["식상은 내가 밖으로 내보내는 기운이라, 말·표현·새 일이 술술 나와요", "식상(食傷)은 내 안에 있던 걸 꺼내는 기운이에요. 하고 싶은 말이 쉽게 나와요"],
    "재성": ["재성은 내가 다스리는 기운이라, 한 만큼 돈과 결과로 남아요", "재성(財星)은 손에 쥐는 기운이에요. 움직인 만큼 통장에 남아요"],
    "관성": ["관성은 나를 이끄는 기운이라, 자리와 맡을 일이 따라와요", "관성(官星)은 자리를 주는 기운이에요. 맡는 일이 늘고 이름이 알려져요"],
    "인성": ["인성은 나를 살려 주는 기운이라, 공부·문서·도와주는 어른이 붙어요", "인성(印星)은 나를 받쳐 주는 기운이에요. 배우는 일이 잘 들어오고 챙겨 주는 사람이 생겨요"],
}


def _dohwa_why(basis: list[str], n: int, lead: str = "") -> list[str]:
    """도화도르식 본글 밑 사주 근거 (사장님 2026-11-01 "디테일한 설명 없어?"):
    빈 줄 + 머리 한 줄 + 엔진 근거(내 글자 기운 → 이 달 기운이 나에게 무엇인지 → 그 십신 뜻) 최대 3줄."""
    ls = [b.removeprefix("- ") for b in basis]
    g = next((k for k in GOD_PLAIN if any(f"{k}(" in x for x in ls)), "")
    if g:   # 십신 근거: 십신 이름이 나온 줄까지만 두고, 그 뜻을 쉬운 말로 붙인다
        cut = next(i for i, x in enumerate(ls) if f"{g}(" in x)
        ls = ls[:cut + 1] + [GOD_PLAIN[g][n % 2]]
    ls = ([lead] if lead else []) + ls
    return ["", DOHWA_WHY_HEAD[n % len(DOHWA_WHY_HEAD)], *ls[:3]] if ls else []


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
    el = ELEMENTS[STEM_ELEMENT[s]]
    why = _dohwa_why(basis_stem(kind, p, r, ws[0])[:1], n + s,
                     lead=f"{STEM_NAMES[s].split('(')[0]} 일간은 태어난 날의 글자가 {el}({EL_HANJA[el]}) 기운이에요")
    return Evening(f"dohwa-s-{kind}-{s}-{p.key}", "dohwa", [line.split("|") + why, reply], facts=((STEMS[s], p.key, kind, "+"),))


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
        # 원문 상위 글처럼 목록 글(❶~❺, 10일간 스포)을 팁 글 사이사이에 넣는다 (사장님 2026-11-01 레퍼런스 심사)
        lists = [lambda: dohwa_ten(day, n)] + [(lambda x=x: dohwa_list(day, x, n)) for x in _rot(list(range(5)), n)]
        for i, t in enumerate(_rot(list(range(len(B["dohwa"]))), n // 3 + off)):
            if i % 2 == 0 and lists:
                yield lists.pop(0)()
            yield dohwa(day, t)
        for f in lists:
            yield f()

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


def salgu_list(i: int) -> Evening:
    """살구식 정리본 (레퍼런스 '남자복 좋은 여자 사주 특징 정리본 (살구 ver.)' 틀): 짧은 줄 8개, 주제 하나."""
    L = B["salgu_lists"][i]
    p1 = [L["title"], ""] + [f"{k}. {x}" for k, x in enumerate(L["items"], 1)]
    end = B["salgu_list_end"][i % len(B["salgu_list_end"])]   # 정리본 끝맺음 ('○탄'이 아니라서 따로)
    return Evening(f"salgu-list-{i}", "salgu", [p1, list(end)], topic=f"salgu-{L['theme']}")


def salgu_pool(day: dt.date, used: set[str]):
    n_tan = sum(1 for k in used if k.startswith("salgu-") and k.split("-")[1].isdigit()) + 1
    n_list = sum(1 for k in used if k.startswith("salgu-list-"))
    if (n_tan + n_list) % 6 == 0:   # 여섯 번에 한 번은 정리본 (레퍼런스 원문 틀, 심사 2026-11-01)
        for i in range(len(B["salgu_lists"])):
            if f"salgu-list-{i}" not in used:
                yield salgu_list(i)
                break
    yield salgu_tan(day, n_tan)


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
    # 그래도 없으면 쓴 적 없는 재료부터 (같은 글이 두 번 나오는 것보다 낫다). 제1조항 겹침(clash)은 끝까지 지킨다.
    for c in cands:
        if c.key not in used and "first:" + c.parts[0] not in used and not clash(c, facts):
            return c
    return cands[0]


def evening(day: dt.date, used: set[str]) -> Evening:
    return pick(evening_candidates(day, used), used)


@dataclass
class Day:
    date: dt.date
    morning: Morning
    threads: list[tuple[str, str, Evening]]   # (시간대, 시각, 글)
    video2: Morning | None = None             # 저녁 영상 (사장님 2026-11-01 "릴스는 쇼츠처럼 2개")

    @property
    def evening(self) -> Evening:
        """18:00 대표 글 (캡처 영상으로도 올린다)."""
        return next(e for s, _, e in self.threads if s == "저녁")

    def __iter__(self):   # d, m, e = day
        return iter((self.date, self.morning, self.evening))


def _negative(e: Evening) -> bool:
    return e.kind == "care" or any(sign == "-" for _, _, _, sign in e.facts[:1]) and e.key.startswith(("jone-", "jstem-"))


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
    negs: list[tuple[int, str]] = []       # (날, 'one'|'list'): 사주장인식 조심 글
    onekinds: list[tuple[int, str]] = []   # (날, 주제): 한 장 글 주제

    def ok(i: int):
        def f(c: Evening) -> bool:
            if c.is_list and c.kind:
                ks = [k for j, k in lists if i - j < 7]
                if c.kind in [k for j, k in lists if j == i - 1] or ks.count(c.kind) >= (1 if c.kind == "care" else 2):
                    return False
            if c.key.startswith(("jone-", "jstem-", "dohwa-d-", "dohwa-s-")):
                if c.facts[0][0] in [a for j, a in ones if i - j < 7]:
                    return False
            if c.style == "jangin" and _negative(c):
                # 조심 글은 한 주에 두 번까지, 한 장 조심 글은 한 번만 (심사 2026-11-01: 조심 글이 많으면 계정이 무섭게 느껴진다)
                ng = [k for j, k in negs if i - j < 7]
                if len(ng) >= 2 or (c.key.startswith(("jone-", "jstem-")) and "one" in ng):
                    return False
            if c.key.startswith(("jone-", "jstem-")) and c.kind in [k for j, k in onekinds if i - j < 3]:
                return False   # 한 장 글은 같은 주제를 사흘 안에 다시 쓰지 않는다 (같은 틀이 되풀이되지 않게)
            if c.topic and c.topic in [x for j, x in topics if i - j < 7]:
                return False
            return True
        return f

    for i in range(days):
        d = start + dt.timedelta(days=i)
        m = morning(d, used)
        used.add(m.key)
        # 저녁 영상은 아침과 다른 형식. 두 칸 뒤 형식을 쓰면 아침·저녁·다음 날 아침이 서로 겹치지 않는다.
        m2 = morning(d, used, fmt=rules.morning_format(d + dt.timedelta(days=2)))
        used.add(m2.key)
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
            if e.style == "jangin" and _negative(e):
                negs.append((i, "one" if e.key.startswith(("jone-", "jstem-")) else "list"))
            if e.key.startswith(("jone-", "jstem-")):
                onekinds.append((i, e.kind))
            for subj, pk, kind, sign in e.facts:
                facts.setdefault((subj, pk), []).append((kind, sign))
                today.add(subj)
            new_frames[s] = e.frame
            ths.append((s, t, e))
        frames = new_frames
        ths.sort(key=lambda x: x[1])
        out.append(Day(d, m, ths, m2))
    _teasers(out)
    _follow_all(out)
    _vary_lines(out)
    _fresh_acts(out)
    return out


# 이모지 규칙 (사장님 2026-11-01 "띠는 이모지로 다 넣고 좋고 나쁨도 저렇게, 첫 글 시작하기 전에도 잘 보이는 이모지 하나. 전부 못박아둬")
# 번호는 숫자 글자 그대로 둔다("1."), 숫자 이모지(1️⃣)는 쓰지 않는다.
DDI_EMOJI = {"쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰", "용": "🐲", "뱀": "🐍",
             "말": "🐴", "양": "🐑", "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"}
ELEM_EMOJI = {"목": "🌳", "화": "🔥", "토": "⛰️", "금": "🪙", "수": "💧"}
KIND_EMOJI = {"love": "💕", "money": "💰", "work": "💼", "help": "🤝", "study": "📚", "move": "🧳", "care": "🌙"}
GOOD, BAD = "🟢", "🔴"
BAD_HEAD = ("조심", "속도 줄", "멈추")


def _is_emoji(ch: str) -> bool:
    return ord(ch[0]) >= 0x2190 and not ("\uac00" <= ch[0] <= "\ud7a3") and ch[0] not in "※←→↑↓"


def lead_emoji(e: Evening) -> str:
    """첫 줄 앞에 붙일 이모지: 글 종류에 어울리는 것 하나."""
    k = e.key
    if k.startswith("salgu-list"):
        return "📌"
    if k.startswith("salgu"):
        return "🔮"
    if k.startswith("jangin-double"):
        return "🎉"
    if k.startswith("dohwa-list-"):
        return ELEM_EMOJI.get(k.split("-")[2], "💡")
    if k.startswith("dohwa-ten"):
        return "✨"
    if k.startswith("dohwa"):
        return "💡"
    return KIND_EMOJI.get(e.kind, "✨")


DDI_LABEL = re.compile(r"^(\d+\.\s|.*?년생\s)?(원숭이|호랑이|돼지|토끼|쥐|소|용|뱀|말|양|닭|개)띠")


def _ddi(line: str) -> str:
    """띠가 이름표 자리(줄 맨 앞, '1.' 다음, '○○년생' 다음)에 오면 띠 이모지를 붙인다. 문장 중간에는 붙이지 않는다(읽기 어려움)."""
    mo = DDI_LABEL.match(line)
    if not mo:
        return line
    i = mo.start(2)
    return line[:i] + f"{DDI_EMOJI[mo.group(2)]} " + line[i:]


def emojify(e: Evening) -> list[list[str]]:
    """보여 줄 글: 띠 이름 앞에 띠 이모지, 좋은·조심 신호 머리에 🟢·🔴, 첫 줄 앞에 글에 어울리는 이모지 하나.
    e.pages(재료·검사용 원문)는 그대로 두고, 스레드 글(parts)과 캡처 영상이 이것을 쓴다."""
    pages = [[_ddi(x) for x in p] for p in e.pages]
    for p in pages:
        for i, x in enumerate(p):
            if x.startswith("※ ") and ("신호" in x or "생기는 일" in x or "멈추" in x):
                p[i] = (BAD if any(w in x for w in BAD_HEAD) else GOOD) + x[1:]
    if pages and pages[0] and pages[0][0] and not _is_emoji(pages[0][0].lstrip()[0]):
        pages[0][0] = f"{lead_emoji(e)} {pages[0][0]}"
    return pages


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
    """사주장인식 끝장에 다음 사주장인식 글 예고 한 줄 (시간·날짜는 약속하지 않는다, 사장님 2026-11-01) (팔로우 이유, 실제로 잡힌 글만). 같은 주 안에서만."""
    seq = [(d.date, t, e) for d in days for _, t, e in d.threads if e.style == "jangin"]
    for j, ((d0, t0, e0), (d1, t1, e1)) in enumerate(zip(seq, seq[1:])):
        if d1 - d0 > dt.timedelta(days=1):
            continue
        if e1.key.startswith(("jone-", "jstem-")):
            subj, pk = e1.facts[0][0], e1.facts[0][1]
            who = ddi(subj) if subj in ZODIAC_ANIMALS else f"{STEM_NAMES[STEMS.index(subj)].split('(')[0]} 일간"
            what = f"{who} {int(pk[5:])}월 {ONE_NOUN[e1.kind]} 이야기"
        else:
            what = f"'{title_of(e1)}'"
        last = e0.pages[-1]
        if last[-2:] in LB["find_me"]:    # 끝의 팔로우 두 줄을 '다음 글 예고 + 팔로우'로 바꾼다 (팔로우 말이 두 번 나오지 않게)
            last = last[:-2]
        e0.pages[-1] = last + [f"다음엔 {what} 올려요", LB["follow"][j % len(LB["follow"])]]


FOLLOW_END = {"jangin": ["이런 이야기 계속 올려요", "팔로우 해 두시면 놓치지 않아요"],
              "dohwa": ["🫨 이런 사주 팁 계속 올려요", "놓치기 싫으면 팔로우 해 두세요!"],
              "salgu": ["🍀 다음 탄도 곧 올려요", "다음 탄 놓치기 싫으면 팔로우 해 두세요🧚🏻‍♀️"]}


def has_follow(e: Evening) -> bool:
    return any("팔로우" in x for x in e.pages[-1])


def _follow_all(days: list[Day]) -> None:
    """모든 스레드 글은 마지막 장에 팔로우 말이 있다 (사장님 2026-11-01 '어떤 건 하고 어떤 건 안 하면 안 됨'). 프로필 링크 말은 쓰지 않는다."""
    for d in days:
        for _, _, e in d.threads:
            if not has_follow(e):
                e.pages[-1] = e.pages[-1] + ["", *FOLLOW_END[e.style]]


def _periods_of(days: list[Day]) -> list[Period]:
    ps: dict[str, Period] = {}
    for d in days:
        for p in [*_month_periods(d.date), month_period(*target_month(d.date))]:
            ps[p.key] = p
    return list(ps.values())


def _groups(days: list[Day]) -> list[list[tuple[str, ...]]]:
    """뜻이 같은 줄 묶음 (한 줄 또는 여러 줄). 한 주 안에서 같은 말이 되풀이되지 않게 돌려 쓴다 (심사 2026-11-01 '사람 말투').
    묶음 안의 말은 엔진 사실(절기 날짜·간지·오행)이 같고 말투만 다르다 (제1조항)."""
    g: list[list[tuple[str, ...]]] = []
    for p in _periods_of(days):
        g.append([tuple(period_intro(p, k)) for k in range(len(LB["intro"]))])
        d = start_label(p)
        for k in ("세", "네"):
            g.append([(fill(h, d=d, k=k),) for h in LB["do_head"]])
        g.append([(f"※ 왜 {d}부터일까",), (f"※ {d}부터 뭐가 달라질까",), (f"※ 왜 하필 {d}부터일까",)])
        g.append([(f"※ 왜 {d}부터 천천히 가야 할까",), (f"※ {d}부터 왜 속도를 줄여야 할까",)])
        g.append([(x,) for x in dohwa_month_lines(p)])
    g += [[tuple(x) for x in B["salgu_end"]], [tuple(x) for x in B["dohwa_reply"]], [tuple(x) for x in LB["find_me"]]]
    for s in [LB["close"], LB["follow"], LB["sign_head"], LB["sign_head_bad"], LB["next_keep"], LB["next_go"], *B["vary"]]:
        g.append([(x,) for x in s])
    g.append([(x,) for x in DOHWA_WHY_HEAD])
    g += [[(x,) for x in v] for v in GOD_PLAIN.values()]
    for k, v in B["heart_hooks"].items():
        for gb in v.values():
            g.append([tuple(x) for x in gb])
    return g


def _pools() -> list[list[str]]:
    """서로 바꿔 써도 되는 줄 모음 (같은 주제의 신호·할 일). 한 글 안에서는 겹치지 않게 고른다."""
    out = [v for k in B["signals"] for v in B["signals"][k].values()]
    out += [v for v in LB["signals"].values()] + [v for v in LB["actions"].values()] + [v for v in LB["bad_actions"].values()]
    return out


def _fresh_acts(days: list[Day]) -> None:
    """도화도르 목록 글(❶~❺·10일간)의 할 일이 같은 주 다른 글의 할 일과 겹치면 같은 십신의 다른 할 일로 바꾼다
    (심사 2026-11-01: 11/7 아침 글과 낮 목록 글에 '자동이체 목록'이 두 번)."""
    allacts = {g: v for g, v in B["dohwa_acts"].items()}
    key = lambda a: re.sub(r"\s", "", a)[:4]
    for i, d in enumerate(days):
        win = days[max(0, i - 3): i + 4]
        for _, _, e in d.threads:
            if not e.key.startswith(("dohwa-list-", "dohwa-ten-")):
                continue
            others = re.sub(r"\s", "", "".join(x for dd in win for _, _, o in dd.threads if o is not e for pg in o.pages for x in pg))
            mine = re.sub(r"\s", "", "".join(e.pages[0]))
            for li, line in enumerate(e.pages[0]):
                m = re.match(r"^(❶|❷|❸|❹|❺) (.+)$", line) or re.match(r"^(.+?\] — )(.+?)( \((\S+) 달\))$", line)
                if not m:
                    continue
                act = m.group(2)
                if key(act) not in others:
                    continue
                g = m.group(4) if m.lastindex and m.lastindex >= 4 else next((k for k in GOD_PLAIN if f"{k}(" in "".join(e.pages[0][-2:])), None)
                for alt in allacts.get(g, []):
                    a2 = alt.split(". ")[0] if m.lastindex and m.lastindex >= 4 else alt
                    if key(alt) not in others and key(alt) not in mine:
                        e.pages[0][li] = line.replace(act, a2)
                        mine = re.sub(r"\s", "", "".join(e.pages[0]))
                        break


def _vary_lines(days: list[Day]) -> None:
    """같은 뜻 묶음 안에서 지금까지 가장 덜 쓴 말로 바꾼다 (같은 줄이 한 주에 세 번 넘게 나오지 않게)."""
    groups = _groups(days)
    index: dict[str, list[tuple[list, tuple]]] = {}
    for grp in groups:
        for v in grp:
            index.setdefault(v[0], []).append((grp, v))
    used: dict[tuple[str, ...], int] = {}
    last: dict[tuple[str, ...], int] = {}   # 마지막으로 쓴 글 번호: 같은 횟수면 오래전에 쓴 말을 고른다
    pos = 0
    for d in days:
        for _, _, e in d.threads:
            pos += 1
            body = "\n".join(x for pg in e.pages for x in pg)   # 같은 글 안에 이미 있는 말은 고르지 않는다
            for pi, pg in enumerate(e.pages):
                out, i = [], 0
                while i < len(pg):
                    hit = next(((grp, v) for grp, v in index.get(pg[i], []) if tuple(pg[i:i + len(v)]) == v), None)
                    if not hit:
                        out.append(pg[i]); i += 1
                        continue
                    grp, v = hit
                    best = min(grp, key=lambda w: (w != v and any(x in body for x in w if len(x) > 6), used.get(w, 0), last.get(w, -99), w != v))
                    used[best] = used.get(best, 0) + 1
                    last[best] = pos
                    out += list(best); i += len(v)
                e.pages[pi] = out
    # 한 장 글 첫 줄 끝말 ('11월 ○○띠는 통장 숫자가 달라져요'): 같은 뜻의 다른 말로
    tails = {x: grp for grp in B["one_tail_vary"] for x in grp}
    tcnt: dict[str, int] = {}
    for d in days:
        for _, _, e in d.threads:
            if not e.key.startswith(("jone-", "jstem-")):
                continue
            p1 = e.pages[0]
            for i, x in enumerate(p1):
                m = re.match(r"^(\d+월 .+?[은는] )(.+)$", x)
                if m and m.group(2) in tails:
                    best = min(tails[m.group(2)], key=lambda y: (tcnt.get(y, 0), y != m.group(2)))
                    tcnt[best] = tcnt.get(best, 0) + 1
                    p1[i] = m.group(1) + best
    # 신호·할 일 줄: 같은 모음 안에서 이번 주에 덜 쓴 줄로 (한 글 안에서 겹치지 않게)
    pools = _pools()
    where = {x: pl for pl in pools for x in pl}
    cnt: dict[str, int] = {}
    for d in days:
        for _, _, e in d.threads:
            for pi, pg in enumerate(e.pages):
                taken = set(pg)
                new = []
                for x in pg:
                    pl = where.get(x)
                    if pl:
                        best = min((y for y in pl if y == x or y not in taken), key=lambda y: (cnt.get(y, 0), y != x))
                        taken.add(best)
                        cnt[best] = cnt.get(best, 0) + 1
                        x = best
                    new.append(x)
                e.pages[pi] = new


def all_text(m: Morning, *es: Evening) -> str:
    parts = [json.dumps(m.texts(), ensure_ascii=False), *[json.dumps(e.texts(), ensure_ascii=False) for e in es], " ".join(m.title),
             json.dumps(m.data, ensure_ascii=False)]
    return "\n".join(parts)
