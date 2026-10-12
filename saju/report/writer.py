"""리포트 본문 글쓰기.

ClaudeWriter: 장마다 Claude API를 한 번씩 불러 그 장의 모든 칸(slot)을 채운다.
DraftWriter: API 없이 기초 지식으로 초안을 만든다(도안 확인, 테스트, API 장애 시 대비용).

글 형식(slot.format)
- paragraphs: ["문단", ...]
- lead:       {"lead": "한 문장 요약", "paragraphs": [...]}
- summary:    {"bullets": ["", "", ""], "word": "한 문장 조언"}
- fortune:    {"summary": "", "items": [{"label": "일", "text": ""}, ...], "advice": ""}
- plan:       {"notes": ["표 앞 설명 문단"], "rows": [{"when": "", "do": "", "avoid": ""}, ...]}
- qa:         {"items": [{"q": "", "a": ""}, ...]}
- checklist:  ["", ...]
- months:     {"months": [{"summary": "", "good": "", "careful": ""}, x3]}
- bullets:    ["", ...]
"""

from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor

from . import knowledge as K

# 1~14장은 값싼 모델, 결론인 15장은 가장 좋은 모델로 쓴다(한 권 비용을 크게 줄이면서 결론의 품질을 지킨다).
DEFAULT_MODEL = os.environ.get("SAJU_WRITER_MODEL", "claude-haiku-5-5")
FINAL_MODEL = os.environ.get("SAJU_WRITER_FINAL_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("SAJU_WRITER_EFFORT", "medium")

STYLE_RULES = """당신은 사주 리포트 '평생사주'의 본문을 쓰는 작가입니다.

[독자]
- 사주를 처음 보는 일반인이 재미와 취미로 읽습니다.

[문체]
- 해요체로 씁니다. 고객은 "{name}님"이라고 부릅니다.
- 비유, 시적인 표현, 멋 부린 카피를 쓰지 않습니다. 핵심을 쉬운 말로 바로 말합니다.
  (예외: '고전 판단'의 물상 그림은 적힌 그대로 쓰고, 바로 뒤에 생활에서 무슨 뜻인지 풀어 씁니다.)
- 사주 용어(십신, 신강, 격국, 대운 등)가 나오면 처음 나올 때 괄호 안에 쉬운 풀이를 붙입니다. 예: 편관(나를 단련하는 기운)
- 문장은 짧게 씁니다. 한 문단은 2~4문장입니다.
- "~할 수 있어요", "~하기 쉬워요"처럼 가능성으로 말하고, 단정하거나 겁주지 않습니다.

[문장: 처음 읽는 사람도 한 번에 알아듣게]
- 모든 문장에 누가(주어), 무엇을(목적어), 어떻게 하는지가 분명히 드러나게 씁니다. 앞 문장에서 알 수 있어도 빼지 않습니다.
  나쁜 예: "손실이 나면 되찾으려고 더 넣기 쉬워요." 좋은 예: "{name}님은 투자에서 돈을 잃으면, 잃은 돈을 되찾으려고 돈을 더 넣기 쉬워요."
- 한 문장에는 한 가지 내용만 씁니다. 한 문장은 60자 안팎으로, 길어지면 두 문장으로 나눕니다.
- 사주 용어 풀이는 지어낸 표현이나 비유로 쓰지 않습니다. 그 기운이 생활에서 무엇인지 쉬운 말로 씁니다.
  나쁜 예: 겁재(내 몫을 다투는 기운). 좋은 예: 겁재(나와 비슷한 사람과 경쟁하는 기운이에요. 친구나 동료 때문에 돈이 나가기 쉬운 것을 뜻해요).
- "이것", "그것", "이 기운"처럼 가리키는 말이 무엇인지 헷갈리면 그 이름을 다시 씁니다.
- 소리 내어 읽었을 때 어색한 말, 번역한 것 같은 말, 명사를 줄줄이 붙인 말을 쓰지 않습니다.

[사실]
- 사주 글자, 개수, 점수, 연도, 나이, 날짜는 아래 '사주 계산 결과'에 있는 값만 씁니다. 새로 계산하거나 지어내지 않습니다.
- 근거를 말할 때는 어떤 글자나 관계 때문인지 함께 씁니다. 예: "태어난 달에 편관이 있어서"
- 주문 정보의 '요즘 일상'(daily)과 '연애·결혼 상태'(relationship)가 있으면 그 상황에 맞춰 씁니다.
  비어 있는 정보와 자녀 유무는 가정하지 않고, 필요하면 경우를 나눠 씁니다.

[금지]
- 병명을 단정하거나 의학적 진단처럼 쓰지 않습니다. 건강은 생활 습관 중심으로 씁니다.
- 특정 투자 상품, 종목, 금액을 권하지 않습니다.
- 사망, 이혼, 사고를 예언하지 않습니다.
- 성별 고정관념으로 쓰지 않습니다.
- 다른 칸과 같은 문장을 되풀이하지 않습니다.
- "참고용", "참고만 하세요", "재미로 보세요"처럼 풀이의 믿음을 떨어뜨리는 말을 쓰지 않습니다. 점수와 풀이는 사주 근거와 함께 그대로 말합니다.

[내용의 깊이: 30만원짜리 대면 상담을 받은 느낌으로]
- 문단은 '사주 근거 → 생활 속 구체적인 장면 → 바로 해 볼 수 있는 방법' 순서로 씁니다.
- 근거는 한 글자로 끝내지 않고 이어서 씁니다: 어떤 글자가 어디에 있고(예: 태어난 달 지지의 편관) → 다른 글자와 어떤 관계이며(합·충, 많고 적음) → 그래서 어느 해·어느 달에 어떻게 드러나는지.
- 누구에게나 맞는 말 대신, 이 사람 사주에만 있는 글자·개수·관계를 근거로 댑니다. "다른 사람이라면 ~하겠지만 {name}님은 ~해서"처럼 이 사람만의 차이를 보여 줍니다.
- 때를 말할 때는 '사주 계산 결과'에 있는 연도·달·나이를 그대로 짚습니다. "언젠가", "때가 되면" 대신 "OOOO년 O월(OO 절기부터)"처럼 계산 결과에 있는 해와 달을 그대로 넣어 씁니다.
- 장면은 이 사람의 나이, 성별, '요즘 일상', 질문에 맞춰 구체적으로 씁니다. 예: 회의에서 의견이 갈릴 때, 첫 데이트에서, 월급날, 이직 제안을 받았을 때.
- 방법은 오늘부터 할 수 있는 행동으로, 언제·무엇을·얼마나를 넣어 씁니다. 예: "한 달 예산을 세 칸으로 나누기", "용신 색 소품을 책상 오른쪽에 두기", "계약서는 서명 전에 믿을 만한 사람에게 한 번 보여 주기".
- 방법은 그 칸의 주제와 이 사람의 사주에 맞게 새로 생각해 씁니다. 위 예시를 그대로 옮겨 쓰지 않습니다.
- 흔한 방법(하루 뒤에 다시 보기, 메모하기, 심호흡, 산책, 일찍 자기, 물 마시기)은 이 장에서 많아야 한 번만 씁니다. 같은 방법이 책 전체에서 세 번을 넘지 않게, 다른 장과 겹치지 않을 방법을 고릅니다.
- 좋은 점과 조심할 점을 함께 씁니다. 조심할 점에는 반드시 대처 방법을 붙입니다.
- 대처 방법은 문장 끝 다음에 "보완법:", "방법:"처럼 이름표를 붙여 씁니다. 이름표가 붙은 부분은 PDF에서 새 줄로 나옵니다.

[사주에 없는 것]
- '쓸 내용'에 나온 신살·십신·관계가 이 사주에 없거나 0개이면, 없다는 것을 한 문장으로 짧게 말하고 사주에 실제로 있는 다른 근거로 씁니다. 없는 것을 있다고 쓰지 않습니다.
- 신살은 '신살' 목록에 있는 것만 이 사람의 신살로 씁니다. 운(해·달)에 그 글자가 들어오는 것은 '그 해에 도화의 글자가 들어와요'처럼 운의 일로 씁니다.
- 십신·오행 개수를 말할 때는 '십신 무리', '오행'의 값을 그대로 씁니다. 오행 비율(pct)은 숨은 글자까지 합친 힘이라서, 개수가 0개여도 비율이 조금 있을 수 있습니다. 이때는 "겉으로는 없지만 속에 조금 있어요"라고 씁니다.
- 관성(직장·명예) 운은 사주에 상관이 강하면(상관격이거나 상관이 2개 이상) 승진·인정만 쓰지 않고, 윗사람·규칙과 부딪히기 쉬운 면도 함께 씁니다.

[올해 이야기]
- 세운의 첫 해(주문한 해)는 이미 지난 달이 있습니다. 올해 남은 기간을 말할 때는 그 해 점수보다 남은 달의 월운 점수를 근거로 씁니다.

[고전 판단 쓰는 법: 자평진전으로 뼈대, 적천수로 흐름]
- 일·돈·지위·성취는 '고전 판단'의 격국 성패(성격·파격), 좋은 점, 흠, 상신(격을 살리는 글자)을 근거로 씁니다.
- 성격의 결, 감정, 건강, 생활 리듬은 조후(계절의 온도), 통관, 물상을 근거로 씁니다.
- 특별한 격(종격·화기격)이 있으면 그 사주는 '버티기보다 그 기운을 따라갈 때' 잘 풀린다는 점을 중심에 둡니다.
- 운(대운·세운·월운)을 풀 때는 점수와 함께 '격국 효과'를 근거로 댑니다. 도움이면 격을 살리는 글자가 들어오는 때, 방해면 격을 해치는 글자가 들어오는 때입니다.
- 파격이나 흠은 겁주지 말고, 상신이 들어오는 시기와 그때까지의 보완법을 함께 씁니다.
- 물상 그림은 한 장에 한두 번만 씁니다. 고전 이름(자평진전, 적천수)은 2장의 '사주의 뼈대와 흐름' 쪽에서만 소개합니다.

[다 쓴 뒤 스스로 확인]
- 답하기 전에 모든 문장을 처음 읽는 사람의 눈으로 다시 읽습니다. 누가, 무엇을 하는지 빠진 문장, 뜻이 흐린 용어 풀이, 어색한 말을 고친 뒤 답합니다.

[분량]
- 각 칸의 chars(공백 포함 글자 수)를 채웁니다. chars의 95~108% 사이로 써야 쪽이 비거나 넘치지 않습니다.
- 분량이 모자라면 장면 예시와 실천 방법을 더하고, 같은 말을 늘이거나 인사말, "앞서 말했듯이" 같은 채우는 말을 쓰지 않습니다.
"""

FORMAT_SCHEMA = {
    "paragraphs": {"type": "array", "items": {"type": "string"}},
    "bullets": {"type": "array", "items": {"type": "string"}},
    "lead": {"type": "object", "properties": {"lead": {"type": "string"}, "paragraphs": {"type": "array", "items": {"type": "string"}}},
             "required": ["lead", "paragraphs"]},
    "summary": {"type": "object", "properties": {"bullets": {"type": "array", "items": {"type": "string"}}, "word": {"type": "string"}},
                "required": ["bullets", "word"]},
    "fortune": {"type": "object", "properties": {
        "summary": {"type": "string"},
        "items": {"type": "array", "items": {"type": "object", "properties": {"label": {"type": "string"}, "text": {"type": "string"}},
                                             "required": ["label", "text"]}},
        "advice": {"type": "string"}}, "required": ["summary", "items", "advice"]},
    "plan": {"type": "object", "properties": {"rows": {"type": "array", "items": {"type": "object", "properties": {
        "when": {"type": "string"}, "do": {"type": "string"}, "avoid": {"type": "string"}},
        "required": ["when", "do", "avoid"]}}, "notes": {"type": "array", "items": {"type": "string"}}},
        "required": ["notes", "rows"]},
    "qa": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {
        "q": {"type": "string"}, "a": {"type": "string"}}, "required": ["q", "a"]}}}, "required": ["items"]},
    "checklist": {"type": "array", "items": {"type": "string"}},
    "months": {"type": "object", "properties": {"months": {"type": "array", "items": {"type": "object", "properties": {
        "summary": {"type": "string"}, "good": {"type": "string"}, "careful": {"type": "string"}},
        "required": ["summary", "good", "careful"]}}}, "required": ["months"]},
}


