import { createRouter, createWebHashHistory, RouteRecordRaw } from 'vue-router';

import Login from './views/Login.vue';
import Token from './views/Token.vue';
import Workspaces from './views/Workspaces.vue';

const routes: RouteRecordRaw[] = [
  { name: 'workspaces', path: '/workspaces', component: Workspaces },
  { name: 'login', path: '/login', component: Login },
  { name: 'token', path: '/token', component: Token },
  { path: '/', redirect: '/workspaces' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

export default router;
