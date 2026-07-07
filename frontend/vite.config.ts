import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import vuetify from "vite-plugin-vuetify";

export default defineConfig({
  plugins: [vue(), vuetify({ autoImport: true })],
  server: {
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: false },
      "/login": { target: "http://localhost:8000", changeOrigin: false },
      "/logout": { target: "http://localhost:8000", changeOrigin: false },
    },
  },
});
