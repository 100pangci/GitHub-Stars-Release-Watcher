<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { t } from "../locales";

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
    } else if (res.message.includes("rate limit") || res.message.includes("attempts")) {
      error.value = t("login.error.rateLimit");
    } else {
      error.value = t("login.error.invalid");
    }
  } catch {
    error.value = t("login.error.invalid");
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card variant="elevated" elevation="3" class="pa-6 text-center rounded-xl">
          <v-avatar size="56" color="primary-container" variant="flat" rounded="lg" class="mb-4">
            <v-icon color="primary" size="32">mdi-star-shooting</v-icon>
          </v-avatar>
          <v-card-title class="text-h6 font-weight-bold mb-1 px-0">
            {{ t("login.title") }}
          </v-card-title>

          <v-card-text class="px-0">
            <v-alert v-if="error" type="error" closable class="mb-4" @click:close="error = ''">
              {{ error }}
            </v-alert>

            <v-form @submit.prevent="handleLogin">
              <v-text-field
                v-model="password"
                :label="t('login.password')"
                type="password"
                :placeholder="t('login.placeholder')"
                autofocus
                class="mb-4"
              />

              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="loading"
                :disabled="loading"
              >
                <template #prepend>
                  <v-icon>mdi-login</v-icon>
                </template>
                {{ loading ? t("login.loggingIn") : t("login.login") }}
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>
