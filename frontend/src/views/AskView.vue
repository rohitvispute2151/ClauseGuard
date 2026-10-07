<script setup lang="ts">
import DocumentSelector from '../components/common/DocumentSelector.vue';
import QuestionView from '../components/qa/QuestionView.vue';
</script>

<template>
  <div class="ask-view-page">
    <div class="page-header">
      <h2>Grounded Contract Assistant</h2>
      <p class="page-sub">
        Ask natural-language questions and receive real-time streaming answers grounded in verified source clauses.
      </p>
    </div>

    <DocumentSelector />
    <QuestionView />
  </div>
</template>

<style scoped>
.ask-view-page {
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
