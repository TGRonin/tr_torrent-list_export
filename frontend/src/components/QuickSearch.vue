<script setup>
/**
 * 快速搜索栏组件
 * - 搜索输入框 + 搜索历史弹出层
 * - 快捷标签 chips 一键筛选
 * - 当前活跃筛选 chip 展示
 */
import { ref, computed } from "vue";
import { Search, Clock } from "@element-plus/icons-vue";

const props = defineProps({
  search: { type: String, default: "" },
  label: { type: String, default: "全部" },
  maker: { type: String, default: "全部" },
  excludeLabels: { type: Array, default: () => [] },
  labels: { type: Array, default: () => [] },
  makers: { type: Array, default: () => [] },
  searchHistory: { type: Array, default: () => [] },
});

const emit = defineEmits([
  "update:search",
  "update:label",
  "update:maker",
  "update:excludeLabels",
  "search-change",
  "save-history",
]);

const showHistory = ref(false);

/** 快捷标签取前 12 个 */
const quickLabels = computed(() => (props.labels || []).slice(0, 12));

/** 当前活跃的筛选条件 */
const activeFilters = computed(() => {
  const list = [];
  if (props.label && props.label !== "全部") {
    list.push({ type: "label", value: props.label });
  }
  if (props.maker && props.maker !== "全部") {
    list.push({ type: "maker", value: props.maker });
  }
  for (const ex of props.excludeLabels) {
    list.push({ type: "exclude", value: ex });
  }
  return list;
});

function handleInput(val) {
  emit("update:search", val);
  emit("search-change");
}

function handleFocus() {
  if (props.searchHistory.length > 0) {
    showHistory.value = true;
  }
}

function handleBlur() {
  setTimeout(() => {
    showHistory.value = false;
  }, 200);
}

function selectHistory(item) {
  emit("update:search", item);
  emit("search-change");
  showHistory.value = false;
}

function quickLabelClick(tag) {
  emit("update:label", tag === props.label ? "全部" : tag);
}

function removeFilter(filter) {
  if (filter.type === "label") {
    emit("update:label", "全部");
  } else if (filter.type === "maker") {
    emit("update:maker", "全部");
  } else if (filter.type === "exclude") {
    emit("update:excludeLabels", props.excludeLabels.filter((l) => l !== filter.value));
  }
}
</script>

<template>
  <div class="quick-search-wrapper">
    <!-- 搜索输入 + 历史 -->
    <div class="search-input-area">
      <el-input
        :model-value="search"
        placeholder="搜索名称 / 标签..."
        clearable
        :prefix-icon="Search"
        class="search-input"
        @update:model-value="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
        @keyup.enter="emit('save-history')"
      />

      <!-- 搜索历史弹出层 -->
      <transition name="history-fade">
        <div v-if="showHistory && searchHistory.length > 0" class="search-history-panel">
          <div class="history-header">
            <el-icon><Clock /></el-icon>
            <span>搜索历史</span>
          </div>
          <div
            v-for="item in searchHistory"
            :key="item"
            class="history-item"
            @mousedown="selectHistory(item)"
          >
            <el-icon class="history-item-icon"><Clock /></el-icon>
            <span class="history-item-text">{{ item }}</span>
          </div>
        </div>
      </transition>
    </div>

    <!-- 快捷标签 chips -->
    <div v-if="quickLabels.length > 0" class="tag-chips-row">
      <span class="chips-label">快捷标签</span>
      <div class="chips-scroll">
        <el-tag
          v-for="tag in quickLabels"
          :key="tag"
          :type="tag === label ? 'primary' : 'info'"
          :effect="tag === label ? 'dark' : 'plain'"
          size="small"
          class="quick-chip"
          @click="quickLabelClick(tag)"
        >
          {{ tag }}
        </el-tag>
      </div>
    </div>

    <!-- 当前活跃筛选 -->
    <div v-if="activeFilters.length > 0" class="active-filters-row">
      <span class="chips-label">当前筛选</span>
      <div class="chips-scroll">
        <el-tag
          v-for="(f, i) in activeFilters"
          :key="i"
          :type="f.type === 'exclude' ? 'danger' : f.type === 'maker' ? 'warning' : 'success'"
          size="small"
          closable
          @close="removeFilter(f)"
        >
          <span v-if="f.type === 'exclude'" class="filter-prefix">排除</span>
          {{ f.value }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quick-search-wrapper {
  position: relative;
}

.search-input-area {
  position: relative;
}

.search-input {
  width: 100%;
}

.search-history-panel {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--glass-bg-strong, rgba(255, 255, 255, 0.9));
  backdrop-filter: blur(18px) saturate(150%);
  -webkit-backdrop-filter: blur(18px) saturate(150%);
  border-radius: 12px;
  box-shadow: 0 16px 44px rgba(30, 64, 175, 0.18);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.7));
  z-index: 100;
  max-height: 260px;
  overflow-y: auto;
  padding: 8px 0;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  font-size: 12px;
  color: #94a3b8;
  font-weight: 600;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.history-item:hover {
  background: #f0f9ff;
}

.history-item-icon {
  color: #94a3b8;
  font-size: 12px;
}

.history-item-text {
  font-size: 13px;
  color: var(--text, #0f172a);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tag-chips-row,
.active-filters-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 10px;
}

.chips-label {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
  white-space: nowrap;
  line-height: 24px;
  flex-shrink: 0;
}

.chips-scroll {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.quick-chip {
  cursor: pointer;
  transition: transform 0.15s ease;
}

.quick-chip:hover {
  transform: scale(1.06);
}

.filter-prefix {
  margin-right: 2px;
  font-weight: 600;
}

/* 历史面板淡入动画 */
.history-fade-enter-active,
.history-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.history-fade-enter-from,
.history-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 768px) {
  .tag-chips-row,
  .active-filters-row {
    flex-direction: column;
    gap: 6px;
  }

  .chips-label {
    line-height: 20px;
  }
}
</style>
