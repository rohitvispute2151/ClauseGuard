import { reactive } from 'vue';
import { streamAnswer } from '@/api/endpoints';
import type { AskTelemetry, Citation } from '@/types/api';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: Citation[];
  telemetry?: AskTelemetry;
  streaming: boolean;
  error?: string;
}

interface Thread {
  messages: ChatMessage[];
  controller: AbortController | null;
}

const threads = reactive<Record<string, Thread>>({});

function thread(documentId: string): Thread {
  return (threads[documentId] ??= { messages: [], controller: null });
}

let seq = 0;
const uid = () => `${Date.now().toString(36)}-${seq++}`;

/** Per-document conversation state. Survives navigation between tabs/documents. */
export const chat = {
  messages: (documentId: string) => thread(documentId).messages,
  isStreaming: (documentId: string) => thread(documentId).controller !== null,

  stop(documentId: string) {
    thread(documentId).controller?.abort();
  },

  clear(documentId: string) {
    this.stop(documentId);
    thread(documentId).messages = [];
  },

  async ask(documentId: string, question: string) {
    const t = thread(documentId);
    const text = question.trim();
    if (!text || t.controller) return;

    t.messages.push({ id: uid(), role: 'user', content: text, citations: [], streaming: false });
    t.messages.push({ id: uid(), role: 'assistant', content: '', citations: [], streaming: true });
    const reply = t.messages[t.messages.length - 1];

    const controller = new AbortController();
    t.controller = controller;

    // Coalesce token bursts into one reactive write per frame.
    let pending = '';
    let frame = 0;
    const flush = () => {
      frame = 0;
      reply.content += pending;
      pending = '';
    };

    try {
      for await (const ev of streamAnswer(documentId, text, controller.signal)) {
        if (ev.type === 'token') {
          pending += ev.text;
          if (!frame) frame = requestAnimationFrame(flush);
        } else if (ev.type === 'citations') {
          reply.citations = ev.citations;
        } else {
          reply.telemetry = ev.telemetry;
        }
      }
    } catch (err) {
      if (!(err instanceof DOMException && err.name === 'AbortError')) {
        reply.error = err instanceof Error ? err.message : 'Something went wrong.';
      }
    } finally {
      if (frame) cancelAnimationFrame(frame);
      flush();
      reply.streaming = false;
      t.controller = null;
    }
  },
};
