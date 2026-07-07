<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api } from "../api";

interface Settings {
  github_username: string;
  github_token_set: boolean;
  check_schedule: string;
  check_weekday: string;
  check_time: string;
  custom_interval_minutes: string;
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
      showMsg("GitHub settings saved", "success");
    } else {
      showMsg(res.message, "error");
    }
  } catch (e) {
    showMsg(e instanceof Error ? e.message : "Failed to save", "error");
  }
}

async function saveSchedule() {
  if (!settings.value) return;
  const data: Record<string, string> = {
    check_schedule: settings.value.check_schedule,
    check_weekday: settings.value.check_weekday,
    check_time: settings.value.check_time,
    custom_interval_minutes: settings.value.custom_interval_minutes,
  };
  try {
    const res = await api.saveSetting("/api/settings/schedule", data);
    showMsg(res.success ? "Schedule saved" : res.message, res.success ? "success" : "error");
  } catch (e) {
    showMsg(e instanceof Error ? e.message : "Failed to save", "error");
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
    showMsg(res.success ? "Release policy saved" : res.message, res.success ? "success" : "error");
  } catch (e) {
    showMsg(e instanceof Error ? e.message : "Failed to save", "error");
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
      showMsg("Email settings saved", "success");
    } else {
      showMsg(res.message, "error");
    }
  } catch (e) {
    showMsg(e instanceof Error ? e.message : "Failed to save", "error");
  }
}

async function testEmail() {
  try {
    const res = await api.testEmail();
    showMsg(res.message, res.success ? "success" : "error");
  } catch (e) {
    showMsg(e instanceof Error ? e.message : "Test failed", "error");
  }
}

async function changePassword() {
  if (!currentPassword.value || !newPassword.value) {
    showMsg("Fill in both password fields", "error");
    return;
  }
  if (newPassword.value.length < 8) {
    showMsg("New password must be at least 8 characters", "error");
    return;
  }
  try {
    const res = await api.changePassword(currentPassword.value, newPassword.value);
    showMsg(res.message, res.success ? "success" : "error");
    if (res.success) {
      currentPassword.value = "";
      newPassword.value = "";
    }
  } catch (e) {
    showMsg(e instanceof Error ? e.message : "Failed to change password", "error");
  }
}
</script>

<template>
  <div>
    <div class="page-header">
      <h2>Settings</h2>
    </div>

    <div class="alert" :class="'alert-' + messageType" v-if="message">{{ message }}</div>

    <div v-if="loading" class="card">Loading...</div>

    <template v-if="settings">
      <div class="card settings-section">
        <h3>GitHub</h3>
        <div class="form-group">
          <label>Username</label>
          <input v-model="settings.github_username" placeholder="GitHub username" />
        </div>
        <div class="form-group">
          <label>Token</label>
          <input v-model="githubToken" type="password" placeholder="Leave blank to keep current" />
          <div class="hint" v-if="settings.github_token_set">Token is currently set</div>
        </div>
        <button class="btn btn-primary" @click="saveGithub">Save GitHub Settings</button>
      </div>

      <div class="card settings-section">
        <h3>Schedule</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Frequency</label>
            <select v-model="settings.check_schedule">
              <option value="weekly">Weekly</option>
              <option value="daily">Daily</option>
              <option value="hourly">Hourly</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          <div class="form-group" v-if="settings.check_schedule === 'weekly'">
            <label>Weekday</label>
            <select v-model="settings.check_weekday">
              <option value="mon">Monday</option>
              <option value="tue">Tuesday</option>
              <option value="wed">Wednesday</option>
              <option value="thu">Thursday</option>
              <option value="fri">Friday</option>
              <option value="sat">Saturday</option>
              <option value="sun">Sunday</option>
            </select>
          </div>
          <div class="form-group">
            <label>Time</label>
            <input v-model="settings.check_time" type="time" />
          </div>
          <div class="form-group" v-if="settings.check_schedule === 'custom'">
            <label>Interval (minutes, min 15)</label>
            <input v-model="settings.custom_interval_minutes" type="number" min="15" />
          </div>
        </div>
        <button class="btn btn-primary" @click="saveSchedule">Save Schedule</button>
      </div>

      <div class="card settings-section">
        <h3>Release / Tag Policy</h3>
        <div class="form-row">
          <div class="form-group">
            <label>
              <input type="checkbox" true-value="true" false-value="false" v-model="settings.monitor_prereleases" />
              Monitor pre-releases
            </label>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" true-value="true" false-value="false" v-model="settings.fallback_to_tags" />
              Fallback to tags
            </label>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" true-value="true" false-value="false" v-model="settings.ignore_archived" />
              Ignore archived repos
            </label>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" true-value="true" false-value="false" v-model="settings.allow_initial_notifications" />
              Allow initial notifications
            </label>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" true-value="true" false-value="false" v-model="settings.send_no_updates_email" />
              Send "no updates" email
            </label>
          </div>
          <div class="form-group">
            <label>API request delay (s)</label>
            <input v-model="settings.github_request_delay" type="number" step="0.1" min="0.01" />
          </div>
        </div>
        <button class="btn btn-primary" @click="saveReleasePolicy">Save Release Policy</button>
      </div>

      <div class="card settings-section">
        <h3>Email (SMTP)</h3>
        <div class="form-row">
          <div class="form-group">
            <label>SMTP Host</label>
            <input v-model="settings.smtp_host" placeholder="smtp.example.com" />
          </div>
          <div class="form-group">
            <label>SMTP Port</label>
            <input v-model="settings.smtp_port" type="number" />
          </div>
          <div class="form-group">
            <label>Username</label>
            <input v-model="settings.smtp_username" />
          </div>
          <div class="form-group">
            <label>Password</label>
            <input v-model="smtpPassword" type="password" placeholder="Leave blank to keep current" />
            <div class="hint" v-if="settings.smtp_password_set">Password is currently set</div>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" true-value="true" false-value="false" v-model="settings.smtp_use_tls" />
              Use TLS
            </label>
          </div>
          <div class="form-group">
            <label>From address</label>
            <input v-model="settings.smtp_from_addr" type="email" />
          </div>
          <div class="form-group">
            <label>To address</label>
            <input v-model="settings.smtp_to_addr" type="email" />
          </div>
        </div>
        <div style="display: flex; gap: 8px">
          <button class="btn btn-primary" @click="saveEmail">Save Email Settings</button>
          <button class="btn" @click="testEmail" v-if="settings.email_configured">Send Test Email</button>
        </div>
      </div>

      <div class="card settings-section">
        <h3>Change Password</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Current password</label>
            <input v-model="currentPassword" type="password" />
          </div>
          <div class="form-group">
            <label>New password (min 8 chars)</label>
            <input v-model="newPassword" type="password" />
          </div>
        </div>
        <button class="btn btn-primary" @click="changePassword">Change Password</button>
      </div>
    </template>
  </div>
</template>
