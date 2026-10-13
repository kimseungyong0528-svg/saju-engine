"""PDF를 만들기 전에 글을 자동으로 검사한다.

AI가 쓴 글이 사주 계산 결과와 어긋나는 곳을 찾는다.
- 사주에 없는 신살을 이 사람의 것처럼 쓴 곳
- 십신 무리 개수를 틀리게 쓴 곳(예: 재성이 0개인데 "재성이 2개")
- 계산 결과에 없는 점수(NN점)
- 계산 결과의 범위를 벗어난 연도
- 같은 흔한 방법(하루 뒤에 다시 보기, 메모하기 등)이 책 전체에서 너무 자주 나온 곳

check()는 문제마다 {"slot", "kind", "detail"}을 돌려준다. ClaudeWriter는 걸린 칸만 한 번 다시 쓴다.
"""

from __future__ import annotations

import json
import re

from . import knowledge as K

# 같은 방법은 책 한 권에서 이 횟수까지만 둔다(몇 번 강조하는 것은 괜찮고, 눈에 띄게 반복되는 것만 막는다)
REPEAT_LIMIT = 3

# 흔한 방법: 이름 → 찾는 말
STOCK = {
    "하루 뒤에 다시 보기": r"하루\s*(뒤|후|이틀|만\s*더|정도\s*미루|묵)",
    "메모하기": r"메모",
    "심호흡": r"심호흡|숨을\s*(크게|깊게)",
    "산책": r"산책",
    "일찍 자기": r"일찍\s*자|잠자리에\s*일찍",
    "물 마시기": r"물을?\s*(한\s*잔|충분히|자주)\s*마",
}

# 목적어(무엇을)가 꼭 있어야 하는 말: "더 넣기 쉬워요"처럼 무엇을 넣는지 빠지면 읽는 사람이 헷갈린다
NEEDS_OBJECT = re.compile(r"(?:^|\s)(?:더|크게|새로|다시)\s*(?:넣|빼|빌려주|맡기)")
# 풀이의 믿음을 떨어뜨리는 말(2026-10-12 사장님 요청으로 금지)
HEDGE = re.compile(r"참고용|참고로만|참고만\s*하|재미로\s*(?:보|읽|참고)|재미\s*삼아")
LONG_SENTENCE = 90   # 이보다 긴 문장은 두 문장으로 나누게 한다(라벨 제외)

GROUPS = ("비겁", "식상", "재성", "관성", "인성")
NEG = re.compile(r"없|않|아니|0개")


def flat(v) -> list[str]:
    if isinstance(v, str):
        return [v]
    if isinstance(v, list):
        return [x for i in v for x in flat(i)]
    if isinstance(v, dict):
        return [x for i in v.values() for x in flat(i)]
    return []


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.?!])\s+|\n", text) if s.strip()]


def _people(f: dict) -> list[dict]:
    return [f] + ([f["partner"]] if f.get("partner") else [])


def _shinsal_names() -> list[str]:
    """찾을 신살 이름. '도화살'과 '도화'처럼 살을 뗀 말도 찾는다(귀인은 일반 낱말이라 이름 전체만)."""
    out = []
    for n in K.SHINSAL:
        out.append(n)
        if n.endswith("살"):
            out.append(n[:-1])
    return out


def _numbers(f: dict) -> tuple[set[str], range]:
    from .writer import facts_digest
    blob = json.dumps(facts_digest(f), ensure_ascii=False)
    nums = set(re.findall(r"\d+", blob))
    years = [int(n) for n in nums if len(n) == 4 and 1900 <= int(n) <= 2150]
    return nums, range(min(years, default=1900), max(years, default=2150) + 1)


def _luck_text(f: dict) -> str:
    """운 표시(t_signs, 연애 표시 등)만 모은 글. 참고 지식(뜻풀이)은 빼고 본다."""
    parts = []
    if f.get("theme"):
        parts.append(json.dumps(f["theme"]["digest"], ensure_ascii=False))
    if f.get("romance"):
        from .writer import romance_digest
        parts.append(json.dumps(romance_digest(f["romance"]), ensure_ascii=False))
    return " ".join(parts)


