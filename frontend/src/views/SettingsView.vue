<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { api } from "../api";
import { t } from "../locales";

interface Settings {
  github_username: string;
  github_token_set: boolean;
  check_schedule: string;
  check_weekday: string;
  check_time: string;
  custom_interval_minutes: string;
  check_monthday: string;
  monitor_prereleases: string;
  fallback_to_tags: string;
  ignore_archived: string;
  allow_initial_notifications: string;
  github_request_delay: string;
  send_no_updates_email: string;
  smtp_host: string;
  smtp_port: string;
  smtp_username: string;
  smtp_password_set: boolean;
  smtp_use_tls: string;
  smtp_from_addr: string;
  smtp_to_addr: string;
  email_configured: boolean;
}

const settings = ref<Settings | null>(null);
const loading = ref(true);
const message = ref("");
const messageType = ref<"success" | "error">("success");

const githubToken = ref("");
const smtpPassword = ref("");
const currentPassword = ref("");
const newPassword = ref("");

const scheduleOptions = computed(() => [
  { title: t("settings.schedule.options.hourly"), value: "hourly" },
  { title: t("settings.schedule.options.daily"), value: "daily" },
  { title: t("settings.schedule.options.weekly"), value: "weekly" },
  { title: t("settings.schedule.options.monthly"), value: "monthly" },
  { title: t("settings.schedule.options.custom"), value: "custom" },
]);

const weekdayOptions = computed(() => [
  { title: t("settings.schedule.weekdays.mon"), value: "mon" },
  { title: t("settings.schedule.weekdays.tue"), value: "tue" },
  { title: t("settings.schedule.weekdays.wed"), value: "wed" },
  { title: t("settings.schedule.weekdays.thu"), value: "thu" },
  { title: t("settings.schedule.weekdays.fri"), value: "fri" },
  { title: t("settings.schedule.weekdays.sat"), value: "sat" },
  { title: t("settings.schedule.weekdays.sun"), value: "sun" },
]);

onMounted(async () => {
  try {
    settings.value = await api.getSettings();
  } finally {
    loading.value = false;
  }
});

function showMsg(msg: string, type: "success" | "error") {
  message.value = msg;
  messageType.value = type;
}

async function saveGithub() {
  const data: Record<string, string> = { github_username: settings.value!.github_username };
  if (githubToken.value) data.github_token = githubToken.value;
  try {
    const res = await api.saveSetting("/api/settings/github", data);
    if (res.success) {
      githubToken.value = "";
      settings.value!.github_token_set = true;
      showMsg(t("settings.saveSuccess"), "success");
    } else {
      showMsg(res.message, "error");
    }
  } catch {
    showMsg(t("settings.saveError"), "error");
  }
}

async function saveSchedule() {
  if (!settings.value) return;
  const data: Record<string, string> = {
    check_schedule: settings.value.check_schedule,
    check_weekday: settings.value.check_weekday,
    check_time: settings.value.check_time,
    custom_interval_minutes: settings.value.custom_interval_minutes,
    check_monthday: settings.value.check_monthday || "1",
  };
  try {
    const res = await api.saveSetting("/api/settings/schedule", data);
    showMsg(res.success ? t("settings.saveSuccess") : res.message, res.success ? "success" : "error");
  } catch {
    showMsg(t("settings.saveError"), "error");
  }
}

async function saveReleasePolicy() {
  if (!settings.value) return;
  try {
    const res = await api.saveSetting("/api/settings/release-policy", {
      monitor_prereleases: settings.value.monitor_prereleases,
      fallback_to_tags: settings.value.fallback_to_tags,
      ignore_archived: settings.value.ignore_archived,
      allow_initial_notifications: settings.value.allow_initial_notifications,
      send_no_updates_email: settings.value.send_no_updates_email,
      github_request_delay: settings.value.github_request_delay,
    });
    showMsg(res.success ? t("settings.saveSuccess") : res.message, res.success ? "success" : "error");
  } catch {
    showMsg(t("settings.saveError"), "error");
  }
}

async function saveEmail() {
  if (!settings.value) return;
  const data: Record<string, string> = {
    smtp_host: settings.value.smtp_host,
    smtp_port: settings.value.smtp_port,
    smtp_username: settings.value.smtp_username,
    smtp_use_tls: settings.value.smtp_use_tls,
    smtp_from_addr: settings.value.smtp_from_addr,
    smtp_to_addr: settings.value.smtp_to_addr,
  };
  if (smtpPassword.value) data.smtp_password = smtpPassword.value;
  try {
    const res = await api.saveSetting("/api/settings/email", data);
    if (res.success) {
      smtpPassword.value = "";
      settings.value!.smtp_password_set = true;
      showMsg(t("settings.saveSuccess"), "success");
    } else {
      showMsg(res.message, "error");
    }
  } catch {
    showMsg(t("settings.saveError"), "error");
  }
}

