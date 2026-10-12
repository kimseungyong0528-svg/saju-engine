"""사이트 33번 파일(한 장짜리 HTML)을 실제로 올릴 수 있는 모양으로 바꾼다.

하는 일
1. HTML 안에 글자로 박힌 사진 53장을 public/assets/ 아래 진짜 파일로 꺼낸다.
   (사이트 코드는 원래 이 경로를 그대로 쓰도록 되어 있다.)
2. "미리보기", "실제 결제가 발생하지 않아요" 같은 문구를 실제 판매 문구로 바꾼다.
3. 사업자 정보(site/business.json)를 화면에 넣는다.
4. 서버도 사이트와 똑같은 기준으로 입력을 검사하도록, 사이트의 검사 코드를
   netlify/functions/lib/intake.mjs 로 복사한다.

예) python site/tools/build_site.py /mnt/project-files/unmyeong-preview-v33.html
"""

import base64
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
PUBLIC = SITE / "public"
LIB = SITE / "netlify" / "functions" / "lib"

ASSET_HEAD = "globalThis.__UNMYEONG_EMBEDDED_ASSETS__=Object.fromEntries(Object.entries("
ASSET_TAIL = "'image/jpeg'}))]));"


def _swap(s: str, old: str, new: str) -> str:
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"바꿀 문구를 {n}번 찾음(1번이어야 함): {old[:60]}")
    return s.replace(old, new)


def extract_assets(s: str) -> str:
    i = s.index(ASSET_HEAD)
    j = s.index(ASSET_TAIL, i) + len(ASSET_TAIL)
    start = i + len(ASSET_HEAD)
    end = s.index("}).map(([path,base64])", start) + 1
    assets = json.loads(s[start:end])
    for path, b64 in assets.items():
        out = PUBLIC / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(b64))
    print(f"사진 {len(assets)}장 꺼냄")
    # 사진 표가 없으면 사이트는 assets/... 경로를 그대로 쓴다.
    return s[:i] + s[j:]


def business_html(b: dict) -> str:
    rows = [("상호", b.get("company")), ("대표자", b.get("owner")), ("사업자등록번호", b.get("registration")),
            ("통신판매업 신고번호", b.get("commerce")), ("주소", b.get("address")),
            ("이메일", b.get("email")), ("전화", b.get("phone"))]
    lines = "<br>".join(f"{k}: {v}" for k, v in rows if v)
    return lines or "사업자 정보 등록 중"


