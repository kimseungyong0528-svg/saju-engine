// 주문 규칙: 접수 확인, 주문 만들기, 상태 바꾸기. 저장소(store)와 바깥 서비스(services)는 밖에서 넣어 준다.
import { createHash, createHmac, randomUUID, randomBytes, timingSafeEqual } from 'node:crypto';
import { INTAKE_POLICY_VERSION, PRODUCTS, intakePayload, evaluateIntake } from './intake.mjs';
import { quote, afterPaid, extraBody } from './discounts.mjs';

export const CALCULATION_VERSION = 'saju-engine-0.2';
export const COVERAGE_VERSION = '2026-10-12';
export const RETENTION_DAYS = 7;
export const MAX_RESENDS = 3;

export const STATUS_MESSAGES = {
  awaiting_payment: '결제 확인을 기다리고 있어요.',
  queued: '결제를 확인했어요. 결과를 준비하고 있어요.',
  processing: '사주 결과를 작성하고 검사하고 있어요.',
  retry: '처리가 잠시 지연되어 다시 진행하고 있어요.',
  held: '결과 준비 중 문제가 확인되어 발송을 보류했어요. 확인 후 다시 보내드리거나 환불해 드릴게요.',
  email_accepted: '결과 PDF를 이메일로 보냈어요.',
  test_paid: '시험 결제가 확인되었어요. 지금은 시험 운영 중이라 결과 PDF는 만들지 않아요.',
  refund_pending: '결제 취소를 처리하고 있어요.',
  refunded: '결제 취소가 확인되었어요.',
  payment_adjusted: '결제 금액이 변경되어 결과 발송이 중단되었어요.',
  payment_failed: '결제가 완료되지 않았어요.',
  payment_expired: '결제 대기 시간이 만료되었어요.',
  erased: '이 주문의 개인정보 보관 기간이 끝나 정보를 지웠어요.',
};

const WORKER_STATUSES = new Set(['processing', 'retry', 'held']);

export class ApiError extends Error {
  constructor(status, code, message = code) { super(message); this.status = status; this.code = code; }
}

export const sha256 = text => createHash('sha256').update(text).digest('hex');
export const productName = id => PRODUCTS.find(p => p.id === id)?.name;

// 결과 PDF 파일 이름: "홍길동님의 연애사주 - 금월선녀의 운명서재.pdf" (2026-10-12 사장님 요청)
export function reportFileName(order) {
  const product = String(productName(order.productId) || '사주 결과').replace(/^금월선녀의\s*/, '');
  const name = String(order.payload?.self?.name || order.mailName || '').replace(/[\\/:*?"<>|\u0000-\u001f]/g, '').trim();
  return `${name ? name + '님의 ' : ''}${product} - 금월선녀의 운명서재.pdf`;
}

export function sameSecret(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || !a || !b) return false;
  const x = Buffer.from(a), y = Buffer.from(b);
  return x.length === y.length && timingSafeEqual(x, y);
}

// 서버가 직접 확인한 분석 범위. 사이트의 evaluateIntake 가 이 값을 믿고 결제를 허락한다.
function serverAssessment(payload, fingerprint) {
  const local = evaluateIntake(payload);
  const disclosures = [];
  for (const u of local.uncertainties || []) {
    const who = u.person === 'partner' ? '상대방의' : '나의';
    if (u.kind === 'time') disclosures.push(`${who} 태어난 시간이 정확하지 않아 가능한 시간을 모두 비교하고, 가장 가능성이 높은 시간으로 풀이해요. 시간에 따라 달라질 수 있는 부분은 결과에 따로 적어 드려요.`);
    if (u.kind === 'place') disclosures.push(`${who} 태어난 지역을 정확히 모르면 대한민국 안의 가능한 지역을 비교해 풀이해요. 몇 분 차이로 시주가 바뀌는 경우에만 결과가 달라질 수 있어요.`);
  }
  return {
    inputFingerprint: fingerprint, policyVersion: INTAKE_POLICY_VERSION,
    calculationConflict: false, coreCoverage: 'complete', allPossibleVariantsEvaluated: true,
    disclosures, calculationVersion: CALCULATION_VERSION, coverageVersion: COVERAGE_VERSION,
  };
}

export function assess(body) {
  const payload = intakePayload(String(body?.productId || ''), body || {});
  const fingerprint = sha256(JSON.stringify(payload));
  const decision = evaluateIntake(payload, { assessment: serverAssessment(payload, fingerprint), inputFingerprint: fingerprint });
  return { ...decision, inputFingerprint: fingerprint, payload };
}

const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,}$/;

