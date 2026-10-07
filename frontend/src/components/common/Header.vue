<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { useHealth } from '../../composables/useHealth';
import { useDocument } from '../../composables/useDocument';

const route = useRoute();
const { health, isLoading: isHealthLoading, error: healthError } = useHealth();
const { activeDocument } = useDocument();

const healthStatusText = computed(() => {
  if (isHealthLoading.value) return 'Connecting...';
  if (healthError.value) return 'API Offline';
  if (health.value?.status === 'healthy') return 'Online';
  return 'Unknown';
});

const healthStatusClass = computed(() => {
  if (healthError.value) return 'badge-danger';
  if (health.value?.status === 'healthy') return 'badge-success';
  return 'badge-warning';
});
</script>

<template>
  <header class="header">
    <div class="header-inner">
      <div class="brand">
        <RouterLink to="/" class="brand-link">
          <div class="brand-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path d="m9 12 2 2 4-4"/>
            </svg>
          </div>
          <div>
            <div class="brand-title">ClauseGuard</div>
            <div class="brand-subtitle">Contract Review & Intelligence</div>
          </div>
        </RouterLink>
      </div>

      <nav class="nav">
        <RouterLink to="/" class="nav-link" :class="{ active: route.path === '/' }">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect width="7" height="9" x="3" y="3" rx="1"/>
            <rect width="7" height="5" x="14" y="3" rx="1"/>
            <rect width="7" height="9" x="14" y="12" rx="1"/>
            <rect width="7" height="5" x="3" y="16" rx="1"/>
          </svg>
          Overview
        </RouterLink>
        <RouterLink to="/upload" class="nav-link" :class="{ active: route.path === '/upload' }">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" x2="12" y1="3" y2="15"/>
          </svg>
          Documents
        </RouterLink>
        <RouterLink to="/extractions" class="nav-link" :class="{ active: route.path === '/extractions' }">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" x2="8" y1="13" line2="13"/>
            <line x1="16" x2="8" y1="17" line2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
          Clause Extraction
        </RouterLink>
        <RouterLink to="/ask" class="nav-link" :class="{ active: route.path === '/ask' }">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          Grounded Q&A
        </RouterLink>
      </nav>

      <div class="header-meta">
        <!-- Active Document Badge -->
        <div v-if="activeDocument" class="active-doc-tag">
          <span class="active-doc-icon">📄</span>
          <span class="active-doc-name" :title="activeDocument.filename">{{ activeDocument.filename }}</span>
          <span class="badge" :class="activeDocument.status === 'COMPLETED' ? 'badge-success' : 'badge-warning'">
            {{ activeDocument.status }}
          </span>
        </div>

        <!-- Health Status Badge -->
        <div class="health-badge-container">
          <span class="badge" :class="healthStatusClass" :title="health ? `Primary: ${health.primary_provider}\nFallback: ${health.fallback_provider}` : 'Checking backend status'">
            <span class="status-dot" :class="health ? 'bg-success' : 'bg-danger'"></span>
            {{ healthStatusText }}
          </span>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: var(--bg-glass);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-subtle);
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0.85rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.brand-link {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  color: var(--text-primary);
}

.brand-icon {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(129, 140, 248, 0.4));
  border: 1px solid var(--border-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #818cf8;
}

.brand-title {
  font-weight: 700;
  font-size: 1.15rem;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #ffffff, #cbd5e1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.brand-subtitle {
  font-size: 0.725rem;
  color: var(--text-muted);
}

.nav {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(0, 0, 0, 0.25);
  padding: 0.25rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.95rem;
  border-radius: var(--radius-md);
  font-size: 0.825rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.15s ease;
}

.nav-link:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.05);
}

.nav-link.active {
  background: var(--bg-card);
  color: #ffffff;
  border: 1px solid var(--border-medium);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.active-doc-tag {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.3rem 0.65rem;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-size: 0.8rem;
}

.active-doc-name {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
  font-weight: 500;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}

.bg-success {
  background-color: var(--success);
  box-shadow: 0 0 6px var(--success);
}

.bg-danger {
  background-color: var(--danger);
  box-shadow: 0 0 6px var(--danger);
}
</style>