def patch_texts(s: str, b: dict) -> str:
    biz = business_html(b)
    contact = b.get("email") or "고객센터"
    s = _swap(s, '"mode":"preview"', '"mode":"live"')
    s = _swap(s, '"business":{"company":"","owner":"","registration":"","commerce":"","address":"","email":"","phone":""}',
              '"business":' + json.dumps(b, ensure_ascii=False, separators=(",", ":")))

    # '재미로' 같은 말은 풀이의 믿음을 떨어뜨려 뺀다(2026-10-12 사장님 요청)
    s = _swap(s, "사주를 통해 성향을 재미로 읽고, 직접 들려준 생활 습관을 돌아봐요.", "사주로 타고난 성향을 읽고, 직접 들려준 생활 습관을 돌아봐요.")

    # 결제 화면
    s = _swap(s, '<div class="checkout-preview">미리보기 · 실제 결제가 발생하지 않아요</div>', '')
    s = _swap(s, '<p class="field-help">정식 서비스에서는 결과 링크와 보관함 조회에 이용돼요.</p>',
              '<p class="field-help">사주 결과 PDF를 이 이메일로 보내드려요. 정확히 입력해주세요.</p>')
    s = _swap(s, "note.textContent=e.message==='COUPON_NOT_AVAILABLE'?",
              "note.textContent=e.message==='TEST_MODE_OWNER_ONLY'?'지금은 시험 운영 중이라 결제할 수 없어요. 곧 정식으로 문을 열어요.':e.message==='COUPON_NOT_AVAILABLE'?")
    s = _swap(s, '<div class="field"><label for="coupon">할인 쿠폰</label>', '<div class="field" hidden><label for="coupon">할인 쿠폰</label>')
    s = _swap(s, '<input type="checkbox" name="payment" required>입력 확인 진행 동의</label>',
              '<input type="checkbox" name="payment" required>구매 조건 확인 동의</label>')
    s = _swap(s, '<button class="primary dark-primary" id="pay" type="submit" disabled>접수 가능 여부 확인</button><p class="fine-print">현재 실제 결제와 주문 생성은 진행되지 않아요. 입력 정보와 제공 가능한 분석 범위를 먼저 확인해요.</p>',
              '<button class="primary dark-primary" id="pay" type="submit" disabled>입력 확인하기</button><p class="fine-print">입력 확인이 끝나면 결제 버튼이 나타나요. 결제 후 보통 10분 안에 이메일로 PDF를 보내드려요.</p>')
    s = _swap(s, '<div class="business-info"><h2>사업자 정보</h2><p>정식 서비스 오픈 전에 사업자 정보와 결제 제공자를 등록할 예정입니다.</p>',
              f'<div class="business-info"><h2>사업자 정보</h2><p>{biz}<br>결제 대행: 토스페이먼츠</p>')
    s = _swap(s, "<p>현재는 접수 가능 여부만 확인하며, 실제 결제·사주 분석·이메일 발송은 진행되지 않습니다.</p><p>날짜가 불확실하거나 핵심 분석이 불가능하면 구매를 제한하고 필요한 정보를 안내합니다.</p>",
              "<p>사주 결과는 결제 후 개인별로 새로 작성하는 디지털 콘텐츠입니다. 결과 PDF를 이메일로 보낸 뒤에는 단순 변심으로 인한 청약철회가 제한됩니다(전자상거래법 제17조 제2항).</p><p>결과를 보내기 전에는 전액 환불할 수 있습니다. 이메일이 오지 않거나 결과에 오류가 있으면 다시 보내드리거나 환불해 드립니다.</p>")
    s = _swap(s, "<p>현재는 화면 확인용 미리보기입니다. 입력한 이름, 출생 정보, 질문과 이메일은 이 브라우저 세션에 보관됩니다. 접수 가능 여부 확인을 누르면 출생 정보와 상품 질문을 이 사이트의 접수 서버에서 검사합니다. 현재 검사 서버는 요청 본문을 저장하거나 외부 업체에 전달하지 않습니다.</p><p>정식 운영 전 수집 목적, 보관 기간, 처리 위탁과 운영자 정보를 별도로 확정해야 합니다.</p>",
              "<p>사주 결과를 작성하고 이메일로 보내기 위해 이름, 성별, 생년월일과 양력·음력, 태어난 시간, 태어난 지역, 질문, 이메일을 받습니다.</p><p>출생 정보와 질문은 결과 메일을 보내는 즉시 지웁니다. 자세한 내용은 개인정보 처리방침에서 확인할 수 있어요.</p>")
    s = _swap(s, '<p class="fine-print">결과는 자동 검증을 통과한 뒤 발행됩니다. 현재 전체 풀이·결제·PDF 발행은 준비 중이에요.</p>',
              '<p class="fine-print">결제 후 사주 결과를 작성하고 자동 검사를 거쳐 이메일로 보내드려요.</p>')

    # 자주 묻는 질문
    s = _swap(s, "['결과는 어떤 형태로 받나요?','정식 서비스 연결 후, 입력한 이메일로 결과 링크를 보내드리는 구조입니다. 현재 미리보기에서는 예시 리포트와 인쇄 화면을 확인할 수 있어요.']",
              "['결과는 어떤 형태로 받나요?','입력한 이메일로 PDF 파일을 보내드려요. 결제 후 주문 상태 화면에서도 PDF를 내려받을 수 있어요.']")
    s = _swap(s, "['결과를 받기까지 얼마나 걸리나요?','현재는 미리보기 단계로 실제 분석이나 이메일 발송을 진행하지 않습니다. 정식 서비스의 소요 시간은 연결 후 안내할 예정이에요.']",
              "['결과를 받기까지 얼마나 걸리나요?','결제 후 보통 10분 안에 이메일로 도착해요. 30분이 지나도 오지 않으면 스팸함을 확인한 뒤 고객센터로 알려주세요.']")
    s = _swap(s, "모르는 시간은 임의로 채우지 않으며, 실제 분석은 서비스 연결 후 제공됩니다.']",
              "시간을 모르면 가능한 시간 전체를 비교하고, 시간에 따라 달라지는 부분은 결과에 따로 안내해요.']")
    s = _swap(s, "['결과를 계속 보관할 수 있나요?','미리보기 주문은 현재 브라우저의 세션에만 저장됩니다. 정식 서비스에서는 온라인 열람과 PDF 다운로드를 별도로 제공할 예정이에요.']",
              "['결과를 계속 보관할 수 있나요?','이메일로 받은 PDF를 내려받아 보관해주세요. 개인정보 보호를 위해 출생 정보는 메일을 보내는 즉시 지우고, 결과 PDF는 7일 뒤 지워요. 7일 안에는 주문 화면에서 다시 받을 수 있어요.']")

    # 예시 후기 숨기기(사장님 결정 2026-10-12: 실제 후기가 모일 때까지 보이지 않게)
    s = _swap(s, "<section class=\"section\"><div class=\"section-head\"><h2>우리의 이야기를 읽은 뒤</h2><p>궁합·재회 후기 영역 · 예시 콘텐츠</p></div>${reviewRail(DEMO_REVIEWS.filter(r=>['intimate','reunion'].includes(r.product)))}</section>", "")
    s = _swap(s, "<section class=\"section\"><div class=\"section-head\"><h2>나를 발견하는 순간들</h2><p>리포트 후기 영역 · 예시 콘텐츠</p></div>${reviewRail(DEMO_REVIEWS.filter(r=>['lifetime','romance'].includes(r.product)))}</section>", "")
    s = _swap(s, "<section class=\"sales-reviews\"><h2>리포트를 읽는 시간</h2>${reviewRail(DEMO_REVIEWS.filter(r=>r.product===p.id).concat(DEMO_REVIEWS.slice(0,1)))}</section>", "")
    s = _swap(s, '<p class="fine-print">표시 금액은 미리보기 기준입니다. 실제 결제는 발생하지 않습니다.</p>',
              '<p class="fine-print">결제 후 보통 10분 안에 이메일로 PDF를 보내드려요.</p>')

    s = _swap(s, '<div class="preview-note">미리보기 · 금월선녀와 함께 펼치는 사주 이야기. 후기·결과는 화면 구성을 위한 예시이며, 실제 결제는 진행되지 않습니다.</div>',
              '<div class="preview-note">금월선녀와 함께 펼치는 사주 이야기. 무료 콘텐츠의 결과 화면은 예시이며, 유료 리포트는 결제 후 개인별로 작성해 이메일로 보내드려요.</div>')
    s = _swap(s, '<span class="pill">미리보기 운영 안내</span>', '<span class="pill">운명서재 이용 안내</span>')
    s = _swap(s, "최종 수정: ${new Date().toLocaleDateString('ko-KR')}", "시행일: 2026년 10월 12일")

    # 아래쪽 안내
    s = _swap(s, "<p>운명서재는 현재 미리보기로 운영됩니다.<br>실제 결제와 개인별 분석 결과는 제공되지 않습니다.</p>",
              f"<p>{biz}</p>")

    # 약관·개인정보·환불
    i = s.index("const content=type==='privacy'?`")
    j = s.index(";layout(title,", i)
    s = s[:i] + "const content=" + legal_js(b, contact) + s[j:]
    return s