// 손님이 들어온 곳(짧은 주소 /d, ?from= 꼬리표). 채널 이름만 받고 이상한 값은 버린다.
export function sourceOf(body) {
  const f = String(body?.from || '').toLowerCase();
  return /^[a-z0-9-]{1,24}$/.test(f) ? f : '';
}

export async function createOrder(store, body, idempotencyKey, now = new Date(), { testOnly = false } = {}) {
  if (!idempotencyKey || !/^[\w-]{8,80}$/.test(idempotencyKey)) throw new ApiError(400, 'IDEMPOTENCY_KEY_REQUIRED');
  const seen = await store.get(`idem/${idempotencyKey}`);
  if (seen) {
    const order = await store.get(`orders/${seen.orderId}`);
    if (order && order.status === 'awaiting_payment') return { orderId: order.id, accessToken: seen.accessToken, amount: order.amount, status: order.status };
    throw new ApiError(409, 'ORDER_ALREADY_USED');
  }
  const email = String(body?.email || '').trim();
  if (!EMAIL.test(email) || email.length > 254) throw new ApiError(400, 'EMAIL_REQUIRED');
  const decision = assess(body);
  if (!decision.paymentAllowed) throw new ApiError(400, decision.code || 'INTAKE_NOT_ALLOWED');
  // 금액은 서버가 계산한다(묶음·할인 코드·친구 초대 중 하나만, 모두 10%). 화면이 보낸 금액·할인값은 쓰지 않는다.
  const price = await quote(store, { ...body, email }, now);
  if (price.notes.includes('COUPON_INVALID')) throw new ApiError(400, 'COUPON_INVALID');
  // 체크한 묶음 상품의 질문·상대방 정보가 비어 있으면 결제하지 않는다(예전에는 말없이 빠지고 토스 이름만 '외 N건'이었다).
  if (price.incomplete.length) throw new ApiError(400, 'BUNDLE_INCOMPLETE');
  // 함께 사는 상품은 같은 출생 정보로 결제가 끝난 뒤 따로 만든다(상품마다 PDF 한 권).
  const bundle = price.extras.map(pid => {
    const x = assess(extraBody(body, pid));
    if (!x.paymentAllowed) throw new ApiError(400, x.code || 'INTAKE_NOT_ALLOWED');
    return { productId: pid, payload: x.payload, disclosures: x.disclosures || [] };
  });
  const id = randomUUID(), accessToken = randomBytes(24).toString('base64url');
  const order = {
    id, productId: decision.payload.productId, amount: price.amount, base: price.base, email, status: 'awaiting_payment',
    ...(price.discount ? { discount: price.discount } : {}), ...(bundle.length ? { bundle } : {}),
    tokenHash: sha256(accessToken), payload: decision.payload, disclosures: decision.disclosures || [],
    createdAt: now.toISOString(), updatedAt: now.toISOString(), history: [{ status: 'awaiting_payment', at: now.toISOString() }],
    resends: 0, ...(testOnly ? { testOnly: true } : {}), ...(sourceOf(body) ? { source: sourceOf(body) } : {}),
  };
  await store.set(`orders/${id}`, order);
  await store.set(`idem/${idempotencyKey}`, { orderId: id, accessToken });
  return { orderId: id, accessToken, amount: order.amount, status: order.status };
}

export async function loadOrder(store, id, token) {
  if (!/^[a-f0-9-]{36}$/.test(id || '')) throw new ApiError(404, 'ORDER_NOT_FOUND');
  const order = await store.get(`orders/${id}`);
  if (!order) throw new ApiError(404, 'ORDER_NOT_FOUND');
  if (token !== undefined && !sameSecret(sha256(token || ''), order.tokenHash)) throw new ApiError(403, 'ORDER_SESSION_REQUIRED');
  return order;
}

export function publicView(order, hasPdf = false) {
  return {
    orderId: order.id, productId: order.productId, productName: productName(order.productId),
    amount: order.amount, status: order.status, message: STATUS_MESSAGES[order.status] || '',
    emailHint: order.email ? order.email.replace(/^(.).*(@.*)$/, '$1***$2') : '',
    createdAt: order.createdAt, updatedAt: order.updatedAt, pdfAvailable: hasPdf,
    canResend: order.status === 'email_accepted' && hasPdf && order.resends < MAX_RESENDS,
    fileName: reportFileName(order),
  };
}

