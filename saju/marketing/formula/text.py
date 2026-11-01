"""SNS 게시물 공식: 날짜만 넣으면 그날 아침 영상·저녁 스레드 글 재료가 나온다 (사장님 2026-11-01 "공식으로, 무한 발행").

- 순위·띠·합충·출생연도는 모두 엔진 계산(ranking.rank, analysis.branch_relation)에서 나온다 (제1조항).
- 문장은 banks.json 재료를 엔진 결과에 맞춰 고른다. 이미 쓴 재료(key)는 건너뛴다.
- 아침 형식은 rules.json 의 5가지를 날마다 돌린다. 저녁은 사주장인식(댓글로 이어 쓰기)·살구식·도화도르식을 돌린다.
"""

from __future__ import annotations

import datetime as dt
import json
import random
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
EVENING_STYLES = ["jangin", "salgu", "jangin", "dohwa"]
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
    dark: bool = True

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
    whys = main_whys(r)
    good = [t for w, t in whys if w > 0]
    tag = pick_unique([why_bank(kind, t)["tag"] for _, t in whys], tags)
    lines = [f"{ddi(r.ddi)} ({years_full(r.ddi)})", f"- {tag}", ""]
    lines += _basis(kind, p, r, good[0] if good else whys[0][1])
    if len(good) > 1 and why_key(kind, good[1]).split(":")[-1] in REL_NAMES7:
        lines += [""] + _basis(kind, p, r, good[1])
    bad = [t for w, t in whys if w < 0] if kind != "care" else []
    if bad:
        key = why_key(kind, bad[0]).split(":")[-1]
        if key in REL_NAMES7:
            lines += ["", f"다만 {key}({B['rel'][key]['hanja']})도 같이 있어요", why_bank(kind, bad[0])["long"][0].split(". ")[-1].rstrip(".")]
        else:
            lines += ["", f"다만 {bad[0]}", why_bank(kind, bad[0])["long"][0].split(". ")[-1].rstrip(".")]
    main = good[0] if good and kind != "care" else whys[0][1]
    feel = why_bank(kind, main).get("feel") or B["feel"][kind][k % len(B["feel"][kind])]
    lines += ["", feel[0], feel[1]]
    return lines


def jangin(kind: str, p: Period, n: int) -> Evening:
    K = B["kinds"][kind]
    rows = rank(kind, p)[:3]
    hook = [fill(x, p=p.label) for x in K["hooks"][n % len(K["hooks"])]]
    p1 = hook + [""] + [f"{i}. {ddi(r.ddi)} - ({years_short(r.ddi)}년생)" for i, r in enumerate(rows, 1)]
    good = kind != "care"
    p2 = ["특히", "", f"{josa(p.label, '은', '는')} {copula(p.ganzhi)}",
          f"세 띠 모두 {p.label} 기운과 {'좋게 만나요' if good else '부딪혀요'}", "",
          f"그런데 {'만나는' if good else '부딪히는'} 모양이 달라요"]
    tags: set[str] = set()
    cards = [jangin_card(kind, p, r, n + i, tags) for i, r in enumerate(rows)]
    end = [fill(x, where=K["where"]) for x in B["ending"]] + [""] + K["ask"] + ["", B["cta"][n % len(B["cta"])]]
    return Evening(f"jangin-{kind}-{p.key}", "jangin", [p1, p2, *cards, end])


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


