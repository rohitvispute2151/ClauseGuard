<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { chat } from '@/stores/chat';
import { SUGGESTED_QUESTIONS } from '@/lib/clauses';
import MessageBubble from '@/components/ask/MessageBubble.vue';
import Icon from '@/components/ui/Icon.vue';

const props = defineProps<{ id: string }>();
const MIN = 5;
const MAX = 2000;

const messages = computed(() => chat.messages(props.id));
const streaming = computed(() => chat.isStreaming(props.id));
const draft = ref('');
const textarea = ref<HTMLTextAreaElement>();
const canSend = computed(() => draft.value.trim().length >= MIN && !streaming.value);

function resize() {
  const el = textarea.value;
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
}

function send(text = draft.value) {
  if (text.trim().length < MIN || streaming.value) return;
  draft.value = '';
  nextTick(resize);
  chat.ask(props.id, text);
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    send();
  }
}

// Follow the stream unless the user has scrolled up to read.
function scrollToEnd(force = false) {
  const nearBottom = window.innerHeight + window.scrollY >= document.body.scrollHeight - 160;
  if (force || nearBottom) window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
}
watch(() => messages.value.length, () => nextTick(() => scrollToEnd(true)));
watch(() => messages.value[messages.value.length - 1]?.content, () => nextTick(() => scrollToEnd()));
</script>

<template>
  <div class="ask">
    <div v-if="!messages.length" class="intro">
      <h2>Ask anything about this contract</h2>
      <p>Answers are generated only from the document and cite the exact passages they rely on.</p>
      <div class="suggest">
        <button v-for="q in SUGGESTED_QUESTIONS" :key="q" class="card s" @click="send(q)">
          <span>{{ q }}</span>
          <Icon name="arrow" :size="15" />
        </button>
      </div>
    </div>

    <div v-else class="thread" aria-live="polite">
      <MessageBubble v-for="m in messages" :key="m.id" :message="m" />
    </div>

    <div class="composer-wrap">
      <form class="composer card" @submit.prevent="send()">
        <textarea
          ref="textarea"
          v-model="draft"
          rows="1"
          :maxlength="MAX"
          placeholder="Ask about termination, liability, renewal…"
          aria-label="Your question"
          @input="resize"
          @keydown="onKey"
        />
        <button v-if="streaming" type="button" class="btn btn-icon" aria-label="Stop generating" @click="chat.stop(id)">
          <Icon name="stop" />
        </button>
        <button v-else type="submit" class="btn btn-primary btn-icon" :disabled="!canSend" aria-label="Send question">
          <Icon name="send" />
        </button>
      </form>
      <div class="hint">
        <span>Enter to send · Shift+Enter for a new line</span>
        <button v-if="messages.length && !streaming" class="clear" @click="chat.clear(id)">Clear conversation</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ask { display: flex; flex-direction: column; gap: 24px; min-height: 50vh; }
.intro { padding: 24px 0 8px; }
.intro h2 { font-size: 20px; }
.intro p { color: var(--text-2); margin-top: 6px; }
.suggest { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px; margin-top: 20px; }
.s {
  display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 16px;
  text-align: left; color: var(--text); font-size: 13.5px; line-height: 1.45;
  transition: border-color 0.15s, transform 0.15s;
}
.s:hover { border-color: var(--accent); transform: translateY(-1px); }
.s svg { color: var(--text-3); }
.thread { display: flex; flex-direction: column; gap: 24px; }
.composer-wrap { position: sticky; bottom: 0; padding: 12px 0 16px; margin-top: auto; background: linear-gradient(to top, var(--bg) 70%, transparent); }
.composer { display: flex; align-items: flex-end; gap: 8px; padding: 8px; box-shadow: var(--shadow-md); }
.composer:focus-within { border-color: var(--accent); box-shadow: var(--ring), var(--shadow-md); }
textarea { flex: 1; resize: none; border: 0; outline: 0; background: transparent; padding: 7px 8px; line-height: 1.5; max-height: 160px; }
textarea::placeholder { color: var(--text-3); }
.hint { display: flex; justify-content: space-between; margin-top: 8px; padding: 0 4px; font-size: 12px; color: var(--text-3); }
.clear { border: 0; background: none; color: var(--text-3); font-size: 12px; }
.clear:hover { color: var(--text); text-decoration: underline; }
</style>
