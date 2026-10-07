export type DocumentStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'ALREADY_EXISTS';

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

export const ALL_CLAUSE_TYPES: { id: ClauseType; label: string; description: string; riskCategory: 'high' | 'medium' | 'standard' }[] = [
  { id: 'termination', label: 'Termination', description: 'Conditions, notice periods, and termination for convenience or cause', riskCategory: 'high' },
  { id: 'liability_cap', label: 'Liability Cap', description: 'Maximum aggregate liability, supercaps, and exclusions', riskCategory: 'high' },
  { id: 'indemnity', label: 'Indemnity', description: 'Defense and hold harmless obligations, IP and third-party claims', riskCategory: 'high' },
  { id: 'auto_renewal', label: 'Auto-Renewal', description: 'Automatic extension triggers, opt-out notice windows', riskCategory: 'medium' },
  { id: 'governing_law', label: 'Governing Law', description: 'Jurisdiction, venue, and choice of legal system', riskCategory: 'standard' },
  { id: 'confidentiality', label: 'Confidentiality', description: 'Scope of proprietary information, non-disclosure terms and duration', riskCategory: 'standard' },
  { id: 'ip_ownership', label: 'IP Ownership', description: 'Assignment of inventions, work-for-hire, and license reservations', riskCategory: 'high' },
  { id: 'non_compete', label: 'Non-Compete', description: 'Restrictive covenants, non-solicitation, and geographic scope', riskCategory: 'medium' },
  { id: 'force_majeure', label: 'Force Majeure', description: 'Excused delays, unforeseeable acts of God, pandemics', riskCategory: 'standard' },
  { id: 'assignment', label: 'Assignment', description: 'Transferability, change of control restrictions', riskCategory: 'medium' }
];

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

export interface ClauseResultDetail {
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
  clause_results: ClauseResultDetail[];
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

export interface SSEDonePayload {
  cost_usd: number;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  citations?: Citation[];
  telemetry?: SSEDonePayload;
  isStreaming?: boolean;
  error?: string;
}

export interface RecentDocument {
  id: string;
  filename: string;
  status: DocumentStatus;
  total_pages: number | null;
  total_chunks: number | null;
  lastAccessed: string;
}
