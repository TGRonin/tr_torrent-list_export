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

  /**
   * 加载筛选选项
   * @param {boolean} refresh 为 true 时追加 refresh=true，绕过后端缓存强制拉取
   */
  async function loadFilters(refresh = false) {
    try {
      const url = refresh ? "/api/filters?refresh=true" : "/api/filters";
      const data = await fetchJson(url);
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