export function setStatus(order, status, now = new Date(), note) {
  order.status = status;
  order.updatedAt = now.toISOString();
  order.history.push({ status, at: order.updatedAt, ...(note ? { note: String(note).slice(0, 200) } : {}) });
  return order;
}

// 토스 결제 승인. 금액은 반드시 서버에 저장된 금액과 같아야 한다.
export async function confirmPayment(store, services, order, { paymentKey, amount }, now = new Date()) {
  if (order.status !== 'awaiting_payment') return order;
  if (typeof paymentKey !== 'string' || !paymentKey || paymentKey.length > 200) throw new ApiError(400, 'PAYMENT_KEY_REQUIRED');
  if (Number(amount) !== order.amount) {
    setStatus(order, 'payment_adjusted', now, `amount ${amount}`);
    await store.set(`orders/${order.id}`, order);
    throw new ApiError(400, 'AMOUNT_MISMATCH');
  }
  const result = await services.tossConfirm({ paymentKey, orderId: order.id, amount: order.amount });
  if (!result.ok) {
    setStatus(order, 'payment_failed', now, result.code);
    await store.set(`orders/${order.id}`, order);
    throw new ApiError(402, result.code || 'PAYMENT_FAILED');
  }
  order.paymentKey = paymentKey;
  order.paidAt = now.toISOString();
  if (order.testOnly) {
    // 시험 결제(심사용): 결과를 만들지 않고 출생 정보·질문은 바로 지운다.
    setStatus(order, 'test_paid', now);
    delete order.payload; delete order.disclosures; delete order.bundle;
    await store.set(`orders/${order.id}`, order);
    return order;
  }
  setStatus(order, 'queued', now);
  const bundle = order.bundle || [];
  delete order.bundle;
  order.children = [];
  const children = bundle.map(b => {
    const child = {
      id: randomUUID(), productId: b.productId, amount: 0, parentId: order.id, email: order.email, status: 'queued',
      tokenHash: order.tokenHash, payload: b.payload, disclosures: b.disclosures || [],
      createdAt: now.toISOString(), updatedAt: now.toISOString(), history: [{ status: 'queued', at: now.toISOString() }], resends: 0,
    };
    order.children.push(child.id);
    return child;
  });
  await store.set(`orders/${order.id}`, order);
  for (const c of children) await store.set(`orders/${c.id}`, c);
  await afterPaid(store, order, now).catch(e => console.error('afterPaid', e?.message));
  for (const o of [order, ...children]) {
    try { await services.startWorker(o.id); }
    catch (e) { setStatus(o, 'retry', now, 'worker dispatch failed'); await store.set(`orders/${o.id}`, o); }
  }
  return order;
}

export async function markFailed(store, order, code, now = new Date()) {
  if (order.status !== 'awaiting_payment') return order;
  setStatus(order, 'payment_failed', now, String(code || '').slice(0, 60));
  await store.set(`orders/${order.id}`, order);
  return order;
}

// 결과 작성 작업(깃허브)이 보내는 상태.
export async function workerStatus(store, services, order, status, note, now = new Date()) {
  if (!WORKER_STATUSES.has(status)) throw new ApiError(400, 'BAD_STATUS');
  if (!['queued', 'processing', 'retry', 'held'].includes(order.status)) return order;
  setStatus(order, status, now, note);
  await store.set(`orders/${order.id}`, order);
  if (status === 'held' && services.notifyOwner) await services.notifyOwner(order, note).catch(() => {});
  return order;
}

// 결제 취소 반영(P-VC-3, 11-05): 토스 관리자 화면에서 환불해도 주문은 그대로라 리포트가 만들어져 메일로 나갔다.
// 토스에 결제 상태를 직접 물어 전액 취소(CANCELED)면 그 결제의 주문(묶음 포함)을 refunded로 바꾸고
// 출생 정보·질문을 지운다. 토스 조회가 실패하면 아무것도 바꾸지 않는다(정상 주문 발송을 막지 않음).
const TOSS_CANCELED = new Set(['CANCELED']); // 부분 취소(묶음 중 한 권 환불 등)는 다른 책까지 멈추지 않도록 여기서 다루지 않는다
const REFUNDABLE = new Set(['queued', 'processing', 'retry', 'held', 'email_accepted']);

