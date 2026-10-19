import { ApiError } from './ApiError';
import { reportUnauthorized } from '@/shared/auth/authEvents';

const configuredBase = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const baseUrl = configuredBase
  .replace(/\/$/, '')
  .replace(/\/api$/, '/api/v1');

type HttpOptions = Omit<RequestInit, 'body'> & { body?: unknown };

async function request<T>(path: string, options: HttpOptions = {}): Promise<T> {
  const { body, ...requestOptions } = options;
  const headers = new Headers(requestOptions.headers);
  headers.set('Accept', 'application/json');
  if (body !== undefined && !(body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${baseUrl}${path}`, {
    ...requestOptions,
    headers,
    body: body === undefined || body instanceof FormData
      ? body as BodyInit | null | undefined
      : JSON.stringify(body),
  });

  let payload: unknown = null;
  try { payload = await response.json(); } catch { /* empty response */ }
  if (!response.ok) {
    const bearer = /^Bearer\s+(\S+)$/i.exec(headers.get('Authorization') ?? '');
    if (response.status === 401 && bearer) reportUnauthorized(bearer[1]);
    // A 403 is permission denial, not proof that the session is invalid.
    throw new ApiError(response.status, payload);
  }
  return payload as T;
}

export const httpClient = {
  get: <T>(path: string, options?: HttpOptions) => request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: HttpOptions) => request<T>(path, { ...options, method: 'POST', body }),
  put: <T>(path: string, body?: unknown, options?: HttpOptions) => request<T>(path, { ...options, method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown, options?: HttpOptions) => request<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options?: HttpOptions) => request<T>(path, { ...options, method: 'DELETE' }),
};
