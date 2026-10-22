<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useDocument } from '@/api/queries';
import { library, type LibraryEntry } from '@/stores/library';
import { timeAgo } from '@/lib/format';
import StatusPill from '@/components/ui/StatusPill.vue';
import Icon from '@/components/ui/Icon.vue';

const props = defineProps<{ entry: LibraryEntry }>();
const router = useRouter();
const { data: doc, isError } = useDocument(() => props.entry.id);
</script>

<template>
  <tr class="row" tabindex="0" @click="router.push(`/documents/${entry.id}`)" @keydown.enter="router.push(`/documents/${entry.id}`)">
    <td>
      <div class="file">
        <span class="ficon"><Icon name="file" :size="16" /></span>
        <span class="fname">{{ entry.filename }}</span>
      </div>
    </td>
    <td>
      <span v-if="isError" class="pill pill-bad">Unavailable</span>
      <StatusPill v-else-if="doc" :status="doc.status" />
      <span v-else class="skeleton" style="display: inline-block; width: 70px; height: 22px" />
    </td>
    <td class="num hide-sm">{{ doc?.total_pages ?? '—' }}</td>
    <td class="num hide-sm">{{ doc?.total_chunks ?? '—' }}</td>
    <td class="muted hide-sm">{{ timeAgo(entry.addedAt) }}</td>
    <td class="actions">
      <button class="btn btn-ghost btn-icon btn-sm" aria-label="Remove from library" @click.stop="library.remove(entry.id)">
        <Icon name="trash" />
      </button>
    </td>
  </tr>
</template>

<style scoped>
.row { cursor: pointer; transition: background 0.12s; }
.row:hover { background: var(--surface-2); }
td { padding: 12px 16px; border-top: 1px solid var(--border); vertical-align: middle; }
.file { display: flex; align-items: center; gap: 12px; min-width: 0; }
.ficon { display: grid; place-items: center; width: 32px; height: 32px; border-radius: 8px; background: var(--sunken); color: var(--text-2); }
.fname { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 380px; }
.num { font-variant-numeric: tabular-nums; color: var(--text-2); }
.muted { color: var(--text-3); }
.actions { text-align: right; width: 56px; }
@media (max-width: 700px) { .hide-sm { display: none; } .fname { max-width: 200px; } }
</style>
