async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok && data.error) throw new Error(data.error);
  return data;
}

export const api = {
  login(password: string) {
    return request<{ success: boolean; message: string }>("/login", {
      method: "POST",
      body: new URLSearchParams({ password }),
    });
  },

  logout() {
    return request<{ success: boolean; message: string }>("/logout", {
      method: "POST",
    });
  },

  getDashboard() {
    return request<{
      total_stars: number;
      active_repos: number;
      inactive_repos: number;
      week_updates: number;
      last_check: string | null;
      next_check: string | null;
      github_configured: boolean;
    }>("/api/dashboard/stats");
  },

  getRepos(search?: string, filter?: string) {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (filter) params.set("filter", filter);
    return request<
      Array<{
        id: number;
        full_name: string;
        html_url: string;
        description: string;
        language: string;
        archived: boolean;
        active: boolean;
        pushed_at: string | null;
        last_synced_at: string | null;
        last_checked_at: string | null;
        current_version: string | null;
        current_source: string | null;
        current_version_url: string | null;
      }>
    >(`/api/repos?${params.toString()}`);
  },

  getEvents(repo_id?: string) {
    const params = new URLSearchParams();
    if (repo_id) params.set("repo_id", repo_id);
    return request<
      Array<{
        id: number;
        title: string;
        message: string;
        event_type: string;
        created_at: string;
        repo_name: string;
        repo_url: string;
      }>
    >(`/api/events?${params.toString()}`);
  },

  getSettings() {
    return request<any>("/api/settings");
  },

  saveSetting(endpoint: string, data: Record<string, string>) {
    return request<{ success: boolean; message: string }>(endpoint, {
      method: "POST",
      body: new URLSearchParams(data),
    });
  },

  changePassword(current_password: string, new_password: string) {
    return request<{ success: boolean; message: string }>("/api/change-password", {
      method: "POST",
      body: new URLSearchParams({ current_password, new_password }),
    });
  },

  testEmail() {
    return request<{ success: boolean; message: string }>("/api/settings/test-email", {
      method: "POST",
    });
  },
};
