// /api/* 요청을 나눠 처리한다. 저장소와 바깥 서비스는 밖에서 넣어 주므로 시험할 때 가짜로 바꿀 수 있다.
import { PRODUCTS } from './intake.mjs';
import {
  ApiError, assess, createOrder, loadOrder, publicView, confirmPayment, markFailed,
  workerStatus, deliverPdf, resend, sameSecret, STATUS_MESSAGES, reportFileName,
} from './orders.mjs';
import { ready } from './services.mjs';
import { quote, rebuyForJob, unsubToken } from './discounts.mjs';
import { makeStudio } from './studio.mjs';

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
});

async function readJson(req, limit = 65_536) {
  const text = await req.text();
  if (text.length > limit) throw new ApiError(413, 'TOO_LARGE');
  try { return text ? JSON.parse(text) : {}; } catch { throw new ApiError(400, 'BAD_JSON'); }
}

const bearer = req => (req.headers.get('authorization') || '').replace(/^Bearer\s+/i, '') || '';

export function makeApi({ store, services, env, studioStore = store }) {
  const studio = makeStudio({ store: studioStore, services, env });
  return async function handle(req) {
    const url = new URL(req.url);
    const parts = url.pathname.replace(/^\/api\/?/, '').split('/').filter(Boolean);
    const m = req.method;
    try {
      if (parts[0] === 'studio' || (parts[0] === 'internal' && parts[1] === 'studio')) return await studio(req, parts);
      if (m === 'GET' && parts.join('/') === 'payment-config') {
        return json({
          customerAnalysisReady: ready(env), clientKey: ready(env) ? env.TOSS_CLIENT_KEY : '',
          productNames: Object.fromEntries(PRODUCTS.map(p => [p.id, p.name])),
        });
      }
      // 결제 화면의 금액 안내. 주문을 만들 때와 같은 계산(quote)을 쓴다.
      if (m === 'POST' && parts.join('/') === 'quote') {
        const q = await quote(store, await readJson(req));
        if (!q) throw new ApiError(400, 'PRODUCT_REQUIRED');
        return json({ items: q.items, base: q.base, discount: q.discount, amount: q.amount, notes: q.notes });
      }
      // 광고 메일 끝의 수신 거부 링크.
      if (m === 'GET' && parts.join('/') === 'unsubscribe') {
        const h = String(url.searchParams.get('h') || ''), t = String(url.searchParams.get('t') || '');
        const ok = /^[a-f0-9]{64}$/.test(h) && env.WORKER_SECRET && sameSecret(t, unsubToken(h, env.WORKER_SECRET));
        if (ok) await store.set(`unsub/${h}`, { at: new Date().toISOString() });
        const msg = ok ? '수신 거부가 완료되었어요. 앞으로 할인·이벤트 메일을 보내지 않아요.' : '링크가 올바르지 않아요. 메일에 답장으로 수신 거부를 알려주시면 바로 처리해 드릴게요.';
        return new Response(`<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>운명서재 수신 거부</title><body style="font-family:sans-serif;background:#0e0d0b;color:#efe8da;padding:48px 20px;text-align:center;font-size:17px;line-height:1.6"><p>${msg}</p><p><a style="color:#d8bb78" href="/">운명서재로 가기</a></p></body>`,
          { status: ok ? 200 : 400, headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } });
      }
      if (m === 'POST' && parts.join('/') === 'intake/assess') {
        const { payload, ...decision } = assess(await readJson(req));
        return json(decision);
      }
      if (parts[0] === 'orders' && parts.length === 1 && m === 'POST') {
        if (!ready(env)) throw new ApiError(503, 'CHECKOUT_NOT_READY');
        const body = await readJson(req);
        // 토스 시험 키(test_)를 쓰는 동안 사장님 이메일이 아닌 주문은 시험 결제창까지만 연다(토스·카드사 심사용).
        // 시험 결제는 돈이 안 나가지만 결과 작성은 API 비용이 나가므로, 이런 주문은 결제가 끝나도 결과를 만들지 않는다.
        const testOnly = String(env.TOSS_CLIENT_KEY).startsWith('test_')
          && String(body.email || '').trim().toLowerCase() !== String(env.OWNER_EMAIL || '').trim().toLowerCase();
        return json(await createOrder(store, body, req.headers.get('idempotency-key'), new Date(), { testOnly }), 201);
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
          const rebuy = await rebuyForJob(store, order, env.SITE_URL).catch(() => null);
          return json({ orderId: order.id, productId: order.productId, status: order.status, paidAt: order.paidAt, payload: order.payload, disclosures: order.disclosures, rebuy });
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
