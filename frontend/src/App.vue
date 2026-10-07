<script setup lang="ts">
import { RouterView } from 'vue-router';
import Header from './components/common/Header.vue';
</script>

<template>
  <div class="app-layout">
    <Header />
    <main class="main-content">
      <div class="content-container">
        <RouterView />
      </div>
    </main>
    <footer class="footer">
        <div class="footer-left">
          <span>ClauseGuard</span>
        </div>
    </footer>
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding: 2rem 1.5rem;
}

.content-container {
  max-width: 1400px;
  margin: 0 auto;
}

.footer {
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  padding: 1.25rem 1.5rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.footer-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.dot {
  color: var(--border-medium);
}
</style>