def jangin_stem(kind: str, p: Period, n: int) -> Evening | None:
    K = B["kinds"][kind]
    rows = [r for r in stem_rank(kind, p) if r.score > 0][:3]
    if len(rows) < 3:
        return None
    word = {"money": "돈 들어오는", "love": "인연 들어오는", "care": "특히 조심해야 할", "work": "일이 풀리는", "help": "귀인 만나는",
            "study": "문서운 들어오는", "move": "움직이면 풀리는"}[kind]
    p1 = [f"<{p.label}, {word} 일간>", ""] + [f"{i}. {STEM_NAMES[r.stem]} 일간" for i, r in enumerate(rows, 1)]
    p2 = ["일간이 뭐냐면", "", "태어난 날의 첫 글자예요", "사주 여덟 글자 중 '나'를 뜻하는 글자예요", "",
          f"{josa(p.label, '은', '는')} {copula(p.ganzhi)}", "이 글자와 내 일간이 어떻게 만나는지 보면", f"{p.label} 흐름이 보여요"]
    cards, tags = [], set()
    for j, r in enumerate(rows):
        ws = sorted(r.why, key=lambda x: -x[0])
        lines = [f"{STEM_NAMES[r.stem]} 일간"]
        bank = why_bank(kind, ws[0][1]) if ws[0][1] != "천간합" else B["stem_hap"]
        lines += [f"- {pick_unique([bank['tag'].replace('{n}', K['noun'])] + [why_bank(kind, w[1])['tag'] for w in ws[1:] if w[1] != '천간합'], tags)}", ""]
        for w, t, e, g in ws[:2]:
            if w <= 0 and kind != "care":
                continue
            if t == "천간합":
                a, c = sorted((r.stem, p.stem))
                lines += [f"{p.label} 천간 {josa(_stem(p.stem), '과', '와')}", f"{STEMS[r.stem]}{STEM_NAMES[r.stem][1:]} 일간이 {STEMS[a]}{STEMS[c]}합(合)이에요", B["stem_hap"]["mean"], ""]
            else:
                lines += [f"{p.label} {p.ganzhi}의 {ELEMENTS[e]}({EL_HANJA[ELEMENTS[e]]}) 기운은",
                          f"{STEM_NAMES[r.stem].split('(')[0]} 일간에게 {copula(f'{g}({GH[g]})')}", t, ""]
        bad = [t for w, t, e, g in ws if w < 0] if kind != "care" else []
        if bad:
            lines += [f"다만 {bad[0]}", why_bank(kind, bad[0])["long"][0].split(". ")[-1].rstrip("."), ""]
        main = ws[0][1]
        feel = (why_bank(kind, main).get("feel") if main != "천간합" else None) or B["feel"][kind][(n + j) % len(B["feel"][kind])]
        lines += [feel[0], feel[1]]
        cards.append(lines)
    end = ["같은 일간이라도", "나머지 일곱 글자에 따라", f"{K['where']} 달라요", "그건 따로 봐야 알아요", ""] + K["ask"] + \
          ["", "내 일간이 뭔지 모르면", B["cta"][1]]
    return Evening(f"jangin-stem-{kind}-{p.key}", "jangin", [p1, p2, *cards, end])


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
    head = f"<남은 {p.label}, 겹경사 터지는 사람>" if p.year else f"<{p.label}, 겹경사 터지는 사람>"
    p1 = [head, ""] + [f"{i}. {d['year']}년생 {ddi(d['ddi'])}" for i, d in enumerate(ys, 1)]
    p2 = ["겹경사인 이유", "", "태어난 해는 천간과 지지, 두 글자예요",
          f"{p.label} {p.ganzhi}의 두 글자가", "이 두 글자와 모두 좋게 만나면", "경사가 두 번 겹쳐요"]
    cards = []
    for i, d in enumerate(ys):
        g = _rot(DOUBLE_GOOD, n + i * 2)[:2]
        cards.append([f"{d['year']}년생 {ddi(d['ddi'])} - {d['gz']}년생", "", "- 천간", d["stem"], "", "- 지지", d["branch"], "",
                      "천간도 합, 지지도 합이라 천합지합이에요" if d["both"] else "생과 합이 같이 들어와요", "",
                      f"- {g[0]}", f"- {g[1]}"])
    by: dict[str, list[int]] = {}
    for d in ys:
        by.setdefault(d["ddi"], []).append(d["year"])
    end = [f"같은 {ddi(a)}라도 {', '.join(map(str, v))}년생이에요" for a, v in by.items()]
    end += ["같은 띠라도 천간이 다른 해에 태어났으면", "겹경사는 아니에요", "", "좋은 일이 겹칠수록", "계약서와 약속은 한 번 더 읽고 도장 찍으세요", ""]
    end += ["태어난 해는 여덟 글자 중 두 글자예요", "나머지 여섯 글자에 따라", "경사가 어디로 오는지 달라요", "그건 따로 봐야 알아요",
            "", B["cta"][n % len(B["cta"])]]
    return Evening(f"jangin-double-{p.key}", "jangin", [p1, p2, *cards, end])


def salgu_left(used: set[str]) -> int:
    """아직 안 쓴 살구식 ○탄 수. 재료(60개)를 한 번씩만 쓴다."""
    return len(B["salgu"]) // 6 - sum(1 for k in used if k.startswith("salgu-"))


def salgu(n_tan: int) -> Evening:
    items = list(B["salgu"])
    rng = random.Random(len(items))
    rng.shuffle(items)
    start = ((n_tan - 1) * 6) % len(items)
    six = (items + items)[start:start + 6]
    p1 = [f"흥미로운 사주 이야기들 (금월선녀 ver.) - {n_tan}탄", ""] + [f"{i}. {t}" for i, t in enumerate(six, 1)]
    return Evening(f"salgu-{n_tan}", "salgu", [p1, B["salgu_end"][n_tan % len(B["salgu_end"])]], dark=False)


