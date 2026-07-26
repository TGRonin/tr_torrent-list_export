import { ref } from "vue";
import { fetchJson } from "../api";

/**
 * 筛选选项 composable
 * - 管理标签和制作组选项列表
 */
export function useFilters() {
  const labels = ref([]);
  const makers = ref([]);
  const totalRecords = ref(0);

  async function loadFilters() {
    try {
      const data = await fetchJson("/api/filters");
      labels.value = data.labels || [];
      makers.value = data.makers || [];
      totalRecords.value = data.total || 0;
    } catch (err) {
      console.error("加载筛选选项失败:", err);
    }
  }

  return {
    labels,
    makers,
    totalRecords,
    loadFilters,
  };
}
