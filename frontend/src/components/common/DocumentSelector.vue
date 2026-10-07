<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useDocument } from '../../composables/useDocument';

const router = useRouter();
const { activeDocument, recentDocuments, selectDocument, clearActive } = useDocument();

const showManualModal = ref(false);
const manualDocId = ref('');
const isSubmitting = ref(false);
const manualError = ref('');

async function handleSelectRecent(id: string) {
  await selectDocument(id);
}

async function handleManualSubmit() {
  if (!manualDocId.value.trim()) return;
  isSubmitting.value = true;
  manualError.value = '';
  try {
    const doc = await selectDocument(manualDocId.value.trim());
    if (doc) {
      showManualModal.value = false;
      manualDocId.value = '';
    } else {
      manualError.value = 'Document not found with this ID.';
    }
  } catch (err: any) {
    manualError.value = err.message || 'Failed to load document';
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <div class="doc-selector-card card">
    <div class="doc-selector-header">
      <div class="doc-title-group">
        <span class="doc-badge-icon">📑</span>
        <div>
          <div class="section-label">Active Contract Document</div>
          <div v-if="activeDocument" class="active-filename">
            {{ activeDocument.filename }}
          </div>
          <div v-else class="no-doc-selected">
            No contract currently selected
          </div>
        </div>
      </div>

      <div class="actions-group">
        <button 
          class="btn btn-sm btn-secondary" 
          @click="showManualModal = true"
          title="Enter an existing Document UUID directly"
        >
          Enter ID
        </button>
        <button 
          class="btn btn-sm btn-primary" 
          @click="router.push('/upload')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" x2="12" y1="3" y2="15"/>
          </svg>
          Upload New
        </button>
        <button 
          v-if="activeDocument" 
          class="btn btn-sm btn-ghost" 
          @click="clearActive" 
          title="Clear current selection"
        >
          ✕
        </button>
      </div>
    </div>

    <!-- Active Document Details Strip -->
    <div v-if="activeDocument" class="doc-meta-strip">
      <div class="meta-item">
        <span class="meta-label">UUID:</span>
        <span class="meta-val font-mono" :title="activeDocument.id">{{ activeDocument.id.slice(0, 13) }}...</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">Status:</span>
        <span 
          class="badge" 
          :class="{
            'badge-success': activeDocument.status === 'COMPLETED',
            'badge-warning': activeDocument.status === 'PROCESSING' || activeDocument.status === 'PENDING',
            'badge-danger': activeDocument.status === 'FAILED'
          }"
        >
          {{ activeDocument.status }}
        </span>
      </div>
      <div class="meta-item" v-if="activeDocument.total_pages !== null">
        <span class="meta-label">Pages:</span>
        <span class="meta-val font-mono">{{ activeDocument.total_pages }}</span>
      </div>
      <div class="meta-item" v-if="activeDocument.total_chunks !== null">
        <span class="meta-label">Indexed Chunks:</span>
        <span class="meta-val font-mono">{{ activeDocument.total_chunks }}</span>
      </div>
      <div class="meta-item" v-if="activeDocument.content_hash">
        <span class="meta-label">SHA-256:</span>
        <span class="meta-val font-mono">{{ activeDocument.content_hash.slice(0, 8) }}...</span>
      </div>
    </div>

    <!-- Recent Documents Quick Chips -->
    <div v-if="recentDocuments.length > 0" class="recent-docs-bar">
      <span class="recent-label">Recent Contracts:</span>
      <div class="recent-chips">
        <button 
          v-for="doc in recentDocuments" 
          :key="doc.id"
          class="chip-btn" 
          :class="{ active: activeDocument?.id === doc.id }"
          @click="handleSelectRecent(doc.id)"
        >
          <span class="chip-name">{{ doc.filename }}</span>
          <span class="chip-status-dot" :class="doc.status === 'COMPLETED' ? 'dot-success' : 'dot-pending'"></span>
        </button>
      </div>
    </div>

    <!-- Manual ID Modal -->
    <div v-if="showManualModal" class="modal-backdrop" @click.self="showManualModal = false">
      <div class="modal-card card">
        <div class="modal-header">
          <h3>Load Existing Document by ID</h3>
          <button class="btn btn-sm btn-ghost" @click="showManualModal = false">✕</button>
        </div>
        <p class="modal-desc">
          Paste a previously generated ClauseGuard document UUID to load its status, extractions, and enable grounded Q&A.
        </p>
        <div class="form-group">
          <input 
            v-model="manualDocId" 
            placeholder="e.g. 3fa85f64-5717-4562-b3fc-2c963f66afa6" 
            class="input font-mono"
            @keyup.enter="handleManualSubmit"
          />
        </div>
        <div v-if="manualError" class="error-text">
          {{ manualError }}
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showManualModal = false">Cancel</button>
          <button class="btn btn-primary" :disabled="isSubmitting || !manualDocId" @click="handleManualSubmit">
            {{ isSubmitting ? 'Loading...' : 'Load Document' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.doc-selector-card {
  margin-bottom: 1.5rem;
  padding: 1.25rem 1.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.doc-selector-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.doc-title-group {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.doc-badge-icon {
  font-size: 1.6rem;
  background: rgba(255, 255, 255, 0.04);
  padding: 0.35rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}

.section-label {
  font-size: 0.725rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  font-weight: 600;
}

.active-filename {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
}

.no-doc-selected {
  font-size: 0.95rem;
  color: var(--text-secondary);
  font-style: italic;
}

.actions-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.doc-meta-strip {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-top: 1rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--border-subtle);
  font-size: 0.8rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.meta-label {
  color: var(--text-muted);
}

.meta-val {
  color: var(--text-primary);
  font-weight: 500;
}

.font-mono {
  font-family: var(--font-mono);
}

.recent-docs-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.85rem;
  padding-top: 0.75rem;
  border-top: 1px dashed var(--border-subtle);
  overflow-x: auto;
  font-size: 0.775rem;
}

.recent-label {
  color: var(--text-muted);
  white-space: nowrap;
}

.recent-chips {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chip-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.25rem 0.65rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.chip-btn:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  border-color: var(--border-medium);
}

.chip-btn.active {
  background: rgba(99, 102, 241, 0.15);
  border-color: var(--border-primary);
  color: #c7d2fe;
}

.chip-status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.dot-success {
  background-color: var(--success);
}

.dot-pending {
  background-color: var(--warning);
}

/* Modal styles */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 1.5rem;
}

.modal-card {
  width: 100%;
  max-width: 480px;
  background: var(--bg-card);
  border: 1px solid var(--border-medium);
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.modal-desc {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 1.25rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.25rem;
}

.error-text {
  color: var(--danger);
  font-size: 0.8rem;
  margin-top: 0.5rem;
}
</style>
