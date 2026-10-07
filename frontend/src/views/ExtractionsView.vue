<script setup lang="ts">
import DocumentSelector from '../components/common/DocumentSelector.vue';
import ExtractionView from '../components/extraction/ExtractionView.vue';
</script>

<template>
  <div class="extractions-view-page">
    <div class="page-header">
      <h2>Structured Clause Extraction</h2>
      <p class="page-sub">
        Detect high-risk clauses with strict Pydantic schemas, verbatim citation verification, and self-repair loops.
      </p>
    </div>

    <DocumentSelector />
    <ExtractionView />
  </div>
</template>

<style scoped>
.extractions-view-page {
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
