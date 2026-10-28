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
import re
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
            ("이메일", b.get("email")), ("전화번호", b.get("phone"))]
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
    # 첫 화면(전체)과 카테고리 탭의 상품 카드, 검색 결과에서 가격을 뺀다(2026-10-21 사장님 요청).
    # 가격은 마지막 접수 화면에서만 보인다.
    s = _swap(s, "<div class=\"product-meta\"><strong>${p.name}</strong>${priceLabel(p)}</div>", "<div class=\"product-meta\"><strong>${p.name}</strong></div>")
    # 연애사주·깊은 궁합 카드는 제목 붓글씨가 그림 안에 들어간 포스터 그림을 쓴다(2026-10-21 사장님이 고른 그림).
    # 그림에 제목이 있으니 카드 위 글씨와 어둡게 덮는 그늘은 뺀다. 상품 소개 화면 그림은 그대로.
    s = _swap(s, "return `<a href=\"${link(p)}\" class=\"product-card\">${art(p,p.id+'.cover','product-cover',`<h3>${p.short}</h3><p>${p.line}</p>`)}",
              "const poster=CARD_POSTERS[p.id];return `<a href=\"${link(p)}\" class=\"product-card${poster?' poster-card':''}\">${art(p,p.id+(poster?'.card':'.cover'),'product-cover',poster?'':`<h3>${p.short}</h3><p>${p.line}</p>`)}")
    s = _swap(s, "const cards=(ids,layout='rail')=>",
              "const CARD_POSTERS={romance:'assets/geumwol/romance-poster-v2.jpg',intimate:'assets/geumwol/intimate-poster.jpg',reunion:'assets/geumwol/reunion-poster.jpg',career:'assets/geumwol/career-poster.jpg',business:'assets/geumwol/business-poster.jpg',wealth:'assets/geumwol/wealth-poster.jpg',health:'assets/geumwol/health-poster.jpg',lifetime:'assets/geumwol/lifetime-poster.jpg',newyear:'assets/geumwol/newyear-poster.jpg'};"
              "for(const [k,v] of Object.entries(CARD_POSTERS))MEDIA[k+'.card']={image:v,alt:'금월선녀의 '+k,position:'50% 15%'};MEDIA['newyear.hero']={image:CARD_POSTERS.newyear,alt:'금월선녀의 2027 신년운세',position:'50% 0%'};"
              "const cards=(ids,layout='rail')=>")
    s = _swap(s, "</head>", "<style>.poster-card .product-cover:after,.poster-card .product-cover:before{background:none!important}.hero-card[data-art-key='newyear.hero'] .art-media{object-position:50% 0%!important}.hero-card[data-art-key='newyear.hero'] .ny-name{display:none}.hero-card[data-art-key='newyear.hero'] .hero-copy{bottom:14px!important}.hero-card[data-art-key='newyear.hero'] .hero-copy .event-tag{margin-bottom:4px}.hero-card[data-art-key='newyear.hero'] .hero-copy h1{line-height:1.22!important;margin:2px 0 0!important}.hero-card[data-art-key='newyear.hero'] .hero-copy .hero-link{margin-top:8px!important}</style></head>")
    s = _swap(s, "<h2>${p.name}</h2>${priceLabel(p)}<span class=\"step-label\">", "<h2>${p.name}</h2><span class=\"step-label\">")
    # 접수 화면: 입력이 맞으면 "입력 확인 완료 · 분석 범위 확인 필요" 안내 묶음을 보여주지 않는다(입력이 틀렸을 때만 보임).
    s = _swap(s, "function intakeNotice(decision,productId){", "function intakeNotice(decision,productId){if(decision.inputAccepted)return '';")
    # 무료 콘텐츠 4개(무료 사주·인연 우주·태어난 시간 찾기·월간 운세)는 예시 화면뿐이라 숨긴다(2026-10-12 사장님 결정).
    # 코드는 남겨 두고 첫 화면·메뉴에서 빼며, 주소로 들어와도 첫 화면으로 보낸다. 없는 프리미엄 상담 안내와
    # 실제로 없는 5,000원 할인 팝업도 뺀다.
    s = _swap(s, '<section class="section"><div class="section-head"><h2>오늘은 가볍게, 무료 사주</h2><p>혼자 발견하고, 함께 나누는 나의 이야기</p></div><div class="rail free-rail"><a href="#/free" class="banner"><span class="eyebrow">FREE READING</span><h3>내 안의<br>또 다른 나</h3><p>사주팔자 · 운명지도 · 전생</p><span class="pill">무료로 시작하기</span></a><a href="#/friends" class="banner friend-banner"><span class="eyebrow">OUR UNIVERSE</span><h3>친구와 나의<br>인연 우주</h3><p>우리 사이, 새로운 발견</p><span class="pill">함께 알아보기</span></a></div></section>', '')
    s = _swap(s, '<section class="section"><div class="section-head"><h2>태어난 시간을 모르겠다면</h2><p>나의 성향에서 찾는 시간의 실마리</p></div><a class="banner time-banner" href="#/birth"><span class="eyebrow">FIND MY TIME</span><h3>내가 태어난<br>시간을 찾아서</h3><p>몇 가지 질문으로 시작하는 시간 여행</p></a></section>', '')
    s = _swap(s, '<section class="section"><div class="section-head"><h2>이번 계절의 이야기</h2><p>지금 나에게 필요한 운세와 소식</p></div><div class="rail free-rail"><a class="banner monthly-banner" href="#/monthly"><span class="eyebrow">MONTHLY LETTER</span><h3>${new Date().getMonth()+1}월,<br>나의 운세 편지</h3><p>일간별로 펼쳐보는 이번 달</p></a><a class="banner" href="#/support"><span class="eyebrow">WITH YOU</span><h3>궁금한 이야기를<br>직접 물어보세요</h3><p>상담과 서비스 문의</p></a></div></section>',
              '')  # 첫 화면 문의 배너는 뺀다(2026-10-25 사장님). 고객센터는 메뉴에 남아 있다.
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
              "['결과를 받기까지 얼마나 걸리나요?','결제 후 보통 10분 안에, 늦어도 1일 안에 이메일로 도착해요. 30분이 지나도 오지 않으면 스팸함을 확인한 뒤 고객센터로 알려주세요.']")
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

    # 구매 안내는 리포트 안내 페이지에 두지 않고, 결제 화면에서만 친절한 말투로 알려 준다(사장님 2026-10-27, 9개 상품 모두).
    # 처음엔 토스·카드사 심사(2026-10-25) 때문에 안내 페이지 끝에 두었다. 심사에서 보완 요청이 오면 되살린다.
    s = _swap(s, "</head>", "<style>.purchase-info{margin:28px 24px 8px;padding:22px 20px;border:1px solid #ffffff26;border-radius:16px;background:#ffffff0a}"
              ".purchase-info h2{margin:0 0 12px;font-size:18px}.purchase-info ul{margin:0;padding-left:18px;font-size:15px;line-height:1.7}.purchase-info li+li{margin-top:6px}.checkout .purchase-info{margin:16px 0 8px;word-break:keep-all}"
              ".purchase-info h2{margin:0 0 12px;font-size:18px}.purchase-info dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:10px 14px;font-size:15px;line-height:1.55}"
              ".purchase-info dt{font-weight:700;opacity:.8;white-space:nowrap}.purchase-info dd{margin:0}.purchase-info a{color:inherit;text-decoration:underline}"
              ".service-period{margin:10px 0 0;font-size:14px;line-height:1.55}</style></head>")
    # 접수 화면: 금액 아래에 서비스 제공 기간을 적는다.
    s = _swap(s, '<div id="checkout-price">${priceBox(p,d.discount||0)}</div>',
              '<div id="checkout-price">${priceBox(p,d.discount||0)}</div>'
              '<section class="purchase-info"><h2>주문 전에 알아 두시면 좋아요</h2><ul>'
              '<li>사주 결과는 리포트로 정리해서, 위에 적어 주신 이메일로 PDF 파일을 보내드려요.</li>'
              '<li>결제하고 보통 10분 안에 도착해요. 늦어도 1일 이내에는 꼭 보내드려요.</li>'
              '<li>메일이 보이지 않으면 스팸함도 한 번 확인해 주세요.</li>'
              '<li>메일을 보내기 전이라면 전액 환불해 드려요.<br><a href="#/legal/refund">환불 안내 보기</a></li></ul>'
              '</section>')

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


