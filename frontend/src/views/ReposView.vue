<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { api } from "../api";

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

async function loadRepos() {
  loading.value = true;
  try {
    repos.value = await api.getRepos(search.value, filter.value);
  } finally {
    loading.value = false;
  }
}

watch([search, filter], () => loadRepos());
onMounted(() => loadRepos());
</script>

<template>
  <div>
    <div class="page-header">
      <h2>Repositories</h2>
    </div>

    <div class="filter-bar">
      <input v-model="search" placeholder="Search repos..." />
      <select v-model="filter">
        <option value="all">All</option>
        <option value="active">Active</option>
        <option value="inactive">Inactive</option>
        <option value="archived">Archived</option>
        <option value="has_updates">Has Updates</option>
      </select>
    </div>

    <div v-if="loading" class="card">Loading...</div>

    <div v-else-if="repos.length === 0" class="card">
      No repositories found.
    </div>

    <div class="card" v-else style="padding: 0; overflow-x: auto">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Language</th>
            <th>Status</th>
            <th>Current Version</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="repo in repos" :key="repo.id">
            <td>
              <a :href="repo.html_url" target="_blank">{{ repo.full_name }}</a>
              <div v-if="repo.description" style="font-size: 0.75rem; color: var(--text-muted)">
                {{ repo.description }}
              </div>
            </td>
            <td>
              <span v-if="repo.language" class="badge badge-orange">{{ repo.language }}</span>
            </td>
            <td>
              <span v-if="repo.archived" class="badge badge-red">Archived</span>
              <span v-else-if="repo.active" class="badge badge-green">Active</span>
              <span v-else class="badge badge-orange">Inactive</span>
            </td>
            <td>
              <span v-if="repo.current_version">
                <a v-if="repo.current_source === 'release'" :href="repo.html_url + '/releases/tag/' + repo.current_version" target="_blank">
                  {{ repo.current_version }}
                </a>
                <a v-else :href="repo.html_url + '/tags'" target="_blank">
                  {{ repo.current_version }}
                </a>
              </span>
              <span v-else class="text-muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
