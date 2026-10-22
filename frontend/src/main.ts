import { createApp } from 'vue';
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query';
import App from './App.vue';
import router from './router';
import '@/lib/theme';
import './assets/styles.css';

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, staleTime: 30_000 } },
});

createApp(App).use(router).use(VueQueryPlugin, { queryClient }).mount('#app');
