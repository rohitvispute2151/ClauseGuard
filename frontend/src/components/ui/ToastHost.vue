<script setup lang="ts">
import { toasts } from '@/lib/toast';
import Icon from './Icon.vue';
</script>

<template>
  <div class="host" aria-live="polite">
    <TransitionGroup name="t">
      <div v-for="t in toasts" :key="t.id" class="toast" :class="t.kind" role="status">
        <Icon :name="t.kind === 'success' ? 'check' : 'alert'" />
        <span>{{ t.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.host { position: fixed; right: 16px; bottom: 16px; display: flex; flex-direction: column; gap: 8px; z-index: 100; }
.toast {
  display: flex; align-items: center; gap: 10px; max-width: 380px;
  padding: 10px 14px; border-radius: var(--radius); font-size: 13.5px;
  background: var(--text); color: var(--bg); box-shadow: var(--shadow-lg);
}
.toast.error svg { color: #f87171; }
.toast.success svg { color: #4ade80; }
.t-enter-active, .t-leave-active { transition: all 0.2s ease; }
.t-enter-from, .t-leave-to { opacity: 0; transform: translateY(8px); }
</style>
