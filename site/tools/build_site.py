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
              '"business":' + json.dumps({k: v for k, v in b.items() if k != "kakao"}, ensure_ascii=False, separators=(",", ":")))
    # 주문 화면에 남은 미리보기 문구를 실제 서비스 문구로 바꾼다(2026-10-12 전체 검수).
    s = _swap(s, "<div class=\"pillars\">${['생시','생일','생월','생년'].map(t=>`<div><small>${t}</small><b>${t==='생시'&&uncertain?'?':'—'}</b><b>${t==='생시'&&uncertain?'?':'—'}</b></div>`).join('')}</div>", "")
    s = _swap(s, "<p>사주 원국은 분석 서비스 연결 후 표시됩니다.</p>", "")
    s = _swap(s, "<p>개별 분석 결과는 정식 서비스 연결 후 제공됩니다.</p>", "<p>결제하면 이 이야기를 한 권의 PDF로 써서 이메일로 보내드려요.</p>")
    s = _swap(s, "'정식 리포트에는 분석의 근거와 해석을 함께 담도록 연결할 예정이에요.'", "'리포트에는 풀이마다 사주 근거와 해석을 함께 담아요.'")
    # 보관함: 실제 주문은 이메일로 받으므로, 체험 주문 찾기 대신 받는 방법과 문의 방법을 안내한다.
    lib_start = s.index("function libraryPage(){")
    lib_end = s.index("function orderPage(", lib_start)
    s = s[:lib_start] + (
        "function libraryPage(){layout('나의 보관함',`<div class=\"page-pad library\"><div class=\"empty-icon\">${icon('book')}</div>"
        "<h1>나의 리포트는<br>이메일로 보내드려요</h1><p class=\"muted\">결제 후 보통 10분 안에, 주문할 때 입력한 이메일로 PDF 파일을 보내드려요. "
        "PDF는 메일을 보낸 뒤 7일이 지나면 서버에서 지우니, 꼭 내려받아 보관해주세요.</p>"
        "<p class=\"local-note\">메일이 오지 않으면 스팸함을 먼저 확인해주세요. 그래도 없으면 주문한 이메일을 카카오톡으로 알려주세요. 확인한 뒤 다시 보내드려요.</p>"
        "<button class=\"kakao\" data-action=\"support\">카카오톡으로 문의하기</button></div>`,'보관함')} "
    ) + s[lib_end:]
    # 질문 화면의 마지막 선택지가 아래 고정 버튼(다음으로)에 가려지지 않도록 아래 여백을 버튼 높이만큼 준다(2026-10-13).
    s = _swap(s, ".flow-content { padding: 32px 24px 25px; }", ".flow-content { padding: 32px 24px calc(125px + env(safe-area-inset-bottom)); }"
              # 판매 페이지·접수 화면: 맨 아래 글(자주 묻는 질문, 서비스 문의)이 아래 고정 버튼에 가리지 않게 여백을 둔다.
              ".shell.sales { padding-bottom: calc(96px + env(safe-area-inset-bottom)) !important; }"
              # 리포트 안내(판매) 페이지 칸 사이 빈 공간 줄이기 (모든 상품 공통).
              ".shell.sales .sales-panel { min-height: 560px; padding-top: 300px; padding-bottom: 32px; }"
              ".shell.sales .detail-scene { min-height: 0; padding-top: 300px; padding-bottom: 32px; }"
              ".shell.sales .sales-interlude { padding-top: 44px; padding-bottom: 44px; }"
              ".shell.sales .sales-persons { padding-top: 40px; padding-bottom: 40px; }"
              ".shell.sales .chapters { padding-top: 40px; padding-bottom: 40px; } .shell.sales .chapters>h2 { margin: 12px 0 24px; }"
              ".shell.sales .chapter { margin: 12px 0; padding: 24px 22px; }"
              ".shell.sales .faq { padding: 20px 24px 0; } .shell.sales .faq h2 { margin-bottom: 12px; } .shell.sales .faq details { padding: 15px 0; }"
              ".shell.checkout .checkout-content { padding-bottom: calc(110px + env(safe-area-inset-bottom)) !important; }")
    # 첫 화면 섹션 제목·설명 (사장님 문구, 2026-10-13). 평생사주는 건강운과 같은 '인생 총운' 줄로 옮김.
    s = _swap(s, "<h2>오리지널 사주</h2><p>연애, 궁합, 재회부터 나의 평생운까지</p></div>${cards(['romance','intimate','reunion','lifetime'])}",
              "<h2>오리지널 연애 사주</h2><p>나의 연애, 궁합, 재회까지 운명적인 사랑 이야기</p></div>${cards(['romance','intimate','reunion'])}")
    s = _swap(s, "<h2>나의 금전운</h2><p>재물, 직업·이직, 사업의 이야기를 차례로</p>",
              "<h2>나의 금전운</h2><p>재물, 직업·이직, 사업가의 이야기를 차례로</p>")
    s = _swap(s, "<h2>몸과 마음을 돌보는 시간</h2><p>나의 생활 리듬을 돌아보는 건강운</p></div>${cards(['health'])}",
              "<h2>소중한 건강과, 인생 전체를 되돌아본다</h2><p>건강운과 인생 총운</p></div>${cards(['health','lifetime'])}")
    # 접수 화면: 입력이 맞으면 "입력 확인 완료 · 분석 범위 확인 필요" 안내 묶음을 보여주지 않는다(입력이 틀렸을 때만 보임).
    s = _swap(s, "function intakeNotice(decision,productId){", "function intakeNotice(decision,productId){if(decision.inputAccepted)return '';")
    # 무료 콘텐츠 4개(무료 사주·인연 우주·태어난 시간 찾기·월간 운세)는 예시 화면뿐이라 숨긴다(2026-10-12 사장님 결정).
    # 코드는 남겨 두고 첫 화면·메뉴에서 빼며, 주소로 들어와도 첫 화면으로 보낸다. 없는 프리미엄 상담 안내와
    # 실제로 없는 5,000원 할인 팝업도 뺀다.
    s = _swap(s, '<section class="section"><div class="section-head"><h2>오늘은 가볍게, 무료 사주</h2><p>혼자 발견하고, 함께 나누는 나의 이야기</p></div><div class="rail free-rail"><a href="#/free" class="banner"><span class="eyebrow">FREE READING</span><h3>내 안의<br>또 다른 나</h3><p>사주팔자 · 운명지도 · 전생</p><span class="pill">무료로 시작하기</span></a><a href="#/friends" class="banner friend-banner"><span class="eyebrow">OUR UNIVERSE</span><h3>친구와 나의<br>인연 우주</h3><p>우리 사이, 새로운 발견</p><span class="pill">함께 알아보기</span></a></div></section>', '')
    s = _swap(s, '<section class="section"><div class="section-head"><h2>태어난 시간을 모르겠다면</h2><p>나의 성향에서 찾는 시간의 실마리</p></div><a class="banner time-banner" href="#/birth"><span class="eyebrow">FIND MY TIME</span><h3>내가 태어난<br>시간을 찾아서</h3><p>몇 가지 질문으로 시작하는 시간 여행</p></a></section>', '')
    s = _swap(s, '<section class="section"><div class="section-head"><h2>이번 계절의 이야기</h2><p>지금 나에게 필요한 운세와 소식</p></div><div class="rail free-rail"><a class="banner monthly-banner" href="#/monthly"><span class="eyebrow">MONTHLY LETTER</span><h3>${new Date().getMonth()+1}월,<br>나의 운세 편지</h3><p>일간별로 펼쳐보는 이번 달</p></a><a class="banner" href="#/support"><span class="eyebrow">WITH YOU</span><h3>궁금한 이야기를<br>직접 물어보세요</h3><p>상담과 서비스 문의</p></a></div></section>',
              '<section class="section"><div class="section-head"><h2>궁금한 점이 있다면</h2><p>주문과 결과 받기에 관한 문의</p></div><a class="banner" href="#/support"><span class="eyebrow">WITH YOU</span><h3>궁금한 이야기를<br>직접 물어보세요</h3><p>카카오톡으로 문의하기</p></a></section>')
    s = _swap(s, '<section class="section"><div class="section-head"><h2>조금 더 깊은 이야기</h2><p>프리미엄 1대1 상담</p></div><a class="banner premium-banner" href="#/support?type=premium"><span class="eyebrow">PRIVATE CONSULTATION</span><h3>오직 당신의<br>이야기에 집중하는 시간</h3><p>상담 일정과 이용 방법 알아보기</p></a></section>', '')
    s = _swap(s, '<div class="drawer-bottom"><a href="#/free">무료 사주</a><a href="#/support">고객센터</a></div>', '<div class="drawer-bottom"><a href="#/support">고객센터</a></div>')
    s = _swap(s, '서비스 이용과 리포트, 프리미엄 상담에 관한 안내를 확인하세요.', '주문과 결과 받기에 관한 안내를 확인하세요.')
    s = _swap(s, "else if(route==='/game'){go('/');return}else if(['free','friends','birth','monthly'].includes(parts[0]))renderAux(",
              "else if(['game','free','friends','birth','monthly','order','report'].includes(parts[0])){go('/');return}else if(false)renderAux(")
    s = _swap(s, "else if(parts[0]==='order')orderPage(parts[1]);else if(parts[0]==='report')reportPage(parts[1]);", "")
    s = _swap(s, "if(cat==='전체'&&!sessionStorage.getItem('unmyeong.popups')&&!localStorage.getItem('unmyeong.hideOffer')){sessionStorage.setItem('unmyeong.popups','1');offer()}", "")
    # 상품 소개 화면의 그림 설명에 남은 '예시', '연결 후' 문구
    s = _swap(s, "<span>인생 흐름 · 화면 예시</span><svg viewBox=\"0 0 300 145\" role=\"img\" aria-label=\"인생 흐름 그래프 예시\">", "<span>인생 흐름</span><svg viewBox=\"0 0 300 145\" role=\"img\" aria-label=\"인생 흐름 그래프\">")
    s = _swap(s, "<p>개인별 수치는 분석 연결 후 표시됩니다.</p>", "<p>리포트에서는 내 사주로 계산한 시기별 흐름을 보여드려요.</p>")
    s = _swap(s, "<p>관계를 돌아보는 질문과 생각해 볼 행동을 담는 영역입니다.</p>", "<p>관계를 돌아보는 질문과 실천할 행동을 리포트에 담았어요.</p>")
    s = _swap(s, "<p>실제 계산 결과가 들어갈 자리예요.<br>고정된 점수를 개인 결과로 표시하지 않아요.</p>", "<p>두 사람의 사주로 계산한 점수는<br>리포트에서 확인할 수 있어요.</p>")
    # 카카오톡으로 문의하기 버튼은 운명서재 카카오톡 채널로 연결한다.
    if b.get("kakao"):
        s = _swap(s, '"supportUrl":""', '"supportUrl":' + json.dumps(b["kakao"]))
        s = _swap(s, '<p class="local-note">상담 채널 연결 전입니다.</p>', '')

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
    # 리포트 안내(판매) 페이지에서 가격 칸을 뺀다. 가격은 마지막 접수 화면에서만 보인다.
    s = _swap(s, '<section class="sales-interlude"><span class="eyebrow">ONE STORY, MANY CHAPTERS</span><h2 class="serif">한 권으로 만나는<br>${p.short}</h2>${priceBox(p)}<p class="fine-print">결제 후 보통 10분 안에 이메일로 PDF를 보내드려요.</p></section>', '')

    s = _swap(s, '<div class="preview-note">미리보기 · 금월선녀와 함께 펼치는 사주 이야기. 후기·결과는 화면 구성을 위한 예시이며, 실제 결제는 진행되지 않습니다.</div>',
              '<div class="preview-note">금월선녀와 함께 펼치는 사주 이야기. 모든 리포트는 결제 후 한 분 한 분의 사주로 새로 작성해 이메일로 보내드려요.</div>')
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


