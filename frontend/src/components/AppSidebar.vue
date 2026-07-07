<script setup lang="ts">
import { useRouter } from "vue-router";
import { api } from "../api";
import { t, locale, setLocale } from "../locales";

const router = useRouter();

async function handleLogout() {
  try {
    await api.logout();
    router.push("/login");
  } catch {
    router.push("/login");
  }
}

const navItems = [
  { to: "/", icon: "mdi-view-dashboard", key: "sidebar.dashboard" },
  { to: "/repos", icon: "mdi-source-repository", key: "sidebar.repos" },
  { to: "/events", icon: "mdi-bell-outline", key: "sidebar.events" },
  { to: "/settings", icon: "mdi-cog-outline", key: "sidebar.settings" },
];
</script>

<template>
  <v-navigation-drawer permanent rail-width="64" width="240" class="sidebar-drawer">
    <div class="d-flex flex-column align-center py-6 px-4">
      <v-avatar size="40" color="primary-container" variant="flat" rounded="lg" class="mb-2">
        <v-icon color="primary" size="24">mdi-star-shooting</v-icon>
      </v-avatar>
      <div class="text-center">
        <div class="text-body-2 font-weight-bold">{{ t("app.title") }}</div>
        <div class="text-caption text-on-surface-variant">{{ t("app.subtitle") }}</div>
      </div>
    </div>

    <v-divider class="mx-4" />

    <v-list nav class="px-3 mt-2">
      <v-list-item
        v-for="item in navItems"
        :key="item.key"
        :to="item.to"
        :prepend-icon="item.icon"
        :title="t(item.key)"
        color="primary"
        rounded="lg"
        class="nav-item mb-1"
        variant="tonal"
      />
    </v-list>

    <template #append>
      <div class="px-4 pb-4 pt-2">
        <v-divider class="mb-4" />
        <div class="text-caption text-on-surface-variant mb-2">{{ t("language.label") }}</div>
        <div class="d-flex ga-2 mb-3">
          <v-btn
            v-for="lang in [['zh', t('language.zh')], ['en', t('language.en')], ['ja', t('language.ja')]]"
            :key="lang[0]"
            :variant="locale === lang[0] ? 'tonal' : 'text'"
            :color="locale === lang[0] ? 'primary' : undefined"
            size="small"
            class="text-none flex-grow-1"
            @click="setLocale(lang[0] as 'zh' | 'ja' | 'en')"
          >
            {{ lang[1] }}
          </v-btn>
        </div>
        <v-btn variant="text" block rounded="lg" class="logout-btn" @click="handleLogout">
          <v-icon start size="18">mdi-logout</v-icon>
          {{ t("sidebar.logout") }}
        </v-btn>
      </div>
    </template>
  </v-navigation-drawer>
</template>

<style scoped>
.sidebar-drawer {
  border-right: 1px solid rgb(var(--v-theme-outline-variant)) !important;
  background: rgb(var(--v-theme-surface-container)) !important;
}
.nav-item {
  margin: 0;
}
.logout-btn {
  font-size: 0.85rem;
  text-transform: none;
  font-weight: 400;
}
</style>
