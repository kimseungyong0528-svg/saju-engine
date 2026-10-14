// 넷리파이 Blobs 저장소(넷리파이가 무료로 주는 파일 저장 공간).
import { getStore } from '@netlify/blobs';

export function blobStore(name = 'unmyeong-orders') {
  const s = getStore({ name, consistency: 'strong' });
  return {
    get: k => s.get(k, { type: 'json' }),
    set: (k, v) => s.setJSON(k, v),
    setBytes: (k, b) => s.set(k, b),
    getBytes: async k => { const v = await s.get(k, { type: 'arrayBuffer' }); return v ? Buffer.from(v) : null; },
    delete: k => s.delete(k),
    list: async prefix => (await s.list({ prefix })).blobs.map(b => b.key),
  };
}
