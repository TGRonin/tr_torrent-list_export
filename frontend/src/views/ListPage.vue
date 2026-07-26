<script setup>
/**
 * 列表页（重设计版）
 * - StatCards 统计卡片
 * - QuickSearch 快速搜索 + 快捷标签
 * - FilterBar 下拉筛选 + 刷新
 * - TorrentTable 增强表格（选择/展开/视觉增强）
 * - PaginationBar 分页
 * - BatchToolbar 浮动批量操作栏
 */
import { ref, onMounted } from "vue";
import StatCards from "../components/StatCards.vue";
import QuickSearch from "../components/QuickSearch.vue";
import FilterBar from "../components/FilterBar.vue";
import TorrentTable from "../components/TorrentTable.vue";
import PaginationBar from "../components/PaginationBar.vue";
import BatchToolbar from "../components/BatchToolbar.vue";
import { useTorrents } from "../composables/useTorrents";
import { useFilters } from "../composables/useFilters";

const {
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
  fetchTorrents,
  onSearchChange,
  onSortChange,
} = useTorrents();

const { labels, makers, loadFilters } = useFilters();

/** 批量选择状态 */
const selectedItems = ref([]);

/** 搜索历史（localStorage 持久化） */
const searchHistory = ref([]);

const HISTORY_KEY = "torrent_search_history";
const MAX_HISTORY = 8;

function loadSearchHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    searchHistory.value = raw ? JSON.parse(raw) : [];
  } catch {
    searchHistory.value = [];
  }
}

function saveSearchHistory() {
  const val = (search.value || "").trim();
  if (!val) return;
  // 去重并放最前
  searchHistory.value = [val, ...searchHistory.value.filter((h) => h !== val)].slice(0, MAX_HISTORY);
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(searchHistory.value));
  } catch {
    // 忽略存储错误
  }
}

/**
 * 处理标签点击 -> 设为筛选条件
 */
function handleTagClick(tag) {
  label.value = tag;
}

/**
 * 刷新数据
 */
async function handleRefresh() {
  await loadFilters();
  await fetchTorrents();
}

/**
 * 批量选择变化
 */
function handleSelectionChange(selection) {
  selectedItems.value = selection;
}

/**
 * 清除选择（通过切换表格 key 强制刷新）
 */
const tableKey = ref(0);
function clearSelection() {
  selectedItems.value = [];
  tableKey.value++;
}

onMounted(async () => {
  loadSearchHistory();
  await loadFilters();
  await fetchTorrents();
});
</script>

<template>
  <div class="list-page">
    <!-- 统计概览卡片 -->
    <StatCards
      :total="total"
      :filtered="filtered"
      :maker-count="makers.length"
      :page="page"
      :total-pages="totalPages"
    />

    <!-- 快速搜索 + 快捷标签 -->
    <div class="panel">
      <QuickSearch
        v-model:search="search"
        v-model:label="label"
        v-model:maker="maker"
        v-model:excludeLabels="excludeLabels"
        :labels="labels"
        :makers="makers"
        :search-history="searchHistory"
        @search-change="onSearchChange"
        @save-history="saveSearchHistory"
      />
    </div>

    <!-- 下拉筛选栏 -->
    <div class="panel">
      <FilterBar
        v-model:label="label"
        v-model:maker="maker"
        v-model:excludeLabels="excludeLabels"
        :labels="labels"
        :makers="makers"
        @refresh="handleRefresh"
      />
    </div>

    <!-- 数据表格 -->
    <div class="panel">
      <TorrentTable
        :key="tableKey"
        :items="items"
        :loading="loading"
        :error="error"
        @sort-change="onSortChange"
        @tag-click="handleTagClick"
        @selection-change="handleSelectionChange"
      />

      <!-- 分页 -->
      <PaginationBar
        v-if="filtered > 0"
        :total="filtered"
        v-model:page="page"
        v-model:page-size="pageSize"
      />
    </div>

    <!-- 浮动批量操作栏 -->
    <BatchToolbar
      :selected-items="selectedItems"
      @clear-selection="clearSelection"
    />
  </div>
</template>

<style scoped>
.list-page {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding-bottom: 60px;
}
</style>
