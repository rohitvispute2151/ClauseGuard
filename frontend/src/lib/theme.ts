import { ref } from 'vue';

type Theme = 'light' | 'dark';
const KEY = 'clauseguard:theme';

function initial(): Theme {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved === 'light' || saved === 'dark') return saved;
  } catch { /* ignore */ }
  return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export const theme = ref<Theme>(initial());

function apply() {
  document.documentElement.dataset.theme = theme.value;
}

export function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark';
  try { localStorage.setItem(KEY, theme.value); } catch { /* ignore */ }
  apply();
}

apply();
