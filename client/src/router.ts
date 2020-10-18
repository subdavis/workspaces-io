import { createRouter, createWebHashHistory, RouteRecordRaw } from 'vue-router';

import Browse from './views/Browse.vue';
import Login from './views/Login.vue';
import Search from './views/Search.vue';
import Token from './views/Token.vue';
import Workspaces from './views/Workspaces.vue';

const routes: RouteRecordRaw[] = [
  { name: 'browse', path: '/browse', component: Browse },
  { name: 'workspaces', path: '/workspaces', component: Workspaces },
  { name: 'login', path: '/login', component: Login },
  { name: 'search', path: '/search', component: Search },
  { name: 'token', path: '/token', component: Token },
  { path: '/', redirect: '/workspaces' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

export default router;
