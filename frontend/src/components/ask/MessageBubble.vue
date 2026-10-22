<script setup lang="ts">
import { computed, ref } from 'vue';
import type { ChatMessage } from '@/stores/chat';
import { renderMarkdown } from '@/lib/markdown';
import { formatCost, formatLatency, formatNumber } from '@/lib/format';
import Icon from '@/components/ui/Icon.vue';

const props = defineProps<{ message: ChatMessage }>();
const html = computed(() => renderMarkdown(props.message.content));
const open = ref(false);
const verified = computed(() => props.message.citations.filter((c) => c.verified).length);
</script>

<template>
  <div v-if="message.role === 'user'" class="user">
    <div class="bubble">{{ message.content }}</div>
  </div>

  <div v-else class="assistant">
    <span class="avatar"><Icon name="shield" :size="14" /></span>
    <div class="body">
      <div v-if="message.streaming && !message.content" class="typing" aria-label="Searching the contract">
        <span /><span /><span />
      </div>
      <div v-else-if="message.content" class="prose" v-html="html" />

      <div v-if="message.error" class="err" role="alert">
        <Icon name="alert" /> {{ message.error }}
      </div>

      <div v-if="message.citations.length" class="sources">
        <button class="src-toggle" :aria-expanded="open" @click="open = !open">
          <Icon name="quote" :size="13" />
          {{ message.citations.length }} source{{ message.citations.length > 1 ? 's' : '' }}
          <span class="pill pill-ok" v-if="verified"><Icon name="check" :size="11" /> {{ verified }} verified</span>
          <Icon name="chevron" :size="14" class="chev" :class="{ flip: open }" />
        </button>
        <ul v-if="open">
          <li v-for="(c, i) in message.citations" :key="i" class="src">
            <div class="src-meta">
              <span class="pill" :class="c.verified ? 'pill-ok' : 'pill-warn'">{{ c.verified ? 'Verified' : 'Unverified' }}</span>
              <span v-if="c.page_number" class="pill mono">p. {{ c.page_number }}</span>
            </div>
            <blockquote>{{ c.quote }}</blockquote>
          </li>
        </ul>
      </div>

      <div v-if="message.telemetry" class="tele">
        {{ formatLatency(message.telemetry.latency_ms) }} · {{ formatNumber(message.telemetry.input_tokens + message.telemetry.output_tokens) }} tokens · {{ formatCost(message.telemetry.cost_usd) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.user { display: flex; justify-content: flex-end; }
.bubble { max-width: 80%; padding: 10px 14px; border-radius: 16px 16px 4px 16px; background: var(--accent); color: var(--on-accent); line-height: 1.55; white-space: pre-wrap; word-break: break-word; }
.assistant { display: flex; gap: 12px; align-items: flex-start; }
.avatar { display: grid; place-items: center; width: 28px; height: 28px; border-radius: 8px; background: var(--accent-soft); color: var(--accent-text); margin-top: 2px; }
.body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 10px; }
.typing { display: flex; gap: 4px; padding: 10px 0; }
.typing span { width: 6px; height: 6px; border-radius: 50%; background: var(--text-3); animation: bounce 1.2s infinite ease-in-out; }
.typing span:nth-child(2) { animation-delay: 0.15s; } .typing span:nth-child(3) { animation-delay: 0.3s; }
@keyframes bounce { 0%, 60%, 100% { opacity: 0.3; transform: none; } 30% { opacity: 1; transform: translateY(-3px); } }
.err { display: flex; gap: 8px; align-items: center; padding: 10px 12px; border-radius: var(--radius); background: var(--bad-soft); color: var(--bad); font-size: 13.5px; }
.sources { border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); overflow: hidden; }
.src-toggle { display: flex; align-items: center; gap: 8px; width: 100%; padding: 8px 12px; border: 0; background: transparent; font-size: 13px; font-weight: 500; color: var(--text-2); text-align: left; }
.src-toggle:hover { background: var(--surface-2); }
.chev { margin-left: auto; transition: transform 0.15s; } .chev.flip { transform: rotate(180deg); }
ul { list-style: none; padding: 0; }
.src { padding: 12px; border-top: 1px solid var(--border); display: flex; flex-direction: column; gap: 8px; }
.src-meta { display: flex; gap: 6px; }
blockquote { padding: 8px 12px; border-left: 3px solid var(--accent); background: var(--sunken); border-radius: var(--radius-sm); font-size: 13px; font-style: italic; color: var(--text-2); line-height: 1.6; }
.tele { font-size: 12px; color: var(--text-3); }
</style>
