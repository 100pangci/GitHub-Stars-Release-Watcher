<script setup lang="ts">
import { ref, watch } from "vue";
import { api } from "../api";
import { t } from "../locales";

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

watch(repoId, () => loadEvents(), { immediate: true });

function eventChip(type: string) {
  if (type === "new_release") return { color: "success-container", textColor: "on-success-container", text: t("events.release") };
  if (type === "tag") return { color: "warning-container", textColor: "on-warning-container", text: t("events.tag") };
  return { color: "info-container", textColor: "on-info-container", text: type };
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleString();
}
</script>

<template>
  <div>
    <div class="d-flex align-center ga-3 mb-6">
      <v-avatar size="32" color="primary-container" variant="flat" rounded="lg">
        <v-icon color="primary" size="20">mdi-bell-outline</v-icon>
      </v-avatar>
      <h1 class="text-h6 font-weight-bold">{{ t("events.title") }}</h1>
    </div>

    <v-card variant="flat" color="surface-container" class="mb-4 rounded-xl pa-3">
      <v-text-field
        v-model="repoId"
        :placeholder="t('events.filterPlaceholder')"
        type="number"
        density="compact"
        hide-details
        clearable
        prepend-inner-icon="mdi-filter-variant"
        variant="outlined"
        style="max-width: 280px"
      />
    </v-card>

    <v-skeleton-loader v-if="loading" type="list-item-three-line, list-item-three-line" />

    <v-card v-else-if="events.length === 0" variant="outlined" class="pa-10 text-center rounded-xl">
      <v-icon size="40" color="on-surface-variant" class="mb-2">mdi-bell-off-outline</v-icon>
      <div class="text-body-1 text-on-surface-variant">{{ t("events.noEvents") }}</div>
    </v-card>

    <v-slide-y-reverse-transition group>
      <v-card v-for="evt in events" :key="evt.id" variant="outlined" class="mb-2 rounded-xl">
        <v-card-text class="pa-4">
          <div class="d-flex align-start ga-3">
            <v-avatar size="32" :color="eventChip(evt.event_type).color" variant="flat" rounded="lg">
              <v-icon :color="eventChip(evt.event_type).textColor" size="18">
                {{ evt.event_type === 'new_release' ? 'mdi-tag' : 'mdi-source-branch' }}
              </v-icon>
            </v-avatar>
            <div class="flex-grow-1" style="min-width: 0">
              <div class="text-body-2 font-weight-medium text-on-surface mb-1">{{ evt.title }}</div>
              <div class="text-caption text-on-surface-variant">
                <a :href="evt.repo_url" target="_blank" class="text-caption text-primary text-decoration-none">{{ evt.repo_name }}</a>
                — {{ evt.message }}
              </div>
            </div>
            <div class="d-flex flex-column align-end ga-1 flex-shrink-0">
              <v-chip :color="eventChip(evt.event_type).color" variant="flat" size="x-small" class="font-weight-medium">
                {{ eventChip(evt.event_type).text }}
              </v-chip>
              <span class="text-caption text-on-surface-variant mt-1">{{ formatDate(evt.created_at) }}</span>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-slide-y-reverse-transition>
  </div>
</template>
