<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api } from "../api";

interface DashboardStats {
  total_stars: number;
  active_repos: number;
  inactive_repos: number;
  week_updates: number;
  last_check: string | null;
  next_check: string | null;
  github_configured: boolean;
}

const stats = ref<DashboardStats | null>(null);
const loading = ref(true);

onMounted(async () => {
  try {
    stats.value = await api.getDashboard();
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div>
    <div class="page-header">
      <h2>Dashboard</h2>
    </div>

    <div v-if="loading" class="card">Loading...</div>

    <template v-if="stats">
      <div class="grid grid-4">
        <div class="card stat-card">
          <div class="value">{{ stats.total_stars }}</div>
          <div class="label">Starred Repos</div>
        </div>
        <div class="card stat-card">
          <div class="value">{{ stats.active_repos }}</div>
          <div class="label">Active</div>
        </div>
        <div class="card stat-card">
          <div class="value">{{ stats.week_updates }}</div>
          <div class="label">Updates (7d)</div>
        </div>
        <div class="card stat-card">
          <div class="value">
            <span v-if="stats.github_configured" class="badge badge-green">Configured</span>
            <span v-else class="badge badge-red">Not Set</span>
          </div>
          <div class="label">GitHub</div>
        </div>
      </div>

      <div class="card" style="margin-top: 16px">
        <h3 style="margin-bottom: 12px; font-size: 0.875rem; color: var(--text-muted)">Status</h3>
        <table>
          <tr>
            <td>Last check</td>
            <td>{{ stats.last_check ?? "Never" }}</td>
          </tr>
          <tr>
            <td>Inactive repos</td>
            <td>{{ stats.inactive_repos }}</td>
          </tr>
        </table>
      </div>
    </template>
  </div>
</template>
