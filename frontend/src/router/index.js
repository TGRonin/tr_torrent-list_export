import { createRouter, createWebHashHistory } from "vue-router";
import ListPage from "../views/ListPage.vue";
import DashboardPage from "../views/DashboardPage.vue";
import SettingsPage from "../views/SettingsPage.vue";

const routes = [
  { path: "/", name: "list", component: ListPage },
  { path: "/dashboard", name: "dashboard", component: DashboardPage },
  { path: "/settings", name: "settings", component: SettingsPage },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

export default router;
