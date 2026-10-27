// 한 시간마다: 멈춘 주문은 사장님께 알리고, 3일 전에 결과를 받은 손님(동의한 분)께 재구매 할인 메일을 보내고, 오래된 주문의 개인정보를 지운다. 관리 사이트의 35일 지난 게시물 묶음도 지운다.
import { blobStore } from './lib/blobs.mjs';
import { eraseOld, flagStuck } from './lib/orders.mjs';
import { realServices } from './lib/services.mjs';
import { remindRebuy } from './lib/discounts.mjs';
import { eraseOldWeeks } from './lib/studio.mjs';

export default async () => {
  const store = blobStore();
  const services = realServices(process.env);
  const stuck = await flagStuck(store, services);
  const reminded = await remindRebuy(store, services);
  const erased = await eraseOld(store);
  const weeks = await eraseOldWeeks(blobStore('unmyeong-studio'));
  console.log('stuck', stuck, 'rebuy mails', reminded, 'erased', erased, 'studio weeks erased', weeks);
};

export const config = { schedule: '@hourly' };
