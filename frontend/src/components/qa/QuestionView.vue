<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue';
import { marked } from 'marked';
import { useAskStream, SUGGESTED_QUESTIONS } from '../../composables/useAskStream';
import { useDocument } from '../../composables/useDocument';
import CitationCard from './CitationCard.vue';

const { activeDocument } = useDocument();
const { messages, isStreaming, ask, stopStreaming, clearChat } = useAskStream();

const currentQuestion = ref('');
const chatScrollContainer = ref<HTMLElement | null>(null);

const canSubmit = computed(() => {
  const len = currentQuestion.value.trim().length;
  return (
    len >= 5 &&
    len <= 2000 &&
    !isStreaming.value &&
    !!activeDocument.value &&
    activeDocument.value.status === 'COMPLETED'
  );
});

function scrollToBottom() {
  nextTick(() => {
    if (chatScrollContainer.value) {
      chatScrollContainer.value.scrollTop = chatScrollContainer.value.scrollHeight;
    }
  });
}

watch(
  () => messages.value.map(m => m.content).join(''),
  () => {
    scrollToBottom();
  }
);

function submitQuestion() {
  if (!canSubmit.value || !activeDocument.value) return;
  const q = currentQuestion.value.trim();
  currentQuestion.value = '';
  ask(activeDocument.value.id, q);
  scrollToBottom();
}

function handleQuickAsk(suggestion: string) {
  if (!activeDocument.value || isStreaming.value) return;
  currentQuestion.value = suggestion;
  submitQuestion();
}

function renderMarkdown(text: string) {
  try {
    return marked.parse(text || '');
  } catch {
    return text;
  }
}
</script>

<template>
  <div class="qa-container">
    <!-- Active Document Notice / Warning -->
    <div v-if="!activeDocument" class="alert alert-warning">
      <span>⚠️</span>
      <div>
        <strong>No contract selected:</strong> Please upload or select a contract document first to ask grounded questions.
      </div>
    </div>
    <div v-else-if="activeDocument.status !== 'COMPLETED'" class="alert alert-warning">
      <span>⏳</span>
      <div>
        <strong>Ingestion in progress:</strong> The contract is still being chunked and embedded (Status: {{ activeDocument.status }}). Grounded search will be available once indexing completes.
      </div>
    </div>

    <!-- Main Chat Card -->
    <div class="card chat-card">
      <div class="chat-header">
        <div>
          <h3>Grounded Contract Intelligence (SSE Streaming)</h3>
          <p class="chat-sub">
            Ask any question. Answers are retrieved via Reciprocal Rank Fusion (pgvector + FTS) and citations are verified against source contract text.
          </p>
        </div>

        <button 
          v-if="messages.length > 0" 
          class="btn btn-sm btn-ghost" 
          :disabled="isStreaming"
          @click="clearChat"
        >
          Clear History
        </button>
      </div>

      <!-- Suggested Questions Bar -->
      <div v-if="messages.length === 0" class="suggestions-section">
        <span class="suggestions-label">Try Asking:</span>
        <div class="suggestions-grid">
          <button 
            v-for="sq in SUGGESTED_QUESTIONS" 
            :key="sq" 
            class="suggestion-btn"
            :disabled="!activeDocument || activeDocument.status !== 'COMPLETED'"
            @click="handleQuickAsk(sq)"
          >
            "{{ sq }}"
          </button>
        </div>
      </div>

      <!-- Chat History Box -->
      <div ref="chatScrollContainer" class="messages-area">
        <div v-if="messages.length === 0" class="empty-chat-state">
          <div class="empty-icon">💬</div>
          <div class="empty-title">Ready to analyze contract clauses</div>
          <div class="empty-desc">
            Type your legal or procurement query below or click one of the suggested prompts above.
          </div>
        </div>

        <div 
          v-for="msg in messages" 
          :key="msg.id" 
          class="message-row"
          :class="msg.role === 'user' ? 'row-user' : 'row-assistant'"
        >
          <div class="message-avatar">
            <span v-if="msg.role === 'user'">👤</span>
            <span v-else>🛡️</span>
          </div>

          <div class="message-bubble">
            <div class="bubble-header">
              <span class="sender-name">{{ msg.role === 'user' ? 'You' : 'ClauseGuard AI' }}</span>
              <span class="msg-time">{{ new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}</span>
            </div>

            <!-- Content -->
            <div 
              class="bubble-content markdown-body" 
              v-html="renderMarkdown(msg.content)"
            ></div>

            <!-- Blinking cursor during streaming -->
            <span v-if="msg.isStreaming" class="cursor-blink">▋</span>

            <!-- Error message if stream failed -->
            <div v-if="msg.error" class="stream-error">
              <strong>Error:</strong> {{ msg.error }}
            </div>

            <!-- Verified Citations List -->
            <div v-if="msg.citations && msg.citations.length > 0" class="citations-section">
              <div class="citations-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  <path d="m9 12 2 2 4-4"/>
                </svg>
                Verified Source Citations ({{ msg.citations.length }})
              </div>
              <div class="citations-list">
                <CitationCard 
                  v-for="(cit, idx) in msg.citations" 
                  :key="idx" 
                  :citation="cit"
                />
              </div>
            </div>

            <!-- Telemetry Footer -->
            <div v-if="msg.telemetry" class="bubble-telemetry">
              <span class="tele-item">Latency: {{ msg.telemetry.latency_ms }}ms</span>
              <span class="tele-sep">•</span>
              <span class="tele-item">Tokens: {{ msg.telemetry.input_tokens }} in / {{ msg.telemetry.output_tokens }} out</span>
              <span class="tele-sep">•</span>
              <span class="tele-item">Cost: ${{ msg.telemetry.cost_usd.toFixed(4) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Question Input Controls -->
      <div class="input-container">
        <div class="input-wrapper">
          <textarea 
            v-model="currentQuestion" 
            placeholder="Ask a question about rights, obligations, liability, or termination (min 5 characters)..."
            class="textarea" 
            rows="3"
            :disabled="isStreaming || !activeDocument || activeDocument.status !== 'COMPLETED'"
            @keydown.enter.exact.prevent="submitQuestion"
          ></textarea>

          <div class="input-footer">
            <span class="char-count" :class="{ 'text-danger': currentQuestion.length > 2000 }">
              {{ currentQuestion.length }} / 2000 characters
            </span>

            <div class="input-actions">
              <button 
                v-if="isStreaming" 
                class="btn btn-secondary btn-sm" 
                @click="stopStreaming"
              >
                ■ Stop Stream
              </button>

              <button 
                class="btn btn-primary" 
                :disabled="!canSubmit"
                @click="submitQuestion"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"/>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
                Ask Grounded Question
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.qa-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.chat-card {
  display: flex;
  flex-direction: column;
  min-height: 650px;
  padding: 1.5rem;
}

.chat-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 1rem;
}

.chat-sub {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.suggestions-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.suggestions-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
  letter-spacing: 0.04em;
}

.suggestions-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.suggestion-btn {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 0.4rem 0.75rem;
  color: var(--text-secondary);
  font-size: 0.775rem;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
}

.suggestion-btn:hover:not(:disabled) {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  border-color: var(--border-medium);
}

.suggestion-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  max-height: 520px;
  min-height: 380px;
  padding: 1rem 0;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.empty-chat-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 3rem 1rem;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
}

.empty-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.35rem;
}

