export type DocumentStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
export type ExtractionStatus = 'COMPLETED' | 'PARTIAL' | 'FAILED';

export type ClauseType =
  | 'termination'
  | 'liability_cap'
  | 'indemnity'
  | 'auto_renewal'
  | 'governing_law'
  | 'confidentiality'
  | 'ip_ownership'
  | 'non_compete'
  | 'force_majeure'
  | 'assignment';

export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  primary_provider: string;
  fallback_provider: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  job_id: string | null;
  status: 'PENDING' | 'ALREADY_EXISTS';
  message: string;
}

export interface DocumentStatusResponse {
  id: string;
  filename: string;
  content_hash: string;
  status: DocumentStatus;
  total_pages: number | null;
  total_chunks: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExtractionRequest {
  document_id: string;
  clause_types?: ClauseType[];
  prompt_version?: string;
}

export interface ClauseResult {
  id?: string | null;
  clause_type: ClauseType;
  is_present: boolean;
  verbatim_quote?: string | null;
  summary?: string | null;
  page_number?: number | null;
  confidence: number;
  citation_verified: boolean;
  source_chunk_id?: string | null;
  repair_attempts: number;
  used_fallback: boolean;
}

export interface ExtractionResponse {
  extraction_id: string;
  document_id: string;
  status: ExtractionStatus;
  model_id: string;
  prompt_version: string;
  clause_results: ClauseResult[];
  cost_usd: number;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  cache_hit: boolean;
}

export interface Citation {
  quote: string;
  page_number: number | null;
  chunk_id: string | null;
  verified: boolean;
}

export interface AskTelemetry {
  cost_usd: number;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
}

/** Events yielded by the /ask SSE stream. */
export type AskEvent =
  | { type: 'token'; text: string }
  | { type: 'citations'; citations: Citation[] }
  | { type: 'done'; telemetry: AskTelemetry };