# 첫 화면 상품 카드를 고급스럽게 바꾼다(2026-10-21 사장님 요청).
# 카드에는 가격을 빼고(가격은 마지막 접수 화면에서만), 그림 위에 큰 붓글씨 제목과 붉은 낙관(한자)을 얹는다.
CARD_SEALS = {"lifetime": "平生", "romance": "戀愛", "reunion": "再會", "intimate": "宮合", "wealth": "財物",
              "career": "職業", "business": "事業", "health": "健康", "newyear": "丁未"}
# 재물운·직업·이직운·사업운이 같은 그림(master.jpg)이라 카드 그림을 나눈다(시안: 직업 = 상아색, 사업 = 초록).
CARD_COVERS = {"career": ("assets/geumwol/compatibility-cover.jpg", "상아색 한복의 금월선녀"),
               "business": ("assets/geumwol/wealth-cover.jpg", "초록 한복의 금월선녀")}
CARD_CSS = (
    "<style>"
    "@font-face{font-family:'UnmyeongTitle';src:url(assets/fonts/songmyung-title.woff2) format('woff2');font-display:swap}"
    "@font-face{font-family:'UnmyeongSeal';src:url(assets/fonts/notoserif-seal.woff2) format('woff2');font-weight:700;font-display:swap}"
    ".product-card.lux .product-cover{padding:0;border-radius:14px;box-shadow:0 16px 34px #000b,0 0 0 1px #e6c98a2e}"
    ".product-card.lux .product-cover:before{content:'';position:absolute;inset:0;z-index:0;pointer-events:none;"
    "background:linear-gradient(180deg,#0806041a 0%,#08060400 42%,#0b080699 68%,#0b0806f2 100%)}"
    ".product-card.lux .product-cover:after{inset:7px;border:1px solid #e6c98a99;border-radius:9px;z-index:1;"
    "box-shadow:inset 0 0 0 3px #0000,inset 0 0 0 4px #e6c98a33}"
    ".lux-seal{position:absolute;top:15px;right:15px;z-index:2;writing-mode:vertical-rl;font:700 15px/1 'UnmyeongSeal',serif;"
    "letter-spacing:3px;color:#fbefdc;background:linear-gradient(160deg,#b52a33,#8c1820);padding:7px 5px 4px;border-radius:3px;"
    "box-shadow:0 3px 10px #0009,inset 0 0 0 1px #ffffff2e}"
    ".lux-title{position:absolute;left:10px;right:10px;bottom:20px;z-index:2;text-align:center}"
    ".product-card.lux .lux-title h3{margin:0;font:400 34px/1.15 'UnmyeongTitle',Georgia,serif;letter-spacing:.03em;"
    "background:linear-gradient(180deg,#fff7df 0%,#f2d898 46%,#c3923f 100%);-webkit-background-clip:text;background-clip:text;"
    "color:transparent;filter:drop-shadow(0 2px 5px #000d)}"
    ".product-card.lux .lux-title h3.long{font-size:27px}"
    ".lux-rule{position:relative;display:block;width:64px;height:1px;margin:10px auto 9px;"
    "background:linear-gradient(90deg,#e6c98a00,#e6c98a,#e6c98a00)}"
    ".lux-rule:after{content:'';position:absolute;left:50%;top:50%;width:5px;height:5px;background:#e6c98a;transform:translate(-50%,-50%) rotate(45deg)}"
    ".product-card.lux .lux-title p{margin:0;font-size:13px;line-height:1.55;color:#f1e8d8;white-space:pre-line;text-shadow:0 1px 4px #000}"
    ".product-card.lux .product-meta{padding:12px 2px 0}"
    ".product-card.lux .product-meta strong{font-size:16px;font-weight:600;color:#ece6dc}"
    "</style></head>"
)