def legal_js(b: dict, contact: str) -> str:
    company = b.get("company") or "운명서재"
    privacy = f"""<h2>1. 받는 정보</h2><p>이름, 성별, 생년월일과 양력·음력·윤달 여부, 태어난 시간(정확한 시각, 시간 범위 또는 모름), 태어난 지역, 상품별 질문과 답, 이메일을 받습니다. 두 사람 상품은 상대방의 같은 정보를 받습니다. 카드 정보는 토스페이먼츠가 직접 받고, {company}은(는) 카드 번호를 받지 않습니다.</p><h2>2. 쓰는 목적</h2><p>사주 결과를 계산하고 작성해 이메일로 보내는 데 씁니다. 결제 화면에서 '할인·이벤트 소식 이메일 받기(선택)'에 동의하신 분께만 재구매 할인 코드와 친구 초대 링크를 이메일로 보냅니다. 동의하지 않아도 구매할 수 있고, 메일 끝의 링크로 언제든 수신을 거부할 수 있습니다. 그 밖의 광고나 다른 목적으로 쓰지 않습니다.</p><h2>3. 보관 기간</h2><p>출생 정보와 질문은 결과 메일을 보내는 즉시 지웁니다. 결과 PDF는 다시 보내기를 위해 7일 동안 보관한 뒤 지웁니다. 발송이 보류된 주문의 정보는 다시 만들 수 있게 7일 동안 보관한 뒤 지우고, 결제가 안 된 주문의 정보는 8일 안에 지웁니다. 주문번호, 결제 금액, 이메일 같은 거래 기록은 전자상거래법에 따라 5년 동안 보관합니다. 첫 구매 묶음 할인을 확인하려고 이메일을 알아볼 수 없게 바꾼 값(해시)과 구매 여부를 보관하고, 할인 코드 사용 기록과 수신 거부 기록도 보관합니다.</p><h2>4. 처리를 맡기는 곳</h2><p>토스페이먼츠(결제), Netlify(미국, 사이트와 주문 저장), GitHub(미국, 결과 작성 작업 실행), Anthropic(미국, 결과 글 작성), Resend(미국, 이메일 발송)에 필요한 정보만 맡깁니다. 해외 업체로는 주문을 처리하는 동안 암호화된 연결로 전송됩니다.</p><h2>5. 요청할 수 있는 것</h2><p>내 정보의 열람, 정정, 삭제, 처리 중지를 요청할 수 있습니다. 문의: {contact}</p>"""
    terms = """<h2>1. 서비스</h2><p>운명서재는 입력한 출생 정보로 사주를 계산하고, 개인별 결과를 PDF로 작성해 결제 후 1일 이내에 이메일로 보내드립니다.</p><h2>2. 콘텐츠의 성격</h2><p>사주 결과는 자기 이해와 오락을 위한 참고 자료입니다. 의료, 법률, 투자 같은 중요한 판단을 대신하지 않습니다.</p><h2>3. 입력 정보</h2><p>결과는 입력한 정보로 작성됩니다. 생년월일이나 시간이 틀리면 결과도 달라지므로 정확히 입력해주세요.</p><h2>4. 저작권</h2><p>결과 PDF는 구매한 분의 개인적인 이용을 위해 제공되며, 무단으로 다시 팔거나 배포할 수 없습니다.</p>"""
    refund = f"""<h2>서비스 제공 기간</h2><p>결과 PDF는 결제 후 1일 이내에 주문할 때 입력한 이메일로 보내드립니다. 보통 10분 안에 도착합니다. 배송 상품이 아닙니다.</p><h2>결과를 보내기 전</h2><p>결제 후 결과 이메일을 보내기 전에는 전액 환불해 드립니다.</p><h2>결과를 보낸 뒤</h2><p>결과는 결제 후 개인별로 작성하는 디지털 콘텐츠라서, 이메일로 보낸 뒤에는 단순 변심으로 인한 환불이 어렵습니다(전자상거래법 제17조 제2항).</p><h2>오류가 있을 때</h2><p>이메일이 오지 않거나, 입력한 정보와 다른 내용으로 작성되는 등 오류가 있으면 다시 보내드리거나 전액 환불해 드립니다.</p><h2>문의</h2><p>{contact}</p>"""
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
              "['newyear'].map(id=>{const p=pById(id);return `<a class=\"hero-card\" href=\"${link(p)}\">${art(p,p.id+'.hero','hero-card',`<div class=\"hero-copy\"><span class=\"event-tag\">EVENT</span><span class=\"eyebrow\">${p.guide} · 2027 NEW YEAR</span>")
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


TASTER_CSS = (
    ".taster-banner{border:1px solid #d8bb7866}"
    ".taster-banner.palace-banner{background-image:linear-gradient(90deg,#000000e0 5%,#000000c8 62%,#000000b0),var(--palace-bg)}"
    ".taster-banner .eyebrow,.taster-banner p{text-shadow:0 1px 6px #000,0 0 3px #000}.taster-banner p{color:#f3ecdf;font-weight:500}"
    ".taster-banner h3{color:#fff;text-shadow:0 2px 10px #000}.taster-banner p{text-shadow:0 2px 8px #000}"
    ".taster-banner .taster-cta{display:inline-block;margin-top:14px;padding:9px 16px;border-radius:999px;background:#ee3656;color:#fff;font-size:16px;font-weight:700}"
    ".taster-form .taster-submit{width:100%;margin-top:22px}"
    ".taster-result h1{font-size:29px;line-height:1.45;margin:10px 0 18px}"
    ".taster-chart{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:0 0 10px}"
    ".tc-col{position:relative;display:flex;flex-direction:column;align-items:center;gap:2px;padding:12px 0;border:1px solid #ffffff1f;border-radius:12px;background:#151515}"
    ".tc-col.me{border-color:#d8bb78}.tc-col small{font-size:14px;color:#a3a3a3}.tc-col b{font:600 30px/1.25 Georgia,'Batang',serif}"
    ".tc-col span{font-size:15px;color:#e5e5e5}.tc-col em{position:absolute;top:-9px;right:-4px;font-style:normal;font-size:13px;font-weight:700;padding:1px 7px;border-radius:9px;background:#d8bb78;color:#1a1408}"
    ".taster-note{font-size:15px;line-height:1.7;color:#a3a3a3;margin:0 0 14px}"
    ".taster-box{padding:18px 16px 10px;margin:0 0 10px;border-radius:14px;background:#151515;border:1px solid #ffffff17}"
    ".taster-box h3{font-size:20px;margin:0 0 12px}.tb-item{margin:0 0 14px}.tb-item strong{display:block;font-size:17px;color:#d8bb78;margin:0 0 4px}"
    ".tb-item p{font-size:16px;line-height:1.8;margin:0;color:#e5e5e5}.tb-bars{margin:6px 0 8px}"
    ".tb-bar{display:grid;grid-template-columns:44px 1fr 56px;align-items:center;gap:8px;margin:0 0 8px;font-size:15px}"
    ".tb-bar i{height:10px;border-radius:5px;background:#2a2a2a;overflow:hidden}.tb-bar i b{display:block;height:100%;background:#d8bb78}"
    ".tb-bar.lack i b{background:#ff7b8f}.tb-bar.many i b{background:#6fb7ff}.tb-bar em{font-style:normal;color:#a3a3a3;text-align:right}"
    ".taster-intro{font-size:17px;line-height:1.85;color:#e5e5e5;margin:0 0 26px}"
    ".taster-head{font-size:23px;margin:30px 0 12px;padding-left:12px;border-left:4px solid #6fcf97}.taster-head.bad{border-left-color:#ee3656}"
    ".taster-item{padding:18px 18px 16px;margin:0 0 12px;border-radius:14px;background:#171717;border:1px solid #ffffff17}"
    ".taster-rank span{font-size:14px;font-weight:700;color:#6fcf97}.taster-item.bad .taster-rank span{color:#ff7b8f}"
    ".taster-rank h3{font-size:21px;margin:4px 0 10px}.taster-item p{font-size:17px;line-height:1.85;margin:0 0 12px;color:#e5e5e5}.taster-item p.taster-hook{font-weight:800;color:#fff;margin:-2px 0 14px}"
    ".taster-more{display:block;font-size:17px;font-weight:700;line-height:1.6;color:#ff7b8f;text-decoration:underline;text-underline-offset:4px}"
    ".taster-item.good .taster-more{color:#6fcf97}"
    ".taster-redo{display:block;width:100%;margin:14px 0 6px;padding:15px;border-radius:12px;border:1px solid #ffffff40;background:#1b1b1b;color:#fff;font-size:17px;font-weight:700}"
    ".reuse-me{display:flex;gap:12px;align-items:flex-start;margin:0 0 16px;padding:16px;border-radius:14px;border:1px solid #d8bb7880;background:#1a1610;cursor:pointer}"
    ".reuse-me input{width:22px;height:22px;margin:2px 0 0;flex:0 0 22px;accent-color:#d8bb78}"
    ".reuse-me b{display:block;font-size:17px;color:#fff}.reuse-me small{display:block;margin-top:4px;font-size:14px;line-height:1.6;color:#bfb6a5}"
    ".taster-lifetime{display:block;margin:28px 0 6px;padding:26px 20px;min-height:190px;border-radius:14px;border:1px solid #d8bb7866;"
    "background:linear-gradient(90deg,#0d0a06 0%,#0d0a06 34%,#0d0a06b0 60%,#0d0a0610 100%),url(assets/geumwol/lifetime-room.jpg) right 22% / 66% auto no-repeat,#0d0a06}"
    ".taster-lifetime strong{display:block;font-size:27px;line-height:1.4;margin:8px 0 12px;color:#fff;text-shadow:0 2px 10px #000}"
    ".taster-lifetime span:last-child{color:#d8bb78;font-size:19px;font-weight:700;text-decoration:underline;text-underline-offset:4px;text-shadow:0 2px 8px #000}"
)


