<script setup>
/**
 * 增强种子表格组件
 * - 批量选择列 (selection)
 * - 行展开详情面板 (expand)
 * - 视觉增强：文件图标、大小颜色 tag、制作组 tag、标签数量 badge
 * - 骨架屏加载、空状态、错误状态
 * - 可点击标签筛选
 */
import { Document } from "@element-plus/icons-vue";
import TagList from "./TagList.vue";

defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: "" },
});

const emit = defineEmits(["sort-change", "tag-click", "selection-change"]);

function handleSortChange(sortInfo) {
  emit("sort-change", sortInfo);
}

function handleTagClick(tag) {
  emit("tag-click", tag);
}

function handleSelectionChange(selection) {
  emit("selection-change", selection);
}

/** 根据原始文件大小返回颜色类型 */
function sizeTagType(row) {
  const bytes = parseInt(row["原始文件大小"] || 0);
  if (bytes < 100 * 1024 * 1024) return "success"; // <100MB 绿
  if (bytes < 1024 * 1024 * 1024) return "primary"; // <1GB 蓝
  if (bytes < 10 * 1024 * 1024 * 1024) return "warning"; // <10GB 黄
  return "danger"; // >10GB 红
}

/** 解析标签字符串为数组 */
function parseTags(tagsStr) {
  if (!tagsStr || tagsStr === "无标签") return [];
  return tagsStr.split(",").map((t) => t.trim()).filter(Boolean);
}
</script>

