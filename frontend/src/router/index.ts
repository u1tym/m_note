import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'
import FileView from '../views/FileView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/files/:fileId', name: 'file', component: FileView, props: true },
  ],
})

export default router
