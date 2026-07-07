<script setup lang="ts">
import { useRouter } from "vue-router";
import { api } from "../api";

const router = useRouter();

async function handleLogout() {
  try {
    await api.logout();
    router.push("/login");
  } catch {
    router.push("/login");
  }
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1>Release Watcher</h1>
      <p>GitHub Stars</p>
    </div>
    <ul class="sidebar-nav">
      <li>
        <router-link to="/">
          <span class="icon">📊</span> Dashboard
        </router-link>
      </li>
      <li>
        <router-link to="/repos">
          <span class="icon">📦</span> Repositories
        </router-link>
      </li>
      <li>
        <router-link to="/events">
          <span class="icon">🔔</span> Events
        </router-link>
      </li>
      <li>
        <router-link to="/settings">
          <span class="icon">⚙️</span> Settings
        </router-link>
      </li>
    </ul>
    <div class="sidebar-footer">
      <button @click="handleLogout">
        <span class="icon">🚪</span> Logout
      </button>
    </div>
  </aside>
</template>
