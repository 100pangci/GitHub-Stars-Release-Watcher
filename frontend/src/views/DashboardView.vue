<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { Line } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
} from "chart.js";
import { api } from "../api";
import { t } from "../locales";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler);

interface DashboardStats {
  total_stars: number;
  active_repos: number;
  inactive_repos: number;
  week_updates: number;
  last_check: string | null;
  next_check: string | null;
  github_configured: boolean;
}

interface HistoryEntry {
  id: number;
  task_name: string;
  status: string;
  started_at: string;
  checked_repos: number;
  found_updates: number;
}

const stats = ref<DashboardStats | null>(null);
const history = ref<HistoryEntry[]>([]);
const loading = ref(true);

const chartData = computed(() => {
  const labels: string[] = [];
  const synced: (number | null)[] = [];
  const updates: (number | null)[] = [];

  for (const h of history.value) {
    if (h.status === "running") continue;
    const d = new Date(h.started_at);
    labels.push(`${d.getMonth() + 1}/${d.getDate()}`);
    synced.push(h.task_name === "sync_stars" ? h.checked_repos : null);
    updates.push(h.task_name === "check_releases" ? h.found_updates : null);
  }

  const max = 30;
  return {
    labels: labels.length > max ? labels.slice(-max) : labels,
    datasets: [
      {
        label: t("dashboard.chart.synced"),
        data: synced.length > max ? synced.slice(-max) : synced,
        borderColor: "rgb(74, 124, 255)",
        backgroundColor: "rgba(74, 124, 255, 0.08)",
        fill: true,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 5,
        borderWidth: 2,
      },
      {
        label: t("dashboard.chart.updates"),
        data: updates.length > max ? updates.slice(-max) : updates,
        borderColor: "rgb(52, 211, 153)",
        backgroundColor: "rgba(52, 211, 153, 0.08)",
        fill: true,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 5,
        borderWidth: 2,
      },
    ],
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      labels: { color: "rgba(226, 232, 240, 0.6)", boxWidth: 12, padding: 12, usePointStyle: true },
    },
  },
  scales: {
    x: {
      ticks: { color: "rgba(226, 232, 240, 0.4)", maxTicksLimit: 8, font: { size: 11 } },
      grid: { color: "rgba(255,255,255,0.04)" },
    },
    y: {
      beginAtZero: true,
      ticks: { color: "rgba(226, 232, 240, 0.4)", font: { size: 11 } },
      grid: { color: "rgba(255,255,255,0.04)" },
    },
  },
  interaction: { intersect: false, mode: "index" as const },
};

