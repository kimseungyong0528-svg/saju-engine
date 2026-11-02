"""영상 대사와 밑에 글 (사장님 2026-11-01 "레퍼런스 그대로", "구조를 논의하고 만들어").

레퍼런스 (2026-11-01 크롬으로 유튜브 자동 자막 확인): 잘 터진 띠 순위 쇼츠는 5~9초, 목소리는 화면 제목 한 줄만 읽고 끝.
  천복 띠 456만 7초 · 재물복 띠 209만 5초 · 무서운 띠 90만 6초 · 복 부르는 띠 34만 9초.

사장님이 정한 구조:
- 영상은 모두 7초. 타입캐스트는 화면 위 고자극 제목을 읽고 '~ 알아보세요!' / '~ 확인하세요!' 로 끝낸다.
  예) "12월에 연애운 터지는 띠 순위, 10초 만에 알아보세요!"
- 밑에 글은 곳마다 다르다 (영상 내용은 같다).
  유튜브 "나의 12월 연애운을 더 자세히 알고 싶다면 구독!"
  인스타 릴스·페북 = 유튜브 말에서 '구독!' 만 '팔로우!' 로 (인스타도 댓글 말고 팔로우, 사장님 2026-11-01 "댓글해봤자 링크 안주니까").
  '미리 알고 싶다면' 같은 뻔한 말 금지. '나의 ○○을 더 자세히'로 내 이야기가 되게 쓴다.
- 레퍼런스 화면에 밑에 글(분홍 글)이 있는 형식(가림식, 무서운 띠 90만)은 그 글을 영상 화면에 넣는다 → 곳마다 영상 3개.
  레퍼런스에 밑에 글이 없는 형식은 화면에 넣지 않고 게시물 설명글 끝에만 쓴다.
- 대사·상단 제목·영상 내용·밑에 글은 스레드와 같은 심사원 55명(11항목) + 행동 유도 심사원 5명이 100점 줄 때까지 고친다
  (thread_rules.json judges.video, CLAUDE.md 제1조항).
화면 제목과 같은 글만 읽으므로 엔진 계산과 어긋나지 않는다 (제1조항). 한자는 읽지 않는다 (voice.clean).
"""

from __future__ import annotations

import datetime as dt
import re

from .text import josa

SECONDS = 7
ON_SCREEN_CTA = {"hidden", "tier", "sinbi", "forceteller", "solo"}   # 사장님 2026-11-03 "팔로우 문구 넣으랬자나": 모든 영상 화면 밑에
CHANNELS = ("youtube", "instagram-reel", "facebook-reel")
# '나의 ○○' 에 들어갈 말 (순위 종류마다)
TOPIC = {"money": "재물운", "love": "연애운", "work": "승진운", "help": "귀인운", "study": "합격운",
         "move": "이사·이직운", "care": "조심할 일"}