def add_taster(s: str) -> str:
    """무료 사주 맛보기(#/taster): 첫 화면 배너 + 입력·결과 화면 (2026-10-25 사장님 요청).
    계산은 public/assets/free/ 의 계산기가 브라우저에서 한다(AI 호출 없음, 0원)."""
    page = (SITE / "tools" / "taster_page.js").read_text(encoding="utf-8")
    s = _swap(s, "</head>", f"<style>{TASTER_CSS}</style></head>")
    s = _swap(s, "function render(){", page + "function render(){")
    # 배너 배경: 예전 문의 배너와 같은 서재 그림(palace.study).
    s = _swap(s, "href.includes('support')?'palace.study'", "href.includes('support')||href.includes('taster')?'palace.study'")
    s = _swap(s, "else if(route==='/support')supportPage();",
              "else if(route==='/support')supportPage();else if(route==='/taster')tasterPage();")
    s = _swap(s, '</div></div><section class="section"><div class="section-head"><h2>오리지널 연애 사주</h2>',
              '</div></div><section class="section"><a class="banner taster-banner" href="#/taster"><span class="eyebrow">무료 사주 분석</span>'
              '<h3>당신의 6가지 핵심 운을<br>무료로 풀어드립니다.</h3><p>내 사주에서 좋은 운 3개, 조심할 운 3개를<br>바로 알려드려요.</p>'
              '<span class="taster-cta">무료로 나의 운 확인하기</span></a></section>'
              '<section class="section"><div class="section-head"><h2>오리지널 연애 사주</h2>')
    return s


TRUST_HTML = (
    '<section class="trust-box" aria-labelledby="trust-title"><span class="eyebrow">운명서재의 계산 근거</span>'
    '<h2 id="trust-title"><em>국가기관 공식 자료</em>와<br><em>국제 천문 계산법</em>으로<br>사주를 계산합니다</h2>'
    '<p class="trust-lead">풀이가 아무리 좋아도 사주 여덟 글자 계산이 틀리면 리포트 전체가 틀립니다. '
    '그래서 운명서재는 계산의 기준을 감으로 정하지 않고, 모두 공식 자료에 맞췄습니다.</p>'
    '<h3>믿을 수 있는 4가지 공식 출처</h3><ul class="trust-sources">'
    '<li><b>한국천문연구원 음력 기준</b><span>음력 생일과 윤달을 국가 천문 기관 기준으로 바꿉니다.</span></li>'
    '<li><b>행정안전부 지역 목록</b><span>태어난 지역의 경도로 실제 해의 시각을 맞춥니다.</span></li>'
    '<li><b>국제 표준 시간대 자료</b><span>한국 표준시가 바뀐 기록과 서머타임 기간을 그대로 반영합니다.</span></li>'
    '<li><b>국제 천문 계산법(VSOP87)</b><span>태양의 실제 위치로 24절기 시각을 분 단위까지 계산합니다.</span></li></ul>'
    '<h3>계산이 자주 어긋나는 3가지 경우도<br>정확하게 맞춥니다</h3><ul class="trust-cases">'
    '<li><b>절기 날 태어난 분</b><span>몇 분 차이로 태어난 달이 바뀌는데, 절기 시각을 분 단위로 계산해 정확히 나눕니다.</span></li>'
    '<li><b>1948~1961년, 1987~1988년에 태어난 분</b><span>표준시와 서머타임이 지금과 달랐던 시기라 그 시절 시계 기준으로 다시 계산합니다.</span></li>'
    '<li><b>서울이 아닌 지역에서 태어난 분</b><span>같은 시각이라도 지역마다 해의 위치가 달라서 출생 지역 기준으로 시각을 보정합니다.</span></li></ul>'
    '<h3>직접 검증한 결과</h3><div class="trust-stats">'
    '<div><strong>2,664개</strong><span>1940~2050년 24절기 시각 2,664개를 천문 전문 만세력(수성만년력)과 하나씩 대조했고, 차이는 모두 30초 이내였습니다.</span></div>'
    '<div><strong>10,000개</strong><span>서로 다른 생년월일시 10,000개로 사주팔자를 계산해 수성만년력 결과와 대조했고, 한 글자도 틀리지 않았습니다.</span></div></div>'
    '<div class="trust-close"><strong>내 사주가 제대로 계산됐는지,<br>이제 확인할 수 있습니다.</strong>'
    '<p>어떤 자료로 어떻게 계산했는지 모두 공개합니다.<br>확인할 수 있는 정확함, 그것이 운명서재의 기준입니다.</p></div></section>'
    # 근거를 다 읽은 사람이 바로 누를 수 있게 무료 분석 배너를 한 번 더 둔다(2026-10-27 사장님).
    '<section class="section taster-after"><a class="banner taster-banner" href="#/taster"><span class="eyebrow">무료 사주 분석</span>'
    '<h3>정확한 기준으로 계산한 내 사주,<br>지금 무료로 확인해 보세요.</h3><p>내 사주에서 좋은 운 3개, 조심할 운 3개를<br>바로 알려드려요.</p>'
    '<span class="taster-cta">무료로 나의 운 확인하기</span></a></section>'
)