<template>
  <div class="torrent-table-wrapper">
    <!-- 错误状态 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      closable
      style="margin-bottom: 16px"
    />

    <!-- 骨架屏加载状态 -->
    <div v-if="loading && items.length === 0" class="skeleton-wrapper">
      <el-skeleton v-for="i in 8" :key="i" :rows="1" animated style="margin-bottom: 12px" />
    </div>

    <!-- 数据表格 -->
    <el-table
      v-else
      :data="items"
      v-loading="loading"
      stripe
      border
      row-key="名称"
      style="width: 100%"
      class="enhanced-table"
      empty-text=" "
      @sort-change="handleSortChange"
      @selection-change="handleSelectionChange"
    >
      <!-- 批量选择列 -->
      <el-table-column type="selection" width="48" align="center" />

      <!-- 展开行详情列 -->
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="expand-detail-panel">
            <el-row :gutter="16">
              <el-col :span="24">
                <div class="detail-item">
                  <span class="detail-label">完整名称</span>
                  <span class="detail-value detail-name-full">{{ row["名称"] }}</span>
                </div>
              </el-col>
            </el-row>
            <el-row :gutter="16" style="margin-top: 12px">
              <el-col :xs="24" :sm="8">
                <div class="detail-item">
                  <span class="detail-label">制作组</span>
                  <span class="detail-value">{{ row["制作组"] || "未知" }}</span>
                </div>
              </el-col>
              <el-col :xs="24" :sm="8">
                <div class="detail-item">
                  <span class="detail-label">文件大小</span>
                  <span class="detail-value">{{ row["文件大小"] }}</span>
                </div>
              </el-col>
              <el-col :xs="24" :sm="8">
                <div class="detail-item">
                  <span class="detail-label">原始字节</span>
                  <span class="detail-value">{{ (row["原始文件大小"] || 0).toLocaleString() }} B</span>
                </div>
              </el-col>
            </el-row>
            <el-row :gutter="16" style="margin-top: 12px">
              <el-col :span="24">
                <div class="detail-item">
                  <span class="detail-label">标签列表</span>
                  <div class="detail-tags">
                    <el-tag
                      v-for="tag in parseTags(row['标签'])"
                      :key="tag"
                      size="small"
                      class="detail-tag"
                      @click="handleTagClick(tag)"
                    >
                      {{ tag }}
                    </el-tag>
                    <span v-if="!row['标签'] || row['标签'] === '无标签'" class="no-tag-text">无标签</span>
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>
        </template>
      </el-table-column>

      <!-- 名称列 -->
      <el-table-column
        prop="名称"
        label="名称"
        min-width="280"
        sortable="custom"
      >
        <template #default="{ row }">
          <div class="cell-name-wrapper">
            <el-icon class="name-icon"><Document /></el-icon>
            <span class="cell-name">{{ row["名称"] }}</span>
          </div>
        </template>
      </el-table-column>

      <!-- 文件大小列 -->
      <el-table-column
        prop="文件大小"
        label="文件大小"
        width="130"
        sortable="custom"
        align="center"
      >
        <template #default="{ row }">
          <el-tag :type="sizeTagType(row)" size="small" effect="light" round>
            {{ row["文件大小"] }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 制作组列 -->
      <el-table-column
        prop="制作组"
        label="制作组"
        width="140"
        sortable="custom"
        align="center"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          <el-tag
            v-if="row['制作组']"
            type="info"
            size="small"
            effect="plain"
          >
            {{ row["制作组"] }}
          </el-tag>
          <span v-else class="no-tag">-</span>
        </template>
      </el-table-column>

      <!-- 标签数列 -->
      <el-table-column
        prop="标签数量"
        label="标签数"
        width="90"
        sortable="custom"
        align="center"
      >
        <template #default="{ row }">
          <span
            class="tag-count-chip"
            :class="{ 'tag-count-zero': row['标签数量'] === 0 }"
          >
            {{ row['标签数量'] }}
          </span>
        </template>
      </el-table-column>

      <!-- 标签列 -->
      <el-table-column label="标签" min-width="240">
        <template #default="{ row }">
          <TagList :tags="row['标签']" @tag-click="handleTagClick" />
        </template>
      </el-table-column>

      <!-- 空状态 -->
      <template #empty>
        <el-empty description="暂无数据" :image-size="80" />
      </template>
    </el-table>
  </div>
</template>

<style scoped>
.torrent-table-wrapper {
  min-height: 200px;
}

.skeleton-wrapper {
  padding: 16px;
}

.cell-name-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.name-icon {
  color: var(--color-primary, #1e40af);
  font-size: 16px;
  flex-shrink: 0;
}

.cell-name {
  font-weight: 600;
  word-break: break-all;
  white-space: normal;
  line-height: 1.5;
}

.no-tag {
  color: #94a3b8;
  font-size: 12px;
}

.tag-count-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  border-radius: 12px;
  background: rgba(30, 64, 175, 0.10);
  color: var(--color-primary, #1e40af);
  font-size: 12px;
  font-weight: 700;
}

.tag-count-zero {
  background: rgba(148, 163, 184, 0.1);
  color: #94a3b8;
}

/* 展开行详情面板 */
.expand-detail-panel {
  padding: 16px 24px;
  background: rgba(239, 246, 255, 0.6);
  border: 1px solid rgba(30, 64, 175, 0.08);
  border-radius: 12px;
  margin: 4px 0;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 13px;
  color: var(--text, #0f172a);
  font-weight: 500;
}

.detail-name-full {
  word-break: break-all;
  line-height: 1.5;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.detail-tag {
  cursor: pointer;
  transition: transform 0.15s ease;
}

.detail-tag:hover {
  transform: scale(1.08);
}

.no-tag-text {
  font-size: 12px;
  color: #94a3b8;
}

/* 表格增强样式 */
.enhanced-table :deep(.el-table__header th) {
  background: rgba(239, 246, 255, 0.7);
  font-weight: 700;
  color: var(--text-strong, #1e3a8a);
}

.enhanced-table :deep(.el-table__row:hover > td) {
  background: rgba(59, 130, 246, 0.08) !important;
  transition: background-color 0.2s ease;
}

.enhanced-table :deep(.el-table__body td) {
  transition: background-color 0.2s ease;
}

.enhanced-table :deep(.el-table__expand-icon) {
  color: var(--color-primary, #1e40af);
}
</style>
