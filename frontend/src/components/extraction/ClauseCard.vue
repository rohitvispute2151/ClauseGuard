<script setup lang="ts">
import { computed, ref } from 'vue';
import type { ClauseResultDetail } from '../../types/api';
import { ALL_CLAUSE_TYPES } from '../../types/api';

const props = defineProps<{
  clause: ClauseResultDetail;
}>();

const copied = ref(false);

const meta = computed(() => {
  return ALL_CLAUSE_TYPES.find(c => c.id === props.clause.clause_type) || {
    id: props.clause.clause_type,
    label: props.clause.clause_type.replace('_', ' ').toUpperCase(),
    description: '',
    riskCategory: 'standard' as const
  };
});

const confidencePercent = computed(() => {
  return Math.round((props.clause.confidence || 0) * 100);
});

function copyQuote() {
  if (props.clause.verbatim_quote) {
    navigator.clipboard.writeText(props.clause.verbatim_quote);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  }
}
</script>

<template>
  <div 
    class="clause-card card" 
    :class="{
      'is-present': clause.is_present,
      'is-absent': !clause.is_present,
      'high-risk': clause.is_present && meta.riskCategory === 'high'
    }"
  >
    <!-- Header -->
    <div class="card-header">
      <div class="header-left">
        <h4 class="clause-title">{{ meta.label }}</h4>
        <span 
          v-if="clause.is_present && meta.riskCategory === 'high'" 
          class="badge badge-danger" 
          title="High commercial or legal risk category"
        >
          High Risk
        </span>
        <span 
          v-else-if="clause.is_present && meta.riskCategory === 'medium'" 
          class="badge badge-warning"
        >
          Medium Risk
        </span>
      </div>

      <div class="header-right">
        <!-- Verification Badge -->
        <span 
          v-if="clause.is_present && clause.citation_verified" 
          class="badge badge-success verified-badge" 
          title="Verbatim citation matched against source document text"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Grounded
        </span>

        <span 
          v-else-if="clause.is_present && !clause.citation_verified" 
          class="badge badge-warning"
          title="Citation could not be 100% matched to raw document chunks"
        >
          Unverified Quote
        </span>

        <!-- Presence Badge -->
        <span 
          class="badge" 
          :class="clause.is_present ? 'badge-info' : 'badge-neutral'"
        >
          {{ clause.is_present ? 'Present' : 'Not Identified' }}
        </span>
      </div>
    </div>

    <!-- Summary -->
    <div v-if="clause.summary" class="clause-summary">
      <p>{{ clause.summary }}</p>
    </div>

    <!-- Verbatim Quote Box -->
    <div v-if="clause.verbatim_quote" class="quote-section">
      <div class="quote-header">
        <span class="quote-label">
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"/>
            <path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"/>
          </svg>
          Verbatim Contract Citation
        </span>
        <button class="btn btn-sm btn-ghost copy-btn" @click="copyQuote" title="Copy quote to clipboard">
          {{ copied ? 'Copied!' : 'Copy Quote' }}
        </button>
      </div>

      <div class="quote-box" :class="clause.citation_verified ? 'verified' : 'unverified'">
        "{{ clause.verbatim_quote }}"
      </div>
    </div>

    <!-- Absent Message -->
    <div v-else-if="!clause.is_present" class="absent-note">
      This clause was not detected in the contract.
    </div>

    <!-- Footer Meta -->
    <div class="card-footer">
      <div class="footer-left">
        <span v-if="clause.page_number" class="meta-tag font-mono">
          Page {{ clause.page_number }}
        </span>
        <span v-if="clause.repair_attempts > 0" class="meta-tag font-mono text-warning" title="Required self-correction LLM loops">
          Repairs: {{ clause.repair_attempts }}
        </span>
        <span v-if="clause.used_fallback" class="meta-tag font-mono text-info" title="Resolved via secondary LLM provider">
          Fallback LLM
        </span>
      </div>

      <div v-if="clause.is_present" class="footer-right">
        <div class="confidence-container" :title="`Confidence: ${confidencePercent}%`">
          <span class="conf-label">Confidence:</span>
          <div class="conf-bar-wrapper">
            <div 
              class="conf-bar" 
              :style="{ width: `${confidencePercent}%` }"
              :class="confidencePercent > 80 ? 'bg-success' : confidencePercent > 50 ? 'bg-warning' : 'bg-danger'"
            ></div>
          </div>
          <span class="conf-value font-mono">{{ confidencePercent }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.clause-card {
  padding: 1.25rem 1.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  gap: 1rem;
  transition: all 0.2s ease;
}

.clause-card.high-risk {
  border-left: 3px solid var(--danger);
}

.clause-card.is-absent {
  opacity: 0.65;
  background: rgba(22, 32, 51, 0.5);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.clause-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.verified-badge {
  box-shadow: 0 0 10px var(--success-glow);
}

.clause-summary {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.quote-section {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.quote-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.quote-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
  letter-spacing: 0.04em;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.copy-btn {
  padding: 0.15rem 0.45rem;
  font-size: 0.725rem;
}

.absent-note {
  font-size: 0.85rem;
  color: var(--text-muted);
  font-style: italic;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-subtle);
  font-size: 0.8rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.meta-tag {
  background: var(--bg-surface);
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
}

.text-warning {
  color: var(--warning);
}

.text-info {
  color: var(--info);
}

.footer-right {
  display: flex;
  align-items: center;
}

.confidence-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.conf-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.conf-bar-wrapper {
  width: 60px;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.conf-bar {
  height: 100%;
  border-radius: var(--radius-full);
}

.conf-value {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.bg-success { background: var(--success); }
.bg-warning { background: var(--warning); }
.bg-danger { background: var(--danger); }
</style>
