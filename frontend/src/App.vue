<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import AppSidebar from "./components/AppSidebar.vue";

const route = useRoute();
const isLoginPage = computed(() => route.name === "login");
</script>

<template>
  <div class="app-layout" v-if="!isLoginPage">
    <AppSidebar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
  <router-view v-else />
</template>
