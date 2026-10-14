// All calls are relative: Nginx (Docker) or the Ingress (Kubernetes) routes /api to FastAPI.
const BASE = '/api/products';

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d) => d.msg).join(', ');
    } catch {
      // Non-JSON error body (e.g. backend down behind the proxy) — keep the generic message.
    }
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

export const api = {
  list: () => request(''),
  stats: () => request('/stats'),
  create: (product) => request('', { method: 'POST', body: JSON.stringify(product) }),
  update: (id, product) => request(`/${id}`, { method: 'PUT', body: JSON.stringify(product) }),
  adjust: (id, delta) => request(`/${id}/adjust`, { method: 'POST', body: JSON.stringify({ delta }) }),
  remove: (id) => request(`/${id}`, { method: 'DELETE' }),
};