def upgrade_cards(s: str) -> str:
    seals = json.dumps(CARD_SEALS, ensure_ascii=False, separators=(",", ":"))
    s = _swap(s, "const cards=(ids,layout='rail')=>`<div class=\"${layout==='grid'?'product-grid':'rail'}\">${ids.map(id=>{const p=pById(id);return `<a href=\"${link(p)}\" class=\"product-card\">${art(p,p.id+'.cover','product-cover',`<h3>${p.short}</h3><p>${p.line}</p>`)}<div class=\"product-meta\"><strong>${p.name}</strong>${priceLabel(p)}</div></a>`}).join('')}</div>`;",
              "const CARD_SEALS=" + seals + ";"
              "const cards=(ids,layout='rail')=>`<div class=\"${layout==='grid'?'product-grid':'rail'}\">${ids.map(id=>{const p=pById(id);return `<a href=\"${link(p)}\" class=\"product-card lux\">${art(p,p.id+'.cover','product-cover',`<span class=\"lux-seal\" aria-hidden=\"true\">${CARD_SEALS[p.id]||''}</span><div class=\"lux-title\"><h3${[...p.short].length>4?' class=\"long\"':''}>${p.short}</h3><i class=\"lux-rule\"></i><p>${p.line}</p></div>`)}<div class=\"product-meta\"><strong>${p.name}</strong></div></a>`}).join('')}</div>`;")
    s = _swap(s, "<h2>${p.name}</h2>${priceLabel(p)}<span class=\"step-label\">", "<h2>${p.name}</h2><span class=\"step-label\">")
    for pid, (img, alt) in CARD_COVERS.items():
        s = _swap(s, f'"{pid}.cover": {{\n    "image": "assets/geumwol/master.jpg",\n    "alt": "궁궐 사주방의 금월선녀",',
                  f'"{pid}.cover": {{\n    "image": "{img}",\n    "alt": "{alt}",')
    s = _swap(s, "</head>", CARD_CSS)
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
    # 사업운·건강운 질문 흐름은 뒤쪽에 따로 붙어 있다. 빠지면 서버 접수 확인이 두 상품에서 멈춘다.
    ("// New catalog entries use the existing story", "SALES.business={"),
    ("// SCOPE-01 / INPUT-01/02 / INTAKE-C01..06 / ISSUE-01.", "// Status and cancellation"),
]


