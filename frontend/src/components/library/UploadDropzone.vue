<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useUpload } from '@/api/queries';
import { formatBytes } from '@/lib/format';
import { toast } from '@/lib/toast';
import Icon from '@/components/ui/Icon.vue';

const MAX_MB = 50;
const router = useRouter();
const upload = useUpload();
const input = ref<HTMLInputElement>();
const dragging = ref(false);
const fileName = ref('');
const fileSize = ref(0);

function handle(file?: File) {
  if (!file || upload.isPending.value) return;
  if (!file.name.toLowerCase().endsWith('.pdf')) return toast('error', 'Only PDF files are supported.');
  if (file.size > MAX_MB * 1024 * 1024) return toast('error', `File exceeds the ${MAX_MB} MB limit.`);

  fileName.value = file.name;
  fileSize.value = file.size;
  upload.mutate(file, {
    onSuccess: (res) => {
      if (res.status === 'ALREADY_EXISTS') toast('info', 'This contract was already uploaded — opening it.');
      router.push(`/documents/${res.document_id}`);
    },
    onError: (e) => toast('error', e.message),
  });
}

function onDrop(e: DragEvent) {
  dragging.value = false;
  handle(e.dataTransfer?.files?.[0]);
}
function onPick(e: Event) {
  const el = e.target as HTMLInputElement;
  handle(el.files?.[0]);
  el.value = '';
}
</script>

<template>
  <div
    class="drop"
    :class="{ dragging, busy: upload.isPending.value }"
    role="button"
    tabindex="0"
    aria-label="Upload a contract PDF"
    @click="input?.click()"
    @keydown.enter.space.prevent="input?.click()"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="onDrop"
  >
    <input ref="input" type="file" accept="application/pdf,.pdf" class="sr-only" tabindex="-1" @change="onPick" />

    <template v-if="upload.isPending.value">
      <span class="spinner" style="color: var(--accent)" />
      <div>
        <div class="title">Uploading {{ fileName }}</div>
        <div class="sub">{{ formatBytes(fileSize) }}</div>
      </div>
    </template>
    <template v-else>
      <span class="icon"><Icon name="upload" :size="20" /></span>
      <div>
        <div class="title">Drop a contract PDF here, or <span class="link">browse</span></div>
        <div class="sub">PDF up to {{ MAX_MB }} MB · text is extracted and indexed for review</div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.drop {
  display: flex; align-items: center; gap: 16px; padding: 22px 24px;
  border: 1.5px dashed var(--border-strong); border-radius: var(--radius-lg);
  background: var(--surface); cursor: pointer; transition: border-color 0.15s, background 0.15s;
}
.drop:hover, .drop.dragging { border-color: var(--accent); background: var(--accent-soft); }
.drop.busy { cursor: progress; pointer-events: none; }
.icon { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 10px; background: var(--accent-soft); color: var(--accent-text); }
.title { font-weight: 550; }
.link { color: var(--accent-text); text-decoration: underline; text-underline-offset: 3px; }
.sub { color: var(--text-3); font-size: 13px; margin-top: 2px; }
</style>
