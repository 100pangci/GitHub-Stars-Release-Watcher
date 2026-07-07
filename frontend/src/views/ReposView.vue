<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { api } from "../api";
import { t } from "../locales";

interface Repo {
  id: number;
  full_name: string;
  html_url: string;
  description: string;
  language: string;
  archived: boolean;
  active: boolean;
  pushed_at: string | null;
  current_version: string | null;
  current_source: string | null;
}

const repos = ref<Repo[]>([]);
const loading = ref(true);
const search = ref("");
const filter = ref("all");

const filterItems = computed(() => [
  { title: t("repos.filter.all"), value: "all" },
  { title: t("repos.filter.active"), value: "active" },
  { title: t("repos.filter.inactive"), value: "inactive" },
  { title: t("repos.filter.archived"), value: "archived" },
  { title: t("repos.filter.hasUpdates"), value: "has_updates" },
]);

async function loadRepos() {
  loading.value = true;
  try {
    repos.value = await api.getRepos(search.value, filter.value);
  } finally {
    loading.value = false;
  }
}

watch([search, filter], () => loadRepos(), { immediate: true });

function statusChip(repo: Repo) {
  if (repo.archived) return { color: "error", text: t("repos.status.archived") };
  if (repo.active) return { color: "success", text: t("repos.status.active") };
  return { color: "warning", text: t("repos.status.inactive") };
}
</script>

<template>
  <div>
    <div class="d-flex align-center ga-3 mb-6">
      <v-avatar size="32" color="primary-container" variant="flat" rounded="lg">
        <v-icon color="primary" size="20">mdi-source-repository</v-icon>
      </v-avatar>
      <h1 class="text-h6 font-weight-bold">{{ t("repos.title") }}</h1>
    </div>

    <v-card variant="flat" color="surface-container" class="mb-4 rounded-xl pa-3">
      <div class="d-flex ga-3 flex-wrap">
        <v-text-field
          v-model="search"
          :placeholder="t('repos.search')"
          density="compact"
          hide-details
          clearable
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          class="flex-grow-1"
          style="min-width: 200px"
        />
        <v-select
          v-model="filter"
          :items="filterItems"
          density="compact"
          hide-details
          variant="outlined"
          class="flex-shrink-0"
          style="min-width: 140px"
        />
      </div>
    </v-card>

    <v-skeleton-loader v-if="loading" type="table" />

    <v-card v-else-if="repos.length === 0" variant="outlined" class="pa-10 text-center rounded-xl">
      <v-icon size="40" color="on-surface-variant" class="mb-2">mdi-inbox-outline</v-icon>
      <div class="text-body-1 text-on-surface-variant">{{ t("repos.noRepos") }}</div>
    </v-card>

    <v-card v-else variant="outlined" class="rounded-xl">
      <v-table hover>
        <thead>
          <tr>
            <th class="text-caption font-weight-bold text-uppercase text-on-surface-variant">{{ t("repos.columns.name") }}</th>
            <th class="text-caption font-weight-bold text-uppercase text-on-surface-variant">{{ t("repos.columns.language") }}</th>
            <th class="text-caption font-weight-bold text-uppercase text-on-surface-variant">{{ t("repos.columns.status") }}</th>
            <th class="text-caption font-weight-bold text-uppercase text-on-surface-variant">{{ t("repos.columns.version") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="repo in repos" :key="repo.id">
            <td>
              <a :href="repo.html_url" target="_blank" class="font-weight-medium text-body-2 text-primary text-decoration-none">{{ repo.full_name }}</a>
              <div v-if="repo.description" class="text-caption text-on-surface-variant mt-1 line-clamp-1">{{ repo.description }}</div>
            </td>
            <td>
              <v-chip v-if="repo.language" color="primary-container" variant="flat" size="x-small" class="text-on-primary-container">{{ repo.language }}</v-chip>
            </td>
            <td>
              <v-chip :color="statusChip(repo).color" size="x-small">{{ statusChip(repo).text }}</v-chip>
            </td>
            <td>
              <span v-if="repo.current_version">
                <a
                  v-if="repo.current_source === 'release'"
                  :href="repo.html_url + '/releases/tag/' + repo.current_version"
                  target="_blank"
                  class="text-body-2 text-primary text-decoration-none"
                >{{ repo.current_version }}</a>
                <a
                  v-else
                  :href="repo.html_url + '/tags'"
                  target="_blank"
                  class="text-body-2 text-primary text-decoration-none"
                >{{ repo.current_version }}</a>
              </span>
              <span v-else class="text-on-surface-variant">—</span>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>
  </div>
</template>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
