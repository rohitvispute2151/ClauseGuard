<script setup lang="ts">
import { ref } from 'vue';
import type { Citation } from '../../types/api';

const props = defineProps<{
  citation: Citation;
}>();

const copied = ref(false);

function copyQuote() {
  navigator.clipboard.writeText(props.citation.quote);
  copied.value = true;
  setTimeout(() => {
    copied.value = false;
  }, 2000);
}
</script>

<template>
  <div class="citation-card" :class="{ 'is-verified': citation.verified }">
    <div class="citation-header">
      <div class="citation-badges">
        <span 
          class="badge" 
          :class="citation.verified ? 'badge-success' : 'badge-warning'"
        >
          <svg v-if="citation.verified" xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          {{ citation.verified ? 'Verified Grounded Citation' : 'Unverified Citation' }}
        </span>

        <span v-if="citation.page_number" class="badge badge-neutral font-mono">
          Page {{ citation.page_number }}
        </span>
      </div>

      <button class="btn btn-sm btn-ghost copy-btn" @click="copyQuote">
        {{ copied ? 'Copied!' : 'Copy' }}
      </button>
    </div>

    <div class="citation-quote">
      "{{ citation.quote }}"
    </div>

    <div v-if="citation.chunk_id" class="citation-meta">
      <span class="chunk-label">Chunk ID:</span>
      <span class="chunk-val font-mono">{{ citation.chunk_id.slice(0, 8) }}...</span>
    </div>
  </div>
</template>

<style scoped>
.citation-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-left: 3px solid var(--primary);
  border-radius: var(--radius-md);
  padding: 0.85rem 1rem;
  margin-top: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.citation-card.is-verified {
  border-left-color: var(--success);
}

.citation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.citation-badges {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.citation-quote {
  font-size: 0.85rem;
  font-style: italic;
  color: #e2e8f0;
  line-height: 1.5;
}

.citation-meta {
  font-size: 0.725rem;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.chunk-val {
  color: var(--text-secondary);
}

.copy-btn {
  padding: 0.15rem 0.45rem;
  font-size: 0.7rem;
}
</style>