def strict_schema(node):
    """구조화 출력은 모든 객체에 additionalProperties: false가 있어야 한다."""
    if isinstance(node, dict):
        out = {k: strict_schema(v) for k, v in node.items()}
        if out.get("type") == "object":
            out["additionalProperties"] = False
        return out
    if isinstance(node, list):
        return [strict_schema(x) for x in node]
    return node


FINAL_RULES = """[이 장은 책의 결론입니다]
- 앞 장에 나온 보완법과 조언을 빠짐없이 모으고, 겹치는 것은 합쳐서 더 구체적으로 씁니다.
- 명리학의 흐름(용신, 대운·세운의 흐름)에서 벗어나지 않게, 어떤 글자·시기 때문인지 근거를 함께 씁니다.
- 원칙: 조심할 시기에는 피해를 최소로(미리 대비하기, 큰 결정은 미루기, 계약·건강은 한 번 더 확인하기), 좋은 시기에는 운을 최대로(미뤄 둔 일 시작하기, 사람 만나기, 도전하기).
- 현실적이고 납득 가능한 행동만 씁니다. 부적, 굿, 특정 상품 구매는 권하지 않습니다.
- 읽는 사람의 불안이 풀리도록, 걱정마다 '왜 괜찮은지(근거)'와 '무엇을 하면 되는지(행동)'를 함께 답합니다.
- 겁주는 말과 막연한 위로("다 잘될 거예요")는 쓰지 않습니다.
- 아래 '앞 장에서 쓴 글'에 나온 내용과 숫자를 그대로 이어받고, 서로 어긋나지 않게 씁니다.
"""


