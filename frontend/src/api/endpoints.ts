import type {
  AskEvent,
  ClauseType,
  DocumentStatusResponse,
  DocumentUploadResponse,
  ExtractionResponse,
  HealthStatus,
} from '@/types/api';
import { API_BASE, ApiError, baseHeaders, request, toApiError, toNetworkError } from './client';
import { parseSSE } from './sse';

export const api = {
  health: (signal?: AbortSignal) => request<HealthStatus>('/health', { signal, timeoutMs: 8_000 }),

  getDocument: (id: string, signal?: AbortSignal) =>
    request<DocumentStatusResponse>(`/documents/${id}`, { signal }),

  uploadDocument: (file: File) => {
    const body = new FormData();
    body.append('file', file);
    return request<DocumentUploadResponse>('/documents', { method: 'POST', body, timeoutMs: 120_000 });
  },

  // Extraction fans out one LLM call per clause type; allow for slow providers.
  extract: (documentId: string, clauseTypes: ClauseType[], promptVersion = 'v2') =>
    request<ExtractionResponse>('/extract', {
      method: 'POST',
      json: { document_id: documentId, clause_types: clauseTypes, prompt_version: promptVersion },
      timeoutMs: 300_000,
    }),

  getExtraction: (id: string, signal?: AbortSignal) =>
    request<ExtractionResponse>(`/extract/${id}`, { signal }),
};

/** Streams a grounded answer as typed events. Throws ApiError on HTTP/stream failure. */
export async function* streamAnswer(
  documentId: string,
  question: string,
  signal: AbortSignal,
): AsyncGenerator<AskEvent> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/ask`, {
      method: 'POST',
      headers: baseHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ document_id: documentId, question: question.trim() }),
      signal,
    });
  } catch (err) {
    throw toNetworkError(err);
  }
  if (!res.ok) throw await toApiError(res);
  if (!res.body) throw new ApiError(0, 'The server returned an empty response stream.');

  let finished = false;
  try {
    for await (const msg of parseSSE(res.body)) {
      let payload: Record<string, unknown>;
      try {
        payload = JSON.parse(msg.data);
      } catch {
        continue;
      }
      if (msg.event === 'token') {
        yield { type: 'token', text: String(payload.data ?? '') };
      } else if (msg.event === 'citations') {
        yield { type: 'citations', citations: (payload.citations as never[]) ?? [] };
      } else if (msg.event === 'done') {
        finished = true;
        yield { type: 'done', telemetry: payload as never };
      } else if (msg.event === 'error') {
        throw new ApiError(500, String(payload.message ?? 'The answer stream failed.'));
      }
    }
  } catch (err) {
    throw err instanceof ApiError ? err : toNetworkError(err);
  }
  if (!finished && !signal.aborted) {
    throw new ApiError(0, 'The connection closed before the answer completed.');
  }
}