def dohwa(day: dt.date, t: int) -> Evening:
    y, m = target_month(day)
    p = month_period(y, m)
    E = ELEMENTS[BRANCH_ELEMENT[p.branch]]
    i = ELEMENTS.index(E)
    M, C, K, P2 = ELEMENTS[(i - 1) % 5], ELEMENTS[(i + 1) % 5], ELEMENTS[(i - 2) % 5], ELEMENTS[(i + 2) % 5]
    st = lambda e: B["elements"][e]["stems"]
    kw = {"p": p.label, "E": E, "EH": EL_HANJA[E], "Ew": B["elements"][E]["word"], "M": M, "C": C, "CS": st(C), "K": K, "KS": st(K), "P2": P2,
              "P2S": st(P2), "B": BRANCHES[p.branch], "BH": BRANCHES_HANJA[p.branch], "Ega": josa(E, "이", "가"), "EEHga": josa(f"{E}({EL_HANJA[E]})", "이", "가"), "Creul": josa(C, "을", "를"), "jeol": f"{B['jeolgi'][str(m)]}"}
    body = [fill(x, **kw) for x in B["dohwa"][t]]
    body = [x.replace(f"{p.label}은", josa(p.label, "은", "는")) for x in body]
    reply = [fill(x, p=p.label) for x in B["dohwa_reply"][t % len(B["dohwa_reply"])]]
    return Evening(f"dohwa-{t}-{p.key}", "dohwa", [body, reply])


# ── 하루 여러 번 올리는 글 (사장님 2026-11-01 "하루 9번") ──
ONE_KINDS = ["money", "love", "work", "help"]
_RANK: dict = {}


def _rank(kind: str, p: Period) -> list[Row]:
    k = (kind, p.key)
    if k not in _RANK:
        _RANK[k] = rank(kind, p)
    return _RANK[k]


def _action(kind: str, t: str) -> str:
    return why_bank(kind, t)["long"][0].split(". ")[-1].rstrip(".")


def _end(kind: str, n: int) -> list[str]:
    K = B["kinds"][kind]
    return [fill(x, where=K["where"]) for x in B["ending"]] + [""] + K["ask"][:2] + ["", B["cta"][n % len(B["cta"])]]


def ddi_one(kind: str, p: Period, a: str, n: int) -> Evening:
    """띠 하나, 운 하나: '11월 쥐띠 재물운 12띠 중 ○위'. 순위는 엔진 그대로."""
    K, name = B["kinds"][kind], KINDS[kind]["name"]
    r = next(x for x in _rank(kind, p) if x.ddi == a)
    whys = main_whys(r)
    good = [t for w, t in whys if w > 0]
    bad = [t for w, t in whys if w < 0]
    lead = good[0] if r.score > 0 and good else (bad[-1] if bad else (whys[0][1] if whys else ""))
    p1 = [f"<{p.label} {ddi(a)} {name}>", "", f"{years_short(a)}년생", "", f"12띠 중 {copula(f'{r.rank}위')}"]
    if lead:
        p1 += ["", f"- {why_bank(kind, lead)['tag']}"]
    p2 = []
    if lead:
        p2 += _basis(kind, p, r, lead)
    else:
        p2 += [f"{p.label} {p.ganzhi}의 글자가", f"{ddi(a)} 글자와 크게 부딪히지도, 돕지도 않아요"]
    if r.score > 0:
        other = next((t for t in bad), None)
        if other:
            p2 += ["", f"다만 {other}", _action(kind, other)]
        feel = why_bank(kind, lead).get("feel") or B["feel"][kind][n % len(B["feel"][kind])]
        p2 += ["", feel[0], feel[1]]
    else:
        p2 += ["", f"{p.label}에는 {K['noun']} 욕심을 크게 내기보다", _action(kind, lead) if lead else "하던 일을 차분히 이어 가세요"]
    return Evening(f"one-{kind}-{a}-{p.key}", "one", [p1, p2, _end(kind, n)])


