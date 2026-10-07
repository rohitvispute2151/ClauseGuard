<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useDocument } from '../../composables/useDocument';

const router = useRouter();
const { activeDocument, isUploading, isPolling, uploadError, upload } = useDocument();

const isDragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const localError = ref<string | null>(null);

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    processFile(target.files[0]);
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false;
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    processFile(event.dataTransfer.files[0]);
  }
}

async function processFile(file: File) {
  localError.value = null;

  if (!file.name.toLowerCase().endsWith('.pdf')) {
    localError.value = 'Only PDF contracts (.pdf) are supported.';
    return;
  }

  // 50 MB check
  if (file.size > 50 * 1024 * 1024) {
    localError.value = 'File exceeds maximum allowed size of 50 MB.';
    return;
  }

  try {
    await upload(file);
  } catch (err: any) {
    localError.value = err.message || 'Error uploading document';
  }
}

function triggerFileInput() {
  fileInput.value?.click();
}
</script>

<template>
  <div class="upload-container">
    <!-- Drag and Drop Dropzone -->
    <div 
      class="dropzone" 
      :class="{ 'is-dragging': isDragging, 'is-loading': isUploading }"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <input 
        ref="fileInput" 
        type="file" 
        accept="application/pdf" 
        class="hidden-input" 
        @change="handleFileSelect"
      />

      <div class="dropzone-content">
        <div class="upload-icon-wrapper">
          <svg v-if="!isUploading" xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" x2="12" y1="3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <div v-else class="spinner"></div>
        </div>

        <div class="dropzone-text">
          <h3 class="dropzone-title">
            {{ isUploading ? 'Uploading & Queuing for Ingestion...' : 'Drop contract PDF here or click to browse' }}
          </h3>
          <p class="dropzone-subtitle">
            Supported format: PDF agreements up to 50 MB. Fast deduplication via SHA-256 hash.
          </p>
        </div>

        <button 
          type="button" 
          class="btn btn-secondary btn-sm" 
          :disabled="isUploading"
          @click.stop="triggerFileInput"
        >
          Select PDF File
        </button>
      </div>
    </div>

    <!-- Error Alert -->
    <div v-if="localError || uploadError" class="alert alert-danger">
      <span class="alert-icon">⚠️</span>
      <div>
        <strong>Upload Error:</strong> {{ localError || uploadError }}
      </div>
    </div>

    <!-- Ingestion Progress / Active Document Status Card -->
    <div v-if="activeDocument" class="card status-progress-card">
      <div class="card-header">
        <div class="header-title-row">
          <span class="file-icon">📜</span>
          <div>
            <h4>{{ activeDocument.filename }}</h4>
            <div class="sub-meta">UUID: <span class="font-mono">{{ activeDocument.id }}</span></div>
          </div>
        </div>

        <span 
          class="badge" 
          :class="{
            'badge-success': activeDocument.status === 'COMPLETED',
            'badge-warning': activeDocument.status === 'PENDING' || activeDocument.status === 'PROCESSING',
            'badge-danger': activeDocument.status === 'FAILED'
          }"
        >
          {{ activeDocument.status }}
        </span>
      </div>

      <!-- Ingestion Pipeline Stages -->
      <div class="pipeline-stages">
        <div class="stage-item" :class="{ completed: true }">
          <span class="stage-circle">✓</span>
          <span class="stage-label">Upload Accepted</span>
        </div>
        <div class="stage-line" :class="{ active: activeDocument.status !== 'FAILED' }"></div>
        <div class="stage-item" :class="{ completed: activeDocument.status === 'PROCESSING' || activeDocument.status === 'COMPLETED', active: activeDocument.status === 'PROCESSING' }">
          <span class="stage-circle">
            <span v-if="activeDocument.status === 'PROCESSING'" class="mini-spinner"></span>
            <span v-else-if="activeDocument.status === 'COMPLETED'">✓</span>
            <span v-else>2</span>
          </span>
          <span class="stage-label">Text Extraction & Sections</span>
        </div>
        <div class="stage-line" :class="{ active: activeDocument.status === 'COMPLETED' }"></div>
        <div class="stage-item" :class="{ completed: activeDocument.status === 'COMPLETED' }">
          <span class="stage-circle">
            <span v-if="activeDocument.status === 'COMPLETED'">✓</span>
            <span v-else>3</span>
          </span>
          <span class="stage-label">Chunking & Embeddings</span>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-box">
          <div class="stat-label">Document Status</div>
          <div class="stat-value">{{ activeDocument.status }}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Total Pages</div>
          <div class="stat-value font-mono">{{ activeDocument.total_pages ?? (isPolling ? 'Parsing...' : '—') }}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">Vector Chunks</div>
          <div class="stat-value font-mono">{{ activeDocument.total_chunks ?? (isPolling ? 'Embedding...' : '—') }}</div>
        </div>
        <div class="stat-box">
          <div class="stat-label">SHA-256 Hash</div>
          <div class="stat-value font-mono small-hash">{{ activeDocument.content_hash.slice(0, 16) }}...</div>
        </div>
      </div>

      <!-- Ready CTA Buttons -->
      <div v-if="activeDocument.status === 'COMPLETED'" class="cta-actions">
        <button class="btn btn-primary" @click="router.push('/extractions')">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" x2="8" y1="13" line2="13"/>
            <line x1="16" x2="8" y1="17" line2="17"/>
          </svg>
          Extract Structured Clauses
        </button>
        <button class="btn btn-secondary" @click="router.push('/ask')">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          Ask Questions (SSE Stream)
        </button>
      </div>

      <div v-else-if="activeDocument.status === 'FAILED'" class="error-box">
        <strong>Ingestion Failed:</strong> {{ activeDocument.error_message || 'An unknown error occurred during parsing.' }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.dropzone {
  border: 2px dashed var(--border-medium);
  border-radius: var(--radius-xl);
  background: rgba(15, 23, 42, 0.4);
  padding: 3rem 1.5rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.dropzone:hover, .dropzone.is-dragging {
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.06);
  transform: translateY(-2px);
}

.hidden-input {
  display: none;
}

.dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.upload-icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-full);
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid var(--border-primary);
  color: var(--primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
}

