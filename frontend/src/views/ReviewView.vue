<script setup lang="ts">
import { computed, ref } from 'vue';
import { useExtraction } from '@/api/queries';
import { CLAUSES, clauseMeta } from '@/lib/clauses';
import { formatCost, formatLatency, formatNumber } from '@/lib/format';
import { toast } from '@/lib/toast';
import type { ClauseType } from '@/types/api';
import ClauseCard from '@/components/review/ClauseCard.vue';
import Icon from '@/components/ui/Icon.vue';

const props = defineProps<{ id: string }>();
const { data, run, isRestoring } = useExtraction(() => props.id);

const selected = ref<Set<ClauseType>>(new Set(CLAUSES.map((c) => c.id)));
const filter = ref<'all' | 'found' | 'missing' | 'unverified'>('all');

function toggle(id: ClauseType) {
  const next = new Set(selected.value);
  if (next.has(id)) next.size > 1 && next.delete(id);
  else next.add(id);
  selected.value = next;
}

function start() {
  run.mutate([...selected.value], {
    onError: (e) => toast('error', e.message),
  });
}

const results = computed(() => data.value?.clause_results ?? []);
const found = computed(() => results.value.filter((c) => c.is_present));
const highRisk = computed(() => found.value.filter((c) => clauseMeta(c.clause_type).risk === 'high'));
const verified = computed(() => found.value.filter((c) => c.citation_verified));
const avgConf = computed(() =>
  found.value.length ? Math.round((found.value.reduce((s, c) => s + c.confidence, 0) / found.value.length) * 100) : 0,
);

const visible = computed(() => {
  const order = { high: 0, medium: 1, standard: 2 };
  const list = results.value.filter((c) =>
    filter.value === 'found' ? c.is_present
    : filter.value === 'missing' ? !c.is_present
    : filter.value === 'unverified' ? c.is_present && !c.citation_verified
    : true,
  );
  // Present clauses first, then by risk, so the important findings lead.
  return [...list].sort(
    (a, b) =>
      Number(b.is_present) - Number(a.is_present) ||
      order[clauseMeta(a.clause_type).risk] - order[clauseMeta(b.clause_type).risk],
  );
});

const filters = computed(() => [
  { key: 'all', label: 'All', n: results.value.length },
  { key: 'found', label: 'Found', n: found.value.length },
  { key: 'missing', label: 'Not found', n: results.value.length - found.value.length },
  { key: 'unverified', label: 'Unverified', n: found.value.length - verified.value.length },
] as const);

const stats = computed(() => [
  { label: 'Clauses found', value: `${found.value.length}`, sub: `of ${results.value.length} checked` },
  { label: 'High-risk clauses', value: `${highRisk.value.length}`, sub: 'termination, liability, indemnity, IP', tone: highRisk.value.length ? 'warn' : '' },
  { label: 'Citations verified', value: `${verified.value.length}/${found.value.length}`, sub: 'matched verbatim to source' },
  { label: 'Avg. confidence', value: `${avgConf.value}%`, sub: 'across found clauses' },
]);
</script>

