# saju-engine

운명서재(사주 리포트 서비스)의 분석 서버에 들어갈 사주 계산 엔진입니다.
고객이 입력한 출생 정보로 명식을 계산하고, 리포트 작성에 필요한 분석 결과를 JSON으로 돌려줍니다.

## 지금 되는 것

- **만세력**: 24절기 시각(VSOP87 태양 위치, 1940~2050년 독립 구현과 30초 이내 일치), 음력·윤달 변환
- **한국 표준시 이력**: 1954~1961년 UTC+8:30, 1948~1960년대·1987~1988년 서머타임, 서머타임 중복·누락 시각 경고
- **진태양시 보정**: 출생지 경도 보정(기본), 균시차 포함 진태양시(선택)
- **사주팔자**: 입춘 기준 년주, 절입 기준 월주, 자시 규칙 선택(23시 기준 / 야자시·조자시)
- **원국 분석**: 지장간, 십신, 12운성, 오행 개수·세력, 신강·신약, 격국, 용신 후보(억부·조후)
- **관계**: 천간합·충, 육합·삼합·방합·반합, 충·형·파·해·원진
- **신살**: 도화, 역마, 화개, 천을귀인, 문창귀인, 양인, 홍염, 백호, 괴강, 공망
- **운**: 대운(순행·역행, 대운수), 세운, 월운 + 원국과의 합충
- **두 사람 비교**: 일간 관계, 배우자궁(일지), 띠, 오행 보완 (깊은 궁합·재회사주용)
- **불확실성 처리**: 시간 범위·시간 미상·지역 미상·양음력 미확인이면 가능한 경우를 모두 계산해
  공통 기둥과 후보 명식을 나눔. 모르는 시간이나 지역을 정오·서울로 가정하지 않음.

## 사용

```bash
pip install -e ".[dev]"

# 명령줄
python -m saju --name 홍길동 --sex male --birth 1990-05-15 --time 10:30 --region 1100000000
python -m saju --sex female --birth 1988-03-02 --calendar lunar --json

# 테스트
pytest
```

```python
from saju import analyze_person

result = analyze_person({
    "name": "홍길동", "sex": "male",
    "birth": "1990-05-15", "calendar": "solar",
    "timeAccuracy": "exact", "time": "10:30",
    "birthPlace": {"status": "known", "regionChoice": "1100000000"},
})
```

입력 형식은 운명서재 화면의 사람 정보(`timeAccuracy`, `timeRange`, `birthPlace` 등)와 같습니다.
지역 코드는 화면의 `KOREA_REGIONS`(시·도 코드)를 그대로 씁니다.

## 구조

| 파일 | 내용 |
|---|---|
| `saju/astro.py` | 태양 황경, 24절기 |
| `saju/timeutil.py` | 한국 표준시 이력, 태양시 보정 |
| `saju/regions.py` | 시·도별 경도표 |
| `saju/pillars.py` | 사주팔자 계산 |
| `saju/analysis.py` | 십신, 오행, 12운성, 합충, 신살, 신강약, 격국, 용신 후보 |
| `saju/luck.py` | 대운, 세운, 월운 |
| `saju/pair.py` | 두 사람 비교 |
| `saju/chart.py` | 입력 처리, 불확실성 비교, 전체 결과 |
| `saju/report/` | 평생사주 리포트(목차 15장, 약 114쪽 PDF) |
| `docs/product-plan.md` | 상품별 프로그램 계획 |

## 평생사주 리포트 (0.2.0)

```bash
pip install -e ".[report]"
export ANTHROPIC_API_KEY=...        # 없으면 초안 글로 만들어요(디자인 확인용)
python -m saju.report --name 홍길동 --sex male --birth 1990-05-15 --time 10:30 \
    --region 1100000000 --question "올해 이직해도 될까요?" --daily 직장 --out report.pdf
```

| 파일 | 하는 일 |
|---|---|
| `report/facts.py` | 계산 결과 → 리포트 재료(글자, 개수, 점수, 대운 지금 위치, 주문 달부터 12개월, 행운 아이템) |
| `report/outline.py` | 확정 목차 15장을 쪽 단위로 정의. 쪽마다 제목, 그림, 글 칸(목표 글자 수) |
| `report/writer.py` | `ClaudeWriter`: 장마다 Claude API 1회(구조화 출력으로 JSON 받음, 계산 결과는 프롬프트 캐시, 장별 토큰은 `usage`에 기록). `DraftWriter`: API 없이 초안 |
| `report/knowledge.py` | 오행·십신·12운성·신살·합충 쉬운 말 풀이, 용어 사전 |
| `saju/classics.py`, `report/mulsang.py` | 자평진전(격국 성패·상신), 적천수(화기격·종격·조후·통관), 물상 판단과 풀이 |
| `report/render.py`, `templates/` | 동양풍 도안(한지 바탕, 14pt 이상) HTML → WeasyPrint PDF |