def legal_js(b: dict, contact: str) -> str:
    company = b.get("company") or "운명서재"
    privacy = f"""<h2>1. 받는 정보</h2><p>이름, 성별, 생년월일과 양력·음력·윤달 여부, 태어난 시간(정확한 시각, 시간 범위 또는 모름), 태어난 지역, 상품별 질문과 답, 이메일을 받습니다. 두 사람 상품은 상대방의 같은 정보를 받습니다. 카드 정보는 토스페이먼츠가 직접 받고, {company}은(는) 카드 번호를 받지 않습니다.</p><h2>2. 쓰는 목적</h2><p>사주 결과를 계산하고 작성해 이메일로 보내는 데에만 씁니다. 광고나 다른 목적으로 쓰지 않습니다.</p><h2>3. 보관 기간</h2><p>출생 정보와 질문은 결과 메일을 보내는 즉시 지웁니다. 결과 PDF는 다시 보내기를 위해 7일 동안 보관한 뒤 지웁니다. 발송이 보류된 주문의 정보는 다시 만들 수 있게 7일 동안 보관한 뒤 지우고, 결제가 안 된 주문의 정보는 8일 안에 지웁니다. 주문번호, 결제 금액, 이메일 같은 거래 기록은 전자상거래법에 따라 5년 동안 보관합니다.</p><h2>4. 처리를 맡기는 곳</h2><p>토스페이먼츠(결제), Netlify(미국, 사이트와 주문 저장), GitHub(미국, 결과 작성 작업 실행), Anthropic(미국, 결과 글 작성), Resend(미국, 이메일 발송)에 필요한 정보만 맡깁니다. 해외 업체로는 주문을 처리하는 동안 암호화된 연결로 전송됩니다.</p><h2>5. 요청할 수 있는 것</h2><p>내 정보의 열람, 정정, 삭제, 처리 중지를 요청할 수 있습니다. 문의: {contact}</p>"""
    terms = """<h2>1. 서비스</h2><p>운명서재는 입력한 출생 정보로 사주를 계산하고, 개인별 결과를 PDF로 작성해 이메일로 보내드립니다.</p><h2>2. 콘텐츠의 성격</h2><p>사주 결과는 자기 이해와 오락을 위한 참고 자료입니다. 의료, 법률, 투자 같은 중요한 판단을 대신하지 않습니다.</p><h2>3. 입력 정보</h2><p>결과는 입력한 정보로 작성됩니다. 생년월일이나 시간이 틀리면 결과도 달라지므로 정확히 입력해주세요.</p><h2>4. 저작권</h2><p>결과 PDF는 구매한 분의 개인적인 이용을 위해 제공되며, 무단으로 다시 팔거나 배포할 수 없습니다.</p>"""
    refund = f"""<h2>결과를 보내기 전</h2><p>결제 후 결과 이메일을 보내기 전에는 전액 환불해 드립니다.</p><h2>결과를 보낸 뒤</h2><p>결과는 결제 후 개인별로 작성하는 디지털 콘텐츠라서, 이메일로 보낸 뒤에는 단순 변심으로 인한 환불이 어렵습니다(전자상거래법 제17조 제2항).</p><h2>오류가 있을 때</h2><p>이메일이 오지 않거나, 입력한 정보와 다른 내용으로 작성되는 등 오류가 있으면 다시 보내드리거나 전액 환불해 드립니다.</p><h2>문의</h2><p>{contact}</p>"""
    return "type==='privacy'?`" + privacy + "`:type==='terms'?`" + terms + "`:`" + refund + "`"


