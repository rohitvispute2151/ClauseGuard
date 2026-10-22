import { reactive } from 'vue';

export interface Toast {
  id: number;
  kind: 'success' | 'error' | 'info';
  message: string;
}

export const toasts = reactive<Toast[]>([]);
let n = 0;

export function toast(kind: Toast['kind'], message: string, ms = 4500) {
  const id = n++;
  toasts.push({ id, kind, message });
  setTimeout(() => {
    const i = toasts.findIndex((t) => t.id === id);
    if (i >= 0) toasts.splice(i, 1);
  }, ms);
}