- 글 규칙: 비유 없이 쉬운 말, 용어는 처음 나올 때 괄호 풀이, 계산 결과에 있는 값만 사용, 병명·투자·사망 단정 금지.
- 쪽수: 한 쪽 글 약 760자 기준. 실제 글로 만들면 약 110~130쪽(2026-10-11 실제 샘플 128쪽).
- 판단 순서: 화기격 → 종격 → 급한 조후 → 통관 → 격국 상신 → 억부. 일·돈은 격국, 성격·건강은 조후·물상을 근거로 쓴다.

### AI 모델과 비용

| 장 | 모델 | 설정 |
|---|---|---|
| 1~14장 | `claude-haiku-5-5` | `SAJU_WRITER_MODEL` |
| 15장(마지막 조언) | `claude-opus-5-5` | `SAJU_WRITER_FINAL_MODEL` |
| 생각 깊이 | `medium` | `SAJU_WRITER_EFFORT` |

- 1~14장은 동시에 쓰고, 15장은 앞 장의 보완법·조언·요약만 받아 맨 나중에 쓴다.
- 2026-10-11 실제 1권(128쪽, 약 5분): 약 0.51달러 = 약 710원. 1~14장 약 120원, 15장 약 590원.
  15장도 Haiku로 쓰면 1권 약 140원(15장 질문 답이 덜 구체적이라 Opus 유지).
- 클라우드 셸에 `ANTHROPIC_BASE_URL`이 잡혀 있으면 지우고 실행한다.
- 15장(해결 방법과 마지막 조언)은 앞 장 글을 모두 받아 맨 나중에 써요. 끝에 사이트 순서대로 다른 상품 7개 안내(`report/products.py`, 사이트 주소는 `SAJU_SITE_URL`).
- 글꼴: 고운바탕, 송명(SIL OFL, `report/fonts/`).

## 연애사주

```bash
python -m saju.report --product romance --name 이수아 --sex female --birth 2002-04-17 --time 08:40 \
    --region 1100000000 --relationship "지금은 솔로예요" --experience "1~2번" \
    --question "다음 연애는 언제 시작될까요?" --out romance.pdf
```

- 목차 10장, 약 50쪽(목차 원본: 프로젝트 `plan/romance-report-toc.md`). 평생사주와 같은 엔진·도안·글쓰기 방식.
- `report/romance.py`: 연애 재료(배우자 별·배우자 자리·도화, 연도·달·대운별 인연 표시와 인연 점수), 목차, 글 규칙.
- 1~9장 Haiku, 10장(마지막 조언) Opus. 끝에 다른 상품 안내(짝사랑·썸이면 깊은 궁합, 이별 후면 재회사주를 맨 위로).
- 평생사주 결과는 바뀌지 않음(같은 입력으로 HTML과 AI 요청 내용이 v1.0.0과 글자 단위로 같음).

## 주제 사주 6종 (재회·깊은 궁합·재물·직업·이직·사업·건강)

```bash
# 한 사람 상품: wealth, career, business, health
python -m saju.report --product career --name 윤서진 --sex female --birth 1993-09-05 --time 11:50 \
    --region 1100000000 --answer concern=이직을 고민해요 --question "내년에 옮겨도 될까요?" --out career.pdf
# 두 사람 상품: reunion, intimate (상대방 정보 필수)
python -m saju.report --product reunion --name 박지은 --sex female --birth 1997-08-23 --time 14:20 \
    --partner-name 정민호 --partner-sex male --partner-birth 1995-03-11 --partner-time 22:10 \
    --answer "breakup=3~6개월 정도예요" --out reunion.pdf
```

- 상품마다 목차 12장 + 마지막 조언 뒤 "다른 사주도 궁금하다면", 50쪽 이상. 목차 원본과 가상 인터뷰·궁금한 주제 20가지는 프로젝트 `plan/<상품>-interview-topics.md`.
- `report/theme.py`: 공통 도구(연도·달·대운 표시와 점수, 표 쪽, 그래프). `report/<상품>.py`: 그 상품의 재료, 목차, 글 규칙, 다른 상품 순서.
- 1~11장 Haiku, 12장(마지막 조언) Opus. `--use-texts 파일.json`으로 미리 쓴 글을 넣어 API 없이 PDF를 만들 수 있음.
- 표지 색: 재회·궁합·재물·직업은 사이트 캐릭터 옷 색, 사업·건강은 임시 색.
- 평생사주·연애사주 결과는 바뀌지 않음(HTML 공백 한 줄 외 동일).

## 다음 단계

1. 문장 검수(금지어, 계산값 대조). 실제 문장 품질은 2026-10-11 확인 완료
2. 화면 연동 서버(`/api/intake/assess`, `/api/orders`, 토스페이먼츠, 메일 발송)
3. 주제 사주 6종 실제 글 품질 확인(샘플은 API 없이 작성)
4. 시·군·구 단위 좌표표 보강