TRUST_CSS = (
    ".trust-box{margin:8px 20px 12px;padding:26px 20px;border-radius:16px;border:1px solid #d8bb7855;background:linear-gradient(180deg,#17130c,#0e0d0b)}"
    ".trust-box .eyebrow{color:#d8bb78}.trust-box h2{font-size:25px;line-height:1.45;margin:10px 0 14px;color:#fff}.trust-box h2 em{font-style:normal;color:#f0c75e}"
    ".trust-lead{font-size:16px;line-height:1.8;color:#e2dccf;margin:0 0 22px}"
    ".trust-box h3{font-size:18px;line-height:1.5;margin:22px 0 10px;color:#d8bb78}"
    ".trust-box ul{list-style:none;margin:0;padding:0}.trust-box li{padding:12px 0;border-top:1px solid #ffffff14}"
    ".trust-box li b{display:block;font-size:16px;color:#fff;margin-bottom:3px}.trust-box li span{font-size:15px;line-height:1.7;color:#bdb5a6}"
    ".trust-sources li b::before{content:'✓ ';color:#d8bb78}"
    ".trust-stats{display:grid;grid-template-columns:1fr 1fr;gap:10px}"
    ".trust-stats div{padding:14px 12px;border-radius:12px;background:#ffffff0a;border:1px solid #ffffff14}"
    ".trust-stats strong{display:block;font-size:24px;color:#d8bb78;margin-bottom:4px}.trust-stats span{font-size:14px;line-height:1.6;color:#bdb5a6}"
    ".trust-close{margin-top:24px;padding-top:20px;border-top:1px solid #d8bb7855}"
    ".taster-after{padding-top:0!important;margin-top:-31px!important}.taster-after .taster-banner h3{font-size:clamp(18px,calc((100vw - 90px)/12.8),26px);line-height:1.45;letter-spacing:0}.taster-after .taster-banner p{font-size:clamp(14px,calc((100vw - 90px)/16.8),18px)}"
    ".trust-close strong{display:block;font-size:21px;line-height:1.5;color:#fff}.trust-close p{font-size:16px;line-height:1.8;color:#e2dccf;margin:8px 0 0}"
)


def add_trust(s: str) -> str:
    """첫 화면 맨 아래 안내 칸 자리에 '계산 근거' 소개를 넣는다 (2026-10-27 사장님 문구 확정).
    숫자는 tests/test_calendar.py 대조 결과(절기 1940~2050년 최대 약 27초, 무작위 10,000건, tests/test_calendar.py)와 맞춰 둔다."""
    s = _swap(s, "</head>", f"<style>{TRUST_CSS}</style></head>")
    s = _swap(s, '<div class="preview-note">금월선녀와 함께 펼치는 사주 이야기. 모든 리포트는 결제 후 한 분 한 분의 사주로 새로 작성해 이메일로 보내드려요.</div>', TRUST_HTML)
    return s


def add_input_helpers(s: str) -> str:
    """입력 화면 손보기 (2026-10-26 사장님 요청).
    1) 본인 정보 입력 화면 맨 위에 '전에 입력한 내 정보 그대로 쓰기' 체크.
    2) 시·도 목록에서 옛 지역명을 빼고 짧은 이름(서울, 강원도, 광주·전남 …)으로 보여 준다.
    3) '선택한 지역명은 언제 기준인가요?' 질문을 뺀다(사람들이 헷갈려 함)."""
    page = (SITE / "tools" / "reuse_me.js").read_text(encoding="utf-8")
    s = _swap(s, "function render(){", page + "function render(){")
    s = _swap(s, '<form id="person-form" novalidate>${personFields(s.who,d[s.who])}',
              '<form id="person-form" novalidate>${s.who===\'self\'?reuseBox(d.self,\'reuse-me\'):\'\'}${personFields(s.who,d[s.who])}')
    s = _swap(s, "(v,valid)=>{d[s.who]=v;next.disabled=!valid;save()});",
              "(v,valid)=>{d[s.who]=v;next.disabled=!valid;if(valid&&s.who==='self')rememberMe(v);save()});"
              "if(s.type==='info'&&s.who==='self')bindReuse('reuse-me',v=>{d.self=v;save()});")
    s = _swap(s, "KOREA_REGIONS.filter(r=>!r.legacy).map(r=>`<option value=\"${r.id}\" ${region?.id===r.id?'selected':''}>${e(r.label)}</option>`).join('')}"
                 "<optgroup label=\"예전 지역명으로 찾기\">${KOREA_REGIONS.filter(r=>r.legacy).map(r=>`<option value=\"${r.id}\" ${region?.id===r.id?'selected':''}>${e(r.label)}</option>`).join('')}</optgroup>",
              "plainRegions().map(r=>`<option value=\"${r.id}\" ${region?.id===r.id?'selected':''}>${e(REGION_PLAIN[r.name])}</option>`).join('')}")
    s = _swap(s, "목록에 없는 옛 지역명", "목록에 없어요 (직접 입력)")
    s = _swap(s, "기억나는 옛 지역명", "태어난 곳 이름")
    s = _swap(s, "예: 옛 시·군·구 이름", "예: 시·군·구 이름")
    s = _swap(s, "q('[data-place-reference]').hidden=!referenceEnabled;", "q('[data-place-reference]').hidden=true;")
    s = _swap(s, "enable('placeReferenceEra',referenceEnabled);", "enable('placeReferenceEra',false);")
    s = _swap(s, "+(place&&['known','region-only'].includes(place.status)?'<br>'+e(locationEra):'');", ";")
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


def fix_checkout_flow(s: str) -> str:
    """결제 화면 버튼은 처음부터 카드 그림 + '결제하고 결과 받기' 하나만 둔다(사장님 2026-10-27).

    누르면 입력·접수 기준을 확인하고, 통과하면 바로 결제창을 연다. 확인 결과 칸은 버튼 바로 아래에 두어
    화면이 위로 튀지 않게 한다(예전에는 이메일 칸 위에 있었다).
    """
    card = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18v12H3ZM3 10h18"/></svg>'

    status = '<section id="intake-status" aria-live="polite">${intakeNotice(evaluateIntake(intakePayload(p.id,d)),p.id)}</section>'
    s = _swap(s, status, "")
    s = _swap(s, '<button class="primary dark-primary" id="pay" type="submit" disabled>입력 확인하기</button><p class="fine-print">입력 확인이 끝나면 결제 버튼이 나타나요. 결제 후 보통 10분 안에 이메일로 PDF를 보내드려요.</p>',
              '<button class="primary dark-primary pay-button" id="pay" type="submit" disabled>' + card + '결제하고 결과 받기</button>' + status)
    # 확인을 통과하면 숨은 결제 시작 버튼을 바로 눌러 결제창을 연다. 실패 안내는 그 아래에 뜨고, '결제하기'를 다시 누르면 된다.
    s = _swap(s, "if(result.paymentAllowed)bindReadyCheckout(area,p,d);area.scrollIntoView({behavior:'smooth',block:'center'});",
              "if(result.paymentAllowed){bindReadyCheckout(area,p,d);area.querySelector('[data-start-payment]')?.click()}area.scrollIntoView({behavior:'smooth',block:'nearest'});")
    s = _swap(s, "button.dataset.startPayment='true';button.textContent=product.price.toLocaleString('ko-KR')+'원 결제하기';",
              "button.dataset.startPayment='true';button.hidden=true;button.style.display='none';button.textContent='결제하기';")
    s = _swap(s, "</head>", "<style>.pay-button{display:flex;align-items:center;justify-content:center;gap:8px}.pay-button .icon{width:20px;height:20px}</style></head>")
    return s



# 신년운세 이벤트 기간(한국 날짜, 사장님 2026-10-27: 3월 말까지, 추가 할인 없이 남은 날짜만). 기간 밖에는 저절로 사라진다.
NEWYEAR_EVENT = {"start": "2026-10-27", "end": "2027-03-31", "label": "이벤트 마감까지"}
REPORT_MODULES = {"lifetime": "outline", "romance": "romance", "reunion": "reunion", "intimate": "intimate", "wealth": "wealth",
                  "career": "career", "business": "business", "health": "health", "newyear": "newyear"}

