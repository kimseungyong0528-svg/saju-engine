import { makeApi } from './lib/api.mjs';
import { blobStore } from './lib/blobs.mjs';
import { realServices } from './lib/services.mjs';

export default async req => {
  const env = process.env;
  return makeApi({ store: blobStore(), services: realServices(env), env })(req);
};

export const config = { path: '/api/*' };
