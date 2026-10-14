"""PDF 전 글 검사, 걸린 칸 다시 쓰기, 올해 점수, 먼 대운 빼기."""

import copy
import json
from datetime import date

from saju.chart import analyze_person
from saju.report import OrderInfo, DraftWriter, prepare_product, verify as V
from saju.report import theme as T
from saju.report.writer import ClaudeWriter

ME = {"name": "윤서진", "sex": "female", "birth": "1993-09-05", "calendar": "solar", "timeAccuracy": "exact",
      "time": "11:50", "birthPlace": {"status": "known", "regionChoice": "1100000000"}}
ORDER = OrderInfo(date(2026, 10, 11), "이직을 해도 될까요?")


def _career():
    return prepare_product("career", analyze_person(ME, current_year=2026), ORDER)


def _absent(f):
    return next(n for n in ("역마살", "도화살", "화개살", "괴강살", "백호살") if n not in f["shinsal_names"])


def test_check_finds_made_up_facts():
    _, f, _ = _career()
    n = _absent(f)
    real = {g["group"]: g["n"] for g in f["ten_god_groups"]}["재성"]
    texts = {"a": [f"사주에 {n}이 있어요. 재성이 {real + 5}개예요. 이 해는 83점이에요. 2190년에 좋아요."],
             "b": [f"사주에 {n}은 없어요. 재성이 {real}개예요."]}
    kinds = sorted(i["kind"] for i in V.check(f, texts))
    assert kinds == ["개수", "없는 신살", "연도", "점수"]
    assert all(i["slot"] == "a" for i in V.check(f, texts))


def test_repeats_over_limit_only():
    texts = {f"s{i}": [f"중요한 결정은 하루 뒤에 다시 보세요. {i}"] for i in range(5)}
    hits = V.repeats(texts)
    assert [h["slot"] for h in hits] == ["s3", "s4"]
    assert V.repeats(texts, {"s3", "s4"}) == []


def test_current_year_uses_remaining_months():
    _, f, _ = _career()
    years, months = f["theme"]["years"], f["theme"]["months"]
    rest = [m["t_score"] for m in months if m["year"] == years[0]["year"]]
    assert years[0]["rest_months"] == len(rest)
    raw = T.marked({**f, "sewoon": f["sewoon"][:1], "months": []}, lambda x: {"t_score": x["score"], "t_signs": []})[0][0]["t_score"]
    lo, hi = sorted((raw, sum(rest) / len(rest)))
    assert lo - 1 <= years[0]["t_score"] <= hi + 1


def test_far_periods_left_out():
    _, f, _ = _career()
    rows = f["theme"]["digest"]["대운별"]
    ages = [int(r["age_text"].split("~")[0]) for r in rows if r["state"] != "지난"]
    assert ages and max(ages) <= min(80, f["person"]["age"] + 40)


class _Fake:
    """API 없이 ClaudeWriter의 흐름(장별 쓰기 → 검사 → 걸린 칸만 다시 쓰기 → 마지막 장)을 확인한다."""

    def __init__(self, good, bad_slot, bad_text):
        self.good, self.bad_slot, self.bad_text, self.calls = good, bad_slot, bad_text, []
        self.messages = self

    def stream(self, **kw):
        fake = self
        ask = kw["messages"][0]["content"]
        brief = json.loads(ask[ask.index('{"장"'):])
        fix = "고칠 점" in brief["칸"][0]
        out = {c["id"]: copy.deepcopy(fake.good[c["id"]]) for c in brief["칸"]}
        if not fix and fake.bad_slot in out:
            out[fake.bad_slot] = [fake.bad_text]
        fake.calls.append((brief["장"], fix, kw["model"]))

        class S:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def get_final_message(self):
                usage = type("U", (), {"input_tokens": 1, "output_tokens": 1})()
                block = type("B", (), {"type": "text", "text": json.dumps(out, ensure_ascii=False)})()
                return type("M", (), {"content": [block], "stop_reason": "end_turn", "usage": usage})()
        return S()


def test_writer_rewrites_flagged_slot_once():
    M, f, secs = _career()
    good = DraftWriter().write(f, secs)
    w = ClaudeWriter.__new__(ClaudeWriter)
    w.client = _Fake(good, "c4_field", f"사주에 {_absent(f)}이 있어서 자리를 자주 옮겨요.")
    w.model, w.final_model, w.effort, w.max_workers, w.usage, w.issues = "h", "o", "medium", 4, [], []
    w.style, w.final_section = M.STYLE, M.FINAL_SECTION
    out = w.write(f, secs)
    assert out["c4_field"] == good["c4_field"]
    fixes = [c for c in w.client.calls if c[1]]
    assert any(c[0].startswith("4.") for c in fixes)
    first_writes = [c for c in w.client.calls if not c[1]]
    assert first_writes[-1][2] == "o"   # 마지막 장은 앞 장을 고친 뒤에, 좋은 모델로
    assert all(c[2] == "h" for c in w.client.calls if c[1])   # 다시 쓰기는 값싼 모델로
    assert not [i for i in w.issues if i["kind"] not in ("반복", "문장", "분량")]


def test_unclear_sentences():
    _, f, _ = _career()
    texts = {"a": ["손실이 나면 되찾으려고 더 넣기 쉬워요."],
             "b": ["손실이 나면 잃은 돈을 되찾으려고 돈을 더 넣기 쉬워요."],
             "c": ["가" * 95 + "요."],
             "d": ["보완법: 겁재(나와 비슷한 사람과 경쟁하는 기운이에요. 친구나 동료 때문에 돈이 나가기 쉬운 것을 뜻해요)가 있어요."]}
    assert sorted(i["slot"] for i in V.check(f, texts) if i["kind"] == "문장") == ["a", "c"]


def test_length_check():
    slots = [{"id": "a", "chars": 100}, {"id": "b", "chars": 100}, {"id": "c", "chars": 100}]
    texts = {"a": ["가" * 60], "b": ["가" * 100], "c": ["가" * 130]}
    assert [i["slot"] for i in V.lengths(texts, slots)] == ["a", "c"]


def test_crowded_terms():
    crowded = {"a": ["박지은님은 일간이 정화이고, 그 사람은 신금이에요. 식상이 3개 있고, 그 사람은 인성이 3개예요."]}
    calm = {"b": ["박지은님 사주에는 식상이 3개 있어요. 식상은 내 생각과 마음을 밖으로 꺼내는 기운이에요.",
                  "기억할 한 줄: 박지은님은 말해야 풀리고(식상 3개), 그 사람은 생각해야 풀려요(인성 3개)."]}
    assert [i["kind"] for i in V.crowded_terms(crowded)] == ["용어"]
    assert V.crowded_terms(calm) == []
    assert V.crowded_terms(crowded, skip={"a"}) == []
