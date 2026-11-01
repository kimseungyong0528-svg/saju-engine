"""영상 대본: 화면에 나오는 순위·근거를 사람이 말하듯 읽는 대본 (사장님 2026-11-01 "대화 스크립트 따로").

화면과 같은 엔진 계산에서만 만든다 (제1조항). 대본은 스레드 글처럼 심사원 55명(11항목 × 5명)이 100점 줄 때까지 고친다.
타입캐스트가 한 줄씩 읽는다 (video/voice.py). 한자는 읽지 않고 한글만 읽는다 (voice.clean).
한 영상을 유튜브·인스타·페북에 같이 올리므로 끝말은 '구독이나 팔로우'로 둘 다 부른다.
"""

from __future__ import annotations

import datetime as dt
import re

from .text import (KINDS, Morning, _basis, ddi, josa, main_whys, start_label, why_bank, years_short)

END = "놓치기 싫으면 구독이나 팔로우 해 두세요."
# 십신을 처음 듣는 사람도 알아듣게 한 마디로 (쉬운 설명 심사 2026-11-01). 식상=내가 내보냄, 인성=내가 받음 (sipsin_fact).
GOD_PLAIN = {"비겁": "나와 같은 편 기운", "식상": "내 마음을 밖으로 꺼내는 기운", "재성": "내가 손에 쥐는 돈 기운",
             "관성": "나를 누르고 책임을 지우는 기운", "인성": "나를 받쳐 주고 챙겨 주는 기운"}


def _years(a: str) -> str:
    """화면에 나오는 출생연도 네 개를 다 읽는다 (74·62년생만 빠지면 그분들은 넘긴다, 심사 2026-11-01)."""
    return years_short(a) + "년생"


def _say(line: str) -> str:
    """듣는 말로: 문장 끝을 맺는다."""
    line = line.strip()
    if line.endswith("조심"):
        line += "하세요"
    elif line.endswith("사람"):
        line += "이 생겨요"
    return line if line.endswith((".", "?", "!")) else line + "."


def _spoken_basis(m: Morning, r) -> tuple[str, str]:
    """(근거 한 문장, 그래서 생기는 일 한 문장). 화면·스레드와 같은 엔진 근거(_basis)를 말로 바꾼다."""
    whys = main_whys(r) if r.score > 0 else sorted(r.why)
    if not whys:
        return "", ""
    t = whys[0][1]
    ls = _basis(m.kind, m.period, r, t)
    short = why_bank(m.kind, t)["short"][0]
    if len(ls) == 4:
        return _say(f"{ls[0]} {ls[1]} {ls[2]}"), _say(ls[3])
    if len(ls) == 3:
        # '11월 기해(己亥)의 위 글자 기(己)의 토(土) 기운은' 은 귀로 듣기 어렵다 → '11월 위 글자 기토는'
        h = re.search(r"위 글자 (\S)\(.\)의 (\S)\(.\) 기운", ls[0])
        b = re.search(r"\S+\((.)(.)\)의 (\S)\(.\) 기운", ls[0])
        src = f"{m.period.label} 위 글자 {h[1]}{h[2]}" if h else f"{m.period.label} 아래 글자 {m.period.ganzhi[1]}{b[3]}" if b else ls[0]
        g = re.match(r"(\S+)\(", ls[1].split("에게 ")[1])[1]
        return _say(f"{josa(src, '은', '는')} {ls[1].split('에게 ')[0]}에게 {g}이에요. {g}은 {GOD_PLAIN[g]}이에요"), _say(short)
    return "", _say(short)


def _top(m: Morning, r, full: bool) -> list[str]:
    head = f"{r.rank}위, {ddi(r.ddi)}. {_years(r.ddi)}이에요."
    basis, what = _spoken_basis(m, r)
    if not full:
        return [head, what]
    return [head, basis, what]


def _hook(m: Morning) -> str:
    """제목 3줄을 한 번에 말한다. '1위부터 12위.'처럼 끊긴 말로 끝내지 않는다 (사람 말투 심사)."""
    t = [re.sub(r"\(.+?\)", "", x).replace("“", "").replace("”", "").replace("‘", "").replace("’", "") for x in m.title]
    if len(t) == 3 and t[2].startswith("1위"):
        return f"{t[0]} {t[1]}, 1위부터 12위까지 바로 볼게요."
    return f"{t[0]}, {' '.join(t[1:])}. 1위부터 바로 볼게요."


def _clean(lines: list[str]) -> list[str]:
    return [x.strip() for x in lines if x and x.strip()]


def script(m: Morning) -> list[str]:
    """한 줄 = 타입캐스트 한 번 = 자막 한 장."""
    if m.fmt == "sinbi":
        d = dt.date.fromisoformat(m.data["date"])
        out = [f"{d.month}월 {d.day}일, 내 띠 운세 바로 볼게요.", f"오늘은 {m.data['ganzhi']}일이에요."]
        out += [f"{ddi(a)}, {t}" for a, t in m.data["text"].items()]
        return _clean(out + ["내 띠 얘기 맞았는지 댓글로 남겨 주세요.", END])
    if m.fmt == "forceteller":
        head = " ".join(x.replace("<em>", "").replace("</em>", "") for x in m.data["head"])
        say = [s.replace("\n", " ") for s in m.data["say"]]
        return _clean([head + "."] + [_say(x) for x in say] + [END])
    k = KINDS[m.kind]
    p = m.period
    intro = f"{josa(p.label, '은', '는')} {start_label(p).split('(')[0]}부터 {p.ganzhi.split('(')[0]}{'년' if p.year else '월'}이에요."
    if m.fmt == "hidden":
        out = [_hook(m), intro]
        for r in reversed(m.rows[3:]):
            out.append(_say(f"{r.rank}위 {ddi(r.ddi)}, {m.data['phrase'][r.ddi]}"))
        out.append("이제 3위부터예요.")
        for r in reversed(m.rows[:3]):
            out += _top(m, r, full=r.rank == 1)
        return _clean(out + [f"내 띠는 몇 위였는지 댓글로 남겨 주세요.", END])
    out = [_hook(m), intro]
    for r in m.rows[:3]:
        out += _top(m, r, full=True)
    out.append(f"4위부터 12위까지는 화면에 다 적어 뒀어요." if m.fmt == "tier" else f"{k['name']} 순위 전체는 화면에서 확인하세요.")
    return _clean(out + ["내 띠는 몇 위였는지 댓글로 남겨 주세요.", END])