<template>
  <div class="review">
    <section class="card config" aria-label="Clause selection">
      <div class="cfg-head">
        <div>
          <h2>Clauses to analyze</h2>
          <p>{{ selected.size }} of {{ CLAUSES.length }} selected</p>
        </div>
        <div class="cfg-actions">
          <button class="btn btn-ghost btn-sm" @click="selected = new Set(CLAUSES.map((c) => c.id))">Select all</button>
          <button class="btn btn-primary" :disabled="run.isPending.value" @click="start">
            <span v-if="run.isPending.value" class="spinner" />
            <Icon v-else :name="data ? 'refresh' : 'review'" />
            {{ run.isPending.value ? 'Analyzing…' : data ? 'Re-run analysis' : 'Run analysis' }}
          </button>
        </div>
      </div>
      <div class="chips">
        <button
          v-for="c in CLAUSES"
          :key="c.id"
          class="chip"
          :class="{ on: selected.has(c.id) }"
          :aria-pressed="selected.has(c.id)"
          :title="c.description"
          @click="toggle(c.id)"
        >
          <Icon v-if="selected.has(c.id)" name="check" :size="13" />
          {{ c.label }}
        </button>
      </div>
    </section>

    <!-- Loading -->
    <section v-if="run.isPending.value || isRestoring" class="stack" aria-busy="true">
      <p v-if="run.isPending.value" class="progress">
        Reading the contract and verifying each quote against the source. This usually takes under a minute.
      </p>
      <div v-for="n in 4" :key="n" class="card ghost">
        <div class="skeleton" style="height: 18px; width: 30%" />
        <div class="skeleton" style="height: 14px; width: 90%; margin-top: 14px" />
        <div class="skeleton" style="height: 56px; margin-top: 12px" />
      </div>
    </section>

    <!-- Empty -->
    <section v-else-if="!data" class="card empty">
      <span class="eicon"><Icon name="review" :size="22" /></span>
      <h2>No analysis yet</h2>
      <p>Choose the clauses you care about and run the analysis. Results are cached, so re-opening this document is instant.</p>
    </section>

    <!-- Results -->
    <template v-else>
      <div v-if="data.status !== 'COMPLETED'" class="banner" :class="data.status === 'FAILED' ? 'bad' : 'warn'" role="alert">
        <Icon name="alert" />
        {{ data.status === 'FAILED'
          ? 'The analysis failed. Try running it again.'
          : 'Some clauses could not be analyzed. Results below may be incomplete — re-run to retry.' }}
      </div>

      <section class="stats" aria-label="Summary">
        <div v-for="s in stats" :key="s.label" class="card stat">
          <div class="eyebrow">{{ s.label }}</div>
          <div class="value" :class="s.tone">{{ s.value }}</div>
          <div class="sub">{{ s.sub }}</div>
        </div>
      </section>

      <div class="toolbar">
        <div class="seg" role="tablist" aria-label="Filter clauses">
          <button v-for="f in filters" :key="f.key" role="tab" :aria-selected="filter === f.key" :class="{ on: filter === f.key }" @click="filter = f.key">
            {{ f.label }} <span class="n">{{ f.n }}</span>
          </button>
        </div>
        <div class="runmeta">
          <span class="mono">{{ data.model_id }}</span>
          <span>{{ formatLatency(data.latency_ms) }}</span>
          <span>{{ formatNumber(data.input_tokens + data.output_tokens) }} tokens</span>
          <span>{{ formatCost(data.cost_usd) }}</span>
          <span v-if="data.cache_hit" class="pill pill-accent">Cached</span>
        </div>
      </div>

      <div class="stack">
        <ClauseCard v-for="c in visible" :key="c.clause_type" :clause="c" />
        <p v-if="!visible.length" class="none">No clauses match this filter.</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.review { display: flex; flex-direction: column; gap: 20px; }
.config { padding: 18px 20px; display: flex; flex-direction: column; gap: 14px; }
.cfg-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.cfg-head h2 { font-size: 15px; }
.cfg-head p { color: var(--text-3); font-size: 13px; }
.cfg-actions { display: flex; gap: 8px; align-items: center; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip {
  display: inline-flex; align-items: center; gap: 6px; height: 30px; padding: 0 12px;
  border-radius: 999px; border: 1px solid var(--border-strong); background: var(--surface);
  color: var(--text-2); font-size: 13px; font-weight: 500; transition: all 0.12s;
}
.chip:hover { border-color: var(--text-3); }
.chip.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent-text); }
.stack { display: flex; flex-direction: column; gap: 12px; }
.progress { color: var(--text-2); font-size: 13.5px; }
.ghost { padding: 20px; }
.empty { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 8px; padding: 56px 24px; }
.empty h2 { font-size: 17px; }
.empty p { color: var(--text-2); max-width: 46ch; }
.eicon { display: grid; place-items: center; width: 48px; height: 48px; border-radius: 12px; background: var(--accent-soft); color: var(--accent-text); }
.banner { display: flex; gap: 10px; align-items: center; padding: 12px 16px; border-radius: var(--radius); font-size: 13.5px; }
.banner.warn { background: var(--warn-soft); color: var(--warn); }
.banner.bad { background: var(--bad-soft); color: var(--bad); }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
.stat { padding: 16px 18px; }
.value { font-family: var(--font-serif); font-size: 34px; font-weight: 600; letter-spacing: -0.02em; margin-top: 6px; font-variant-numeric: tabular-nums; }
.value.warn { color: var(--warn); }
.sub { color: var(--text-3); font-size: 12.5px; margin-top: 2px; }
.toolbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.seg { display: inline-flex; padding: 3px; background: var(--sunken); border-radius: var(--radius); gap: 2px; }
.seg button { border: 0; background: transparent; height: 30px; padding: 0 12px; border-radius: 7px; font-size: 13px; font-weight: 500; color: var(--text-2); }
.seg button.on { background: var(--surface); color: var(--text); box-shadow: var(--shadow-sm); }
.n { color: var(--text-3); font-variant-numeric: tabular-nums; margin-left: 2px; }
.runmeta { display: flex; gap: 14px; align-items: center; color: var(--text-3); font-size: 12.5px; flex-wrap: wrap; }
.none { text-align: center; color: var(--text-3); padding: 24px; }
</style>
