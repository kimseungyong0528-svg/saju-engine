// 한 시간마다: 멈춘 주문은 사장님께 알리고, 오래된 주문의 개인정보를 지운다. 관리 사이트의 35일 지난 게시물 묶음도 지운다.
import { blobStore } from './lib/blobs.mjs';
import { eraseOld, flagStuck } from './lib/orders.mjs';
import { realServices } from './lib/services.mjs';
import { eraseOldWeeks } from './lib/studio.mjs';
import { sendReminders } from './lib/remind.mjs';

export default async () => {
  const store = blobStore();
  const services = realServices(process.env);
  const stuck = await flagStuck(store, services);
  const erased = await eraseOld(store);
  const weeks = await eraseOldWeeks(blobStore('unmyeong-studio'));
  const reminded = await sendReminders(store, services).catch(e => { console.error('remind', e?.message); return 0; });
  console.log('stuck', stuck, 'erased', erased, 'studio weeks erased', weeks, 'reminded', reminded);
};

export const config = { schedule: '@hourly' };
