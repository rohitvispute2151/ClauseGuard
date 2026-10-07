<script setup lang="ts">
import DocumentSelector from '../components/common/DocumentSelector.vue';
import DocumentUpload from '../components/upload/DocumentUpload.vue';
</script>

<template>
  <div class="upload-view-page">
    <div class="page-header">
      <h2>Contract Document Ingestion</h2>
      <p class="page-sub">
        Upload standard PDF contracts for automated text extraction, section segmentation, and vector embedding.
      </p>
    </div>

    <DocumentSelector />
    <DocumentUpload />
  </div>
</template>

<style scoped>
.upload-view-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.page-header h2 {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.35rem;
}

.page-sub {
  font-size: 0.9rem;
  color: var(--text-secondary);
}
</style>
