import type {
  Citation,
  DocumentStatusResponse,
  DocumentUploadResponse,
  ExtractionRequest,
  ExtractionResponse,
  HealthStatus,
  SSEDonePayload
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: any) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = '';
    try {
      const data = await response.json();
      errorDetail = data.detail || JSON.stringify(data);
    } catch {
      errorDetail = await response.text();
    }
    throw new ApiError(response.status, errorDetail || `Request failed with status ${response.status}`, errorDetail);
  }
  return response.json();
}

export const apiService = {
  /**
   * Fetch backend system health & LLM model providers
   */
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE_URL}/health`);
    return handleResponse<HealthStatus>(res);
  },

  /**
   * Upload PDF contract for asynchronous Celery ingestion and vectorization
   */
  async uploadDocument(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE_URL}/documents`, {
      method: 'POST',
      body: formData
    });
    return handleResponse<DocumentUploadResponse>(res);
  },

  /**
   * Get document ingestion status and chunk metrics
   */
  async getDocument(documentId: string): Promise<DocumentStatusResponse> {
    const res = await fetch(`${API_BASE_URL}/documents/${documentId}`);
    return handleResponse<DocumentStatusResponse>(res);
  },

  /**
   * Trigger parallelized structured clause extraction with repair loop
   */
  async extractClauses(request: ExtractionRequest): Promise<ExtractionResponse> {
    const res = await fetch(`${API_BASE_URL}/extract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        document_id: request.document_id,
        clause_types: request.clause_types,
        prompt_version: request.prompt_version || 'v2'
      })
    });
    return handleResponse<ExtractionResponse>(res);
  },

  /**
   * Retrieve cached extraction results by ID
   */
  async getExtraction(extractionId: string): Promise<ExtractionResponse> {
    const res = await fetch(`${API_BASE_URL}/extract/${extractionId}`);
    return handleResponse<ExtractionResponse>(res);
  },

  /**
   * Stream grounded contract Q&A responses via Server-Sent Events (SSE)
   */
  streamAsk(
    documentId: string,
    question: string,
    handlers: {
      onToken: (token: string) => void;
      onCitations: (citations: Citation[]) => void;
      onDone: (telemetry: SSEDonePayload) => void;
      onError: (error: string) => void;
    }
  ): AbortController {
    const controller = new AbortController();

    (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/ask`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            document_id: documentId,
            question: question.trim()
          }),
          signal: controller.signal
        });

        if (!response.ok) {
          let errDetail = '';
          try {
            const data = await response.json();
            errDetail = data.detail || JSON.stringify(data);
          } catch {
            errDetail = await response.text();
          }
          handlers.onError(errDetail || `Server returned HTTP ${response.status}`);
          return;
        }

        const reader = response.body?.getReader();
        if (!reader) {
          handlers.onError('Response stream body not available.');
          return;
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const messages = buffer.split('\n\n');
          buffer = messages.pop() || '';

          for (const message of messages) {
            const lines = message.split('\n');
            let currentEvent = 'message';
            let currentData = '';

            for (const line of lines) {
              if (line.startsWith('event: ')) {
                currentEvent = line.slice(7).trim();
              } else if (line.startsWith('data: ')) {
                currentData = line.slice(6).trim();
              }
            }

            if (!currentData) continue;

            try {
              const parsed = JSON.parse(currentData);
              if (currentEvent === 'token') {
                handlers.onToken(parsed.data || parsed);
              } else if (currentEvent === 'citations') {
                handlers.onCitations(parsed.citations || []);
              } else if (currentEvent === 'done') {
                handlers.onDone(parsed);
              } else if (currentEvent === 'error') {
                handlers.onError(parsed.message || 'Stream processing error');
              }
            } catch (err) {
              // If not JSON formatted, pass raw data if token
              if (currentEvent === 'token') {
                handlers.onToken(currentData);
              }
            }
          }
        }
      } catch (err: any) {
        if (err.name === 'AbortError') {
          // User aborted manually
          return;
        }
        handlers.onError(err.message || 'Network error streaming answer');
      }
    })();

    return controller;
  }
};