def check(f: dict, texts: dict, skip_repeat: set | frozenset = frozenset()) -> list[dict]:
    """skip_repeat: 반복을 세지 않을 칸(마지막 장처럼 앞 장의 방법을 모으는 칸)."""
    issues: list[dict] = []
    people = _people(f)
    have = set()
    for p in people:
        have |= set(p["shinsal_names"])
    have_base = have | {n[:-1] for n in have if n.endswith("살")}
    # 운(해·달·대운) 표시에 나오는 신살 이름은 '운에 들어오는 것'으로 쓸 수 있다
    luck = _luck_text(f)
    in_luck = {n for n in _shinsal_names() if n not in have_base and n in luck}
    counts = [{g["group"]: g["n"] for g in p["ten_god_groups"]} for p in people]
    nums, year_range = _numbers(f)
    names = _shinsal_names()
    group_re = re.compile(r"(" + "|".join(GROUPS) + r")[^.\d]{0,6}?(\d+)\s*개(?!월)")

    for sid, v in texts.items():
        for para in flat(v):
            for sent in sentences(para):
                negated = bool(NEG.search(sent))
                # 1) 사주에 없는 신살
                for n in names:
                    if n in sent and n not in have_base and not negated and n not in in_luck:
                        # '도화'가 '도화살'의 일부로 이미 걸렸으면 한 번만
                        if n + "살" in sent and n + "살" in names:
                            continue
                        issues.append({"slot": sid, "kind": "없는 신살", "detail": f"사주에 없는 '{n}'을 썼어요: {sent[:80]}"})
                # 2) 십신 무리 개수
                for m in group_re.finditer(sent):
                    g, n = m[1], int(m[2])
                    if not any(c[g] == n for c in counts):
                        right = " / ".join(f"{c[g]}개" for c in counts)
                        issues.append({"slot": sid, "kind": "개수", "detail": f"{g} 개수를 {n}개라고 썼는데 계산 결과는 {right}예요: {sent[:80]}"})
                # 3) 계산에 없는 점수
                for m in re.finditer(r"(\d+)\s*점(?!\s*(이상|이하|넘|미만|만점|대|[을이]\s*넘))", sent):
                    if m[1] not in nums and m[1] != "100":
                        issues.append({"slot": sid, "kind": "점수", "detail": f"계산 결과에 없는 {m[1]}점을 썼어요: {sent[:80]}"})
                # 5) 알아듣기 어려운 문장(목적어 빠짐, 너무 긴 문장)
                body = re.sub(r"^[가-힣 ]{1,8}:\s*", "", sent)
                if NEEDS_OBJECT.search(body) and not re.search(r"[을를](\s|$)", body):
                    issues.append({"slot": sid, "kind": "문장", "detail": f"무엇을 하는지(목적어)가 빠졌어요. '돈을 더 넣기'처럼 무엇을 쓰세요: {sent[:80]}"})
                elif len(re.sub(r"\([^)]*\)", "", body)) > LONG_SENTENCE:   # 괄호 속 용어 풀이는 빼고 센다
                    issues.append({"slot": sid, "kind": "문장", "detail": f"한 문장이 너무 길어요. 한 문장에 한 가지 내용만 쓰세요: {sent[:80]}"})
                if HEDGE.search(sent):
                    issues.append({"slot": sid, "kind": "문장", "detail": f"'참고용', '재미로' 같은 말은 빼고 사주 근거로 그대로 말하세요: {sent[:80]}"})
                # 4) 범위를 벗어난 연도
                for m in re.finditer(r"((?:19|20|21)\d\d)\s*년", sent):
                    if int(m[1]) not in year_range:
                        issues.append({"slot": sid, "kind": "연도", "detail": f"계산 범위 밖의 {m[1]}년을 썼어요: {sent[:80]}"})
    issues += newyear_checks(f, texts)
    issues += repeats(texts, skip_repeat)
    return issues


# 신년운세: 삼재·대운 사실과 사장님 표현 규칙('좋은 때' → '좋은 시기')
SAMJAE_SAID = re.compile(r"(들|눌|날)?삼재(예요|이에요|인\s*해|가\s*(들|시작|겹)|에\s*(들어|해당))")
DAEWOON_CHANGE = re.compile(r"2027년\S*\s*(새\s*)?대운이\s*(바뀌|시작|들어오)")
GOOD_TTAE = re.compile(r"좋은\s*때")


