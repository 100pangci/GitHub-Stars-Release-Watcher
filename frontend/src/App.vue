<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import AppSidebar from "./components/AppSidebar.vue";

const route = useRoute();
const isLoginPage = computed(() => route.name === "login");
</script>

<template>
  <v-app>
    <template v-if="isLoginPage">
      <router-view />
    </template>
    <template v-else>
      <AppSidebar />
      <v-main class="main-content">
        <div style="max-width: 1100px; margin: 0 auto; padding: 32px">
          <router-view />
        </div>
      </v-main>
    </template>
  </v-app>
</template>

<style>
.main-content {
  position: relative;
  min-height: 100vh;
}
.main-content::before {
  content: "";
  position: fixed;
  top: 0;
  right: 0;
  width: 50%;
  height: 100%;
  background: radial-gradient(ellipse at top right, rgba(74, 124, 255, 0.04), transparent 60%);
  pointer-events: none;
}
</style>
