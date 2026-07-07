<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { api } from "../api";

interface EventItem {
  id: number;
  title: string;
  message: string;
  event_type: string;
  created_at: string;
  repo_name: string;
  repo_url: string;
}

const events = ref<EventItem[]>([]);
const loading = ref(true);
const repoId = ref("");

async function loadEvents() {
  loading.value = true;
  try {
    events.value = await api.getEvents(repoId.value);
  } finally {
    loading.value = false;
  }
}

watch(repoId, () => loadEvents());
onMounted(() => loadEvents());

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleString();
}
</script>

<template>
  <div>
    <div class="page-header">
      <h2>Events</h2>
    </div>

    <div class="filter-bar">
      <input v-model="repoId" placeholder="Filter by repo ID..." type="number" />
    </div>

    <div v-if="loading" class="card">Loading...</div>

    <div v-else-if="events.length === 0" class="card">
      No events yet.
    </div>

    <div v-else>
      <div v-for="evt in events" :key="evt.id" class="card" style="margin-bottom: 8px">
        <div style="display: flex; justify-content: space-between; align-items: flex-start">
          <div>
            <strong>{{ evt.title }}</strong>
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px">
              <a :href="evt.repo_url" target="_blank">{{ evt.repo_name }}</a>
              — {{ evt.message }}
            </div>
          </div>
          <div style="text-align: right; flex-shrink: 0">
            <span class="badge badge-green" v-if="evt.event_type === 'new_release'">Release</span>
            <span class="badge badge-orange" v-else-if="evt.event_type === 'tag'">Tag</span>
            <span class="badge" v-else>{{ evt.event_type }}</span>
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px">
              {{ formatDate(evt.created_at) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
