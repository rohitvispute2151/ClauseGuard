import type { ClauseType } from '@/types/api';

export type Risk = 'high' | 'medium' | 'standard';

export interface ClauseMeta {
  id: ClauseType;
  label: string;
  description: string;
  risk: Risk;
}

export const CLAUSES: ClauseMeta[] = [
  { id: 'termination', label: 'Termination', description: 'Notice periods and termination for convenience or cause', risk: 'high' },
  { id: 'liability_cap', label: 'Liability cap', description: 'Aggregate limits, supercaps and carve-outs', risk: 'high' },
  { id: 'indemnity', label: 'Indemnity', description: 'Defense and hold-harmless obligations', risk: 'high' },
  { id: 'ip_ownership', label: 'IP ownership', description: 'Work-for-hire, assignment and license reservations', risk: 'high' },
  { id: 'auto_renewal', label: 'Auto-renewal', description: 'Renewal triggers and opt-out windows', risk: 'medium' },
  { id: 'non_compete', label: 'Non-compete', description: 'Restrictive covenants and non-solicitation', risk: 'medium' },
  { id: 'assignment', label: 'Assignment', description: 'Transfer rights and change-of-control limits', risk: 'medium' },
  { id: 'governing_law', label: 'Governing law', description: 'Jurisdiction, venue and choice of law', risk: 'standard' },
  { id: 'confidentiality', label: 'Confidentiality', description: 'Scope and duration of non-disclosure terms', risk: 'standard' },
  { id: 'force_majeure', label: 'Force majeure', description: 'Excused delays and unforeseeable events', risk: 'standard' },
];

export const clauseMeta = (id: ClauseType): ClauseMeta =>
  CLAUSES.find((c) => c.id === id) ?? { id, label: id.replace(/_/g, ' '), description: '', risk: 'standard' };

export const SUGGESTED_QUESTIONS = [
  'What are the termination conditions and required notice periods?',
  'What is the liability cap, and which claims are excluded from it?',
  'Are there broad indemnification obligations on either party?',
  'Which law governs the agreement and where are disputes resolved?',
  'Does the contract auto-renew, and when is the opt-out deadline?',
];