def add_newyear(s: str) -> str:
    """2027 신년운세 상품을 붙인다(2026-10-13 사장님 결정: 29,800원, 첫 화면 큰 배너는 신년운세 한 장 + EVENT).
    접수 규칙(intake.mjs)에도 들어가야 하므로 write_intake_module 보다 먼저 부른다."""
    s = _swap(s, "  }\n];\n// Kept only so previously saved demo orders still open.",
              '  },\n  {\n    "id": "newyear",\n    "name": "금월선녀의 2027 신년운세",\n    "short": "2027 신년운세",\n'
              '    "guide": "금월선녀",\n    "category": "운세/평생운",\n    "color": "#f09c9c",\n    "tone": "forest",\n'
              '    "symbol": "丁未",\n    "line": "2027년, 나에게\\n어떤 해가 될까요",\n    "price": 29800,\n    "original": 55000,\n'
              '    "steps": 8\n  }\n];\n// Kept only so previously saved demo orders still open.')
    s = _swap(s, "SALES.business={", (
        "FLOWS.newyear=[\n"
        " intro('2027년, 나에게\\n어떤 해가 될까요','새해 계획을 세우기 전에 내 사주로 2027년을 먼저 확인해요.'),\n"
        " scene('year','2027년은\\n정미년이에요','정미년은 불(정화)과 흙(미토)의 기운이 강한 해예요. 이 기운이 내 사주와 맞는지, 삼재와 대운은 어떤지 함께 봐요.'),\n"
        " info,\n"
        " choice('focus','2027년에 가장 궁금한 것은 무엇인가요?',['일과 직장','돈과 재물','연애와 결혼','건강','한 해 전체'],true),\n"
        " {...question,title:'2027년에 대해 묻고 싶은 것이 있나요?',text:'새해 계획이나 고민을 편하게 적어주세요. 비워두셔도 괜찮아요.'},\n"
        " scene('ready','나의 2027년을\\n한 권에 담았어요','월별 운세부터 삼재, 대운, 행운의 색까지 차례로 확인해보세요.','신년운세 리포트 살펴보기'),\n"
        " sales,checkout\n];\n"
        "SALES.business={"))
    s = _swap(s, "DEMO_REVIEWS.push({product:'business'", (
        "SALES.newyear={opening:'2027년을 미리 알고\\n새해를 시작하세요',empathy:'새해 계획을 세우기 전에\\n이것부터 궁금하지 않나요',"
        "empathyBody:'내년에 돈이 들어올지, 이직해도 될지, 좋은 사람을 만날지. 내 사주와 2027년 정미년의 기운을 비교해 달마다 정리해 드려요.',"
        "reveal:'내 사주로 계산한\\n2027년 한 해의 흐름',locks:['2027년이 나에게 좋은 해인지 한마디 요약','삼재와 대운이 바뀌는지 확인','1월부터 12월까지 달마다 할 일'],"
        "chapters:['한눈에 보는 나의 2027년','일·돈·연애·건강운','사람운과 조심할 일','1월~12월 월별 운세','2027년 실천 계획'],"
        "ending:'2027년을 미리 확인하고\\n새해를 준비하세요'};\n"
        "DETAIL_BLOCKS.newyear=[['summary','2027년이 나에게\\n어떤 해인지 한마디로','전체 점수와 좋은 운, 나쁜 운을 첫 장에 정리해요.',''],"
        "['samjae','삼재와 대운을\\n먼저 확인해요','2027년이 삼재인지, 10년마다 바뀌는 대운이 바뀌는 해인지 알려드려요.',''],"
        "['months','1월부터 12월까지\\n달마다 할 일','가장 좋은 달과 조심할 달, 달마다 할 일을 정리해요.','timeline']];\n"
        "DEMO_REVIEWS.push({product:'business'"))
    # 사진: 신년운세 전용 금월선녀 한 장(newyear-cover.jpg). 이야기 화면은 이 사진을 배경으로 쓰고,
    # 눈 깜빡임용 인물 겹침은 쓰지 않는다(투명 그림 + 없는 표정 파일 → 눈·입 창이 숨겨진 채로 둠).
    s = _swap(s, "function home(){", (
        "{const NY={image:'assets/geumwol/newyear-cover.jpg',alt:'붉은 금빛 한복을 입은 금월선녀 · 2027 신년운세',position:'50% 22%',identityReference:'master.jpg'};"
        "for(const k of ['cover','intro','year','ready','sales.1','sales.2','sales.3','sales.4','sales.5','detail.summary','detail.samjae','detail.months'])MEDIA['newyear.'+k]=NY;"
        "for(const k of ['intro','year','ready'])STORY_MEDIA['newyear.'+k]={background:NY.image,backgroundAlt:NY.alt,character:'assets/geumwol/blank.png',width:112,top:68,"
        "originalImage:NY.image,interlude:false,identityReference:'assets/geumwol/master.jpg'};"
        "STORY_FACES.newyear={...STORY_FACES.lifetime,neural:{...STORY_FACES.lifetime.neural,atlas:'assets/geumwol/none.png'},"
        "smile:{...STORY_FACES.lifetime.smile,atlas:'assets/geumwol/none.png'}};}\n"
        "function home(){"))
    # 상단 카테고리: 인생총운 → 운세/평생운. 신년운세와 평생사주가 이 탭에 들어가고 신년운세가 첫 번째.
    s = _swap(s, 'const CATEGORIES=["전체","연애","재회","금전","건강","인생총운"];', 'const CATEGORIES=["전체","연애","재회","금전","건강","운세/평생운"];')
    s = _swap(s, '"guide": "금월선녀",\n    "category": "인생총운",', '"guide": "금월선녀",\n    "category": "운세/평생운",')
    s = _swap(s, "'인생 총운':'인생총운',", "'인생 총운':'운세/평생운','인생총운':'운세/평생운',")
    s = _swap(s, "PRODUCTS.filter(p=>p.category===cat).map(p=>p.id)", "PRODUCTS.filter(p=>p.category===cat).map(p=>p.id).sort((a,b)=>(b==='newyear')-(a==='newyear'))")
    # 첫 화면 큰 배너: 신년운세 한 장, 위에 EVENT 딱지. 넘기는 점은 뺀다.
    s = _swap(s, "['lifetime','wealth','reunion','intimate'].map(id=>{const p=pById(id);return `<a class=\"hero-card\" href=\"${link(p)}\">${art(p,p.id+'.cover','hero-card',`<div class=\"hero-copy\"><span class=\"eyebrow\">${p.guide} · ORIGINAL SAJU</span>",
              "['newyear'].map(id=>{const p=pById(id);return `<a class=\"hero-card\" href=\"${link(p)}\">${art(p,p.id+'.cover','hero-card',`<div class=\"hero-copy\"><span class=\"event-tag\">EVENT</span><span class=\"eyebrow\">${p.guide} · 2027 NEW YEAR</span>")
    s = _swap(s, "<div class=\"dots\">${[0,1,2,3].map(i=>`<button aria-label=\"슬라이드 ${i+1}\" class=\"dot ${!i?'active':''}\" data-slide=\"${i}\"></button>`).join('')}</div>", "")
    s = _swap(s, "advance((i+1)%4)", "advance((i+1)%track.children.length)")
    s = _swap(s, ".hero-copy{position:absolute;inset:auto 26px 32px}",
              ".hero-copy{position:absolute;inset:auto 26px 32px}"
              ".event-tag{display:inline-block;margin-bottom:12px;padding:5px 12px;border-radius:999px;background:#c8102e;color:#fff;"
              "font-size:14px;font-weight:800;letter-spacing:2px}.event-tag+.eyebrow{display:block}"
              ".hero-copy .ny-name{font-size:30px;font-weight:800;line-height:1.35;color:#f09c9c;text-shadow:0 2px 14px #000a;margin:2px 0 6px}"
              ".hero-copy .event-tag{margin-bottom:8px}.hero-copy .event-tag~h1{margin:6px 0 4px}")
    s = _swap(s, "</h1><p>${p.name}</p><span class=\"hero-link\">", "</h1><p class=\"ny-name\">${p.name}</p><span class=\"hero-link\">")
    # 신년운세 화면 색: 금색 대신 연한 빨강(금월선녀 한복 색에 맞춤).
    s = _swap(s, '<div class="shell light checkout">', '<div class="shell light checkout" data-product="${p.id}">')
    s = _swap(s, '.birth-info-page[data-birth-tone="romance"] {', (
        '.birth-info-page[data-birth-tone="newyear"] {\n --birth-accent:#f09c9c;\n --birth-ink:#2b1515;\n --birth-surface-start:#241718;\n'
        ' --birth-surface-end:#151112;\n --birth-card-border:#4a2e30;\n --birth-complete-border:#8f5558;\n --birth-badge-border:#9a5a5e;\n'
        ' --birth-badge-bg:#3b2224;\n --birth-input-border:#6a4a4c;\n --birth-filled-border:#c27f83;\n --birth-focus:#ffe5e5;\n --birth-hint:#f6c4c4;\n'
        ' --birth-track:#45302f;\n --birth-avatar-border:#85494d;\n --birth-focus-glow:#f09c9c16;\n --birth-hint-bg:#f09c9c0b;\n --birth-hint-border:#f09c9c25;\n'
        ' --birth-arrow:url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'16\' height=\'16\' viewBox=\'0 0 16 16\'%3E%3Cpath d=\'m4 6 4 4 4-4\' '
        'fill=\'none\' stroke=\'%23f09c9c\' stroke-width=\'1.5\' stroke-linecap=\'round\' stroke-linejoin=\'round\'/%3E%3C/svg%3E");\n}\n'
        '[data-product="newyear"] .dark-primary,.shell[style*="--accent:#f09c9c"] .dark-primary{background:#f09c9c;color:#2b1515}\n'
        '.shell[style*="--accent:#f09c9c"] .guide-strip strong{color:#f09c9c}.shell[style*="--accent:#f09c9c"] .guide-strip img{border-color:#f09c9c55}\n'
        '[data-product="newyear"] .coupon-input button{background:#f09c9c;color:#2b1515}\n'
        '.layered-story[data-product="newyear"] .scene-name{color:#f09c9c}.layered-story[data-product="newyear"] .scene-eyebrow span{color:#f8d6d6;border-color:#f8d6d6}'
        '.layered-story[data-product="newyear"] .story-speech{border-color:#f09c9c38}\n'
        '.birth-info-page[data-birth-tone="romance"] {'))
    return s


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
    s = add_newyear(s)
    write_intake_module(s)
    s = patch_texts(s, b)
    s = upgrade_cards(s)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "index.html").write_text(s, encoding="utf-8")
    print(f"public/index.html {len(s.encode()) // 1024}KB")


if __name__ == "__main__":
    main()
