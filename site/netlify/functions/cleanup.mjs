// 한 시간마다: 멈춘 주문은 사장님께 알리고, 오래된 주문의 개인정보를 지운다.
import { blobStore } from './lib/blobs.mjs';
import { eraseOld, flagStuck } from './lib/orders.mjs';
import { realServices } from './lib/services.mjs';

export default async () => {
  const store = blobStore();
  const stuck = await flagStuck(store, realServices(process.env));
  const erased = await eraseOld(store);
  console.log('stuck', stuck, 'erased', erased);
};

export const config = { schedule: '@hourly' };
