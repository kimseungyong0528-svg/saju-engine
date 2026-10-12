# 주문 서버 (사이트 → 결제 → PDF → 이메일)

```
손님 → 사이트(넷리파이) → 토스 결제 → /order-status.html 이 결제 승인 요청
     → 넷리파이 함수 /api/*  : 접수 확인, 주문 저장(Netlify Blobs), 토스 승인, 이메일(Resend)
     → 깃허브 Actions "주문 처리" : python -m saju.order 주문번호 → PDF → 주문 서버로 보냄
     → 주문 서버가 손님에게 PDF 첨부 이메일 발송
```

- 사이트: `site/public` (33번 파일을 `site/tools/build_site.py` 로 변환. 사진은 `public/assets` 로 분리)
- 주문 서버: `site/netlify/functions` (입력 검사는 사이트 코드를 그대로 복사한 `lib/intake.mjs`)
- PDF 작업: `saju/order`, `.github/workflows/order.yml`
- 개인정보: 메일 발송 즉시 출생 정보·질문 삭제, PDF는 발송 7일 뒤 삭제(매일 `cleanup` 함수). 보류된 주문은 다시 만들 수 있게 7일 동안 남김. 거래 기록은 남김.
- 사주 계산과 다른 내용(없는 신살·개수·점수·연도)이 글 검사에 남으면 보내지 않고 `held`(사장님께 메일).

## 넣어야 하는 값

넷리파이(Site configuration → Environment variables)

| 이름 | 값 |
|---|---|
| TOSS_CLIENT_KEY | 토스 API 개별 연동 키의 클라이언트 키 |
| TOSS_SECRET_KEY | 토스 API 개별 연동 키의 시크릿 키 |
| GH_DISPATCH_TOKEN | 깃허브 토큰(이 저장소 Contents 읽기·쓰기) |
| WORKER_SECRET | 아무도 모르는 긴 글자(깃허브에도 같은 값) |
| RESEND_API_KEY | Resend API 키 |
| MAIL_FROM | `운명서재 <report@unmyeong-saju.com>` (선택) |
| OWNER_EMAIL | 보류 알림과 답장을 받을 사장님 메일 |

깃허브(Settings → Secrets and variables → Actions): `WORKER_SECRET`, `ANTHROPIC_API_KEY`

키가 하나라도 빠지면 사이트의 결제 버튼이 나타나지 않는다(`/api/payment-config`).

## 시험

```
cd site && npm install && npm test          # 주문 서버
python -m pytest tests/test_order.py        # 주문 → PDF
node site/tools/local-test-server.mjs 8787  # 내 컴퓨터에서 결제~이메일 전체(가짜 결제, 초안 글)
```