EXTRAS_CSS = (
    # 디자인 기준(UI UX Pro Max 추천: 검정 + 금색, 고급스러운 명조 제목, 얇은 금색 선, 큰 터치 영역 44px 이상)
    ":root{--x-gold:#d8bb78;--x-gold-2:#f0d896;--x-ink:#0e0d0b;--x-card:#16130e;--x-line:#d8bb7838;--x-text:#efe8da;--x-muted:#a99f8c}"
    ".x-eyebrow{display:block;font-size:12px;letter-spacing:.32em;color:var(--x-gold);font-weight:600}"
    ".x-title{font-family:'Noto Serif KR','Noto Serif CJK KR',Georgia,serif;font-weight:700;font-size:28px;line-height:1.35;color:#fff;margin:10px 0 6px;letter-spacing:-.01em}"
    ".x-sub{font-size:15px;line-height:1.6;color:var(--x-muted);margin:0 0 20px}"
    ".x-cta{display:flex;align-items:center;justify-content:center;min-height:54px;border-radius:14px;background:linear-gradient(180deg,var(--x-gold-2),var(--x-gold));color:#1a140a;font-size:17px;font-weight:800;text-decoration:none;box-shadow:0 6px 20px #d8bb7833;transition:transform .15s ease,box-shadow .2s ease}"
    ".x-cta:active{transform:scale(.98)}"
    ".x-more{display:flex;align-items:center;justify-content:center;gap:6px;width:100%;min-height:50px;margin-top:14px;border-radius:12px;border:1px solid var(--x-line);background:#ffffff08;color:var(--x-gold);font-size:16px;font-weight:700;cursor:pointer}"
    ".x-more svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;transition:transform .2s ease}.x-more[data-open='1'] svg{transform:rotate(180deg)}"
    # 목차: 실제 리포트 목차 쪽과 같은 모양(saju/report/templates/style.css 의 .toc-sec·h2·@page)
    ".toc-x{margin:24px 20px;text-align:left}"
    ".tp-page{background:#f1e9d6;padding:12px;border-radius:4px;box-shadow:0 12px 30px #000a}"
    ".tp-frame{border:4px double #3a2e22;padding:14px 16px 18px;color:#1f1b16;font-family:'Gowun Batang','Noto Serif CJK KR',serif}"
    ".tp-head{font-family:'Song Myung','Noto Serif CJK KR',serif;font-size:15px;color:#3d362c;margin:0 0 14px}"
    ".tp-h{font-family:'Song Myung','Noto Serif CJK KR',serif;font-weight:400;font-size:24px;line-height:1.35;margin:0 0 10px;padding-left:10px;border-left:6px solid #9e2f22;color:#1f1b16}"
    ".tp-list{list-style:none;margin:0;padding:0}"
    ".tp-list li{display:flex;align-items:baseline;gap:6px;padding:9px 0;border-bottom:1px solid #d3c5a3}"
    ".tp-no{flex:0 0 34px;font-family:'Song Myung','Noto Serif CJK KR',serif;color:#9e2f22;font-size:21px}"
    ".tp-t{word-break:keep-all}.tp-t b{display:block;font-weight:700;font-size:17px;line-height:1.5;color:#1f1b16}"
    ".tp-t small{display:block;font-size:15px;line-height:1.55;color:#5a5144}"
    # 미리보기
    # 결제 화면(밝은 바탕이 아닌 검정 화면) 안의 목차·미리보기는 여백만 줄인다.
    ".checkout .toc-x{margin:18px 0}"
    # 신년 이벤트
    ".hero-tags{display:flex;align-items:center;gap:6px;margin:0 0 6px}.hero-tags .event-tag{margin:0!important}.hero-tags .event-dday{margin:0}"
    ".event-dday{display:inline-flex;align-items:center;gap:5px;margin-left:6px;padding:4px 10px 4px 11px;border-radius:999px;background:#0e0d0bcc;border:1px solid #f09c9c88;color:#f6d4d4;font-size:12px;font-weight:600;vertical-align:middle}.event-dday b{color:#fff;font-size:13px;font-weight:800}"
    # 첫 화면 팝업(2026-10-27 사장님: 너무 어둡다 → 밝게). 신년 포스터 그림 + 밝은 한지색 바탕 + 붉은 버튼. 묶음 할인은 결제 화면에만.
    ".entry-modal{padding:0;overflow:hidden;width:min(88vw,360px);max-width:none;border:0;border-radius:20px;background:#fff8ef;color:#2b1a12;box-shadow:0 24px 60px #0008}"
    # 팝업 닫기 X(사장님): 검정, 굵게, 테두리 네모 없이.
    ".entry-modal .modal-close{top:6px;right:6px;color:#111;outline:none;box-shadow:none;border:0;background:none}.entry-modal .modal-close .icon{width:26px;height:26px;stroke-width:3.2}"
    ".entry-art{position:relative;height:min(112vw,420px,56vh);overflow:hidden;background:#f6d9c4}.entry-art img{display:block;width:100%;height:100%;object-fit:cover;object-position:center 0}"
    ".entry-art:after{content:'';position:absolute;left:0;right:0;bottom:0;height:38%;background:linear-gradient(180deg,#fff8ef00,#fff8efcc 60%,#fff8ef)}"
    ".entry-body{position:relative;margin-top:-34px}"
    ".entry-tag{position:absolute;left:14px;bottom:44px;z-index:1;padding:4px 12px;border-radius:999px;background:#c8102e;color:#fff;font-size:13px;font-weight:800;letter-spacing:.14em}"
    ".entry-body{padding:18px 22px 14px;text-align:center}"
    ".entry-modal .entry-lead{font-size:16px;line-height:1.6;color:#4a3426!important;margin:0 0 14px;word-break:keep-all}"
    ".entry-count{display:flex;align-items:center;justify-content:center;gap:10px;padding:10px;border-radius:14px;background:#fde8e3;border:1px solid #f09c9c;margin-bottom:14px}"
    ".entry-count span{font-size:15px;color:#8a3a2c;font-weight:600}.entry-count b{font-size:26px;color:#c8102e;font-weight:900;letter-spacing:.02em}"
    ".entry-go{display:flex;align-items:center;justify-content:center;min-height:54px;border-radius:14px;background:linear-gradient(180deg,#e0313f,#b3141f);color:#fff;font-size:17px;font-weight:800;text-decoration:none;box-shadow:0 8px 20px #c8102e40}"
    ".entry-hide{min-height:44px;margin-top:4px;border:0;background:none;color:#8a7466;font-size:14px;text-decoration:underline;text-underline-offset:3px;cursor:pointer}"
    # 2단계 할인: 첫 구매 묶음 할인 고르기, 금액 안내, 광고 메일 동의
    ".bundle-x{margin:22px 0;padding:24px 18px 18px;border-radius:18px;border:1px solid var(--x-line);background:linear-gradient(180deg,#1a160f,var(--x-ink));text-align:left}"
    ".bundle-x .x-title{font-size:24px}.bundle-x .x-title em{font-style:normal;color:var(--x-gold-2)}.bundle-x .x-sub b{color:var(--x-text)}"
    ".bundle-list{display:flex;flex-direction:column;gap:8px}"
    ".bundle-item{display:flex;align-items:center;gap:12px;min-height:52px;padding:10px 14px;border-radius:12px;border:1px solid #ffffff18;background:#ffffff06;cursor:pointer;transition:border-color .15s ease,background .15s ease}"
    ".bundle-item:has(input:checked){border-color:var(--x-gold);background:#d8bb7814}"
    ".bundle-item input{width:22px;height:22px;accent-color:var(--x-gold);flex:0 0 auto}"
    ".bundle-q{display:none;padding:10px 4px 4px 14px}.bundle-row:has(input:checked) .bundle-q{display:block}"
    ".bundle-partner{display:none;margin:2px 0 10px;padding:16px 14px;border:1px solid var(--x-line);border-radius:14px;background:#ffffff08}"
    ".bundle-x:has(input[value=reunion]:checked) .bundle-partner,.bundle-x:has(input[value=intimate]:checked) .bundle-partner{display:block}"
    ".bundle-partner .birth-reassurance{display:none}.bundle-partner-title{margin:0 0 4px;color:var(--x-gold);font-size:17px;font-weight:800}.bundle-partner-sub{margin:0 0 12px;color:var(--x-muted);font-size:14px;line-height:1.6;word-break:keep-all}"
    ".bundle-ask{display:block;margin:4px 0 10px}.bundle-ask span{display:block;font-size:14px;color:var(--x-muted);margin-bottom:6px}"
    ".bundle-ask select{width:100%;min-height:48px;padding:0 12px;border-radius:10px;border:1px solid var(--x-line);background:#16130e;color:var(--x-text);font-size:16px}"
    ".bundle-name{flex:1;font-size:16px;font-weight:700;color:var(--x-text)}"
    # 가격: 위에 원래 값(가운데 줄), 아래에 빨간 10% + 할인된 값(2026-10-27 사장님)
    ".bundle-price{display:flex;flex-direction:column;align-items:flex-end;line-height:1.35}.bundle-price s{font-size:13px;color:var(--x-muted)}"
    ".bundle-price span{font-size:16px;font-weight:800;color:var(--x-text);white-space:nowrap}.bundle-price em,.qb-final em{font-style:normal;color:#ff4d5a;font-weight:800;margin-right:6px}"
    ".price-box .qb-final{display:flex;flex-direction:column;align-items:flex-end;line-height:1.3}.price-box .qb-final s{font-size:15px;color:var(--x-muted);font-weight:500}"
    ".price-box .qb-items{display:block;padding:0 0 10px;margin:0 0 10px;border-bottom:1px dashed #ffffff22}.price-box .qb-items div{display:flex;justify-content:space-between;gap:12px;font-size:15px;color:var(--x-muted);padding:3px 0;margin:0;border:0}.price-box .qb-items span{white-space:nowrap}"
    ".price-box .qb-disc span,.price-box .qb-disc strong{color:var(--x-gold-2);font-weight:800}.price-box .qb-disc em{font-style:normal;color:inherit;margin-left:4px}"
    ".qb-note{margin:10px 2px 0;font-size:14px;line-height:1.55;color:var(--x-muted)}"
    ".mk-help{margin:2px 0 6px 30px;font-size:14px;line-height:1.55;color:var(--x-muted)}"
    "@media (prefers-reduced-motion:reduce){.x-cta,.x-more svg,.bundle-item{transition:none}}"
)


