// 매일 한 번: 오래된 주문의 개인정보를 지운다.
import { blobStore } from './lib/blobs.mjs';
import { eraseOld } from './lib/orders.mjs';

export default async () => {
  const erased = await eraseOld(blobStore());
  console.log('erased', erased);
};

export const config = { schedule: '@daily' };
