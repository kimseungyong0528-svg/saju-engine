// SNS 자동 게시 시계 (2026-11-02 사고: 깃허브 예약 실행이 3시간 늦게 시작해 07:30 스레드·08:00 영상이 안 올라감).
// 넷리파이 예약 함수는 제시간에 돌므로, 30분마다 깨어나 그 시각의 칸을 깃허브 'SNS 자동 게시'에 바로 시킨다.
// 칸 시각은 saju/marketing/meta.py SLOT_TIME 과 같다 (한국 시각). 이미 올린 글은 meta.run 이 다시 올리지 않는다.
export const SLOT_AT = {
  '07:30': ['오전'], '08:00': ['아침영상'], '12:00': ['점심'], '12:30': ['점심글'], '15:00': ['오후'],
  '18:00': ['저녁'], '19:00': ['저녁영상'], '21:00': ['밤', '밤글'], '23:00': ['늦은밤'],
};

export function slotsAt(now) {
  const k = new Date(now.getTime() + 9 * 3600e3);              // 한국 시각
  const m = k.getUTCMinutes() < 15 ? 0 : k.getUTCMinutes() < 45 ? 30 : null;
  if (m === null) return { date: '', slots: [] };
  const hm = `${String(k.getUTCHours()).padStart(2, '0')}:${m ? '30' : '00'}`;
  return { date: k.toISOString().slice(0, 10), slots: SLOT_AT[hm] || [] };
}

export default async () => {
  const { date, slots } = slotsAt(new Date());
  if (!slots.length) return;
  const r = await fetch(`https://api.github.com/repos/${process.env.GITHUB_REPO || 'kimseungyong0528-svg/saju-engine'}/dispatches`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${process.env.GH_DISPATCH_TOKEN}`, Accept: 'application/vnd.github+json', 'User-Agent': 'unmyeong-sns', 'Content-Type': 'application/json' },
    body: JSON.stringify({ event_type: 'sns', client_payload: { slot: slots.join(' '), date } }),
  });
  console.log('sns-clock', date, slots.join(' '), r.status);
  if (r.status !== 204) throw Error(`dispatch ${r.status}`);
};

export const config = { schedule: '0,30 * * * *' };
