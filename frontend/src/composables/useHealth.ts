import { ref, onMounted } from 'vue';
import { apiService } from '../services/api';
import type { HealthStatus } from '../types/api';

const health = ref<HealthStatus | null>(null);
const isLoading = ref<boolean>(false);
const error = ref<string | null>(null);

export function useHealth() {
  async function checkHealth() {
    isLoading.value = true;
    error.value = null;
    try {
      health.value = await apiService.getHealth();
    } catch (err: any) {
      error.value = err.message || 'Unable to reach ClauseGuard API';
      health.value = null;
    } finally {
      isLoading.value = false;
    }
  }

  onMounted(() => {
    if (!health.value) {
      checkHealth();
    }
  });

  return {
    health,
    isLoading,
    error,
    checkHealth
  };
}
