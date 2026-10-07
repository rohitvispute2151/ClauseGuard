<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useHealth } from '../composables/useHealth';
import { useDocument } from '../composables/useDocument';
import DocumentSelector from '../components/common/DocumentSelector.vue';

const router = useRouter();
const { health } = useHealth();
const { activeDocument } = useDocument();
</script>

<template>
  <div class="dashboard-page">
    <!-- Hero Banner -->
    <div class="hero-card card card-glass">
      <div class="hero-content">
        <div class="hero-badge badge badge-info">
          <span>Enterprise Legal Intelligence</span>
        </div>
        <h1 class="hero-title">
          Grounded Contract Review & Intelligence
        </h1>
        <p class="hero-subtitle">
          Extract risky clauses, audit liability limits, and query agreements with 100% verified citations grounded in source text. Powered by dual FreeLLM failover (Gemini Flash & Groq).
        </p>

        <div class="hero-cta-row">
          <button class="btn btn-primary btn-lg" @click="router.push('/upload')">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" x2="12" y1="3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Upload Contract PDF
          </button>
          <button 
            class="btn btn-secondary btn-lg" 
            :disabled="!activeDocument || activeDocument.status !== 'COMPLETED'"
            @click="router.push('/extractions')"
          >
            Run Clause Extraction
          </button>
        </div>
      </div>
    </div>

    <!-- Active Document Selector -->
    <DocumentSelector />

    <!-- Feature Action Cards Grid -->
    <div class="features-grid">
      <div class="feature-card card card-hover" @click="router.push('/upload')">
        <div class="feature-icon bg-indigo">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="12" x2="12" y1="11" line2="17"/>
            <polyline points="9 14 12 11 15 14"/>
          </svg>
        </div>
        <h3>Ingest & Vectorize</h3>
        <p>
          Upload agreements up to 50MB. Asynchronous Celery workers extract text, section headings, and generate dense pgvector embeddings.
        </p>
        <span class="feature-link">Upload Document →</span>
      </div>

      <div 
        class="feature-card card card-hover" 
        :class="{ disabled: !activeDocument || activeDocument.status !== 'COMPLETED' }"
        @click="activeDocument && activeDocument.status === 'COMPLETED' && router.push('/extractions')"
      >
        <div class="feature-icon bg-emerald">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m9 11 3 3L22 4"/>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
          </svg>
        </div>
        <h3>Structured Clause Extraction</h3>
        <p>
          Extract 10 core clauses (Liability Cap, Indemnity, Termination, Auto-Renewal, IP) with exact quotes and self-healing repair loops.
        </p>
        <span class="feature-link">View Extractions →</span>
      </div>

      <div 
        class="feature-card card card-hover" 
        :class="{ disabled: !activeDocument || activeDocument.status !== 'COMPLETED' }"
        @click="activeDocument && activeDocument.status === 'COMPLETED' && router.push('/ask')"
      >
        <div class="feature-icon bg-sky">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <h3>Grounded Q&A (SSE Streaming)</h3>
        <p>
          Ask natural-language questions with real-time token streaming. Every response includes verifiable citations mapped to page numbers.
        </p>
        <span class="feature-link">Launch Assistant →</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

.hero-card {
  padding: 3rem 2.5rem;
  background: linear-gradient(135deg, rgba(22, 32, 51, 0.9), rgba(15, 23, 42, 0.95));
  border: 1px solid var(--border-medium);
  box-shadow: var(--shadow-glow);
  border-radius: var(--radius-xl);
}

.hero-content {
  max-width: 820px;
}

.hero-badge {
  margin-bottom: 1rem;
}

.hero-title {
  font-size: 2.35rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.15;
  margin-bottom: 1rem;
  background: linear-gradient(135deg, #ffffff 40%, #94a3b8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-subtitle {
  font-size: 1.05rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 1.75rem;
}

.hero-cta-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.feature-card {
  padding: 1.75rem;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.feature-card.disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.bg-indigo {
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.bg-emerald {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.bg-sky {
  background: rgba(14, 165, 233, 0.15);
  color: #38bdf8;
  border: 1px solid rgba(14, 165, 233, 0.3);
}

.feature-card h3 {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-primary);
}

.feature-card p {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.6;
  flex: 1;
}

.feature-link {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--primary-light);
  margin-top: 0.5rem;
}

.provider-status-card {
  padding: 1.5rem 1.75rem;
}

.provider-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.25rem;
}

.p-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.p-label {
  font-size: 0.725rem;
  text-transform: uppercase;
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

.p-val {
  font-size: 0.875rem;
  color: var(--text-primary);
}
</style>
