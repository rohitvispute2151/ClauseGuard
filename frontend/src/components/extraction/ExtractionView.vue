<script setup lang="ts">
import { ref, computed } from 'vue';
import { useExtraction } from '../../composables/useExtraction';
import { useDocument } from '../../composables/useDocument';
import { ALL_CLAUSE_TYPES } from '../../types/api';
import ClauseCard from './ClauseCard.vue';

const { activeDocument } = useDocument();
const {
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
  selectAllClauses
} = useExtraction();

const existingExtractionId = ref('');
const isLookupLoading = ref(false);
const lookupError = ref('');

const groundingRatePercent = computed(() => {
  if (!extraction.value || presentClausesCount.value === 0) return 0;
  return Math.round((verifiedCitationsCount.value / presentClausesCount.value) * 100);
});

async function handleExtract() {
  if (!activeDocument.value) return;
  try {
    await runExtraction(activeDocument.value.id);
  } catch {}
}

async function handleLookup() {
  if (!existingExtractionId.value.trim()) return;
  isLookupLoading.value = true;
  lookupError.value = '';
  try {
    await loadExisting(existingExtractionId.value.trim());
    existingExtractionId.value = '';
  } catch (err: any) {
    lookupError.value = err.message || 'Extraction record not found';
  } finally {
    isLookupLoading.value = false;
  }
}

function selectHighRiskOnly() {
  const highRisk = ALL_CLAUSE_TYPES.filter(c => c.riskCategory === 'high').map(c => c.id);
  selectedClauseTypes.value = highRisk;
}
</script>

