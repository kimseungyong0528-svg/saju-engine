// 고객센터 질문(P-17): 미도착·오입력 안내가 고객센터에 있고, 적힌 금액·결제 수단이 실제 값과 같다(제1조항).
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { PRODUCTS } from '../netlify/functions/lib/intake.mjs';
import { discounted } from '../netlify/functions/lib/discounts.mjs';

const html = readFileSync(new URL('../public/index.html', import.meta.url), 'utf8');
const won = n => n.toLocaleString('ko-KR') + '원';

test('고객센터에 메일 미도착·이메일 오입력·정보 오입력 안내가 있다 (P-17)', () => {
  const sup = html.slice(html.indexOf('function supportPage'), html.indexOf('function supportPage') + 600);
  assert.ok(sup.includes('SUPPORT_FAQ.map'), '고객센터는 SUPPORT_FAQ를 그린다');
  const list = html.slice(html.indexOf('const SUPPORT_FAQ'), html.indexOf('\n', html.indexOf('const SUPPORT_FAQ')));
  for (const q of ['메일이 안 와요.', '이메일 주소를 잘못 적었어요.', '생년월일·성별을 잘못 넣었어요.']) assert.ok(list.includes(q), q);
});

test('결제 전 이야기 화면의 질문은 그대로 FAQ만 쓴다', () => {
  const rv = html.slice(html.indexOf('function rvScene4'), html.indexOf('const RV_CTA'));
  // 상품 화면은 FAQ만 쓰고 고객센터 질문(SUPPORT_FAQ)은 쓰지 않는다. AI 질문은 FAQ에서 아예 뺐다(사장님 2026-11-06: AI 문구 전부 빼기).
  assert.ok(/\bFAQ\]?\.map\(|\.\.\.FAQ\]|\.\.\.FAQ\.filter\(/.test(rv) && !rv.includes('SUPPORT_FAQ'));
});

test('재구매 금액 답은 실제 할인 계산과 같다', () => {
  const list = html.slice(html.indexOf('const SUPPORT_FAQ'), html.indexOf('\n', html.indexOf('const SUPPORT_FAQ')));
  const life = PRODUCTS.lifetime?.price ?? Object.values(PRODUCTS).find(p => p.id === 'lifetime')?.price;
  assert.equal(life, 49800);
  assert.ok(list.includes(`29,800원 리포트는 ${won(discounted(29800))}`));
  assert.ok(list.includes(`평생사주는 ${won(discounted(life))}`));
});

test('결제 수단 답은 결제 화면 수단과 같다', () => {
  const pm = html.slice(html.indexOf('const PAY_METHODS'), html.indexOf('\n', html.indexOf('const PAY_METHODS')));
  const labels = [...pm.matchAll(/label:'([^']+)'/g)].map(m => m[1]);
  assert.ok(html.includes(labels.join(', ') + '로 결제할 수 있어요'), labels.join(', '));
});
