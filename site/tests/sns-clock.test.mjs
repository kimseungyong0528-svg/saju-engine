import { test } from 'node:test';
import assert from 'node:assert/strict';
import { slotsAt } from '../netlify/functions/sns-clock.mjs';

const at = (iso) => slotsAt(new Date(iso));

test('칸 시각마다 그 칸을 시킨다 (한국 시각, meta.py SLOT_TIME 과 같음)', () => {
  assert.deepEqual(at('2026-11-01T22:30:05Z'), { date: '2026-11-02', slots: ['오전'] });
  assert.deepEqual(at('2026-11-01T23:00:40Z'), { date: '2026-11-02', slots: ['아침영상'] });
  assert.deepEqual(at('2026-11-02T03:30:00Z'), { date: '2026-11-02', slots: ['점심글'] });
  assert.deepEqual(at('2026-11-02T12:00:00Z'), { date: '2026-11-02', slots: ['밤', '밤글'] });
  assert.deepEqual(at('2026-11-02T14:02:00Z'), { date: '2026-11-02', slots: ['늦은밤'] });
});

test('칸이 없는 시각엔 아무것도 안 한다', () => {
  assert.deepEqual(at('2026-11-02T01:00:00Z').slots, []);
  assert.deepEqual(at('2026-11-02T03:50:00Z').slots, []);
});
