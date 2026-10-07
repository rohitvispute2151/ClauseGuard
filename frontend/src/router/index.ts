import { createRouter, createWebHistory } from 'vue-router';
import DashboardView from '../views/DashboardView.vue';
import UploadView from '../views/UploadView.vue';
import ExtractionsView from '../views/ExtractionsView.vue';
import AskView from '../views/AskView.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView
    },
    {
      path: '/upload',
      name: 'upload',
      component: UploadView
    },
    {
      path: '/extractions',
      name: 'extractions',
      component: ExtractionsView
    },
    {
      path: '/ask',
      name: 'ask',
      component: AskView
    }
  ]
});

export default router;