.empty-desc {
  font-size: 0.85rem;
  max-width: 420px;
}

.message-row {
  display: flex;
  gap: 0.85rem;
  align-items: flex-start;
}

.row-user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.row-user .message-avatar {
  background: rgba(99, 102, 241, 0.2);
  border-color: var(--border-primary);
}

.message-bubble {
  max-width: 82%;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 1rem 1.25rem;
}

.row-user .message-bubble {
  background: rgba(99, 102, 241, 0.12);
  border-color: var(--border-primary);
}

.bubble-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.sender-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
}

.msg-time {
  font-size: 0.725rem;
  color: var(--text-muted);
}

.bubble-content {
  font-size: 0.9rem;
  line-height: 1.6;
  color: #e2e8f0;
}

.markdown-body :deep(p) {
  margin-bottom: 0.75rem;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(ul), .markdown-body :deep(ol) {
  margin-left: 1.25rem;
  margin-bottom: 0.75rem;
}

.markdown-body :deep(code) {
  font-family: var(--font-mono);
  background: rgba(0, 0, 0, 0.3);
  padding: 0.15rem 0.35rem;
  border-radius: 4px;
  font-size: 0.85em;
}

.cursor-blink {
  display: inline-block;
  color: var(--primary-light);
  animation: pulse 0.7s infinite;
  margin-left: 2px;
}

.stream-error {
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
  border-radius: var(--radius-sm);
  color: #fca5a5;
  font-size: 0.825rem;
}

.citations-section {
  margin-top: 1rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--border-subtle);
}

.citations-title {
  font-size: 0.775rem;
  font-weight: 600;
  color: var(--success);
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.5rem;
}

.citations-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bubble-telemetry {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px dashed var(--border-subtle);
  font-size: 0.725rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.input-container {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-subtle);
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.char-count {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.alert {
  padding: 0.85rem 1.25rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.alert-warning {
  background: var(--warning-bg);
  border: 1px solid var(--warning-border);
  color: #fbbf24;
}
</style>
