<script setup lang="ts">
import { computed, watchEffect } from 'vue';
import { RouterLink, RouterView, useRouter } from 'vue-router';
import { useDocument } from '@/api/queries';
import { ApiError } from '@/api/client';
import { library } from '@/stores/library';
import { formatNumber, timeAgo } from '@/lib/format';
import StatusPill from '@/components/ui/StatusPill.vue';
import Icon from '@/components/ui/Icon.vue';

const props = defineProps<{ id: string }>();
const router = useRouter();
const { data: doc, error, isLoading, refetch } = useDocument(() => props.id);

const notFound = computed(() => error.value instanceof ApiError && error.value.isNotFound);
const ready = computed(() => doc.value?.status === 'COMPLETED');
const processing = computed(() => doc.value && !['COMPLETED', 'FAILED'].includes(doc.value.status));

// Keep the sidebar's "recent" ordering and names fresh when a document is opened.
watchEffect(() => {
  if (doc.value) library.add({ id: doc.value.id, filename: doc.value.filename });
});

function forget() {
  library.remove(props.id);
  router.replace('/');
}
</script>

<template>
  <div class="ws">
    <RouterLink to="/" class="crumb">← Documents</RouterLink>

    <div v-if="isLoading" class="head">
      <div class="skeleton" style="height: 28px; width: 320px" />
      <div class="skeleton" style="height: 16px; width: 200px; margin-top: 10px" />
    </div>

    <div v-else-if="notFound" class="card state">
      <Icon name="alert" :size="22" />
      <h2>Document not found</h2>
      <p>It may have been removed from the server.</p>
      <button class="btn" @click="forget">Remove from library</button>
    </div>

    <div v-else-if="error" class="card state">
      <Icon name="alert" :size="22" />
      <h2>Couldn’t load this document</h2>
      <p>{{ error.message }}</p>
      <button class="btn" @click="refetch()"><Icon name="refresh" /> Retry</button>
    </div>

    <template v-else-if="doc">
      <header class="head">
        <div class="title-row">
          <h1>{{ doc.filename }}</h1>
          <StatusPill :status="doc.status" />
        </div>
        <div class="meta">
          <span v-if="doc.total_pages">{{ doc.total_pages }} pages</span>
          <span v-if="doc.total_chunks">{{ formatNumber(doc.total_chunks) }} indexed passages</span>
          <span>Uploaded {{ timeAgo(doc.created_at) }}</span>
        </div>
      </header>

      <div v-if="processing" class="card state">
        <span class="spinner" style="color: var(--accent); width: 22px; height: 22px" />
        <h2>Indexing your contract</h2>
        <p>Extracting text and building the search index. This page updates automatically.</p>
      </div>

      <div v-else-if="doc.status === 'FAILED'" class="card state">
        <Icon name="alert" :size="22" />
        <h2>Ingestion failed</h2>
        <p>{{ doc.error_message || 'The document could not be processed. Try uploading it again.' }}</p>
        <button class="btn" @click="forget">Remove from library</button>
      </div>

      <template v-else-if="ready">
        <nav class="tabs" aria-label="Document views">
          <RouterLink :to="`/documents/${id}/review`" class="tab"><Icon name="review" /> Clause review</RouterLink>
          <RouterLink :to="`/documents/${id}/ask`" class="tab"><Icon name="message" /> Ask</RouterLink>
        </nav>
        <RouterView :key="id" />
      </template>
    </template>
  </div>
</template>

<style scoped>
.ws { display: flex; flex-direction: column; gap: 20px; }
.crumb { color: var(--text-3); font-size: 13px; width: fit-content; }
.crumb:hover { color: var(--text); }
.title-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.title-row h1 { font-size: 30px; word-break: break-word; }
.meta { display: flex; flex-wrap: wrap; gap: 4px 18px; margin-top: 6px; color: var(--text-3); font-size: 13px; }
.tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--border); margin-top: 4px; }
.tab {
  display: flex; align-items: center; gap: 8px; padding: 10px 14px; margin-bottom: -1px;
  color: var(--text-2); font-weight: 500; border-bottom: 2px solid transparent;
}
.tab:hover { color: var(--text); }
.tab.router-link-active { color: var(--accent-text); border-bottom-color: var(--accent); }
.state { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 8px; padding: 56px 24px; color: var(--text-2); }
.state h2 { font-size: 17px; color: var(--text); margin-top: 6px; }
.state .btn { margin-top: 10px; }
</style>