<template>
  <div class="extraction-container">
    <!-- Controls Section -->
    <div class="card extraction-controls-card">
      <div class="controls-header">
        <div>
          <h3>Extract Structured Clauses</h3>
          <p class="controls-sub">
            Extract targeted contractual clauses with verbatim citation verification and automated self-repair.
          </p>
        </div>

        <div class="version-select-wrapper">
          <label class="select-label">Prompt Version</label>
          <select v-model="promptVersion" class="select select-sm font-mono">
            <option value="v2">v2 (Structured Zero-Shot + Grounding)</option>
            <option value="v1">v1 (Standard CoT)</option>
          </select>
        </div>
      </div>

      <!-- Clause Type Filters / Chips -->
      <div class="clause-filter-section">
        <div class="filter-header">
          <span class="filter-title">Select Target Clauses ({{ selectedClauseTypes.length }} selected):</span>
          <div class="filter-quick-actions">
            <button class="btn btn-sm btn-ghost" @click="selectAllClauses">Select All</button>
            <button class="btn btn-sm btn-ghost" @click="selectHighRiskOnly">High-Risk Only</button>
          </div>
        </div>

        <div class="clause-chips-grid">
          <button 
            v-for="clause in ALL_CLAUSE_TYPES" 
            :key="clause.id"
            class="clause-chip"
            :class="{
              active: selectedClauseTypes.includes(clause.id),
              'high-risk': clause.riskCategory === 'high'
            }"
            @click="toggleClauseType(clause.id)"
          >
            <span class="chip-check">{{ selectedClauseTypes.includes(clause.id) ? '✓' : '+' }}</span>
            <span class="chip-label">{{ clause.label }}</span>
            <span v-if="clause.riskCategory === 'high'" class="risk-indicator" title="High Risk">*</span>
          </button>
        </div>
      </div>

      <!-- Actions Bar -->
      <div class="controls-actions">
        <button 
          class="btn btn-primary btn-lg" 
          :disabled="isExtracting || !activeDocument || activeDocument.status !== 'COMPLETED'"
          @click="handleExtract"
        >
          <span v-if="isExtracting" class="spinner"></span>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          {{ isExtracting ? 'Analyzing Agreement (Parallel Workers)...' : 'Run Structured Clause Extraction' }}
        </button>

        <!-- Existing ID lookup inline -->
        <div class="lookup-inline">
          <input 
            v-model="existingExtractionId" 
            placeholder="Or load by Extraction ID..." 
            class="input input-sm font-mono"
            @keyup.enter="handleLookup"
          />
          <button 
            class="btn btn-secondary btn-sm" 
            :disabled="isLookupLoading || !existingExtractionId" 
            @click="handleLookup"
          >
            Load
          </button>
        </div>
      </div>

      <div v-if="lookupError" class="error-text">
        {{ lookupError }}
      </div>

      <div v-if="!activeDocument" class="warning-banner">
        ⚠️ Please upload or select a contract document first to perform clause extraction.
      </div>
      <div v-else-if="activeDocument.status !== 'COMPLETED'" class="warning-banner">
        ⚠️ Contract is currently being ingested (Status: {{ activeDocument.status }}). Please wait for chunking to finish.
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="extractionError" class="alert alert-danger">
      <strong>Extraction Error:</strong> {{ extractionError }}
    </div>

    <!-- Extraction Results Section -->
    <div v-if="extraction" class="extraction-results">
      <!-- Telemetry Strip -->
      <div class="telemetry-strip card">
        <div class="telemetry-item">
          <span class="t-label">Status</span>
          <span class="t-val badge badge-success">{{ extraction.status }}</span>
        </div>
        <div class="telemetry-item">
          <span class="t-label">Model Engine</span>
          <span class="t-val font-mono">{{ extraction.model_id }}</span>
        </div>
        <div class="telemetry-item">
          <span class="t-label">Latency</span>
          <span class="t-val font-mono">{{ Math.round(extraction.latency_ms) }} ms</span>
        </div>
        <div class="telemetry-item">
          <span class="t-label">Tokens (In / Out)</span>
          <span class="t-val font-mono">{{ extraction.input_tokens }} / {{ extraction.output_tokens }}</span>
        </div>
        <div class="telemetry-item">
          <span class="t-label">Inference Cost</span>
          <span class="t-val font-mono">${{ extraction.cost_usd.toFixed(4) }}</span>
        </div>
        <div class="telemetry-item">
          <span class="t-label">Grounded Ratio</span>
          <span class="t-val font-mono text-success">{{ groundingRatePercent }}%</span>
        </div>
      </div>

      <!-- Quick Summary Cards -->
      <div class="summary-cards-row">
        <div class="summary-card card">
          <div class="summary-icon icon-danger">⚠️</div>
          <div>
            <div class="summary-num font-mono">{{ highRiskCount }}</div>
            <div class="summary-text">High-Risk Clauses Identified</div>
          </div>
        </div>

        <div class="summary-card card">
          <div class="summary-icon icon-info">📋</div>
          <div>
            <div class="summary-num font-mono">{{ presentClausesCount }}</div>
            <div class="summary-text">Total Detected Clauses</div>
          </div>
        </div>

        <div class="summary-card card">
          <div class="summary-icon icon-success">🛡️</div>
          <div>
            <div class="summary-num font-mono">{{ verifiedCitationsCount }}</div>
            <div class="summary-text">Verified Grounded Citations</div>
          </div>
        </div>
      </div>

      <!-- Clauses Grid -->
      <div class="clauses-grid">
        <ClauseCard 
          v-for="clause in extraction.clause_results" 
          :key="clause.clause_type" 
          :clause="clause"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.extraction-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.extraction-controls-card {
  padding: 1.75rem;
}

.controls-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}

.controls-sub {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.version-select-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.select-label {
  font-size: 0.725rem;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
}

.clause-filter-section {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.85rem;
}

.filter-title {
  font-size: 0.825rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.filter-quick-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.clause-chips-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.clause-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.35rem 0.75rem;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.clause-chip:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  border-color: var(--border-medium);
}

.clause-chip.active {
  background: rgba(99, 102, 241, 0.15);
  border-color: var(--primary);
  color: #c7d2fe;
}

.clause-chip.high-risk.active {
  border-color: rgba(239, 68, 68, 0.6);
}

.risk-indicator {
  color: var(--danger);
  font-weight: bold;
}

.controls-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.lookup-inline {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  max-width: 320px;
}

.warning-banner {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: var(--warning-bg);
  border: 1px solid var(--warning-border);
  border-radius: var(--radius-md);
  color: #fbbf24;
  font-size: 0.85rem;
}

.telemetry-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  padding: 1rem 1.5rem;
  margin-bottom: 1.25rem;
}

.telemetry-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.t-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

.t-val {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
}

.summary-cards-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
}

.summary-icon {
  font-size: 1.8rem;
  padding: 0.5rem;
  border-radius: var(--radius-md);
  background: var(--bg-surface);
}

.summary-num {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
}

.summary-text {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.clauses-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

.error-text {
  color: var(--danger);
  font-size: 0.8rem;
  margin-top: 0.5rem;
}
</style>
