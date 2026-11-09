// 상대 생일 없이 보는 재회사주(2026-11-05): 재회사주만 생일 없이 접수되고, 깊은 궁합은 여전히 생일이 있어야 한다.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { assess } from '../netlify/functions/lib/orders.mjs';

const self = { name: '김테스트', sex: 'female', birth: '1995-03-12', calendar: 'solar', timeAccuracy: 'exact', time: '06:30',
  birthPlace: { status: 'unknown', countryCode: 'KR', countryName: '대한민국' } };
const html = fs.readFileSync(new URL('../public/index.html', import.meta.url), 'utf8');

test('재회사주: 상대 생일을 몰라도 접수된다', () => {
  const d = assess({ productId: 'reunion', self, partner: { name: '그 사람', birthUnknown: true }, answers: { breakup: '3개월 이내예요' } });
  assert.equal(d.paymentAllowed, true, d.code);
  assert.equal(d.payload.partner.birthUnknown, true);
});
test('재회사주: 표시 없이 생일이 비면 막는다. 깊은 궁합은 늘 생일이 필요하다', () => {
  assert.equal(assess({ productId: 'reunion', self, partner: { name: 'x' }, answers: {} }).code, 'PARTNER_BIRTH_REQUIRED');
  assert.equal(assess({ productId: 'intimate', self, partner: { name: 'x', birthUnknown: true }, answers: {} }).code, 'PARTNER_BIRTH_REQUIRED');
});
test('화면: 생일 모름 안내에 두 버튼, 결제 화면 표시, 목차 5·6장 이름이 리포트와 같다', () => {
  assert.ok(html.includes('상대 생일 없이 재회사주 보기') && html.includes('그래도 모르겠다면, 연애사주로 보기'));
  assert.ok(html.includes('생년월일 모름 · 그 사람 사주는 빼고 내 사주로 풀어요'));
  const py = fs.readFileSync(new URL('../../saju/report/reunion.py', import.meta.url), 'utf8');
  for (const t of ['내가 끌리는 사람, 나와 맞는 사람', '그 사람과 나 사이에 반복된 것', '배우자 자리로 보는 인연의 모습']) {
    assert.ok(html.includes(t) && py.includes(t), t);
  }
});
test('이어하기 안내 메일은 없다(사장님 11-05 빼라)', () => {
  assert.ok(!html.includes('remind-ok') && !html.includes('이어하기 안내 메일'));
});
