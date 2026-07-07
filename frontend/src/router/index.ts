import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "../views/DashboardView.vue";
import ReposView from "../views/ReposView.vue";
import EventsView from "../views/EventsView.vue";
import SettingsView from "../views/SettingsView.vue";
import LoginView from "../views/LoginView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "dashboard", component: DashboardView, meta: { requiresAuth: true } },
    { path: "/repos", name: "repos", component: ReposView, meta: { requiresAuth: true } },
    { path: "/events", name: "events", component: EventsView, meta: { requiresAuth: true } },
    { path: "/settings", name: "settings", component: SettingsView, meta: { requiresAuth: true } },
    { path: "/login", name: "login", component: LoginView },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});

router.beforeEach(async (to) => {
  if (to.meta.requiresAuth) {
    try {
      const res = await fetch("/api/dashboard/stats");
      if (!res.ok) return { name: "login" };
      const data = await res.json();
      if (data.error) return { name: "login" };
    } catch {
      return { name: "login" };
    }
  }
});

export default router;