export async function syncRefund(store, services, order, now = new Date()) {
  const root = order.parentId ? await store.get(`orders/${order.parentId}`) : order;
  if (!root) return false;
  if (root.status !== 'refunded') {
    if (!root.paymentKey || !services.tossPayment) return false;
    let p;
    try { p = await services.tossPayment(root.paymentKey); } catch (e) { console.error('toss lookup', e?.message); return false; }
    if (!p || p.orderId !== root.id || !TOSS_CANCELED.has(p.status)) return false;
    root.refundStatus = p.status;
  }
  const kids = await Promise.all((root.children || []).map(id => store.get(`orders/${id}`)));
  // 환불은 사장님이 토스에서 직접 하므로 따로 알리지 않는다. 스튜디오는 refunded를 '취소'로 센다.
  for (const o of [root, ...kids.filter(Boolean)]) {
    if (!REFUNDABLE.has(o.status)) continue;
    setStatus(o, 'refunded', now, `toss ${root.refundStatus || 'CANCELED'}`);
    delete o.payload; delete o.disclosures;
    await store.set(`orders/${o.id}`, o);
  }
  return true;
}

export async function deliverPdf(store, services, order, pdf, now = new Date()) {
  if (!['queued', 'processing', 'retry', 'held'].includes(order.status)) throw new ApiError(409, 'ORDER_NOT_PROCESSING');
  if (!pdf?.byteLength || pdf.byteLength > 5_500_000) throw new ApiError(400, 'PDF_REQUIRED');
  // 보내기 직전에 한 번 더: 그사이 환불된 주문에는 메일을 보내지 않는다(P-VC-3)
  if (await syncRefund(store, services, order, now)) throw new ApiError(409, 'ORDER_REFUNDED');
  await store.setBytes(`pdf/${order.id}`, pdf);
  await rememberMail(store, order, await services.sendEmail(order, pdf));
  order.emailedAt = now.toISOString();
  setStatus(order, 'email_accepted', now);
  // 메일이 나가면 출생 정보·질문은 바로 지운다. PDF와 받는 분 이름은 다시 보내기를 위해 7일만 둔다.
  order.mailName = order.payload?.self?.name || null;
  delete order.payload; delete order.disclosures;
  await store.set(`orders/${order.id}`, order);
  return order;
}

export async function resend(store, services, order, idempotencyKey, now = new Date()) {
  if (order.status !== 'email_accepted') throw new ApiError(409, 'RESEND_NOT_AVAILABLE');
  if (idempotencyKey && order.lastResendKey === idempotencyKey) return order;
  if (order.resends >= MAX_RESENDS) throw new ApiError(429, 'RESEND_LIMIT');
  const pdf = await store.getBytes(`pdf/${order.id}`);
  if (!pdf) throw new ApiError(410, 'PDF_NOT_AVAILABLE');
  // 메일 서비스는 같은 요청 키를 24시간 동안 중복으로 보고 다시 보내지 않으므로 다시 보내기마다 새 번호를 쓴다.
  await rememberMail(store, order, await services.sendEmail({ ...order, resends: order.resends + 1 }, pdf));
  order.resends += 1;
  order.lastResendKey = idempotencyKey || null;
  order.updatedAt = now.toISOString();
  await store.set(`orders/${order.id}`, order);
  return order;
}

// 메일 도착 확인(P-IT-2, 11-05): 보낸 메일 번호를 주문에 붙여 두고, Resend 알림(webhook)이 오면 '도착함/튕김'을 남긴다.
// 지금까지는 '발송 요청됨'까지만 알았다. 메일 주소가 틀린 손님은 책을 못 받고도 아무도 몰랐다.
async function rememberMail(store, order, mailId) {
  if (!mailId || typeof mailId !== 'string') return;
  order.mailIds = [...(order.mailIds || []), mailId].slice(-5);
  await store.set(`mail/${mailId}`, { orderId: order.id });
}

const MAIL_EVENTS = { 'email.delivered': 'delivered', 'email.bounced': 'bounced', 'email.complained': 'complained', 'email.delivery_delayed': 'delayed' };

export async function mailEvent(store, services, event, now = new Date()) {
  const status = MAIL_EVENTS[event?.type];
  const mailId = event?.data?.email_id;
  if (!status || !mailId) return null;
  const link = await store.get(`mail/${mailId}`);
  if (!link?.orderId) return null;
  const order = await store.get(`orders/${link.orderId}`);
  if (!order) return null;
  // 나중에 온 '늦어짐'이 이미 받은 '도착함'을 덮지 않는다
  if (status === 'delayed' && order.mailStatus === 'delivered') return order;
  order.mailStatus = status;
  order.mailStatusAt = now.toISOString();
  await store.set(`orders/${order.id}`, order);
  if (status === 'bounced' && services.notifyOwner) {
    await services.notifyOwner(order, '메일 주소가 틀렸거나 받는 쪽에서 거절했어요. 손님께 다른 연락처로 알리거나 주소를 고쳐 다시 보내 주세요.', 'bounced').catch(() => {});
  }
  return order;
}

