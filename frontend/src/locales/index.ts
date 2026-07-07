import { ref, type Ref } from "vue";
import type { Messages } from "./types";
import { zh } from "./zh";
import { en } from "./en";
import { ja } from "./ja";

export type Locale = "zh" | "en" | "ja";

const STORAGE_KEY = "gsrw_locale";

const locales: Record<Locale, Messages> = { zh, en, ja };

function getInitialLocale(): Locale {
  let stored: string | null = null;
  try { stored = localStorage.getItem(STORAGE_KEY); } catch { /* storage unavailable */ }
  if (stored === "zh" || stored === "en" || stored === "ja") return stored;
  const lang = navigator.language.toLowerCase();
  if (lang.startsWith("zh")) return "zh";
  if (lang.startsWith("ja")) return "ja";
  return "en";
}

export const locale: Ref<Locale> = ref(getInitialLocale());

export function setLocale(l: Locale) {
  locale.value = l;
  try { localStorage.setItem(STORAGE_KEY, l); } catch { /* storage unavailable */ }
}

export function t<K extends string>(path: K): string {
  const msg = locales[locale.value] ?? en;
  const keys = path.split(".");
  let result: unknown = msg;
  for (const k of keys) {
    if (result && typeof result === "object" && k in result) {
      result = (result as Record<string, unknown>)[k];
    } else {
      return path;
    }
  }
  return typeof result === "string" ? result : path;
}
