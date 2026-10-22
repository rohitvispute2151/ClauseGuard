<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { useHealth } from '@/api/queries';
import { theme, toggleTheme } from '@/lib/theme';
import Icon from '@/components/ui/Icon.vue';

const route = useRoute();
const { data: health, isError, isLoading } = useHealth();
const online = computed(() => !!health.value && !isError.value);
</script>

<template>
  <header class="bar">
    <div class="inner">
      <RouterLink to="/" class="brand">
        <span class="logo"><Icon name="shield" :size="17" /></span>
        <span class="display">ClauseGuard</span>
      </RouterLink>

      <nav aria-label="Primary">
        <RouterLink to="/" class="link" :class="{ active: route.name === 'library' || route.path.startsWith('/documents') }">Documents</RouterLink>
      </nav>

      <div class="right">
        <div class="health" :title="online ? `${health?.primary_provider} · fallback ${health?.fallback_provider}` : 'API unreachable'">
          <span class="led" :class="{ on: online, off: !online && !isLoading }" />
          <span class="h-title">{{ isLoading ? 'Connecting…' : online ? `API v${health?.version}` : 'API offline' }}</span>
        </div>
        <button class="btn btn-ghost btn-icon btn-sm" :aria-label="`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`" @click="toggleTheme">
          <Icon :name="theme === 'dark' ? 'sun' : 'moon'" />
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.bar { position: sticky; top: 0; z-index: 40; background: color-mix(in srgb, var(--surface) 88%, transparent); backdrop-filter: saturate(1.4) blur(10px); border-bottom: 1px solid var(--border); }
.inner { max-width: 1120px; margin: 0 auto; height: 60px; padding: 0 32px; display: flex; align-items: center; gap: 32px; }
.brand { display: flex; align-items: center; gap: 10px; font-size: 20px; font-weight: 600; letter-spacing: -0.02em; }
.logo { display: grid; place-items: center; width: 28px; height: 28px; border-radius: 8px; background: var(--accent); color: var(--on-accent); }
nav { display: flex; gap: 4px; }
.link { padding: 6px 12px; border-radius: var(--radius-sm); color: var(--text-2); font-weight: 500; }
.link:hover { color: var(--text); background: var(--sunken); }
.link.active { color: var(--accent-text); }
.right { margin-left: auto; display: flex; align-items: center; gap: 12px; }
.health { display: flex; align-items: center; gap: 8px; font-size: 12.5px; color: var(--text-3); }
.led { width: 7px; height: 7px; border-radius: 50%; background: var(--text-3); }
.led.on { background: var(--ok); } .led.off { background: var(--bad); }
@media (max-width: 700px) { .inner { padding: 0 16px; gap: 16px; } .h-title { display: none; } }
</style>
