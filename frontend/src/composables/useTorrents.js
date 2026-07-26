import { ref, watch } from "vue";
import { fetchJson } from "../api";

/**
 * 手写防抖函数
 */
function debounce(fn, delay) {
  let timer = null;
  return (...args) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fn(...args);
      timer = null;
    }, delay);
  };
}

/**
 * 种子数据获取 composable
 * - 支持搜索防抖 (300ms)
 * - 排序、筛选、翻页统一触发后端请求
 */
export function useTorrents() {
  const items = ref([]);
  const total = ref(0);
  const filtered = ref(0);
  const page = ref(1);
  const pageSize = ref(50);
  const totalPages = ref(1);
  const loading = ref(false);
  const error = ref("");

  // 筛选条件
  const search = ref("");
  const label = ref("全部");
  const maker = ref("全部");
  const excludeLabels = ref([]);

  // 排序条件
  const sortKey = ref("name");
  const sortOrder = ref("asc");

  /**
   * 从后端获取种子数据
   */
  async function fetchTorrents() {
    loading.value = true;
    error.value = "";
    try {
      const params = new URLSearchParams({
        search: search.value,
        label: label.value,
        maker: maker.value,
        exclude_labels: excludeLabels.value.join(","),
        sort: sortKey.value,
        order: sortOrder.value,
        page: String(page.value),
        page_size: String(pageSize.value),
      });
      const data = await fetchJson(`/api/torrents?${params.toString()}`);
      items.value = data.items || [];
      total.value = data.total || 0;
      filtered.value = data.filtered || 0;
      totalPages.value = data.total_pages || 1;
      // 服务端回显的 page 可能与本地不同（如越界），同步时抑制 watch 重复请求
      setPageSilently(data.page || 1);
    } catch (err) {
      error.value = err.message || "加载失败";
      items.value = [];
    } finally {
      loading.value = false;
    }
  }

  // 防抖版本（用于搜索输入）
  const debouncedFetch = debounce(fetchTorrents, 300);

  // 抑制 watch(page) 的标记：当回调主动将 page 复位为 1 时，
  // 由回调自身发起请求，避免 watch(page) 再触发一次重复/非防抖请求。
  let suppressPageWatch = false;
  function setPageSilently(value) {
    if (page.value === value) return;
    suppressPageWatch = true;
    page.value = value;
  }

  /**
   * 搜索输入变化时调用（带防抖）
   * 仅由 debouncedFetch 发起请求，page 复位不再触发额外的 watch 请求。
   */
  function onSearchChange() {
    setPageSilently(1);
    debouncedFetch();
  }

  /**
   * 筛选条件变化时调用（立即请求）
   */
  function onFilterChange() {
    setPageSilently(1);
    fetchTorrents();
  }

  /**
   * 排序变化时调用
   */
  function onSortChange({ prop, order }) {
    // el-table 的 sort-change 事件
    const sortMap = {
      名称: "name",
      文件大小: "size",
      制作组: "maker",
      标签数量: "label_count",
    };
    if (prop && order) {
      sortKey.value = sortMap[prop] || "name";
      sortOrder.value = order === "descending" ? "desc" : "asc";
    } else {
      sortKey.value = "name";
      sortOrder.value = "asc";
    }
    setPageSilently(1);
    fetchTorrents();
  }

  /**
   * 翻页时调用
   */
  function onPageChange(newPage) {
    page.value = newPage;
    fetchTorrents();
  }

  /**
   * 每页条数变化时调用
   */
  function onPageSizeChange(newSize) {
    pageSize.value = newSize;
    setPageSilently(1);
    fetchTorrents();
  }

  // 监听筛选条件变化（除了 search，search 用防抖）
  watch([label, maker, excludeLabels], onFilterChange);

  // 监听分页变化（v-model 绑定更新时触发）。
  // 若 page 是被回调静默复位的，则跳过本次请求，避免重复。
  watch(page, (newVal, oldVal) => {
    if (suppressPageWatch) {
      suppressPageWatch = false;
      return;
    }
    if (newVal !== oldVal) {
      fetchTorrents();
    }
  });

  watch(pageSize, (newVal, oldVal) => {
    if (newVal !== oldVal) {
      setPageSilently(1);
      fetchTorrents();
    }
  });

  return {
    items,
    total,
    filtered,
    page,
    pageSize,
    totalPages,
    loading,
    error,
    search,
    label,
    maker,
    excludeLabels,
    sortKey,
    sortOrder,
    fetchTorrents,
    onSearchChange,
    onFilterChange,
    onSortChange,
    onPageChange,
    onPageSizeChange,
  };
}
