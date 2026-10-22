<script setup lang="ts">
import { computed, ref } from 'vue';
import type { ClauseResult } from '@/types/api';
import { clauseMeta } from '@/lib/clauses';
import { toast } from '@/lib/toast';
import Icon from '@/components/ui/Icon.vue';

const props = defineProps<{ clause: ClauseResult }>();
const meta = computed(() => clauseMeta(props.clause.clause_type));
const pct = computed(() => Math.round(props.clause.confidence * 100));
const copied = ref(false);

const riskPill = computed(() => ({ high: 'pill-bad', medium: 'pill-warn', standard: '' }[meta.value.risk]));
const confTone = computed(() => (pct.value >= 80 ? 'ok' : pct.value >= 50 ? 'warn' : 'bad'));

async function copy() {
  try {
    await navigator.clipboard.writeText(props.clause.verbatim_quote ?? '');
    copied.value = true;
    setTimeout(() => (copied.value = false), 1500);
  } catch {
    toast('error', 'Could not copy to clipboard.');
  }
}
</script>

<template>
  <article class="card clause" :class="[{ missing: !clause.is_present }, clause.is_present && `risk-${meta.risk}`]">
    <header>
      <div class="left">
        <h3>{{ meta.label }}</h3>
        <span v-if="meta.risk !== 'standard'" class="pill" :class="riskPill">{{ meta.risk }} risk</span>
      </div>
      <div class="right">
        <span v-if="!clause.is_present" class="pill">Not found</span>
        <template v-else>
          <span v-if="clause.citation_verified" class="pill pill-ok"><Icon name="check" :size="12" /> Citation verified</span>
          <span v-else class="pill pill-warn"><Icon name="alert" :size="12" /> Unverified</span>
          <span v-if="clause.page_number" class="pill mono">p. {{ clause.page_number }}</span>
        </template>
      </div>
    </header>

    <p v-if="!clause.is_present" class="none">This clause doesn’t appear in the contract.</p>

    <template v-else>
      <p v-if="clause.summary" class="summary">{{ clause.summary }}</p>

      <blockquote v-if="clause.verbatim_quote" class="quote">
        <Icon name="quote" :size="14" class="qicon" />
        <span>{{ clause.verbatim_quote }}</span>
        <button class="btn btn-ghost btn-sm btn-icon copy" :aria-label="copied ? 'Copied' : 'Copy quote'" @click="copy">
          <Icon :name="copied ? 'check' : 'copy'" :size="14" />
        </button>
      </blockquote>

      <footer>
        <div class="conf" :title="`Model confidence ${pct}%`">
          <span class="bar"><span class="fill" :class="confTone" :style="{ width: `${pct}%` }" /></span>
          <span class="conf-label">{{ pct }}% confidence</span>
        </div>
        <span v-if="clause.repair_attempts" class="note">Self-corrected ×{{ clause.repair_attempts }}</span>
        <span v-if="clause.used_fallback" class="note">Fallback model</span>
      </footer>
    </template>
  </article>
</template>

<style scoped>
.clause { padding: 18px 20px; display: flex; flex-direction: column; gap: 12px; }
.clause { border-left: 4px solid var(--border-strong); }
.clause.risk-high { border-left-color: var(--bad); }
.clause.risk-medium { border-left-color: var(--warn); }
.clause.risk-standard { border-left-color: var(--accent); }
.clause.missing { background: var(--surface-2); box-shadow: none; }
header { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.left, .right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
h3 { font-family: var(--font-serif); font-size: 18px; }
.none { color: var(--text-3); font-size: 13.5px; }
.summary { color: var(--text); line-height: 1.6; }
.quote {
  position: relative; display: flex; gap: 10px; padding: 12px 40px 12px 14px;
  background: var(--sunken); border-left: 3px solid var(--border-strong); border-radius: var(--radius-sm);
  font-family: var(--font-serif); font-size: 15.5px; line-height: 1.65; color: var(--text-2); font-style: italic;
}
.qicon { color: var(--text-3); margin-top: 4px; }
.copy { position: absolute; top: 6px; right: 6px; }
footer { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; font-size: 12.5px; color: var(--text-3); }
.conf { display: flex; align-items: center; gap: 8px; }
.bar { width: 72px; height: 5px; border-radius: 3px; background: var(--sunken); overflow: hidden; }
.fill { display: block; height: 100%; border-radius: 3px; }
.fill.ok { background: var(--ok); } .fill.warn { background: var(--warn); } .fill.bad { background: var(--bad); }
.note { padding-left: 16px; border-left: 1px solid var(--border-strong); }
</style>