INTAKE_PARTS = [
    ("const KoreanLunarCalendar = (()=>{", "function personBirthSummary"),
    ("const PRODUCTS=[", "// Kept only so previously saved demo orders still open."),
    ("const scene=(id,title,text,cta=", "const SALES={"),
    ("// SCOPE-01 / INPUT-01/02 / INTAKE-C01..06 / ISSUE-01.", "// Status and cancellation"),
]


def write_intake_module(s: str) -> None:
    parts = []
    for a, b in INTAKE_PARTS:
        i = s.index(a)
        parts.append(s[i:s.index(b, i)])
    code = ("// 자동 생성: site/tools/build_site.py 가 사이트 코드에서 그대로 복사함. 직접 고치지 말 것.\n"
            + "\n".join(parts)
            + "\nexport {INTAKE_POLICY_VERSION,PRODUCTS,FLOWS,intakePayload,evaluateIntake,personValid,birthPrecision};\n")
    LIB.mkdir(parents=True, exist_ok=True)
    (LIB / "intake.mjs").write_text(code, encoding="utf-8")


def main() -> None:
    src = Path(sys.argv[1])
    b = json.loads((SITE / "business.json").read_text(encoding="utf-8"))
    s = src.read_text(encoding="utf-8")
    s = extract_assets(s)
    write_intake_module(s)
    s = patch_texts(s, b)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "index.html").write_text(s, encoding="utf-8")
    print(f"public/index.html {len(s.encode()) // 1024}KB")


if __name__ == "__main__":
    main()
