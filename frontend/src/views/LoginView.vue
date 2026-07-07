<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";

const router = useRouter();
const password = ref("");
const error = ref("");
const loading = ref(false);

async function handleLogin() {
  error.value = "";
  loading.value = true;
  try {
    const res = await api.login(password.value);
    if (res.success) {
      router.push("/");
    } else {
      error.value = res.message;
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Login failed";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="card">
        <h2>GitHub Stars Release Watcher</h2>
        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="password">Password</label>
            <input id="password" v-model="password" type="password" placeholder="Enter password" autofocus />
          </div>
          <div class="alert alert-error" v-if="error">{{ error }}</div>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            {{ loading ? "Logging in..." : "Login" }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
