// 바깥 서비스: 토스페이먼츠(결제 승인), 깃허브(결과 작성·SNS 게시물 작업 시작), Resend(이메일).
import { productName, reportFileName } from './orders.mjs';
import { PERCENT } from './discounts.mjs';

const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export function realServices(env, fetcher = fetch) {
  const toss = path => `https://api.tosspayments.com/v1/payments${path}`;
  const tossAuth = 'Basic ' + Buffer.from(`${env.TOSS_SECRET_KEY}:`).toString('base64');

  async function tossConfirm({ paymentKey, orderId, amount }) {
    const r = await fetcher(toss('/confirm'), {
      method: 'POST', headers: { Authorization: tossAuth, 'Content-Type': 'application/json', 'Idempotency-Key': `confirm-${orderId}` },
      body: JSON.stringify({ paymentKey, orderId, amount }),
    });
    const body = await r.json().catch(() => ({}));
    if (r.ok && body.status === 'DONE' && body.orderId === orderId && body.totalAmount === amount) return { ok: true };
    if (body.code === 'ALREADY_PROCESSED_PAYMENT') {
      const g = await fetcher(toss(`/${encodeURIComponent(paymentKey)}`), { headers: { Authorization: tossAuth } });
      const p = await g.json().catch(() => ({}));
      if (g.ok && p.status === 'DONE' && p.orderId === orderId && p.totalAmount === amount) return { ok: true };
    }
    return { ok: false, code: body.code || 'PAYMENT_FAILED' };
  }

  // 결제 한 건의 지금 상태(DONE·CANCELED·PARTIAL_CANCELED …). 환불 반영(P-VC-3)에 쓴다.
  async function tossPayment(paymentKey) {
    const r = await fetcher(toss(`/${encodeURIComponent(paymentKey)}`), { headers: { Authorization: tossAuth } });
    if (!r.ok) throw Error(`toss ${r.status}`);
    const p = await r.json();
    return { status: p.status, orderId: p.orderId };
  }

  async function startWorker(orderId) {
    const r = await fetcher(`https://api.github.com/repos/${env.GITHUB_REPO || 'kimseungyong0528-svg/saju-engine'}/dispatches`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`, Accept: 'application/vnd.github+json', 'User-Agent': 'unmyeong-orders', 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: 'order', client_payload: { orderId } }),
    });
    if (r.status !== 204) throw Error(`dispatch ${r.status}`);
  }

  // 관리 사이트의 "만들기" 버튼: 깃허브에서 SNS 게시물 만들기 작업을 시작한다.
  async function startStudio(start, days = 7) {
    const r = await fetcher(`https://api.github.com/repos/${env.GITHUB_REPO || 'kimseungyong0528-svg/saju-engine'}/dispatches`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`, Accept: 'application/vnd.github+json', 'User-Agent': 'unmyeong-studio', 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: 'studio', client_payload: { start, days } }),
    });
    if (r.status !== 204) throw Error(`dispatch ${r.status}`);
  }

  async function resendEmail(message, key) {
    const r = await fetcher('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, 'Content-Type': 'application/json', ...(key ? { 'Idempotency-Key': key } : {}) },
      body: JSON.stringify({ from: env.MAIL_FROM || '운명서재 <report@unmyeong-saju.com>', ...message }),
    });
    if (!r.ok) throw Error(`email ${r.status}`);
    // Resend가 돌려주는 메일 번호. 나중에 '도착함/튕김' 알림(webhook)을 이 주문에 붙일 때 쓴다(P-IT-2).
    return (await r.json().catch(() => ({})))?.id || null;
  }

  async function sendEmail(order, pdf) {
    const name = order.payload?.self?.name || order.mailName || '고객';
    const product = productName(order.productId) || '사주 결과';
    const site = env.SITE_URL || 'https://unmyeong-saju.com';
    const text = [
      `${name}님, 운명서재입니다.`, '',
      `주문하신 ${product} 결과를 PDF 파일로 보내드려요. 이 메일에 붙어 있는 파일을 내려받아 보관해주세요.`, '',
      '개인정보 보호를 위해 출생 정보는 이 메일을 보내면서 바로 지웠어요. 결과 파일도 7일 뒤 서버에서 지워요. 이 PDF를 꼭 내려받아 보관해주세요.',
      '7일 안에는 결제한 기기의 주문 화면에서 다시 내려받을 수 있고, 이 메일에 답장하시면 다시 보내 드려요.',
      ...(order.amount === 0 && order.parentId ? ['함께 주문하신 다른 리포트는 따로 메일로 보내드려요.', ''] : []),
      `리포트 끝의 '자세히 보기 (재구매 ${PERCENT}% 할인)' 링크를 누르면 다음 리포트를 ${PERCENT}% 할인받을 수 있어요.`,
      '리포트를 이미 보내 드렸기 때문에, 이제 단순 변심 환불은 안 돼요(디지털 콘텐츠).',
      '결과에 오류가 있거나 파일이 열리지 않으면 이 메일에 답장으로 알려주세요. 확인한 뒤 다시 보내 드리거나 환불해 드려요.', '',
      `운명서재 ${site}`,
    ].join('\n');
    const html = text.split('\n').map(l => l ? `<p style="margin:0 0 6px">${esc(l)}</p>` : '<br>').join('');
    return await resendEmail({
      to: [order.email], subject: `[운명서재] ${name}님의 ${product} 결과가 도착했어요`, text, html,
      ...(env.OWNER_EMAIL ? { reply_to: env.OWNER_EMAIL } : {}),
      attachments: [{ filename: reportFileName(order), content: Buffer.from(pdf).toString('base64') }],
    }, `pdf-${order.id}-${order.resends || 0}`);
  }

  async function notifyOwner(order, note, kind = 'held') {
    if (!env.OWNER_EMAIL) return;
    const what = kind === 'sent_refund' ? '이미 리포트를 보낸 주문이 환불됐어요' : kind === 'stuck' ? '작업이 멈춘 주문이 있어요' : kind === 'bounced' ? '리포트 메일이 손님에게 닿지 않았어요' : '발송 보류된 주문이 있어요';
    await resendEmail({
      to: [env.OWNER_EMAIL], subject: `[운명서재] ${what} (${productName(order.productId)})`,
      text: `주문번호 ${order.id}${order.parentId ? ` (묶음 주문, 결제는 주문 ${order.parentId})` : ''}\n상품 ${productName(order.productId)}\n금액 ${order.amount}원\n사유 ${note || '-'}${kind === 'sent_refund' ? '\n\n토스 관리자 화면: https://app.tosspayments.com' : '\n\n작업 기록: https://github.com/kimseungyong0528-svg/saju-engine/actions\n환불: https://app.tosspayments.com\n작업 기록을 확인하고 다시 만들거나, 토스 관리자 화면에서 환불해주세요.'}`,
    });
  }

  // 무료 맛보기 결과 메일(leads.mjs가 내용을 만든다). 답장은 사장님 메일로.
  const sendMail = (message, key) => resendEmail({ ...message, ...(env.OWNER_EMAIL ? { reply_to: env.OWNER_EMAIL } : {}) }, key);

  return { tossConfirm, tossPayment, startWorker, startStudio, sendEmail, notifyOwner, sendMail };
}

