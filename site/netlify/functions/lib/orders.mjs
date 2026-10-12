// 주문 규칙: 접수 확인, 주문 만들기, 상태 바꾸기. 저장소(store)와 바깥 서비스(services)는 밖에서 넣어 준다.
import { createHash, randomUUID, randomBytes, timingSafeEqual } from 'node:crypto';
import { INTAKE_POLICY_VERSION, PRODUCTS, intakePayload, evaluateIntake } from './intake.mjs';

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

export async function createOrder(store, body, idempotencyKey, now = new Date()) {
  if (!idempotencyKey || !/^[\w-]{8,80}$/.test(idempotencyKey)) throw new ApiError(400, 'IDEMPOTENCY_KEY_REQUIRED');
  const seen = await store.get(`idem/${idempotencyKey}`);
  if (seen) {
    const order = await store.get(`orders/${seen.orderId}`);
    if (order && order.status === 'awaiting_payment') return { orderId: order.id, accessToken: seen.accessToken, amount: order.amount, status: order.status };
    throw new ApiError(409, 'ORDER_ALREADY_USED');
  }
  if (Number(body?.discount || 0) > 0) throw new ApiError(400, 'COUPON_NOT_AVAILABLE');
  const email = String(body?.email || '').trim();
  if (!EMAIL.test(email) || email.length > 254) throw new ApiError(400, 'EMAIL_REQUIRED');
  const decision = assess(body);
  if (!decision.paymentAllowed) throw new ApiError(400, decision.code || 'INTAKE_NOT_ALLOWED');
  const product = PRODUCTS.find(p => p.id === decision.payload.productId);
  const id = randomUUID(), accessToken = randomBytes(24).toString('base64url');
  const order = {
    id, productId: product.id, amount: product.price, email, status: 'awaiting_payment',
    tokenHash: sha256(accessToken), payload: decision.payload, disclosures: decision.disclosures || [],
    createdAt: now.toISOString(), updatedAt: now.toISOString(), history: [{ status: 'awaiting_payment', at: now.toISOString() }],
    resends: 0,
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
  setStatus(order, 'queued', now);
  await store.set(`orders/${order.id}`, order);
  try { await services.startWorker(order.id); }
  catch (e) { setStatus(order, 'retry', now, 'worker dispatch failed'); await store.set(`orders/${order.id}`, order); }
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

export async function deliverPdf(store, services, order, pdf, now = new Date()) {
  if (!['queued', 'processing', 'retry', 'held'].includes(order.status)) throw new ApiError(409, 'ORDER_NOT_PROCESSING');
  if (!pdf?.byteLength || pdf.byteLength > 5_500_000) throw new ApiError(400, 'PDF_REQUIRED');
  await store.setBytes(`pdf/${order.id}`, pdf);
  await services.sendEmail(order, pdf);
  order.emailedAt = now.toISOString();
  setStatus(order, 'email_accepted', now);
  // 메일이 나가면 출생 정보·질문은 바로 지운다. PDF는 다시 보내기를 위해 7일만 둔다.
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
  await services.sendEmail(order, pdf);
  order.resends += 1;
  order.lastResendKey = idempotencyKey || null;
  order.updatedAt = now.toISOString();
  await store.set(`orders/${order.id}`, order);
  return order;
}

// 개인정보 지우기: 끝난 주문은 7일 뒤 남은 출생 정보·질문·PDF를 지운다(발송된 주문은 출생 정보를 발송 때 이미 지움). 결제 안 된 주문은 1일 뒤 만료.
const DONE = new Set(['email_accepted', 'held', 'refunded', 'payment_failed', 'payment_expired', 'payment_adjusted']);

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
      delete order.payload; delete order.disclosures;
      await store.delete(`pdf/${order.id}`);
      erased += 1;
    } else continue;
    await store.set(key, order);
  }
  return erased;
}