def _plain(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\(.+?\)", "", s)
    return re.sub(r"[“”‘’\"']", "", s).strip()


def top_title(m) -> str:
    """화면 위에 보이는 제목 그대로 (형식마다 화면이 다르다)."""
    if m.fmt == "hidden":
        from .render import B
        a, b = [x.replace("{p}", m.period.label) for x in B["kinds"][m.kind]["hidden"]]
        return f"{a} {b} 띠 순위"
    if m.fmt == "sinbi":
        d = dt.date.fromisoformat(m.data["date"])
        return f"{d.month}월 {d.day}일 띠별 운세"
    if m.fmt == "solo":
        return " ".join(_plain(x) for x in m.data["lines"]).replace(", ", ",").replace(",", ", ")
    if m.fmt == "forceteller":
        h1, h2 = (_plain(x) for x in m.data["head"])
        return f"{h1} {h2}"
    t = [_plain(x) for x in m.title]
    # 천복식: '1위부터 12위'는 화면 글로만. 둘째 줄이 '…할'로 끝나면 셋째 줄('구설수 낀 띠')까지 읽어야 말이 된다
    return " ".join(t[:2] if t[1].endswith("띠") or len(t) < 3 or t[2].startswith("1위") else t[:3])


def _spoken(s: str, m) -> str:
    """'수 없는 사주'는 귀로 들으면 숫자 '수'처럼 들린다 → 기운 이름을 붙인다 (쉬운 설명 심사)."""
    if m.fmt == "forceteller":
        for el in {m.data["el"], m.data.get("pair") or m.data["el"]}:
            s = re.sub(rf"(?<![가-힣]){el}(의| 없는| 많은)", rf"{el} 기운\1", s)
    return s


def script(m) -> list[str]:
    """타입캐스트가 읽는 한 줄: 화면 위 제목 + '~ 알아보세요!/확인하세요!'."""
    if m.fmt == "sinbi":
        # 화면 제목(날짜)만으로는 멈추지 않는다 (후킹 심사) → 표에 실제로 있는 좋은 띠·조심할 띠를 묶어 말한다
        # 저녁 영상은 다음 날 표라서 '오늘'이라 하지 않고 날짜로 말한다
        return [f"{top_title(m).replace(' 띠별 운세', '')} 웃는 띠와 조심할 띠, 지금 바로 확인하세요!"]
    if m.fmt == "forceteller":
        h1, h2 = (_spoken(_plain(x), m) for x in m.data["head"])
        # 화면은 7초라 앞 두 장만 보이고 나머지 풀이는 설명란에 있다 (render.forceteller)
        if h2.endswith("이렇게"):        # '11월, 수의 달 / 수 없는 사주는 이렇게'
            return [f"{h1.replace(',', '은')}! {h2[:-3]}어떻게 해야 할까요? 본문에서 끝까지 확인하세요!"]
        if h2.endswith("만나면"):        # '수 많은 사람과 / 목 많은 사람이 만나면'
            return [f"{h1} {h2} 어떻게 될까요? 본문에서 끝까지 확인하세요!"]
        return [f"{h1} {h2}, 본문에서 끝까지 확인하세요!"]
    if m.fmt == "hidden":
        # 화면에서 1~3위는 ???? 로 가려져 있고 설명란 맨 아래에 있다 → '10초 만에'라 하면 거짓 (신뢰 심사)
        return [f"{top_title(m)}, 1위부터 3위는 본문에서 확인하세요!"]
    if m.fmt == "solo":
        # 띠 3개가 화면에 바로 나온다 (사장님 2026-11-01 "더보기 말고 사진으로 보여줘")
        return [f"{top_title(m)}, 지금 바로 확인하세요!"]
    return [f"{top_title(m)}, 내 띠는 몇 위인지 확인하세요!"]   # 천복식: 12띠가 화면에 다 있다


def _topic(m) -> str:
    """'나의 ○○' : 영상 주제와 같은 말 (행동 유도 심사: 주제와 따로 놀지 않게)."""
    if m.fmt == "sinbi":
        return "띠 운세"                      # 하루 지나면 끝나는 날짜 운세는 '더 자세히'와 안 맞는다
    if m.fmt == "forceteller":
        h2 = _plain(m.data["head"][1])
        if "만나야 하는 사람" in h2:
            return "인연 궁합"
        if h2.endswith("만나면"):
            return "궁합"
        if "조심" in h2:
            return "사주가 조심할 점"
        return f"사주 속 {m.data['el']} 기운"
    return f"{m.period.label} {TOPIC[m.kind]}"


def cta(m) -> dict[str, str]:
    """밑에 글: 곳마다 다르게 (유튜브 구독 · 인스타·페북 팔로우). 지금 올리는 곳은 인스타뿐 (사장님 2026-11-03)."""
    t = josa(_topic(m), "을", "를")
    yt = f"나의 {t} 더 자세히 알고 싶다면 구독!"
    # 인스타는 일단 팔로우 (사장님 2026-11-03 "일단 인스타는 댓글 말고 팔로우로 해 일단").
    # 댓글→디엠 자동 응답이 준비되면 댓글로 바꾼다.
    ig = yt.replace("구독!", "팔로우!")
    return {"youtube": yt, "instagram-reel": ig, "facebook-reel": yt.replace("구독!", "팔로우!")}