def extras_data() -> dict:
    """목차(saju/report 의 SECTIONS, 숫자 장만)와 미리보기 그림 목록."""
    import importlib
    sys.path.insert(0, str(SITE.parent))
    toc = {}
    for pid, mod in REPORT_MODULES.items():
        sections = importlib.import_module(f"saju.report.{mod}").SECTIONS
        toc[pid] = [[num, title, desc] for num, title, desc in sections if str(num).isdigit()]
    from saju.report.render import PRODUCT
    header = {pid: PRODUCT.get(pid, {}).get("header", "平生四柱") for pid in REPORT_MODULES}
    return {"toc": toc, "header": header, "event": NEWYEAR_EVENT, "bundle": True}


REVEAL_CSS = (
    ".reveal-flow .rv-body{padding-bottom:110px}.reveal-flow h1{font-size:28px;line-height:1.4;margin:8px 0 16px}"
    ".rv-dots{display:flex;gap:6px;justify-content:center;padding:4px 0 2px}.rv-dots i{width:26px;height:4px;border-radius:2px;background:#ffffff26}.rv-dots i.on{background:#d8bb78}"
    ".rv-guide{display:flex;gap:12px;align-items:flex-start;margin:6px 0 22px;padding:14px;border-radius:14px;border:1px solid #d8bb7859;background:#17130c}"
    ".rv-guide img{width:54px;height:54px;flex:0 0 54px;border-radius:50%;object-fit:cover;object-position:50% 18%;border:1px solid #d8bb78}"
    ".rv-guide strong{display:block;font-size:14px;color:#d8bb78;margin:0 0 3px}.rv-guide p{margin:0;font-size:17px;line-height:1.7;color:#f3ecdf}"
    ".rv-card{padding:16px;margin:0 0 12px;border-radius:14px;background:#151515;border:1px solid #ffffff17}"
    ".rv-card strong,.rv-card small{display:block;font-size:16px;font-weight:700;color:#d8bb78;margin:0 0 6px}"
    ".rv-card p{font-size:17px;line-height:1.8;margin:0 0 8px;color:#e5e5e5}.rv-card p:last-child{margin-bottom:0}"
    ".rv-card.good{border-color:#6fcf9766}.rv-card.good small{color:#6fcf97}.rv-card.bad{border-color:#ee365666}.rv-card.bad small{color:#ff7b8f}"
    ".rv-card p.rv-hook{font-weight:800;color:#fff;padding-top:8px;border-top:1px solid #ffffff1a;margin-top:10px}"
    ".rv-confirm p{font-size:18px;color:#fff}.rv-yesno{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}"
    ".rv-yesno button{padding:13px;border-radius:10px;border:1px solid #ffffff40;background:#1d1d1d;color:#fff;font-size:17px;font-weight:700}"
    ".rv-yesno button.on[data-v=yes]{background:#d8bb78;border-color:#d8bb78;color:#1a1408}.rv-yesno button.on[data-v=no]{background:#3a3a3a}"
    ".rv-result{margin:16px 0 0;padding:16px;border-radius:14px;background:#d8bb781f;border:1px solid #d8bb78;font-size:18px;line-height:1.7;font-weight:700;color:#fff}"
    ".rv-score-label{display:block;font-size:16px;font-weight:700;color:#cfc6b4;margin:0 0 4px}.rv-score{margin:0 0 14px}.rv-score strong{display:block;font-size:64px;line-height:1;font-weight:900}.rv-score strong small{font-size:24px;margin-left:2px}"
    ".rv-score span{display:block;margin:6px 0 10px;font-size:18px;font-weight:700}.rv-score i{display:block;height:12px;border-radius:6px;background:#2a2a2a;overflow:hidden}.rv-score i b{display:block;height:100%}"
    ".rv-score.good strong,.rv-score.good span{color:#6fcf97}.rv-score.good i b{background:#6fcf97}"
    ".rv-score.mid strong,.rv-score.mid span{color:#d8bb78}.rv-score.mid i b{background:#d8bb78}"
    ".rv-score.bad strong,.rv-score.bad span{color:#ff7b8f}.rv-score.bad i b{background:#ff7b8f}"
    ".rv-bridge{font-size:19px;font-weight:800;line-height:1.55;margin:26px 0 14px;color:#fff}.rv-bridge.bad{color:#ff7b8f}.rv-bridge.good{color:#6fcf97}"
    ".rv-sub{font-size:20px;margin:26px 0 12px}.rv-bars{margin:0 0 16px}"
    ".rv-bar{display:grid;grid-template-columns:92px 1fr 48px;align-items:center;gap:8px;margin:0 0 9px;font-size:15px}"
    ".rv-bar i{height:10px;border-radius:5px;background:#2a2a2a;overflow:hidden}.rv-bar i b{display:block;height:100%;background:#d8bb78}"
    ".rv-bar.good i b{background:#6fcf97}.rv-bar.bad i b{background:#ff7b8f}.rv-bar em{font-style:normal;color:#cfc6b4;text-align:right}"
    ".rv-locks{margin:16px 0;border-top:1px solid #ffffff1a}.rv-locks div{display:flex;align-items:center;gap:10px;padding:13px 2px;border-bottom:1px solid #ffffff1a;font-size:16px;color:#e5e5e5}"
    ".rv-locks .icon{width:18px;height:18px;color:#d8bb78;flex:0 0 18px}.rv-locks span{flex:1}.rv-locks i{font-style:normal;font-size:13px;color:#d8bb78}"
    ".rv-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:0 0 10px}"
    ".rv-cell{display:flex;flex-direction:column;align-items:center;gap:2px;padding:9px 2px;min-height:78px;border-radius:10px;background:#1b1b1b;border:1px solid #ffffff14}"
    ".rv-cell b{font-size:15px;color:#e5e5e5}.rv-cell small{font-size:12px;color:#8f8f8f}.rv-cell span{font-size:11px;font-weight:700;padding:1px 6px;border-radius:7px;margin-top:2px;white-space:nowrap}"
    ".rv-cell span.g{background:#6fcf97;color:#0b1f14}.rv-cell span.r{background:#ee3656;color:#fff}"
    ".rv-cell.good{border-color:#6fcf97;background:#10241a}.rv-cell.bad{border-color:#ee3656}.rv-cell.good.bad{background:linear-gradient(135deg,#10241a 50%,#2a1015 50%)}"
    ".rv-legend{display:flex;flex-wrap:wrap;gap:12px;font-size:13px;color:#a3a3a3;margin:0 0 16px}.rv-legend .g::before,.rv-legend .r::before{content:'';display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;background:#6fcf97}.rv-legend .r::before{background:#ee3656}"
    ".rv-mark-head{display:flex;align-items:flex-start;gap:10px;margin:0 0 8px}.rv-mark-head b{font-size:18px;line-height:1.45;color:#fff;word-break:keep-all}"
    ".rv-tag{flex:0 0 auto;white-space:nowrap;font-size:14px;font-weight:800;padding:3px 10px;border-radius:9px}.rv-tag.good{background:#6fcf97;color:#0b1f14}.rv-tag.bad{background:#ee3656;color:#fff}"
    ".rv-card p.rv-mark-line{font-weight:700;color:#6fcf97}.rv-mark.bad p.rv-mark-line{color:#ff7b8f}.rv-mark.good{border-color:#6fcf9766}"
    ".rv-page{margin:4px 0 16px}.rv-ch{display:flex;gap:10px;align-items:flex-start;padding:12px 0;border-top:1px solid #3a2e2233}"
    ".rv-ch b{display:block;font-size:17px;margin:2px 0 4px}.rv-ch p{font-size:15px;line-height:1.75;margin:0 0 6px;color:#2a2018}"
    ".rv-ch .icon{width:16px;height:16px;flex:0 0 16px;margin-top:6px;color:#9e2f22;margin-left:auto}"
    ".rv-ch.open{background:#fffaf0;margin:0 -8px;padding:12px 8px;border-radius:6px}.rv-blur{filter:blur(4px);user-select:none}"
    ".rv-close{font-size:17px;line-height:1.75;color:#f3ecdf;text-align:center;margin:8px 0 0}"
)