def facts_digest(f: dict) -> dict:
    """AI에게 보낼 사주 계산 결과(필요한 것만)."""
    d = _digest(f)
    if f.get("romance"):
        d["연애 재료"] = romance_digest(f["romance"])
    if f.get("theme"):
        d[f["theme"]["label"]] = f["theme"]["digest"]
    return d


def romance_digest(r: dict) -> dict:
    keep = ("love_signs", "love_score", "score")
    return {
        **{k: r[k] for k in ("spouse_group", "spouse_gods", "spouse_count", "spouse_seats", "main_seat", "day_branch",
                             "day_branch_relations", "peach", "peach_branches", "best_years", "best_months", "careful_months",
                             "marriage_periods", "status", "experience")},
        "연도별 인연": [{"year": y["year"], "ganzhi": y["ganzhi"], **{k: y[k] for k in keep}} for y in r["years"]],
        "달별 인연": [{"start_text": m["start_text"], "ganzhi": m["ganzhi"], **{k: m[k] for k in keep}} for m in r["months"]],
        "대운별 인연": [{"age_text": p["age_text"], "ganzhi": p["ganzhi"], "state": p["state"], **{k: p[k] for k in keep}} for p in r["periods"]],
    }


def _digest(f: dict) -> dict:
    return {
        "고객": f["person"], "주문": f["order"], "불확실한 점": f["uncertainties"],
        "사주표": [{k: p.get(k) for k in ("label", "ganzhi", "hanja", "stem_element", "branch_element",
                                         "stem_ten_god", "branch_ten_god", "hidden_text", "twelve_stage", "animal")}
                   for p in f["pillars"]],
        "일간": {k: f["day_master"][k] for k in ("stem", "hanja", "element", "image", "yin_yang", "basic", "strengths", "weaknesses")},
        "오행": [{k: e[k] for k in ("el", "name", "count", "pct", "status")} for e in f["elements"]],
        "십신 무리": [{k: g[k] for k in ("group", "label", "n")} for g in f["ten_god_groups"]],
        "신강약": {k: f["strength"].get(k) for k in ("label", "score", "득령", "득지")},
        "격국": {k: f["gyeokguk"][k] for k in ("name", "ten_god", "text")},
        "용신": {k: f["yongsin"].get(k) for k in ("조후", "억부", "억부_근거", "chosen")}, "행운": f["lucky"],
        "고전 판단": f.get("classics"),
        "원국 합충": [{k: r.get(k) for k in ("type", "between", "chars")} for r in f["relations"]],
        "신살": [{k: s[k] for k in ("name", "label")} for s in f["shinsal"]],
        "대운": {"방향": f["daewoon"]["direction"], "대운수": f["daewoon"]["number"],
                 "목록": [{k: p[k] for k in ("age_text", "years_text", "ganzhi", "hanja", "stem_ten_god", "branch_ten_god",
                                           "twelve_stage", "relations_text", "gyeok_effect", "score", "state")} for p in f["daewoon"]["periods"]]},
        "세운": [{k: s[k] for k in ("year", "ganzhi", "hanja", "animal", "stem_ten_god", "branch_ten_god", "relations_text", "gyeok_effect", "score")}
                 for s in f["sewoon"]],
        "월운": [{k: m[k] for k in ("start_text", "term", "ganzhi", "stem_ten_god", "branch_ten_god", "relations_text", "gyeok_effect", "score")}
                 for m in f["months"]],
        "읽는 법": {
            "오행": "count는 겉으로 보이는 글자 수, pct는 숨은 글자까지 합친 힘의 비율이에요. count가 0이어도 pct가 조금 있으면 '겉으로는 없지만 속에 조금 있다'는 뜻이에요.",
            "올해": f"세운의 첫 해({f['sewoon'][0]['year']}년)는 이미 지난 달이 있어요. 올해 남은 기간은 월운 점수를 함께 보고 씁니다." if f.get("sewoon") else "",
        },
        "참고 지식": {
            "십신 뜻": {k: v["meaning"] for k, v in K.TEN_GOD.items()},
            "신살 뜻": {n: K.SHINSAL.get(n, "") for n in f["shinsal_names"]},
            "합충 뜻": K.RELATION,
        },
    }


