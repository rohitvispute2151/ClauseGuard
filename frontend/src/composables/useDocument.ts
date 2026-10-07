import { ref, computed } from 'vue';
import { apiService } from '../services/api';
import type { DocumentStatusResponse, RecentDocument } from '../types/api';

const RECENT_DOCS_KEY = 'clauseguard_recent_documents';
const ACTIVE_DOC_ID_KEY = 'clauseguard_active_document_id';

function loadRecentDocuments(): RecentDocument[] {
  try {
    const raw = localStorage.getItem(RECENT_DOCS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveRecentDocuments(docs: RecentDocument[]) {
  try {
    localStorage.setItem(RECENT_DOCS_KEY, JSON.stringify(docs.slice(0, 10)));
  } catch {}
}

const recentDocuments = ref<RecentDocument[]>(loadRecentDocuments());
const activeDocument = ref<DocumentStatusResponse | null>(null);
const isUploading = ref<boolean>(false);
const isPolling = ref<boolean>(false);
const uploadError = ref<string | null>(null);

export function useDocument() {
  const isDocumentReady = computed(() => {
    return activeDocument.value?.status === 'COMPLETED';
  });

  function updateRecentDocument(item: Partial<RecentDocument> & { id: string }) {
    const idx = recentDocuments.value.findIndex(d => d.id === item.id);
    if (idx >= 0) {
      recentDocuments.value[idx] = {
        ...recentDocuments.value[idx],
        ...item,
        lastAccessed: new Date().toISOString()
      };
    } else if (item.filename && item.status) {
      recentDocuments.value.unshift({
        id: item.id,
        filename: item.filename,
        status: item.status,
        total_pages: item.total_pages ?? null,
        total_chunks: item.total_chunks ?? null,
        lastAccessed: new Date().toISOString()
      });
    }
    saveRecentDocuments(recentDocuments.value);
  }

  async function fetchDocument(documentId: string): Promise<DocumentStatusResponse | null> {
    try {
      const doc = await apiService.getDocument(documentId);
      activeDocument.value = doc;
      localStorage.setItem(ACTIVE_DOC_ID_KEY, doc.id);
      updateRecentDocument({
        id: doc.id,
        filename: doc.filename,
        status: doc.status,
        total_pages: doc.total_pages,
        total_chunks: doc.total_chunks
      });
      return doc;
    } catch (err: any) {
      uploadError.value = err.message || 'Failed to fetch document status';
      return null;
    }
  }

  async function pollStatus(documentId: string, maxAttempts = 60, intervalMs = 2000): Promise<DocumentStatusResponse | null> {
    isPolling.value = true;
    let attempts = 0;

    return new Promise((resolve) => {
      const interval = setInterval(async () => {
        attempts++;
        try {
          const doc = await apiService.getDocument(documentId);
          activeDocument.value = doc;
          updateRecentDocument({
            id: doc.id,
            filename: doc.filename,
            status: doc.status,
            total_pages: doc.total_pages,
            total_chunks: doc.total_chunks
          });

          if (doc.status === 'COMPLETED' || doc.status === 'FAILED' || attempts >= maxAttempts) {
            clearInterval(interval);
            isPolling.value = false;
            resolve(doc);
          }
        } catch (err) {
          if (attempts >= maxAttempts) {
            clearInterval(interval);
            isPolling.value = false;
            resolve(null);
          }
        }
      }, intervalMs);
    });
  }

  async function upload(file: File) {
    isUploading.value = true;
    uploadError.value = null;

    try {
      const response = await apiService.uploadDocument(file);
      
      // Save placeholder in recents
      updateRecentDocument({
        id: response.document_id,
        filename: file.name,
        status: response.status === 'ALREADY_EXISTS' ? 'COMPLETED' : 'PENDING'
      });

      // Immediately fetch status
      const initialDoc = await fetchDocument(response.document_id);

      // If still pending/processing, start polling
      if (initialDoc && initialDoc.status !== 'COMPLETED' && initialDoc.status !== 'FAILED') {
        pollStatus(response.document_id);
      }

      return response;
    } catch (err: any) {
      uploadError.value = err.message || 'Upload failed';
      throw err;
    } finally {
      isUploading.value = false;
    }
  }

  async function selectDocument(id: string) {
    return fetchDocument(id);
  }

  function clearActive() {
    activeDocument.value = null;
    localStorage.removeItem(ACTIVE_DOC_ID_KEY);
  }

  // Restore on initial load if possible
  const savedId = localStorage.getItem(ACTIVE_DOC_ID_KEY);
  if (savedId && !activeDocument.value) {
    fetchDocument(savedId);
  }

  return {
    activeDocument,
    recentDocuments,
    isUploading,
    isPolling,
    uploadError,
    isDocumentReady,
    upload,
    selectDocument,
    fetchDocument,
    pollStatus,
    clearActive
  };
}