def add_extras(s: str) -> str:
    """사이트 추가 기능 1단계 (2026-10-27 사장님 선택 12개 중 화면만 바뀌는 것).
    리포트 목차, 신년 이벤트 남은 날짜와 첫 화면 팝업."""
    page = (SITE / "tools" / "extras.js").read_text(encoding="utf-8")
    data = json.dumps(extras_data(), ensure_ascii=False, separators=(",", ":"))
    s = _swap(s, "</head>", '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
              '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@700&family=Song+Myung&family=Gowun+Batang:wght@400;700&display=swap" rel="stylesheet">'
              f"<style>{EXTRAS_CSS}</style></head>")
    s = _swap(s, "function render(){", f"const EXTRA_DATA={data};\n" + page + "function render(){")
    # 리포트 안내 페이지: 예전 짧은 목차 → 실제 리포트 목차(펼쳐보기) + 미리보기.
    s = _swap(s, "<section class=\"chapters\"><span class=\"eyebrow\">CONTENTS</span><h2 class=\"serif\">리포트의 목차</h2>${s.chapters.map((c,n)=>`<article class=\"chapter\"><span>${String(n+1).padStart(2,'0')}</span><h3>${c}</h3><p>${chapterLine(n)}</p></article>`).join('')}</section>",
              "${tocBlock(p)}")
    # 재물운·직업운은 리포트 안내 페이지 없이 바로 결제 화면으로 가므로, 목차·미리보기를 결제 화면 위쪽에 둔다.
    # 첫 구매 묶음 할인은 결제 화면 맨 위(상품 그림 바로 아래)에 둔다(2026-10-27 사장님).
    s = _swap(s, '<section class="checkout-birth-summary">', '${bundleBlock(p,d)}${SALES[p.id]?\'\':tocBlock(p)}<section class="checkout-birth-summary">')
    # 2026-10-27 사장님: 신년 큰 배너의 '금월선녀 · 2027 NEW YEAR' 줄은 빼고, EVENT·D-day 두 표시를 제목 바로 위로.
    s = _swap(s, '<span class=\"event-tag\">EVENT</span><span class=\"eyebrow\">${p.guide} · 2027 NEW YEAR</span>',
              '<span class=\"hero-tags\"><span class=\"event-tag\">EVENT</span>${eventBadge()}</span>')
    s = _swap(s, "${footer()}</div>`;bindHome();}", "${footer()}</div>`;bindHome();entryPopup();}")
    return add_sales_pages(add_discounts(s))


def add_sales_pages(s: str) -> str:
    """재물운·직업운에도 리포트 안내 화면을 붙인다(2026-10-27 사장님: 대충이라도 만들어 목차·미리보기를 거기에, 나중에 다시 고침)."""
    s = _swap(s, "'언제 나아질지 궁금해요','잠시 쉬고 있어요'],true),checkout]",
              "'언제 나아질지 궁금해요','잠시 쉬고 있어요'],true),"
              "scene('ready','나의 재물운을\\n한 권에 담았어요','돈이 들어오는 길과 새는 곳, 좋은 해와 조심할 해를 차례로 확인해 보세요.','재물운 리포트 살펴보기'),sales,checkout]")
    s = _swap(s, "{...question,title:'직업에 관해 꼭 묻고 싶은 것이 있나요?'},checkout],",
              "{...question,title:'직업에 관해 꼭 묻고 싶은 것이 있나요?'},"
              "scene('ready','나의 직업운을\\n한 권에 담았어요','나에게 맞는 일과 이직하기 좋은 시기를 차례로 확인해 보세요.','직업운 리포트 살펴보기'),sales,checkout],")
    s = _swap(s, "DEMO_REVIEWS.push({product:'business'", (
        "SALES.wealth={opening:'내 돈은 언제 들어오고\\n어디로 새고 있을까요',empathy:'열심히 버는데\\n왜 돈이 모이지 않을까요',"
        "empathyBody:'월급은 그대로인데 나가는 돈만 늘고, 큰돈이 들어올 때는 언제인지 궁금할 때. 내 사주로 돈이 들어오는 길과 새는 곳을 정리해 드려요.',"
        "reveal:'내 사주로 계산한\\n나의 재물 흐름',locks:['타고난 재물 그릇의 크기','돈이 새기 쉬운 해와 달','큰돈이 들어오는 시기와 준비할 일'],"
        "chapters:['한눈에 보는 나의 재물운','돈을 버는 방식과 새는 곳','나이별·연도별 재물운','월별 재물운','재물운을 키우는 방법'],"
        "ending:'내 돈의 흐름을\\n미리 확인하세요'};\n"
        "DETAIL_BLOCKS.wealth=[['bowl','타고난 재물 그릇을\\n먼저 확인해요','내 사주에 돈이 얼마나, 어떤 모양으로 들어오는지 알려드려요.',''],"
        "['leak','돈이 새는 곳과\\n막는 방법','나도 몰랐던 소비 습관과 돈이 빠지기 쉬운 시기를 짚어요.',''],"
        "['years','큰돈이 오가는 해와\\n달마다 할 일','앞으로 5년과 12개월의 재물 흐름을 정리해요.','timeline']];\n"
        "SALES.career={opening:'나에게 맞는 일과\\n옮겨야 할 때',empathy:'지금 일이 맞는지\\n계속 고민되나요',"
        "empathyBody:'이직을 해야 할지, 버텨야 할지, 다른 일을 시작해도 될지 고민될 때. 내 사주로 맞는 일과 움직이기 좋은 시기를 정리해 드려요.',"
        "reveal:'내 사주로 계산한\\n나의 직업 흐름',locks:['나에게 맞는 일과 일하는 방식','이직하기 좋은 해와 피할 해','승진·면접·시험에 좋은 시기'],"
        "chapters:['한눈에 보는 나의 직업운','나에게 맞는 일과 환경','이직과 승진의 시기','10년마다 바뀌는 직업운','나의 다음 선택'],"
        "ending:'다음 선택을 하기 전에\\n먼저 확인하세요'};\n"
        "DETAIL_BLOCKS.career=[['fit','나에게 맞는 일을\\n먼저 찾아요','타고난 성향으로 잘 맞는 직업과 일하는 환경을 알려드려요.',''],"
        "['move','이직하기 좋은 해와\\n피할 해','움직이면 좋은 시기와 버티는 게 나은 시기를 짚어요.',''],"
        "['ten','10년마다 바뀌는\\n직업 흐름','지금 지나는 10년과 다음 10년의 직업운을 정리해요.','timeline']];\n"
        "DEMO_REVIEWS.push({product:'business'"))
    return s