// Resend 알림 서명 확인(Svix 방식): 'whsec_' 뒤 base64 비밀값으로 `id.시각.본문`을 HMAC-SHA256 한 값이 svix-signature 안에 있어야 한다. 5분 넘은 알림은 받지 않는다.
export function verifyMailWebhook(secret, headers, body, now = Date.now()) {
  const id = headers.get('svix-id'), ts = headers.get('svix-timestamp'), sigs = headers.get('svix-signature') || '';
  if (!secret || !id || !ts || !/^\d+$/.test(ts) || Math.abs(now / 1000 - Number(ts)) > 300) return false;
  const key = Buffer.from(String(secret).replace(/^whsec_/, ''), 'base64');
  const want = createHmac('sha256', key).update(`${id}.${ts}.${body}`).digest('base64');
  return sigs.split(' ').some(s => { const v = s.split(',')[1] || ''; return v.length === want.length && timingSafeEqual(Buffer.from(v), Buffer.from(want)); });
}

// 멈춘 주문 알림: 결제는 됐는데 1시간이 넘도록 결과 작업이 끝나지 않은 주문(작업 서버가 꺼졌을 때 등)을 사장님 메일로 한 번 알린다.
const RUNNING = new Set(['queued', 'processing', 'retry']);

// 한 시간마다(cleanup): 결제 뒤 1시간 넘게 끝나지 않았거나 발송 보류된 주문은 결과 작업을 자동으로 한 번 다시 시작하고,
// 그래도 1시간 넘게 안 끝나면 사장님께 한 번 알린다. (11-04 재물운 주문이 5시간 50분 방치된 일, P-22)
const AUTO_RETRY = new Set(['queued', 'processing', 'retry', 'held']);
export async function flagStuck(store, services, now = new Date()) {
  let flagged = 0;
  for (const key of await store.list('orders/')) {
    const order = await store.get(key);
    if (!order || !AUTO_RETRY.has(order.status)) continue;
    if ((now - new Date(order.updatedAt)) / 3_600_000 < 1) continue;
    if (!order.autoRetriedAt && order.payload) {
      order.autoRetriedAt = now.toISOString();
      const from = order.status;
      try {
        await services.startWorker(order.id);
        setStatus(order, 'queued', now, `auto retry from ${from}`);
      } catch {
        setStatus(order, 'retry', now, 'auto retry dispatch failed');
      }
      await store.set(key, order);
      flagged += 1;
      continue;
    }
    if (!RUNNING.has(order.status) || order.stuckNotifiedAt) continue;
    await services.notifyOwner?.(order, `결과 작업이 1시간 넘게 끝나지 않았어요 (상태 ${order.status}, 자동 재실행 ${order.autoRetriedAt ? '했음' : '못 함'})`, 'stuck').catch(() => {});
    order.stuckNotifiedAt = now.toISOString();
    await store.set(key, order);
    flagged += 1;
  }
  return flagged;
}

// 개인정보 지우기: 끝난 주문은 7일 뒤 남은 출생 정보·질문·PDF를 지운다(발송된 주문은 출생 정보를 발송 때 이미 지움). 결제 안 된 주문은 1일 뒤 만료.
const DONE = new Set(['email_accepted', 'test_paid', 'held', 'refunded', 'payment_failed', 'payment_expired', 'payment_adjusted']);

export async function eraseOld(store, now = new Date()) {
  let erased = 0;
  for (const key of await store.list('orders/')) {
    const order = await store.get(key);
    if (!order || order.status === 'erased') continue;
    // 다시 보내기로 updatedAt이 바뀌어도 PDF 보관 기간이 늘지 않게 발송 시각을 기준으로 한다.
    const age = (now - new Date(order.emailedAt || order.updatedAt)) / 86_400_000;
    if (order.status === 'awaiting_payment' && age > 1) {
      setStatus(order, 'payment_expired', now);
    } else if (DONE.has(order.status) && age > RETENTION_DAYS) {
      setStatus(order, 'erased', now);
      delete order.payload; delete order.disclosures; delete order.mailName; delete order.bundle;
      for (const id of order.mailIds || []) await store.delete(`mail/${id}`);
      await store.delete(`pdf/${order.id}`);
      erased += 1;
    } else continue;
    await store.set(key, order);
  }
  return erased;
}
