import { ref, watch } from "vue";
import { fetchJson } from "../api";

/**
 * 种子数据获取 composable
 * - 支持搜索防抖 (300ms)
 * - 排序、筛选、翻页统一触发后端请求
 * - 请求序号机制：丢弃乱序返回的旧响应，避免慢请求覆盖新数据
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

  // 请求序号：每次发起新请求时递增；响应返回时若与最新序号不符则丢弃，
  // 防止慢响应（如防抖搜索 A）后返回覆盖新请求 B 的结果
  let requestId = 0;

  // 防抖定时器句柄：直接请求（筛选/排序/翻页/刷新）时清掉，
  // 避免输入后立即点筛选，300ms 后防抖又补发一次重复请求
  let debounceTimer = null;

  /** 取消尚未触发的防抖请求 */
  function cancelDebounce() {
    if (debounceTimer !== null) {
      clearTimeout(debounceTimer);
      debounceTimer = null;
    }
  }

  /**
   * 从后端获取种子数据
   * @param {boolean} refresh 为 true 时追加 refresh=true，绕过后端缓存强制拉取
   */
  async function fetchTorrents(refresh = false) {
    // 直接请求时清掉待触发的防抖定时器，避免重复请求
    cancelDebounce();
    const id = ++requestId;
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
      if (refresh) {
        params.set("refresh", "true");
      }
      const data = await fetchJson(`/api/torrents?${params.toString()}`);
      // 期间已有更新的请求发出，本次响应已过期，直接丢弃
      if (id !== requestId) return;
      items.value = data.items || [];
      total.value = data.total || 0;
      filtered.value = data.filtered || 0;
      totalPages.value = data.total_pages || 1;
      // 服务端回显的 page 可能与本地不同（如越界），同步时抑制 watch 重复请求
      setPageSilently(data.page || 1);
    } catch (err) {
      // 过期请求的错误同样丢弃
      if (id !== requestId) return;
      error.value = err.message || "加载失败";
      items.value = [];
    } finally {
      // 仅当本次仍是最新请求时才关闭 loading，避免慢请求先返回时提前关掉 loading
      if (id === requestId) {
        loading.value = false;
      }
    }
  }

  // 防抖版本（用于搜索输入，300ms）
  function debouncedFetch() {
    cancelDebounce();
    debounceTimer = setTimeout(() => {
      debounceTimer = null;
      fetchTorrents();
    }, 300);
  }

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
   * 每页条数变化时调用（由 PaginationBar 的 size-change 事件接线）
   * 更新 pageSize -> 静默重置 page 为 1 -> 单次请求。
   * 注意：el-pagination 在页码越界时可能紧随 size-change 追发一次
   * current-change（钳制页码），该变化由 watch(page) 消费抑制标记后跳过，
   * 最终由服务端回显的 page 校正，全程只发一次请求。
   */
  function onPageSizeChange(newSize) {
    pageSize.value = newSize;
    setPageSilently(1);
    fetchTorrents();
  }

  // 监听筛选条件变化（除了 search，search 用防抖）
  watch([label, maker, excludeLabels], onFilterChange);

  // 监听翻页（v-model 绑定更新时触发），翻页恰好一次请求。
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
    onPageSizeChange,
  };
}