def add_discounts(s: str) -> str:
    """사이트 추가 기능 2단계: 결제 화면의 첫 구매 묶음 할인·할인 코드·친구 초대·광고 메일 동의. 금액은 서버가 계산한다."""
    s = _swap(s, '<div class="field" hidden><label for="coupon">할인 쿠폰</label><p class="field-help">이메일을 입력한 뒤 쿠폰을 적용해주세요.</p>',
              '<div class="field"><label for="coupon">할인 코드 (선택)</label><p class="field-help">재구매·친구 초대로 받은 코드가 있으면 넣고 적용을 눌러주세요.</p>')
    s = _swap(s, 'placeholder="쿠폰 코드"', 'placeholder="예) UNM-ABC123"')
    s = _swap(s, '<h2 class="checkout-label">상품 금액 안내</h2><div id="checkout-price">${priceBox(p,d.discount||0)}</div>',
              '<h2 class="checkout-label">상품 금액 안내</h2><div id="checkout-price">${priceBox(p,0)}</div>')
    s = _swap(s, '<button type="button" data-consent="payment">자세히</button></div></fieldset>',
              '<button type="button" data-consent="payment">자세히</button></div><div><label class="check-line"><input type="checkbox" name="marketing">할인·이벤트 소식 이메일 받기 (선택)</label></div>'
              '<p class="mk-help">동의하시면 재구매 10% 할인 코드와 친구 초대 링크를 메일로 보내드려요. 메일 끝의 링크로 언제든 수신 거부할 수 있어요.</p></fieldset>')
    s = _swap(s, "form.elements.payment.checked=e.target.checked;update()}",
              "form.elements.payment.checked=e.target.checked;if(form.elements.marketing){form.elements.marketing.checked=e.target.checked;d.marketing=e.target.checked}update()}")
    s = _swap(s, "update();if(d.discount)document.querySelector('#coupon-message').textContent=money(d.discount)+' 체험 할인이 적용되어 있어요.'}",
              "update();bindDiscounts(p,d)}")
    # 예전 체험용 쿠폰(UNMYEONG5000) 대신 서버가 확인하는 코드만 쓴다. 친구 초대 코드와 묶음 상품을 주문에 함께 보낸다.
    s = _swap(s, " if(Number(draft.discount||0)>0)throw Error('COUPON_NOT_AVAILABLE');\n",
              " draft={...draft,ref:savedRef(),extras:EXTRA_DATA.bundle?(draft.extras||[]):[]};delete draft.discount;\n")
    s = _swap(s, "orderName:config.productNames?.[productId]??'운명서재 사주 결과',",
              "orderName:(config.productNames?.[productId]??'운명서재 사주 결과')+(draft.extras.length?` 외 ${draft.extras.length}건`:''),")
    s = _swap(s, "e.message==='COUPON_NOT_AVAILABLE'?'체험용 쿠폰은 실제 결제에 사용할 수 없어요.'",
              "e.message==='COUPON_INVALID'?'할인 코드를 쓸 수 없어요. 코드 칸을 비우고 다시 결제해주세요.'")
    return s


def add_reveal(s: str) -> str:
    """결제 전 이야기 화면(2026-10-28 사장님): 정보 입력 뒤 금월선녀가 내 사주·점수·12년 지도·리포트 1장을 보여 주고 결제로 잇는다."""
    page = (SITE / "tools" / "reveal_page.js").read_text(encoding="utf-8")
    s = _swap(s, "</head>", f"<style>{REVEAL_CSS}</style></head>")
    s = _swap(s, "function render(){", page + "function render(){")
    s = _swap(s, "if(s.type==='sales')return salesPage(p,i);", "if(s.type==='sales')return salesPage(p,i);if(s.type==='reveal')return revealPage(p,i);")
    return s


def extract_font(s: str) -> str:
    """HTML 안에 글자로 박힌 2.7MB 글꼴을 따로 떼어 첫 화면이 빨리 뜨게 한다(2026-10-27)."""
    m = re.search(r"url\('data:font/woff2;base64,([A-Za-z0-9+/=]+)'\)", s)
    if not m:
        return s
    out = PUBLIC / "assets/fonts/PretendardVariable.woff2"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(m.group(1)))
    s = s[:m.start()] + "url('assets/fonts/PretendardVariable.woff2')" + s[m.end():]
    return _swap(s, '<meta charset="UTF-8">', '<meta charset="UTF-8"><link rel="preload" href="assets/fonts/PretendardVariable.woff2" as="font" type="font/woff2" crossorigin>')


def fix_story_face(s: str) -> str:
    """눈·입 조각은 인물 사진이 다 뜬 뒤에만 보이게 한다(2026-10-27 사장님: 눈코입만 둥둥 뜸).

    SVG의 visibility="visible"은 숨긴 부모 안에서도 보이므로, 인물보다 먼저 받은 눈·입 그림이 따로 떠 있었다.
    """
    s = _swap(s, "loadImage(face.neural.atlas).then(ok=>{if(disposed)return;blinkReady=ok;eyeWindow.setAttribute('visibility',ok?'visible':'hidden')});",
              "const personShown=new Promise(r=>{showFace=r});"
              "Promise.all([loadImage(face.neural.atlas),personShown]).then(([ok])=>{if(disposed)return;blinkReady=ok;eyeWindow.setAttribute('visibility',ok?'visible':'hidden')});")
    s = _swap(s, "smileLoaded.then(ok=>{if(disposed)return;smileReady=ok;if(ok)paintExpression();smileWindow.setAttribute('visibility',ok?'visible':'hidden')});",
              "Promise.all([smileLoaded,personShown]).then(([ok])=>{if(disposed)return;smileReady=ok;if(ok)paintExpression();smileWindow.setAttribute('visibility',ok?'visible':'hidden')});")
    # 인물 사진을 받은 뒤 그림으로 풀어 놓기(decode)까지 기다려야 빈칸 없이 한 번에 나온다.
    s = _swap(s, "stage.classList.toggle('story-person-missing',!ok);portrait.classList.add('is-ready')});",
              "stage.classList.toggle('story-person-missing',!ok);portrait.classList.add('is-ready');if(ok)showFace()});")
    s = _swap(s, " const initial=STORY_MEDIA[stage.dataset.artKey],face=STORY_FACES[stage.dataset.product];",
              " let showFace=()=>{};const initial=STORY_MEDIA[stage.dataset.artKey],face=STORY_FACES[stage.dataset.product];")
    # 다 받은 사진도 화면에 그리기 전에 풀어 두어야 몸과 눈이 같이 나온다.
    s = _swap(s, "img.onload=()=>finish(true);",
              "img.onload=()=>{if(img.decode)img.decode().then(()=>finish(true),()=>finish(true));else finish(true)};")
    return s


def optimize_images(s: str) -> str:
    """큰 사진을 WebP로 줄여 이야기 화면이 늦게 뜨지 않게 한다(2026-10-27 사장님: 첫 장면 렉).

    인물 PNG가 장당 2.7MB라 휴대폰에서 눈·입 조각이 먼저 뜨고 몸이 늦게 떴다. 원본 파일은 그대로 둔다.
    """
    from PIL import Image
    saved = 0
    for path in sorted(set(re.findall(r"assets/[\w/.-]+\.(?:png|jpg)", s))):
        src = PUBLIC / path
        if not src.exists() or src.stat().st_size < 150_000:
            continue
        webp = path.rsplit(".", 1)[0] + ".webp"
        out = PUBLIC / webp
        if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
            Image.open(src).save(out, "WEBP", quality=85, method=6)
        saved += src.stat().st_size - out.stat().st_size
        s = s.replace(path, webp)
    print(f"사진 WebP 변환으로 {saved // 1024}KB 줄임")
    return s


def main() -> None:
    src = Path(sys.argv[1])
    b = json.loads((SITE / "business.json").read_text(encoding="utf-8"))
    s = src.read_text(encoding="utf-8")
    s = extract_assets(s)
    s = add_newyear(s)
    write_intake_module(s)
    s = patch_texts(s, b)
    s = add_taster(s)
    s = add_input_helpers(s)
    s = add_trust(s)
    s = fix_checkout_flow(s)
    s = add_extras(s)
    s = add_reveal(s)
    s = extract_font(s)
    s = fix_story_face(s)
    s = optimize_images(s)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "index.html").write_text(s, encoding="utf-8")
    print(f"public/index.html {len(s.encode()) // 1024}KB")


if __name__ == "__main__":
    main()
