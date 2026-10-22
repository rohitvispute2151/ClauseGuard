import { computed, toValue, type MaybeRefOrGetter } from 'vue';
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query';
import type { ClauseType, DocumentStatusResponse } from '@/types/api';
import { api } from './endpoints';
import { ApiError } from './client';
import { library } from '@/stores/library';

export const keys = {
  health: ['health'] as const,
  document: (id: string) => ['document', id] as const,
  extraction: (id: string) => ['extraction', id] as const,
};

const isTerminal = (s?: string) => s === 'COMPLETED' || s === 'FAILED';

export function useHealth() {
  return useQuery({
    queryKey: keys.health,
    queryFn: ({ signal }) => api.health(signal),
    refetchInterval: 60_000,
    retry: 1,
  });
}

/** Fetches a document and polls every 2s until ingestion reaches a terminal state. */
export function useDocument(id: MaybeRefOrGetter<string | undefined>) {
  const query = useQuery({
    queryKey: computed(() => keys.document(toValue(id) ?? '')),
    queryFn: ({ signal }) => api.getDocument(toValue(id)!, signal),
    enabled: computed(() => !!toValue(id)),
    refetchInterval: (q) => (isTerminal(q.state.data?.status) ? false : 2_000),
    staleTime: (q) => (isTerminal(q.state.data?.status) ? Infinity : 0),
    retry: (count, err) => !(err instanceof ApiError && err.isNotFound) && count < 2,
  });
  return query;
}

export function useUpload() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => api.uploadDocument(file),
    onSuccess: (res, file) => {
      library.add({ id: res.document_id, filename: file.name });
      qc.invalidateQueries({ queryKey: keys.document(res.document_id) });
    },
  });
}

export function useExtraction(documentId: MaybeRefOrGetter<string>) {
  const qc = useQueryClient();

  // Rehydrate the last run for this document without re-calling the LLM.
  const cached = useQuery({
    queryKey: computed(() => keys.extraction(library.extractionId(toValue(documentId)) ?? '')),
    queryFn: ({ signal }) => api.getExtraction(library.extractionId(toValue(documentId))!, signal),
    enabled: computed(() => !!library.extractionId(toValue(documentId))),
    staleTime: Infinity,
    retry: false,
  });

  const run = useMutation({
    mutationFn: (types: ClauseType[]) => api.extract(toValue(documentId), types),
    onSuccess: (res) => {
      library.setExtractionId(res.document_id, res.extraction_id);
      qc.setQueryData(keys.extraction(res.extraction_id), res);
    },
  });

  const data = computed(() => run.data.value ?? cached.data.value ?? null);
  return { data, run, isRestoring: cached.isLoading };
}

export type { DocumentStatusResponse };
