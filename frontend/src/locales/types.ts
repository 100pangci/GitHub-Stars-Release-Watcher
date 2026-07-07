export interface Messages {
  app: { title: string; subtitle: string };
  sidebar: {
    dashboard: string;
    repos: string;
    events: string;
    settings: string;
    logout: string;
  };
  login: {
    title: string;
    password: string;
    placeholder: string;
    login: string;
    loggingIn: string;
    error: { invalid: string; rateLimit: string };
  };
  dashboard: {
    title: string;
    loading: string;
    starredRepos: string;
    active: string;
    updates7d: string;
    github: string;
    configured: string;
    notSet: string;
    status: string;
    lastCheck: string;
    never: string;
    inactiveRepos: string;
    chart: {
      title: string;
      synced: string;
      updates: string;
      noData: string;
    };
  };
  repos: {
    title: string;
    search: string;
    noRepos: string;
    loading: string;
    filter: { all: string; active: string; inactive: string; archived: string; hasUpdates: string };
    columns: { name: string; language: string; status: string; version: string };
    status: { archived: string; active: string; inactive: string };
  };
  events: {
    title: string;
    filterPlaceholder: string;
    noEvents: string;
    loading: string;
    release: string;
    tag: string;
  };
  settings: {
    title: string;
    loading: string;
    saveSuccess: string;
    saveError: string;
    sections: {
      github: string;
      schedule: string;
      releasePolicy: string;
      email: string;
      password: string;
    };
    github: {
      username: string;
      token: string;
      tokenHint: string;
      tokenGuide: string;
      tokenGuideLink: string;
      tokenSet: string;
      save: string;
    };
    schedule: {
      frequency: string;
      weekday: string;
      time: string;
      interval: string;
      monthday: string;
      save: string;
      options: { weekly: string; daily: string; hourly: string; monthly: string; custom: string };
      weekdays: { mon: string; tue: string; wed: string; thu: string; fri: string; sat: string; sun: string };
    };
    releasePolicy: {
      monitorPrereleases: string;
      fallbackToTags: string;
      ignoreArchived: string;
      allowInitialNotifications: string;
      sendNoUpdatesEmail: string;
      apiDelay: string;
      save: string;
    };
    email: {
      host: string;
      port: string;
      username: string;
      password: string;
      passwordHint: string;
      passwordSet: string;
      useTls: string;
      fromAddr: string;
      toAddr: string;
      save: string;
      test: string;
    };
    password: {
      current: string;
      new: string;
      change: string;
      empty: string;
      minLength: string;
    };
  };
  language: {
    label: string;
    zh: string;
    en: string;
    ja: string;
  };
}
