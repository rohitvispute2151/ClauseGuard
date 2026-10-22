import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', name: 'library', component: () => import('@/views/LibraryView.vue'), meta: { title: 'Documents' } },
    {
      path: '/documents/:id',
      component: () => import('@/views/WorkspaceView.vue'),
      props: true,
      children: [
        { path: '', redirect: (to) => `/documents/${to.params.id}/review` },
        { path: 'review', name: 'review', component: () => import('@/views/ReviewView.vue'), props: true, meta: { title: 'Clause review' } },
        { path: 'ask', name: 'ask', component: () => import('@/views/AskView.vue'), props: true, meta: { title: 'Ask' } },
      ],
    },
    { path: '/upload', redirect: '/' },
    { path: '/extractions', redirect: '/' },
    { path: '/ask', redirect: '/' },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
});

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · ClauseGuard` : 'ClauseGuard';
});

export default router;
