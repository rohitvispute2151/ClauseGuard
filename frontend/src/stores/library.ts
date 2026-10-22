import { reactive, watch } from 'vue';

export interface LibraryEntry {
  id: string;
  filename: string;
  addedAt: string;
  extractionId?: string;
}

const KEY = 'clauseguard:library:v1';
const MAX = 25;

function load(): LibraryEntry[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) ?? '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

const state = reactive({ entries: load() });

watch(
  () => state.entries,
  (entries) => {
    try {
      localStorage.setItem(KEY, JSON.stringify(entries));
    } catch {
      /* storage unavailable */
    }
  },
  { deep: true },
);

/** The backend has no "list documents" endpoint, so the library is remembered client-side. */
export const library = {
  get entries() {
    return state.entries;
  },
  add(entry: Pick<LibraryEntry, 'id' | 'filename'>) {
    const existing = state.entries.find((e) => e.id === entry.id);
    if (existing) {
      state.entries = [existing, ...state.entries.filter((e) => e !== existing)];
      return;
    }
    state.entries = [{ ...entry, addedAt: new Date().toISOString() }, ...state.entries].slice(0, MAX);
  },
  remove(id: string) {
    state.entries = state.entries.filter((e) => e.id !== id);
  },
  extractionId(documentId: string) {
    return state.entries.find((e) => e.id === documentId)?.extractionId;
  },
  setExtractionId(documentId: string, extractionId: string) {
    const entry = state.entries.find((e) => e.id === documentId);
    if (entry) entry.extractionId = extractionId;
  },
};
