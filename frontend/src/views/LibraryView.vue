<script setup lang="ts">
import { library } from '@/stores/library';
import UploadDropzone from '@/components/library/UploadDropzone.vue';
import DocumentRow from '@/components/library/DocumentRow.vue';
import Icon from '@/components/ui/Icon.vue';

const features = [
  { icon: 'review', title: 'Structured clause extraction', text: 'Ten clause types pulled into typed records with page numbers and confidence scores.' },
  { icon: 'shield', title: 'Verified citations', text: 'Every quote is checked verbatim against the source text, so nothing is paraphrased into existence.' },
  { icon: 'message', title: 'Grounded Q&A', text: 'Ask in plain English. Answers stream in real time and link back to the exact passage.' },
] as const;
</script>

<template>
  <div class="page">
    <header class="head">
      <h1>Read every clause. <em>Trust every quote.</em></h1>
      <p>Upload an agreement to extract key clauses and ask questions — every answer backed by a verifiable quote.</p>
    </header>

    <UploadDropzone />

    <section v-if="library.entries.length" class="card table-card" aria-label="Your documents">
      <div class="table-head">
        <h2>Your documents</h2>
        <span class="count">{{ library.entries.length }}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Name</th><th>Status</th><th class="hide-sm">Pages</th><th class="hide-sm">Chunks</th><th class="hide-sm">Added</th><th />
          </tr>
        </thead>
        <tbody>
          <DocumentRow v-for="e in library.entries" :key="e.id" :entry="e" />
        </tbody>
      </table>
    </section>

    <section v-else class="features">
      <article v-for="f in features" :key="f.title" class="card feature">
        <span class="ficon"><Icon :name="f.icon" :size="18" /></span>
        <h3>{{ f.title }}</h3>
        <p>{{ f.text }}</p>
      </article>
    </section>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 28px; }
.head h1 { font-size: 40px; line-height: 1.1; max-width: 18ch; }
.head em { display: block; font-style: italic; color: var(--accent-text); }
.head p { color: var(--text-2); margin-top: 14px; max-width: 58ch; font-size: 16px; }
.table-card { overflow: hidden; }
.table-head { display: flex; align-items: center; gap: 10px; padding: 16px 16px 14px; }
.table-head h2 { font-size: 15px; }
.count { font-size: 12px; color: var(--text-3); background: var(--sunken); padding: 1px 8px; border-radius: 999px; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 8px 16px; font-size: 11.5px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-3); background: var(--surface-2); border-top: 1px solid var(--border); }
.features { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
.feature { padding: 20px; display: flex; flex-direction: column; gap: 8px; }
.feature h3 { font-size: 14.5px; }
.feature p { color: var(--text-2); font-size: 13.5px; }
.ficon { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 9px; background: var(--accent-soft); color: var(--accent-text); margin-bottom: 4px; }
@media (max-width: 700px) { .hide-sm { display: none; } }
</style>