def ddi_month(a: str, p: Period, n: int) -> Evening:
    """띠 하나의 그달 운 총정리: 재물·인연·일·귀인 순위 + 조심운 순위. 모두 엔진 순위."""
    ranks = {k: next(x for x in _rank(k, p) if x.ddi == a) for k in ONE_KINDS + ["care"]}
    p1 = [f"<{p.label} {ddi(a)} 운세 총정리>", "", f"{years_short(a)}년생", ""]
    p1 += [f"- {KINDS[k]['name']} {ranks[k].rank}위" for k in ONE_KINDS]
    p1 += [f"- 조심할 일 {ranks['care'].rank}위 (1위가 가장 조심)", "", "12띠 중 순위예요"]
    best = min(ONE_KINDS, key=lambda k: (ranks[k].rank, ONE_KINDS.index(k)))
    worst = max(ONE_KINDS, key=lambda k: (ranks[k].rank, -ONE_KINDS.index(k)))
    rb, rw = ranks[best], ranks[worst]
    gb = [t for w, t in main_whys(rb) if w > 0]
    p2 = [f"가장 좋은 건 {KINDS[best]['name']}이에요", ""]
    if gb:
        p2 += _basis(best, p, rb, gb[0])
        feel = why_bank(best, gb[0]).get("feel") or B["feel"][best][n % len(B["feel"][best])]
        p2 += ["", feel[0], feel[1]]
    else:
        p2 += ["크게 들어오는 기운은 없지만", "12띠 중에서는 앞쪽이에요"]
    bw = [t for w, t in sorted(rw.why) if w < 0]
    p3 = [f"가장 약한 건 {KINDS[worst]['name']}이에요", ""]
    if bw:
        p3 += _basis(worst, p, rw, bw[0]) + ["", _action(worst, bw[0])]
    else:
        p3 += [f"{p.label} 글자가 {KINDS[worst]['name']}을 크게 돕지 않아요", "이 부분은 욕심내지 말고 하던 대로 하세요"]
    end = ["같은 띠라도", "태어난 해는 여덟 글자 중 두 글자예요", "나머지 여섯 글자에 따라", "어느 운이 먼저 오는지 달라요", "그건 따로 봐야 알아요",
           "", B["cta"][n % len(B["cta"])]]
    return Evening(f"month-{a}-{p.key}", "month", [p1, p2, p3, end])


def stem_one(kind: str, p: Period, s: int, n: int) -> Evening:
    """일간 하나, 운 하나: '11월 갑목 일간 재물운 10개 중 ○위'. ranking 과 같은 무게로 매긴 stem_rank 그대로."""
    name = KINDS[kind]["name"]
    rows = stem_rank(kind, p)
    rk = next(i for i, r in enumerate(rows, 1) if r.stem == s)
    r = rows[rk - 1]
    nm = STEM_NAMES[s]
    p1 = [f"<{p.label} {nm} 일간 {name}>", "", f"태어난 날 첫 글자가 {STEMS[s]}({STEMS_HANJA[s]})인 사람", "",
          f"일간 10개 중 {copula(f'{rk}위')}"]
    ws = sorted(r.why, key=lambda x: -x[0])
    p2 = []
    for w, t, e, g in ws[:2]:
        if t == "천간합":
            a, c = sorted((s, p.stem))
            p2 += [f"{p.label} 천간 {josa(_stem(p.stem), '과', '와')}", f"{nm.split('(')[0]} 일간이 {STEMS[a]}{STEMS[c]}합(合)이에요", B["stem_hap"]["mean"], ""]
        else:
            p2 += [f"{p.label} {p.ganzhi}의 {ELEMENTS[e]}({EL_HANJA[ELEMENTS[e]]}) 기운은",
                   f"{nm.split('(')[0]} 일간에게 {copula(f'{g}({GH[g]})')}", t, ""]
    if not ws:
        p2 += [f"{p.label} 글자가", f"{nm.split('(')[0]} 일간의 {name}을 크게 돕지도 막지도 않아요", ""]
    if r.score > 0:
        t0 = ws[0][1]
        feel = (why_bank(kind, t0).get("feel") if t0 != "천간합" else None) or B["feel"][kind][n % len(B["feel"][kind])]
        p2 += [feel[0], feel[1]]
    else:
        bad = [t for w, t, e, g in ws if w < 0]
        p2 += [_action(kind, bad[0]) if bad else "하던 일을 차분히 이어 가세요"]
    end = ["같은 일간이라도", "나머지 일곱 글자에 따라", f"{B['kinds'][kind]['where']} 달라요", "그건 따로 봐야 알아요", "",
           "내 일간이 뭔지 모르면", B["cta"][1]]
    return Evening(f"stemone-{kind}-{s}-{p.key}", "stemone", [p1, p2, end])