FINAL_SECTION = "15"


ADVICE_MARK = re.compile(r"(보완법|방법|대처법|조언|주의|팁)\s*:")


def previous_text(texts: dict, limit: int = 20000) -> str:
    """앞 장에서 쓴 글 가운데 마지막 장에 필요한 것만 모은다.

    15장은 앞 장의 보완법·조언을 모아 쓰므로, 이름표(보완법:, 방법: 등)가 붙은 문단과
    각 장의 요약·한 줄 정리만 넘긴다. 앞 글 전체를 넘기면 가장 비싼 모델의 읽기 비용이 몇 배로 늘어난다."""
    def flat(v):
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return [x for i in v for x in flat(i)]
        if isinstance(v, dict):
            return [x for i in v.values() for x in flat(i)]
        return []
    lines = []
    for k, v in texts.items():
        keep_all = isinstance(v, dict) and ("bullets" in v or "lead" in v or "advice" in v)
        parts = flat(v) if keep_all else [x for x in flat(v) if ADVICE_MARK.search(x)]
        if parts:
            lines.append(f"[{k}] " + " ".join(parts))
    return "\n".join(lines)[:limit]


# 반복·문장 문제로 다시 쓰는 칸은 한 권에 이만큼까지(사실 오류는 개수와 상관없이 모두 고친다)
MAX_REPEAT_FIX = int(os.environ.get("SAJU_MAX_REPEAT_FIX", "6"))

