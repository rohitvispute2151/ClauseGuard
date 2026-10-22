// Dev: relative path, proxied by Vite. Production: full URL of the deployed API, e.g. https://api.example.com/api/v1
export const API_BASE = ((import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api/v1').replace(/\/+$/, '');

// Optional shared key. Anything in a browser bundle is public, so this only deters casual scripts.
const API_KEY = import.meta.env.VITE_API_KEY as string | undefined;

export function baseHeaders(extra: Record<string, string> = {}): Record<string, string> {
  return API_KEY ? { ...extra, 'X-API-Key': API_KEY } : extra;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  get isNotFound() {
    return this.status === 404;
  }
}

/** FastAPI returns `detail` as a string, or an array of validation issues (422). */
function extractMessage(body: unknown, fallback: string): string {
  if (body && typeof body === 'object' && 'detail' in body) {
    const { detail } = body as { detail: unknown };
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) => (d && typeof d === 'object' && 'msg' in d ? String((d as { msg: unknown }).msg) : String(d)))
        .join('; ');
    }
  }
  return fallback;
}

export async function toApiError(res: Response): Promise<ApiError> {
  let body: unknown;
  try {
    body = await res.json();
  } catch {
    /* non-JSON error body */
  }
  return new ApiError(res.status, extractMessage(body, `Request failed (${res.status})`));
}

export function toNetworkError(err: unknown): Error {
  if (err instanceof DOMException && err.name === 'AbortError') return err;
  if (err instanceof DOMException && err.name === 'TimeoutError') {
    return new ApiError(0, 'The request timed out. Please try again.');
  }
  return new ApiError(0, 'Unable to reach the ClauseGuard API. Check that the backend is running.');
}

interface RequestOptions {
  method?: string;
  json?: unknown;
  body?: BodyInit;
  signal?: AbortSignal;
  timeoutMs?: number;
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', json, body, signal, timeoutMs = 30_000 } = opts;
  const signals = [AbortSignal.timeout(timeoutMs), ...(signal ? [signal] : [])];

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: baseHeaders(json !== undefined ? { 'Content-Type': 'application/json' } : {}),
      body: json !== undefined ? JSON.stringify(json) : body,
      signal: AbortSignal.any(signals),
    });
  } catch (err) {
    throw toNetworkError(err);
  }
  if (!res.ok) throw await toApiError(res);
  return res.json() as Promise<T>;
}
