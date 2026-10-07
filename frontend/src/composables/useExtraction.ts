import { ref, computed } from 'vue';
import { apiService } from '../services/api';
import type { ClauseType, ExtractionResponse } from '../types/api';
import { ALL_CLAUSE_TYPES } from '../types/api';

const extraction = ref<ExtractionResponse | null>(null);
const isExtracting = ref<boolean>(false);
const extractionError = ref<string | null>(null);
const selectedClauseTypes = ref<ClauseType[]>(ALL_CLAUSE_TYPES.map(c => c.id));
const promptVersion = ref<string>('v2');

export function useExtraction() {
  const verifiedCitationsCount = computed(() => {
    if (!extraction.value) return 0;
    return extraction.value.clause_results.filter(c => c.citation_verified).length;
  });

  const presentClausesCount = computed(() => {
    if (!extraction.value) return 0;
    return extraction.value.clause_results.filter(c => c.is_present).length;
  });

  const highRiskCount = computed(() => {
    if (!extraction.value) return 0;
    const highRiskTypes = new Set(['termination', 'liability_cap', 'indemnity', 'ip_ownership']);
    return extraction.value.clause_results.filter(c => c.is_present && highRiskTypes.has(c.clause_type)).length;
  });

  async function runExtraction(documentId: string) {
    if (!documentId) return;
    isExtracting.value = true;
    extractionError.value = null;

    try {
      const result = await apiService.extractClauses({
        document_id: documentId,
        clause_types: selectedClauseTypes.value,
        prompt_version: promptVersion.value
      });
      extraction.value = result;
      return result;
    } catch (err: any) {
      extractionError.value = err.message || 'Clause extraction failed';
      throw err;
    } finally {
      isExtracting.value = false;
    }
  }

  async function loadExisting(extractionId: string) {
    if (!extractionId) return;
    isExtracting.value = true;
    extractionError.value = null;

    try {
      const result = await apiService.getExtraction(extractionId);
      extraction.value = result;
      return result;
    } catch (err: any) {
      extractionError.value = err.message || 'Failed to retrieve extraction';
      throw err;
    } finally {
      isExtracting.value = false;
    }
  }

  function toggleClauseType(type: ClauseType) {
    const idx = selectedClauseTypes.value.indexOf(type);
    if (idx >= 0) {
      if (selectedClauseTypes.value.length > 1) {
        selectedClauseTypes.value.splice(idx, 1);
      }
    } else {
      selectedClauseTypes.value.push(type);
    }
  }

  function selectAllClauses() {
    selectedClauseTypes.value = ALL_CLAUSE_TYPES.map(c => c.id);
  }

  function clearExtraction() {
    extraction.value = null;
    extractionError.value = null;
  }

  return {
    extraction,
    isExtracting,
    extractionError,
    selectedClauseTypes,
    promptVersion,
    verifiedCitationsCount,
    presentClausesCount,
    highRiskCount,
    runExtraction,
    loadExisting,
    toggleClauseType,
    selectAllClauses,
    clearExtraction
  };
}
