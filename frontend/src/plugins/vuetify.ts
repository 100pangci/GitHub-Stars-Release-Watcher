import "vuetify/styles";
import "@mdi/font/css/materialdesignicons.css";
import { createVuetify } from "vuetify";
import * as components from "vuetify/components";
import * as directives from "vuetify/directives";

const md3DarkTheme = {
  dark: true,
  colors: {
    // MD3 Core
    background: "#0b0e14",
    "on-background": "#e2e8f0",
    surface: "#131820",
    "on-surface": "#e2e8f0",
    "surface-variant": "#1c2330",
    "on-surface-variant": "#94a3b8",
    "surface-container-lowest": "#0a0d12",
    "surface-container-low": "#0f141d",
    "surface-container": "#181e2a",
    "surface-container-high": "#1e2535",
    "surface-container-highest": "#252d40",
    "surface-bright": "#2a3347",
    "surface-dim": "#0b0e14",

    // MD3 Primary
    primary: "#4a7cff",
    "on-primary": "#ffffff",
    "primary-container": "#1a2a4a",
    "on-primary-container": "#b3c7ff",

    // MD3 Secondary
    secondary: "#6b96ff",
    "on-secondary": "#ffffff",
    "secondary-container": "#1a2a4a",
    "on-secondary-container": "#b3c7ff",

    // MD3 Tertiary
    tertiary: "#c084fc",
    "on-tertiary": "#000000",
    "tertiary-container": "#2e1a4a",
    "on-tertiary-container": "#e9d5ff",

    // MD3 Error
    error: "#f87171",
    "on-error": "#ffffff",
    "error-container": "#4a1a1a",
    "on-error-container": "#fca5a5",

    // MD3 Success
    success: "#34d399",
    "on-success": "#ffffff",
    "success-container": "#143a2a",
    "on-success-container": "#86efac",

    // MD3 Warning
    warning: "#fbbf24",
    "on-warning": "#000000",
    "warning-container": "#3a2a14",
    "on-warning-container": "#fde68a",

    // MD3 Info
    info: "#60a5fa",
    "on-info": "#000000",
    "info-container": "#1a2a4a",
    "on-info-container": "#b3c7ff",

    // MD3 Outline
    outline: "#2a3347",
    "outline-variant": "#1c2330",

    // Legacy aliases (for Vuetify compat)
    "primary-darken-1": "#3b6ae0",
    border: "#232b38",
  },
};

export const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: "md3Dark",
    themes: {
      md3Dark: md3DarkTheme,
    },
  },
  defaults: {
    VApp: {
      style: "background: rgb(var(--v-theme-surface-dim)); color: rgb(var(--v-theme-on-surface));",
    },
    VCard: {
      elevation: 0,
      rounded: "xl",
    },
    VBtn: {
      rounded: "pill",
      variant: "tonal",
      elevation: 0,
    },
    VTextField: {
      variant: "outlined",
      density: "comfortable",
      hideDetails: "auto",
    },
    VSelect: {
      variant: "outlined",
      density: "comfortable",
      hideDetails: "auto",
    },
    VTextarea: {
      variant: "outlined",
      density: "comfortable",
      hideDetails: "auto",
    },
    VCheckbox: {
      density: "comfortable",
      hideDetails: "auto",
    },
    VChip: {
      rounded: "pill",
      size: "x-small",
    },
    VAlert: {
      rounded: "lg",
      variant: "tonal",
    },
    VList: {
      density: "compact",
    },
    VListItem: {
      rounded: "xl",
    },
    VTable: {
      density: "comfortable",
    },
    VNavigationDrawer: {
      floating: false,
    },
    VDivider: {
      thickness: 1,
    },
  },
});
