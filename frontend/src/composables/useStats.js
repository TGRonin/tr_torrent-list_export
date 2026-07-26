import { ref } from "vue";
import { fetchJson } from "../api";

/**
 * 统计数据 composable
 * - 封装 /api/stats 请求逻辑
 * - 返回 stats, loading, error, fetchStats
 */
export function useStats() {
  const stats = ref(null);
  const loading = ref(false);
  const error = ref("");

  async function fetchStats() {
    loading.value = true;
    error.value = "";
    try {
      const data = await fetchJson("/api/stats");
      stats.value = data;
    } catch (err) {
      error.value = err.message || "加载统计数据失败";
      stats.value = null;
    } finally {
      loading.value = false;
    }
  }

  return {
    stats,
    loading,
    error,
    fetchStats,
  };
}
