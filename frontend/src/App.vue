<script setup lang="ts">
import { RouterView } from 'vue-router';
import AppHeader from '@/components/layout/AppHeader.vue';
import ToastHost from '@/components/ui/ToastHost.vue';
</script>

<template>
  <AppHeader />
  <main><RouterView /></main>
  <ToastHost />
</template>

<style scoped>
main { max-width: 1120px; margin: 0 auto; padding: 40px 32px 72px; }
@media (max-width: 700px) { main { padding: 24px 16px 48px; } }
</style>