onMounted(async () => {
  try {
    const [s, h] = await Promise.all([api.getDashboard(), api.getHistory()]);
    stats.value = s;
    history.value = h;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div>
    <div class="d-flex align-center ga-3 mb-6">
      <v-avatar size="32" color="primary-container" variant="flat" rounded="lg">
        <v-icon color="primary" size="20">mdi-view-dashboard</v-icon>
      </v-avatar>
      <h1 class="text-h6 font-weight-bold">{{ t("dashboard.title") }}</h1>
    </div>

    <v-skeleton-loader v-if="loading" type="card, card, card" />

    <template v-if="stats">
      <v-row>
        <v-col cols="6" sm="3">
          <v-card variant="elevated" elevation="2" class="text-center pa-5 rounded-xl d-flex flex-column align-center justify-center" style="min-height: 148px">
            <v-icon color="primary" size="24" class="mb-2">mdi-star</v-icon>
            <div class="text-h4 font-weight-bold text-primary mb-1">{{ stats.total_stars }}</div>
            <div class="text-caption text-on-surface-variant font-weight-medium">{{ t("dashboard.starredRepos") }}</div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card variant="elevated" elevation="2" class="text-center pa-5 rounded-xl d-flex flex-column align-center justify-center" style="min-height: 148px">
            <v-icon color="success" size="24" class="mb-2">mdi-check-circle</v-icon>
            <div class="text-h4 font-weight-bold text-success mb-1">{{ stats.active_repos }}</div>
            <div class="text-caption text-on-surface-variant font-weight-medium">{{ t("dashboard.active") }}</div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card variant="elevated" elevation="2" class="text-center pa-5 rounded-xl d-flex flex-column align-center justify-center" style="min-height: 148px">
            <v-icon color="warning" size="24" class="mb-2">mdi-bell-ring</v-icon>
            <div class="text-h4 font-weight-bold text-warning mb-1">{{ stats.week_updates }}</div>
            <div class="text-caption text-on-surface-variant font-weight-medium">{{ t("dashboard.updates7d") }}</div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card variant="elevated" elevation="2" class="text-center pa-5 rounded-xl d-flex flex-column align-center justify-center" style="min-height: 148px">
            <v-icon :color="stats.github_configured ? 'success' : 'error'" size="24" class="mb-2">mdi-github</v-icon>
            <div class="text-h4 font-weight-bold" :class="stats.github_configured ? 'text-success' : 'text-error'">{{ stats.github_configured ? t("dashboard.configured") : t("dashboard.notSet") }}</div>
            <div class="text-caption text-on-surface-variant font-weight-medium">{{ t("dashboard.github") }}</div>
          </v-card>
        </v-col>
      </v-row>

      <v-row class="mt-2" align="stretch">
        <v-col cols="12" md="4">
          <v-card variant="flat" color="surface-container" height="100%" class="rounded-xl">
            <v-card-item class="px-4 pt-4 pb-0">
              <template #prepend>
                <v-avatar size="28" color="surface-container-high" variant="flat" rounded="lg">
                  <v-icon color="on-surface-variant" size="16">mdi-information-outline</v-icon>
                </v-avatar>
              </template>
              <v-card-title class="text-body-2 font-weight-bold text-on-surface">{{ t("dashboard.status") }}</v-card-title>
            </v-card-item>
            <v-list lines="one" class="px-2 pb-2">
              <v-list-item>
                <template #prepend>
                  <v-icon color="on-surface-variant" size="18" class="mr-2">mdi-clock-outline</v-icon>
                </template>
                <v-list-item-title class="text-body-2 text-on-surface-variant">{{ t("dashboard.lastCheck") }}</v-list-item-title>
                <template #append>
                  <span class="text-body-2 text-on-surface">{{ stats.last_check ?? t("dashboard.never") }}</span>
                </template>
              </v-list-item>
              <v-list-item>
                <template #prepend>
                  <v-icon color="on-surface-variant" size="18" class="mr-2">mdi-cancel</v-icon>
                </template>
                <v-list-item-title class="text-body-2 text-on-surface-variant">{{ t("dashboard.inactiveRepos") }}</v-list-item-title>
                <template #append>
                  <span class="text-body-2 text-on-surface">{{ stats.inactive_repos }}</span>
                </template>
              </v-list-item>
            </v-list>
          </v-card>
        </v-col>

        <v-col cols="12" md="8">
          <v-card variant="outlined" height="100%" class="rounded-xl">
            <v-card-item class="px-4 pt-4 pb-0">
              <template #prepend>
                <v-avatar size="28" color="surface-container-high" variant="flat" rounded="lg">
                  <v-icon color="on-surface-variant" size="16">mdi-chart-timeline-variant</v-icon>
                </v-avatar>
              </template>
              <v-card-title class="text-body-2 font-weight-bold text-on-surface">{{ t("dashboard.chart.title") }}</v-card-title>
            </v-card-item>
            <v-card-text class="pt-4 px-4 pb-4">
              <div style="height: 220px">
                <Line v-if="history.length" :data="chartData" :options="chartOptions" />
                <div v-else class="text-body-2 text-on-surface-variant text-center py-10">{{ t("dashboard.chart.noData") }}</div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </div>
</template>