async function testEmail() {
  try {
    const res = await api.testEmail();
    showMsg(res.message, res.success ? "success" : "error");
  } catch {
    showMsg(t("settings.saveError"), "error");
  }
}

async function changePassword() {
  if (!currentPassword.value || !newPassword.value) {
    showMsg(t("settings.password.empty"), "error");
    return;
  }
  if (newPassword.value.length < 8) {
    showMsg(t("settings.password.minLength"), "error");
    return;
  }
  try {
    const res = await api.changePassword(currentPassword.value, newPassword.value);
    showMsg(res.message, res.success ? "success" : "error");
    if (res.success) {
      currentPassword.value = "";
      newPassword.value = "";
    }
  } catch {
    showMsg(t("settings.saveError"), "error");
  }
}
</script>

<template>
  <div>
    <div class="d-flex align-center ga-3 mb-6">
      <v-avatar size="32" color="primary-container" variant="flat" rounded="lg">
        <v-icon color="primary" size="20">mdi-cog-outline</v-icon>
      </v-avatar>
      <h1 class="text-h6 font-weight-bold">{{ t("settings.title") }}</h1>
    </div>

    <v-alert v-if="message" :type="messageType" closable class="mb-4" @click:close="message = ''">
      {{ message }}
    </v-alert>

    <v-skeleton-loader v-if="loading" type="card, card, card" />

    <template v-if="settings">
      <!-- GitHub -->
      <v-card variant="flat" color="surface-container" class="mb-4 rounded-xl">
        <v-card-item class="pa-4 pb-0">
          <template #prepend>
            <v-icon color="on-surface-variant" size="20">mdi-github</v-icon>
          </template>
          <v-card-title class="text-body-2 font-weight-bold text-on-surface">{{ t("settings.sections.github") }}</v-card-title>
        </v-card-item>
        <v-card-text class="pa-4">
          <v-row dense>
            <v-col cols="12" sm="6">
              <v-text-field v-model="settings.github_username" :label="t('settings.github.username')" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="githubToken"
                :label="t('settings.github.token')"
                type="password"
                :hint="t('settings.github.tokenGuide')"
                persistent-hint
              >
                <template #append-inner>
                  <v-chip v-if="settings.github_token_set" color="success" size="x-small" variant="tonal">{{ t("settings.github.tokenSet") }}</v-chip>
                </template>
              </v-text-field>
            </v-col>
          </v-row>
          <v-btn color="primary" size="small" class="mt-2" @click="saveGithub">{{ t("settings.github.save") }}</v-btn>
        </v-card-text>
      </v-card>

      <!-- Schedule -->
      <v-card variant="flat" color="surface-container" class="mb-4 rounded-xl">
        <v-card-item class="pa-4 pb-0">
          <template #prepend>
            <v-icon color="on-surface-variant" size="20">mdi-calendar-clock</v-icon>
          </template>
          <v-card-title class="text-body-2 font-weight-bold text-on-surface">{{ t("settings.sections.schedule") }}</v-card-title>
        </v-card-item>
        <v-card-text class="pa-4">
          <v-row dense>
            <v-col cols="12" sm="6" md="3">
              <v-select v-model="settings.check_schedule" :label="t('settings.schedule.frequency')" :items="scheduleOptions" />
            </v-col>
            <v-col cols="12" sm="6" md="3" v-if="settings.check_schedule === 'weekly'">
              <v-select v-model="settings.check_weekday" :label="t('settings.schedule.weekday')" :items="weekdayOptions" />
            </v-col>
            <v-col cols="12" sm="6" md="3" v-if="settings.check_schedule === 'monthly'">
              <v-text-field v-model="settings.check_monthday" :label="t('settings.schedule.monthday')" type="number" min="1" max="31" />
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-text-field v-model="settings.check_time" :label="t('settings.schedule.time')" type="time" />
            </v-col>
            <v-col cols="12" sm="6" md="3" v-if="settings.check_schedule === 'custom'">
              <v-text-field v-model="settings.custom_interval_minutes" :label="t('settings.schedule.interval')" type="number" min="15" />
            </v-col>
          </v-row>
          <v-btn color="primary" size="small" class="mt-1" @click="saveSchedule">{{ t("settings.schedule.save") }}</v-btn>
        </v-card-text>
      </v-card>

      <!-- Release Policy -->
      <v-card variant="flat" color="surface-container" class="mb-4 rounded-xl">
        <v-card-item class="pa-4 pb-0">
          <template #prepend>
            <v-icon color="on-surface-variant" size="20">mdi-tune-variant</v-icon>
          </template>
          <v-card-title class="text-body-2 font-weight-bold text-on-surface">{{ t("settings.sections.releasePolicy") }}</v-card-title>
        </v-card-item>
        <v-card-text class="pa-4">
          <v-row dense>
            <v-col cols="6" sm="4" md="3">
              <v-checkbox v-model="settings.monitor_prereleases" true-value="true" false-value="false" :label="t('settings.releasePolicy.monitorPrereleases')" density="compact" hide-details />
            </v-col>
            <v-col cols="6" sm="4" md="3">
              <v-checkbox v-model="settings.fallback_to_tags" true-value="true" false-value="false" :label="t('settings.releasePolicy.fallbackToTags')" density="compact" hide-details />
            </v-col>
            <v-col cols="6" sm="4" md="3">
              <v-checkbox v-model="settings.ignore_archived" true-value="true" false-value="false" :label="t('settings.releasePolicy.ignoreArchived')" density="compact" hide-details />
            </v-col>
            <v-col cols="6" sm="4" md="3">
              <v-checkbox v-model="settings.allow_initial_notifications" true-value="true" false-value="false" :label="t('settings.releasePolicy.allowInitialNotifications')" density="compact" hide-details />
            </v-col>
            <v-col cols="6" sm="4" md="3">
              <v-checkbox v-model="settings.send_no_updates_email" true-value="true" false-value="false" :label="t('settings.releasePolicy.sendNoUpdatesEmail')" density="compact" hide-details />
            </v-col>
            <v-col cols="6" sm="4" md="3">
              <v-text-field v-model="settings.github_request_delay" :label="t('settings.releasePolicy.apiDelay')" type="number" step="0.1" min="0.01" density="compact" />
            </v-col>
          </v-row>
          <v-btn color="primary" size="small" class="mt-1" @click="saveReleasePolicy">{{ t("settings.releasePolicy.save") }}</v-btn>
        </v-card-text>
      </v-card>

      <!-- Email -->
      <v-card variant="flat" color="surface-container" class="mb-4 rounded-xl">
        <v-card-item class="pa-4 pb-0">
          <template #prepend>
            <v-icon color="on-surface-variant" size="20">mdi-email-outline</v-icon>
          </template>
          <v-card-title class="text-body-2 font-weight-bold text-on-surface">{{ t("settings.sections.email") }}</v-card-title>
        </v-card-item>
        <v-card-text class="pa-4">
          <v-row dense>
            <v-col cols="12" sm="6" md="4">
              <v-text-field v-model="settings.smtp_host" :label="t('settings.email.host')" placeholder="smtp.example.com" density="compact" />
            </v-col>
            <v-col cols="12" sm="6" md="4">
              <v-text-field v-model="settings.smtp_port" :label="t('settings.email.port')" type="number" density="compact" />
            </v-col>
            <v-col cols="12" sm="6" md="4">
              <v-text-field v-model="settings.smtp_username" :label="t('settings.email.username')" density="compact" />
            </v-col>
            <v-col cols="12" sm="6" md="4">
              <v-text-field v-model="smtpPassword" :label="t('settings.email.password')" type="password" :hint="settings.smtp_password_set ? t('settings.email.passwordSet') : undefined" persistent-hint density="compact" />
            </v-col>
            <v-col cols="6" sm="4" md="4">
              <v-checkbox v-model="settings.smtp_use_tls" true-value="true" false-value="false" :label="t('settings.email.useTls')" density="compact" hide-details />
            </v-col>
            <v-col cols="12" sm="6" md="4">
              <v-text-field v-model="settings.smtp_from_addr" :label="t('settings.email.fromAddr')" type="email" density="compact" />
            </v-col>
            <v-col cols="12" sm="6" md="4">
              <v-text-field v-model="settings.smtp_to_addr" :label="t('settings.email.toAddr')" type="email" density="compact" />
            </v-col>
          </v-row>
          <div class="d-flex ga-2 mt-1">
            <v-btn color="primary" size="small" @click="saveEmail">{{ t("settings.email.save") }}</v-btn>
            <v-btn v-if="settings.email_configured" variant="outlined" size="small" @click="testEmail">{{ t("settings.email.test") }}</v-btn>
          </div>
        </v-card-text>
      </v-card>

      <!-- Password -->
      <v-card variant="flat" color="surface-container" class="rounded-xl">
        <v-card-item class="pa-4 pb-0">
          <template #prepend>
            <v-icon color="on-surface-variant" size="20">mdi-lock-outline</v-icon>
          </template>
          <v-card-title class="text-body-2 font-weight-bold text-on-surface">{{ t("settings.sections.password") }}</v-card-title>
        </v-card-item>
        <v-card-text class="pa-4">
          <v-row dense>
            <v-col cols="12" sm="6">
              <v-text-field v-model="currentPassword" :label="t('settings.password.current')" type="password" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="newPassword" :label="t('settings.password.new')" type="password" />
            </v-col>
          </v-row>
          <v-btn color="primary" size="small" class="mt-1" @click="changePassword">{{ t("settings.password.change") }}</v-btn>
        </v-card-text>
      </v-card>
    </template>
  </div>
</template>