def daily(day: dt.date) -> Evening:
    """그날 띠별 운세 (아침 '띠별 운세 표'와 같은 계산 sinbi_data)."""
    d = sinbi_data(day)
    rows = [f"{ddi(a)}: {t}" for a, t in d["text"].items()]
    p1 = [f"<{day.month}월 {day.day}일 띠별 운세>", "", *rows[:6]]
    p2 = [*rows[6:], "", f"오늘 일진은 {d['ganzhi']}일이에요", "띠 글자와 오늘 글자의 관계로 풀었어요", "",
          "내 생년월일로 보는 운세는 프로필 링크에서"]
    return Evening(f"daily-{day.isoformat()}", "daily", [p1, p2], dark=False)


def _month_periods(day: dt.date) -> list[Period]:
    return [p for p in periods(day) if not p.year]


def one_pool(day: dt.date, off: int = 0):
    n = day.toordinal()
    for p in _month_periods(day):
        for kind in _rot(ONE_KINDS, n + off):
            for a in _rot(list(ZODIAC_ANIMALS), n * 5 + off * 3):
                yield ddi_one(kind, p, a, n)


def stem_pool(day: dt.date):
    n = day.toordinal()
    for p in _month_periods(day):
        for kind in _rot(ONE_KINDS, n + 2):
            for s in _rot(list(range(10)), n * 3):
                yield stem_one(kind, p, s, n)


def month_pool(day: dt.date):
    n = day.toordinal()
    for p in _month_periods(day):
        for a in _rot(list(ZODIAC_ANIMALS), n * 7):
            yield ddi_month(a, p, n)


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


def evening_candidates(day: dt.date, used: set[str]):
    """저녁 18:00 대표 글 (캡처 영상도 이 글로 만든다): 사주장인식이 기본, 날마다 살구식·도화도르식이 끼어든다."""
    n = day.toordinal()
    style = EVENING_STYLES[n % len(EVENING_STYLES)]
    if style == "salgu" and salgu_left(used) > 0:
        yield salgu(sum(1 for k in used if k.startswith("salgu-")) + 1)
    if style == "dohwa":
        for t in _rot(list(range(len(B["dohwa"]))), n // 4):
            yield dohwa(day, t)
    yield from jangin_pool(day)


# 스레드 시간대 (사장님 2026-11-01 "하루 9번": 스레드 5개, 릴스·쇼츠 2개)
THREAD_SLOTS = [("오전", "07:30"), ("점심", "12:00"), ("저녁", "18:00"), ("밤", "21:00"), ("늦은밤", "23:00")]


def slot_candidates(day: dt.date, slot: str, used: set[str]):
    n = day.toordinal()
    if slot == "저녁":
        yield from evening_candidates(day, used)
    elif slot == "오전":
        if rules.morning_format(day) != "sinbi":   # 아침 영상이 띠별 운세 표인 날은 같은 표를 또 올리지 않는다
            yield daily(day)
        yield from one_pool(day)
    elif slot == "점심":
        yield from one_pool(day, 2)   # 오전과 다른 운으로
    elif slot == "밤":
        if n % 2 == 0:
            for t in _rot(list(range(len(B["dohwa"]))), n // 2):
                yield dohwa(day, t)
        elif salgu_left(used) > 0:
            yield salgu(sum(1 for k in used if k.startswith("salgu-")) + 1)
        yield from month_pool(day)
    elif slot == "늦은밤":
        yield from stem_pool(day)
    # 모자라면 남은 재료 어디서든
    yield from month_pool(day)
    yield from stem_pool(day)
    yield from one_pool(day)
    yield from jangin_pool(day)


def pick(cands, used: set[str]) -> Evening:
    first = None
    for c in cands:
        first = first or c
        if c.key not in used:
            return c
    return first


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


def plan(start: dt.date, days: int, used: set[str] | None = None, slots=None) -> list[Day]:
    """며칠치를 한 번에 고른다. 앞에서 고른 재료는 뒤에서 다시 쓰지 않는다."""
    used = set(used or ())
    slots = slots or THREAD_SLOTS
    out = []
    for i in range(days):
        d = start + dt.timedelta(days=i)
        m = morning(d, used)
        used.add(m.key)
        ths = []
        # 대표 글(저녁)을 먼저 고른다
        for s, t in sorted(slots, key=lambda x: x[0] != "저녁"):
            e = pick(slot_candidates(d, s, used), used)
            used.add(e.key)
            ths.append((s, t, e))
        ths.sort(key=lambda x: x[1])
        out.append(Day(d, m, ths))
    return out


def all_text(m: Morning, *es: Evening) -> str:
    parts = [json.dumps(m.texts(), ensure_ascii=False), *[json.dumps(e.texts(), ensure_ascii=False) for e in es], " ".join(m.title),
             json.dumps(m.data, ensure_ascii=False)]
    return "\n".join(parts)
