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

  async function startWorker(orderId) {
    const r = await fetcher(`https://api.github.com/repos/${env.GITHUB_REPO || 'kimseungyong0528-svg/saju-engine'}/dispatches`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`, Accept: 'application/vnd.github+json', 'User-Agent': 'unmyeong-orders', 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: 'order', client_payload: { orderId } }),
    });
    if (r.status !== 204) throw Error(`dispatch ${r.status}`);
  }

  // 관리 사이트의 "만들기" 버튼: 깃허브에서 SNS 게시물 만들기 작업을 시작한다.
  async function startStudio(start) {
    const r = await fetcher(`https://api.github.com/repos/${env.GITHUB_REPO || 'kimseungyong0528-svg/saju-engine'}/dispatches`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`, Accept: 'application/vnd.github+json', 'User-Agent': 'unmyeong-studio', 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: 'studio', client_payload: { start } }),
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
  }

  async function sendEmail(order, pdf) {
    const name = order.payload?.self?.name || order.mailName || '고객';
    const product = productName(order.productId) || '사주 결과';
    const site = env.SITE_URL || 'https://unmyeong-saju.com';
    const text = [
      `${name}님, 운명서재입니다.`, '',
      `주문하신 ${product} 결과를 PDF 파일로 보내드려요. 이 메일에 붙어 있는 파일을 내려받아 보관해주세요.`, '',
      '개인정보 보호를 위해 출생 정보는 이 메일을 보내면서 바로 지웠어요. 결과 파일도 7일 뒤 서버에서 지워요. 이 PDF를 꼭 내려받아 보관해주세요.',
      ...(order.amount === 0 && order.parentId ? ['함께 주문하신 다른 리포트는 따로 메일로 보내드려요.', ''] : []),
      `리포트 끝의 '자세히 보기 (재구매 ${PERCENT}% 할인)' 링크를 누르면 다음 리포트를 ${PERCENT}% 할인받을 수 있어요. 30일 안에 한 번 쓸 수 있어요.`,
      '결과에 오류가 있거나 파일이 열리지 않으면 이 메일에 답장으로 알려주세요.', '',
      `운명서재 ${site}`,
    ].join('\n');
    const html = text.split('\n').map(l => l ? `<p style="margin:0 0 6px">${esc(l)}</p>` : '<br>').join('');
    await resendEmail({
      to: [order.email], subject: `[운명서재] ${name}님의 ${product} 결과가 도착했어요`, text, html,
      ...(env.OWNER_EMAIL ? { reply_to: env.OWNER_EMAIL } : {}),
      attachments: [{ filename: reportFileName(order), content: Buffer.from(pdf).toString('base64') }],
    }, `pdf-${order.id}-${order.resends || 0}`);
  }

  async function notifyOwner(order, note, kind = 'held') {
    if (!env.OWNER_EMAIL) return;
    const what = kind === 'stuck' ? '작업이 멈춘 주문이 있어요' : '발송 보류된 주문이 있어요';
    await resendEmail({
      to: [env.OWNER_EMAIL], subject: `[운명서재] ${what} (${productName(order.productId)})`,
      text: `주문번호 ${order.id}${order.parentId ? ` (묶음 주문, 결제는 주문 ${order.parentId})` : ''}\n상품 ${productName(order.productId)}\n금액 ${order.amount}원\n사유 ${note || '-'}\n\n작업 기록: https://github.com/kimseungyong0528-svg/saju-engine/actions\n환불: https://app.tosspayments.com\n작업 기록을 확인하고 다시 만들거나, 토스 관리자 화면에서 환불해주세요.`,
    });
  }

  return { tossConfirm, startWorker, startStudio, sendEmail, notifyOwner };
}

export function ready(env) {
  return Boolean(env.TOSS_CLIENT_KEY && env.TOSS_SECRET_KEY && env.GH_DISPATCH_TOKEN && env.WORKER_SECRET && env.RESEND_API_KEY);
}