.dropzone-title {
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.35rem;
}

.dropzone-subtitle {
  font-size: 0.85rem;
  color: var(--text-secondary);
  max-width: 460px;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-top-color: var(--primary-light);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.mini-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: var(--primary-light);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

.alert {
  padding: 0.85rem 1.25rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.alert-danger {
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
  color: #fca5a5;
}

.status-progress-card {
  padding: 1.75rem;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.file-icon {
  font-size: 1.8rem;
}

.sub-meta {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.pipeline-stages {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 1rem 1.75rem;
  margin-bottom: 1.5rem;
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.stage-circle {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid var(--border-medium);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
}

.stage-item.completed {
  color: var(--text-primary);
}

.stage-item.completed .stage-circle {
  background: var(--success);
  border-color: var(--success);
  color: var(--text-inverse);
}

.stage-item.active {
  color: var(--primary-light);
}

.stage-item.active .stage-circle {
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.2);
}

.stage-line {
  flex: 1;
  height: 2px;
  background: var(--border-subtle);
  margin: 0 1rem;
}

.stage-line.active {
  background: var(--primary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-box {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 0.85rem 1rem;
}

.stat-label {
  font-size: 0.725rem;
  text-transform: uppercase;
  color: var(--text-muted);
  letter-spacing: 0.04em;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.small-hash {
  font-size: 0.85rem;
}

.cta-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.error-box {
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
  padding: 0.85rem 1.25rem;
  border-radius: var(--radius-md);
  color: #fca5a5;
  font-size: 0.875rem;
}
</style>