// 토스 키 확인. 이 사이트는 결제창(payment)을 쓰므로 'API 개별 연동 키'(ck/sk)만 맞는다.
// 결제위젯 키(gck/gsk)를 넣었거나, 클라이언트·시크릿 키가 하나는 시험(test_)·하나는 정식(live_)이면
// 결제가 토스에서 실패하므로 아예 결제를 열지 않고 이유를 알려 준다.
export function tossKeyMode(env) {
  const c = String(env.TOSS_CLIENT_KEY || '').trim(), s = String(env.TOSS_SECRET_KEY || '').trim();
  if (!c || !s) return { mode: '', problem: 'TOSS_KEY_MISSING' };
  if (/^(live|test)_g(c|s)k/.test(c) || /^(live|test)_g(c|s)k/.test(s)) return { mode: '', problem: 'TOSS_WIDGET_KEY' };
  const cm = (c.match(/^(live|test)_ck/) || [])[1], sm = (s.match(/^(live|test)_sk/) || [])[1];
  if (!cm || !sm) return { mode: '', problem: 'TOSS_KEY_FORMAT' };
  if (cm !== sm) return { mode: '', problem: 'TOSS_KEY_MIXED' };
  return { mode: cm, problem: '' };
}

export function ready(env) {
  return Boolean(tossKeyMode(env).mode && env.GH_DISPATCH_TOKEN && env.WORKER_SECRET && env.RESEND_API_KEY);
}