def newyear_checks(f: dict, texts: dict) -> list[dict]:
    th = f.get("theme") or {}
    if th.get("product") != "newyear":
        return []
    sj, dw = th["data"]["samjae"], th["data"]["daewoon"]
    out = []
    for sid, v in texts.items():
        for para in flat(v):
            for sent in sentences(para):
                negated = bool(NEG.search(sent))
                for m in SAMJAE_SAID.finditer(sent):
                    if negated:
                        continue
                    if not sj["is_samjae"] and "2027" in sent:
                        out.append({"slot": sid, "kind": "삼재", "detail": f"2027년은 이 띠에게 삼재가 아닌데 삼재라고 썼어요: {sent[:80]}"})
                    elif sj["is_samjae"] and m[1] and m[1] + "삼재" != sj["kind"] and "2027" in sent:
                        out.append({"slot": sid, "kind": "삼재", "detail": f"2027년은 {sj['kind']}인데 {m[1]}삼재라고 썼어요: {sent[:80]}"})
                if DAEWOON_CHANGE.search(sent) and not negated and not dw["changes_in_2027"]:
                    out.append({"slot": sid, "kind": "대운", "detail": f"2027년에는 대운이 바뀌지 않는데 바뀐다고 썼어요: {sent[:80]}"})
                if GOOD_TTAE.search(sent):
                    out.append({"slot": sid, "kind": "문장", "detail": f"'좋은 때' 대신 '좋은 시기'라고 써 주세요: {sent[:80]}"})
    return out


def repeats(texts: dict, skip: set | frozenset = frozenset()) -> list[dict]:
    """같은 흔한 방법이 REPEAT_LIMIT번을 넘게 나온 칸(앞에서부터 세고, 넘친 칸만)."""
    seen: dict[str, int] = {}
    out = []
    for sid, v in texts.items():
        if sid in skip:
            continue
        text = " ".join(flat(v))
        for name, pat in STOCK.items():
            n = len(re.findall(pat, text))
            if not n:
                continue
            before = seen.get(name, 0)
            seen[name] = before + n
            if seen[name] > REPEAT_LIMIT:
                out.append({"slot": sid, "kind": "반복", "detail": f"'{name}'이 책에서 {seen[name]}번째로 나왔어요. 이 칸의 주제에 맞는 다른 방법으로 바꿔 주세요."})
    return out


# 칸의 글자 수가 목표(chars)의 이 범위를 벗어나면 다시 쓴다(짧으면 쪽 아래가 비고, 길면 다음 쪽으로 밀린다)
LENGTH_RANGE = (0.85, 1.10)


def lengths(texts: dict, slots: list[dict]) -> list[dict]:
    """칸마다 글자 수를 목표와 비교한다. slots: [{id, chars}, ...]"""
    lo, hi = LENGTH_RANGE
    out = []
    for s in slots:
        if s["id"] not in texts:
            continue
        n = sum(len(x) for x in flat(texts[s["id"]]))
        if n < s["chars"] * lo:
            out.append({"slot": s["id"], "kind": "분량", "detail": f"글이 {n}자로 목표 {s['chars']}자보다 짧아요. 이 사람 사주에 맞는 장면과 구체적인 방법을 더해 {s['chars']}자 안팎으로 채워 주세요."})
        elif n > s["chars"] * hi:
            out.append({"slot": s["id"], "kind": "분량", "detail": f"글이 {n}자로 목표 {s['chars']}자보다 길어 다음 쪽으로 밀려요. 중요한 내용은 남기고 {s['chars']}자 안팎으로 줄여 주세요."})
    return out


def by_slot(issues: list[dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for i in issues:
        out.setdefault(i["slot"], []).append(i["detail"])
    return out


def summary(issues: list[dict]) -> str:
    if not issues:
        return "글 검사: 문제 없음"
    kinds: dict[str, int] = {}
    for i in issues:
        kinds[i["kind"]] = kinds.get(i["kind"], 0) + 1
    return "글 검사: " + ", ".join(f"{k} {n}곳" for k, n in kinds.items())
