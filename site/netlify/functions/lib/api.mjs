// /api/* 요청을 나눠 처리한다. 저장소와 바깥 서비스는 밖에서 넣어 주므로 시험할 때 가짜로 바꿀 수 있다.
import { PRODUCTS } from './intake.mjs';
import {
  ApiError, assess, createOrder, loadOrder, publicView, confirmPayment, markFailed,
  workerStatus, deliverPdf, resend, sameSecret, STATUS_MESSAGES, reportFileName,
} from './orders.mjs';
import { ready } from './services.mjs';

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
});

async function readJson(req, limit = 65_536) {
  const text = await req.text();
  if (text.length > limit) throw new ApiError(413, 'TOO_LARGE');
  try { return text ? JSON.parse(text) : {}; } catch { throw new ApiError(400, 'BAD_JSON'); }
}

const bearer = req => (req.headers.get('authorization') || '').replace(/^Bearer\s+/i, '') || '';

export function makeApi({ store, services, env }) {
  return async function handle(req) {
    const url = new URL(req.url);
    const parts = url.pathname.replace(/^\/api\/?/, '').split('/').filter(Boolean);
    const m = req.method;
    try {
      if (m === 'GET' && parts.join('/') === 'payment-config') {
        return json({
          customerAnalysisReady: ready(env), clientKey: ready(env) ? env.TOSS_CLIENT_KEY : '',
          productNames: Object.fromEntries(PRODUCTS.map(p => [p.id, p.name])),
        });
      }
      if (m === 'POST' && parts.join('/') === 'intake/assess') {
        const { payload, ...decision } = assess(await readJson(req));
        return json(decision);
      }
      if (parts[0] === 'orders' && parts.length === 1 && m === 'POST') {
        if (!ready(env)) throw new ApiError(503, 'CHECKOUT_NOT_READY');
        const body = await readJson(req);
        // 토스 시험 키(test_)를 쓰는 동안에는 사장님 이메일 주문만 받는다. 시험 결제는 돈이 안 나가지만 API 비용은 나가므로.
        if (String(env.TOSS_CLIENT_KEY).startsWith('test_')
          && String(body.email || '').trim().toLowerCase() !== String(env.OWNER_EMAIL || '').trim().toLowerCase()) {
          throw new ApiError(403, 'TEST_MODE_OWNER_ONLY');
        }
        return json(await createOrder(store, body, req.headers.get('idempotency-key')), 201);
      }
      if (parts[0] === 'orders' && parts.length >= 2) {
        const action = parts[2] || '';
        // 결제 승인은 토스가 준 paymentKey·금액으로 확인하므로 접근 열쇠가 없어도 받는다
        // (카드 앱을 다녀오며 브라우저 저장값이 사라져도 결제가 승인되게).
        const order = await loadOrder(store, parts[1], action === 'confirm' && !bearer(req) ? undefined : bearer(req));
        const hasPdf = async () => Boolean(await store.getBytes(`pdf/${order.id}`));
        if (m === 'GET' && !action) return json(publicView(order, await hasPdf()));
        if (m === 'GET' && action === 'pdf') {
          const pdf = await store.getBytes(`pdf/${order.id}`);
          if (!pdf) throw new ApiError(404, 'PDF_NOT_AVAILABLE');
          return new Response(pdf, { headers: { 'Content-Type': 'application/pdf', 'Content-Disposition': `attachment; filename="unmyeong-report.pdf"; filename*=UTF-8''${encodeURIComponent(reportFileName(order))}`, 'Cache-Control': 'no-store' } });
        }
        if (m === 'POST' && action === 'confirm') {
          const updated = await confirmPayment(store, services, order, await readJson(req));
          if (!bearer(req)) return json({ orderId: updated.id, status: updated.status, message: STATUS_MESSAGES[updated.status] });
          return json(publicView(updated, await hasPdf()));
        }
        if (m === 'POST' && action === 'fail') {
          const body = await readJson(req);
          return json(publicView(await markFailed(store, order, body.code), false));
        }
        if (m === 'POST' && action === 'resend') {
          const updated = await resend(store, services, order, req.headers.get('idempotency-key'));
          return json(publicView(updated, true));
        }
      }
      if (parts[0] === 'internal' && parts[1] === 'orders' && parts[2]) {
        if (!sameSecret(req.headers.get('x-worker-secret') || '', env.WORKER_SECRET || '')) throw new ApiError(403, 'FORBIDDEN');
        const order = await loadOrder(store, parts[2]);
        const action = parts[3] || '';
        if (m === 'GET' && !action) {
          if (!order.payload) throw new ApiError(410, 'ERASED');
          return json({ orderId: order.id, productId: order.productId, status: order.status, paidAt: order.paidAt, payload: order.payload, disclosures: order.disclosures });
        }
        if (m === 'POST' && action === 'status') {
          const body = await readJson(req);
          return json(publicView(await workerStatus(store, services, order, body.status, body.note)));
        }
        if (m === 'POST' && action === 'result') {
          const pdf = new Uint8Array(await req.arrayBuffer());
          return json(publicView(await deliverPdf(store, services, order, pdf), true));
        }
      }
      throw new ApiError(404, 'NOT_FOUND');
    } catch (e) {
      if (e instanceof ApiError) return json({ code: e.code }, e.status);
      console.error('api error', e?.message);
      return json({ code: 'SERVER_ERROR' }, 500);
    }
  };
}

export function memoryStore() {
  const data = new Map();
  return {
    data,
    get: async k => (data.has(k) ? structuredClone(data.get(k)) : null),
    set: async (k, v) => { data.set(k, structuredClone(v)); },
    setBytes: async (k, b) => { data.set(k, Buffer.from(b)); },
    getBytes: async k => data.get(k) || null,
    delete: async k => { data.delete(k); },
    list: async prefix => [...data.keys()].filter(k => k.startsWith(prefix)),
  };
}
