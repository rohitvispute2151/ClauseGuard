import { ref } from 'vue';
import { apiService } from '../services/api';
import type { ChatMessage, Citation, SSEDonePayload } from '../types/api';

export const SUGGESTED_QUESTIONS = [
  'What are the termination conditions and required notice periods?',
  'What is the aggregate liability cap and what claims are uncapped?',
  'Does the agreement contain broad indemnification obligations?',
  'What is the governing law and designated dispute resolution forum?',
  'Is there an auto-renewal clause and when is the opt-out deadline?'
];

export function useAskStream() {
  const messages = ref<ChatMessage[]>([]);
  const isStreaming = ref<boolean>(false);
  const currentController = ref<AbortController | null>(null);

  function stopStreaming() {
    if (currentController.value) {
      currentController.value.abort();
      currentController.value = null;
    }
    isStreaming.value = false;
  }

  function clearChat() {
    stopStreaming();
    messages.value = [];
  }

  function ask(documentId: string, questionText: string) {
    if (!documentId || !questionText.trim() || isStreaming.value) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: questionText.trim(),
      timestamp: new Date()
    };

    const assistantMessageId = `asst-${Date.now()}`;
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      citations: [],
      isStreaming: true
    };

    messages.value.push(userMessage, assistantMessage);
    isStreaming.value = true;

    currentController.value = apiService.streamAsk(documentId, questionText.trim(), {
      onToken: (token: string) => {
        const target = messages.value.find(m => m.id === assistantMessageId);
        if (target) {
          target.content += token;
        }
      },
      onCitations: (citations: Citation[]) => {
        const target = messages.value.find(m => m.id === assistantMessageId);
        if (target) {
          target.citations = citations;
        }
      },
      onDone: (telemetry: SSEDonePayload) => {
        const target = messages.value.find(m => m.id === assistantMessageId);
        if (target) {
          target.telemetry = telemetry;
          target.isStreaming = false;
        }
        isStreaming.value = false;
        currentController.value = null;
      },
      onError: (errMsg: string) => {
        const target = messages.value.find(m => m.id === assistantMessageId);
        if (target) {
          target.error = errMsg;
          target.isStreaming = false;
        }
        isStreaming.value = false;
        currentController.value = null;
      }
    });
  }

  return {
    messages,
    isStreaming,
    ask,
    stopStreaming,
    clearChat
  };
}