FIX_RULES = """[고쳐 쓰기]
- 각 칸의 '먼저 쓴 글'에서 '고칠 점'만 고쳐 다시 씁니다. 나머지 내용, 형식, 분량(chars)은 그대로 지킵니다.
- 사주에 없는 것, 계산 결과에 없는 숫자·연도는 지우고 계산 결과에 있는 근거로 바꿉니다.
- 반복이라고 한 방법은 이 칸의 주제와 이 사람 사주에 맞는 다른 구체적인 방법으로 바꿉니다.
- 문장 문제는 주어와 목적어(무엇을)를 채우고, 긴 문장은 두 문장으로 나눕니다.
- 분량 문제는 chars에 맞춥니다. 모자라면 같은 말을 늘이지 말고 장면과 방법을 더하고, 넘치면 덜 중요한 문장을 뺍니다.
"""


class ClaudeWriter:
    # 상품마다 바꿔 쓰는 글쓰기 규칙(기본값은 평생사주)
    style = STYLE_RULES
    final_section = FINAL_SECTION
    final_rules = FINAL_RULES

    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None, max_workers: int = 6,
                 final_model: str = FINAL_MODEL, effort: str = EFFORT):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self.model = model
        self.final_model = final_model
        self.effort = effort
        self.max_workers = max_workers
        self.usage: list[dict] = []   # 장마다 쓴 토큰(비용 확인용)
        self.issues: list[dict] = []  # 마지막 검사에서 남은 문제
        self.fixed: dict[str, list[str]] = {}  # 검사에 걸려 다시 쓴 칸과 그 까닭

    def _section(self, f: dict, section: dict, slots: list[dict], previous: str = "", fix: dict | None = None) -> dict:
        schema = strict_schema({"type": "object", "properties": {s["id"]: FORMAT_SCHEMA[s["format"]] for s in slots},
                                "required": [s["id"] for s in slots]})
        system = [
            {"type": "text", "text": self.style.format(name=f["person"]["name"])},
            {"type": "text", "text": "사주 계산 결과:\n" + json.dumps(facts_digest(f), ensure_ascii=False),
             "cache_control": {"type": "ephemeral"}},
        ]
        brief = {
            "장": f"{section['no']}. {section['title']}" + (f" — {section['subtitle']}" if section["subtitle"] else ""),
            "칸": [{"id": s["id"], "쪽 제목": s["title"], "쓸 내용": s["guide"], "chars": s["chars"], "형식": s["format"],
                   **({"고칠 점": fix[s["id"]]["issues"], "먼저 쓴 글": fix[s["id"]]["text"]} if fix else {})} for s in slots],
        }
        ask = "아래 장의 칸을 모두 채워 JSON으로 답해 주세요. 칸 id가 키입니다.\n" + json.dumps(brief, ensure_ascii=False)
        if fix:
            ask = FIX_RULES + "\n" + ask
        if previous:
            ask = self.final_rules + "\n앞 장에서 쓴 글:\n" + previous + "\n\n" + ask
        model = self.final_model if previous else self.model
        # 글이 길어서 스트리밍으로 받는다(요청 시간 초과 방지)
        with self.client.messages.stream(
            model=model, max_tokens=64000, system=system,
            output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": ask}],
        ) as stream:
            msg = stream.get_final_message()
        u = msg.usage
        self.usage.append({"section": section["no"], "model": model, "input": u.input_tokens, "output": u.output_tokens,
                           "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0,
                           "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0, "fix": bool(fix)})
        if msg.stop_reason != "end_turn":
            raise RuntimeError(f"{section['no']}장 글이 끝까지 오지 않았어요(stop_reason={msg.stop_reason})")
        text = next(b.text for b in msg.content if b.type == "text")
        return json.loads(text)

    def write(self, f: dict, sections: list[dict]) -> dict:
        from .outline import slots_by_section
        from . import verify as V
        by_no = {s["no"]: s for s in sections}
        jobs = slots_by_section(sections)
        out: dict = {}
        # 마지막 장은 앞 장의 보완법·조언을 모아야 하므로 나머지를 다 쓴 뒤에 쓴다
        first = {no: sl for no, sl in jobs.items() if no != self.final_section}
        with ThreadPoolExecutor(self.max_workers) as ex:
            futures = {no: ex.submit(self._section, f, by_no[no], sl) for no, sl in first.items()}
            for no, fut in futures.items():
                out.update(fut.result())
        # 마지막 장을 쓰기 전에 앞 장을 검사하고, 걸린 칸만 한 번 다시 쓴다(마지막 장이 고친 글을 이어받게)
        final_ids = {s["id"] for s in jobs.get(self.final_section, [])}
        first_slots = [s for sl in first.values() for s in sl]
        self._fix(f, by_no, first, out, V.check(f, out, final_ids) + V.lengths(out, first_slots))
        if self.final_section in jobs:
            final_slots = jobs[self.final_section]
            out.update(self._section(f, by_no[self.final_section], final_slots, previous_text(out)))
            after = [i for i in V.check(f, out, final_ids) if i["slot"] in final_ids and i["kind"] not in ("반복", "문장")]
            if after:
                self._fix(f, by_no, {self.final_section: final_slots}, out, after, previous_text(out))
            # 마지막 장의 분량만 맞추는 다시 쓰기는 먼저 쓴 글을 고치는 일이라 값싼 모델로 한다
            short = V.lengths(out, final_slots)
            if short:
                self._fix(f, by_no, {self.final_section: final_slots}, out, short)
        self.issues = V.check(f, out, final_ids) + V.lengths(out, [s for sl in jobs.values() for s in sl])
        return out

    def _fix(self, f: dict, by_no: dict, jobs: dict, out: dict, issues: list[dict], previous: str = "") -> None:
        """검사에 걸린 칸을 장별로 묶어 한 번씩 다시 쓴다. 반복은 MAX_REPEAT_FIX칸까지만 고친다(비용을 묶어 둔다)."""
        from . import verify as V
        soft = ("반복", "문장")   # 사실 오류가 아닌 것: 한 권에 MAX_REPEAT_FIX칸까지만 따로 다시 쓴다
        facts_issues = [i for i in issues if i["kind"] not in soft]   # 사실 오류와 분량은 걸린 칸을 모두 고친다
        fact_slots = {i["slot"] for i in facts_issues}
        soft_slots = [x for x in dict.fromkeys(i["slot"] for i in issues if i["kind"] in soft) if x not in fact_slots][:MAX_REPEAT_FIX]
        # 사실 오류로 어차피 다시 쓰는 칸은 문장·반복 문제도 함께 고친다(비용 그대로)
        picked = V.by_slot(facts_issues + [i for i in issues if i["kind"] in soft and (i["slot"] in fact_slots or i["slot"] in soft_slots)])
        if not picked:
            return
        self.fixed = {**getattr(self, "fixed", {}), **picked}
        todo = {}
        for no, sl in jobs.items():
            redo = [s for s in sl if s["id"] in picked]
            if redo:
                todo[no] = {"slots": redo, "fix": {s["id"]: {"issues": picked[s["id"]], "text": out[s["id"]]} for s in redo}}
        with ThreadPoolExecutor(self.max_workers) as ex:
            futures = [ex.submit(self._section, f, by_no[no], t["slots"], previous, t["fix"]) for no, t in todo.items()]
            for fut in futures:
                try:
                    out.update(fut.result())
                except Exception:   # 다시 쓰기가 실패하면 먼저 쓴 글을 그대로 둔다
                    pass


# ── API 없이 만드는 초안 ──────────────────────────────────────

def _ten_god_word(tg: str) -> str:
    return f"{tg}({K.TEN_GOD[tg]['simple']})" if tg in K.TEN_GOD else tg


class DraftWriter:
    """기초 지식만으로 쓰는 초안. 문장 수가 적고 반복이 있지만 쪽 구성과 디자인을 확인할 수 있다."""

    def write(self, f: dict, sections: list[dict]) -> dict:
        from .outline import slots_by_section
        out = {}
        for sl in slots_by_section(sections).values():
            for s in sl:
                out[s["id"]] = self._one(f, s)
        return out

    def _one(self, f: dict, s: dict):
        name = f["person"]["name"]
        dm = f["day_master"]
        fmt = s["format"]
        many = [e for e in f["elements"] if e["status"] == "많음"]
        few = [e for e in f["elements"] if e["status"] == "부족"]
        base = [
            f"{name}님의 일간(나를 나타내는 글자)은 {dm['stem']}({dm['hanja']})이에요. {dm['image']}의 기운으로, {dm['basic']}",
            f"사주 전체로 보면 {', '.join(e['name'] for e in many) or '특별히 넘치는 기운 없이'} 기운이 강하고 "
            f"{', '.join(e['name'] for e in few) or '모자란 기운'}이 약해요. {f['strength']['text']}",
            f"태어난 달을 기준으로 한 사주의 틀(격국)은 {f['gyeokguk']['name']}이에요. {f['gyeokguk']['text']}",
        ]
        if f.get("classics"):
            c = f["classics"]
            base.append(f"자평진전으로 보면 {c['gyeok']}은 {c['verdict']}이에요. {c['verdict_text']}")
            if c["image"]:
                base.append(f"물상으로 보면 '{c['image']['title']}'의 모습이에요. {c['image']['text']}")
        if fmt == "lead":
            return {"lead": f"{dm['image']}처럼 {dm['strengths'][0]}과 {dm['strengths'][1]}이 돋보이는 사람이에요.",
                    "paragraphs": base[:2]}
        if fmt == "summary":
            return {"bullets": [f"일간 {dm['stem']}: {dm['strengths'][0]}, {dm['strengths'][1]}",
                                f"{f['strength']['label']} · {f['gyeokguk']['name']}",
                                f"도움 되는 기운: {f['lucky']['element_name']}({f['lucky']['element']})"],
                    "word": f"{dm['weaknesses'][0]}만 조금 덜어 내면 장점이 더 크게 보여요."}
        if fmt == "fortune":
            target = self._fortune_target(f, s["id"])
            tg = [target["stem_ten_god"], target["branch_ten_god"]]
            rel = ", ".join(target["relations_text"]) or "특별한 합충 없이"
            items = [{"label": "일", "text": f"{_ten_god_word(tg[0])} 기운이 일에 영향을 줘요. {K.TEN_GOD[tg[0]]['meaning']}"},
                     {"label": "돈", "text": f"{_ten_god_word(tg[1])} 기운이 생활과 재물에 작용해요. {K.TEN_GOD[tg[1]]['meaning']}"},
                     {"label": "연애", "text": f"내 사주와 {rel} 관계가 생겨요. 사람 사이의 변화를 살펴보세요."},
                     {"label": "건강", "text": "무리한 일정은 줄이고 잠을 충분히 자는 것이 좋아요."}]
            return {"summary": f"{target['ganzhi']}({target['hanja']})의 기운이 들어오는 시기예요. 흐름 점수는 {target['score']}점이에요.",
                    "items": items, "advice": "좋은 흐름일 때 미뤄 둔 일을 시작하고, 부딪히는 시기에는 속도를 늦추세요."}
        if fmt == "months":
            a, b = self._month_range(f, s["id"])
            return {"months": [{"summary": f"{m['term']}부터 시작하는 {m['ganzhi']}월이에요. {_ten_god_word(m['stem_ten_god'])}의 달이에요.",
                                "good": K.TEN_GOD[m["stem_ten_god"]]["meaning"],
                                "careful": "합충 관계가 있어 일정과 말을 한 번 더 확인하세요." if m["relations_text"] else "큰 부딪힘이 없는 달이에요."}
                               for m in f["months"][a:b]]}
        if fmt == "plan":
            rows = []
            for sw in f["sewoon"]:
                good = sw["score"] >= 60
                rows.append({"when": f"{sw['year']}년", "do": "미뤄 둔 일을 시작하고 사람을 많이 만나세요." if good else "하던 일을 다지고 건강을 챙기세요.",
                             "avoid": "무리한 확장" if good else "큰 계약과 보증"})
            return {"notes": ["해마다 할 일과 피할 일을 정리했어요."], "rows": rows}
        if fmt == "qa":
            return {"items": [{"q": "올해 큰 결정을 해도 될까요?", "a": f"흐름 점수와 대운을 보면 서두르기보다 준비를 먼저 하는 것이 좋아요. {f['lucky']['element_name']} 기운이 들어오는 해에 움직이세요."},
                              {"q": "돈이 모이지 않아 걱정이에요.", "a": "재물이 들어오는 해를 표시해 두고, 그 전까지는 지출을 세 칸으로 나눠 관리하세요."}]}
        if fmt == "checklist":
            return [f"행운의 색({f['lucky']['color'].split('·')[0]}) 소품 하나 지니기", "중요한 결정은 하루 뒤에 다시 보기",
                    "일주일에 한 번 속마음 말하기", "한 달에 하루 쉬는 날 먼저 정하기", "잠들기 전 10분 생각 적기"]
        if fmt == "bullets":
            return [f"성격: {dm['basic']}", f"사주의 틀: {f['gyeokguk']['text']}",
                    f"도움 되는 기운: {f['lucky']['element_name']} · 색 {f['lucky']['color']}"]
        n = max(1, round(s["chars"] / 200))
        return (base * 3)[:n]

    @staticmethod
    def _fortune_target(f: dict, sid: str) -> dict:
        kind, key = sid.split("_", 1)
        if kind == "dw":
            return f["daewoon"]["periods"][int(key)]
        return next(x for x in f["sewoon"] if str(x["year"]) == key)

    @staticmethod
    def _month_range(f: dict, sid: str) -> tuple[int, int]:
        q = int(sid.split("_")[1])
        return q * 3, q * 3 + 3
