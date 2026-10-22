<script setup lang="ts">
import { computed } from 'vue';
import type { DocumentStatus } from '@/types/api';

const props = defineProps<{ status: DocumentStatus }>();

const view = computed(() => ({
  PENDING: { label: 'Queued', cls: 'pill-info', busy: true },
  PROCESSING: { label: 'Processing', cls: 'pill-info', busy: true },
  COMPLETED: { label: 'Ready', cls: 'pill-ok', busy: false },
  FAILED: { label: 'Failed', cls: 'pill-bad', busy: false },
}[props.status]));
</script>

<template>
  <span class="pill" :class="view.cls">
    <span v-if="view.busy" class="spinner" style="width: 10px; height: 10px; border-width: 1.5px" />
    <span v-else class="dot" />
    {{ view.label }}
  </span>
</template>

<style scoped>
.dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
</style>
