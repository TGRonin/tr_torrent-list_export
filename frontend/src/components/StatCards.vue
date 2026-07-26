<script setup>
/**
 * 紧凑统计卡片组件
 * - 4 个卡片：总数、已筛选、制作组数、当前页码
 * - 替换原有 el-tag 统计栏
 */
import { Files, Filter, User, Collection } from "@element-plus/icons-vue";

defineProps({
  total: { type: Number, default: 0 },
  filtered: { type: Number, default: 0 },
  makerCount: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  totalPages: { type: Number, default: 1 },
});
</script>

<template>
  <div class="stat-cards-row">
    <div class="stat-card-mini">
      <div class="stat-card-icon" style="background: rgba(30, 64, 175, 0.12); color: #1e40af">
        <el-icon :size="18"><Files /></el-icon>
      </div>
      <div class="stat-card-body">
        <div class="stat-card-label">总种子数</div>
        <div class="stat-card-value">{{ total.toLocaleString() }}</div>
      </div>
    </div>

    <div class="stat-card-mini">
      <div class="stat-card-icon" style="background: rgba(59, 130, 246, 0.12); color: #3b82f6">
        <el-icon :size="18"><Filter /></el-icon>
      </div>
      <div class="stat-card-body">
        <div class="stat-card-label">筛选结果</div>
        <div class="stat-card-value">{{ filtered.toLocaleString() }}</div>
      </div>
    </div>

    <div class="stat-card-mini">
      <div class="stat-card-icon" style="background: rgba(13, 148, 136, 0.12); color: #0d9488">
        <el-icon :size="18"><User /></el-icon>
      </div>
      <div class="stat-card-body">
        <div class="stat-card-label">制作组数</div>
        <div class="stat-card-value">{{ makerCount }}</div>
      </div>
    </div>

    <div class="stat-card-mini">
      <div class="stat-card-icon" style="background: rgba(217, 119, 6, 0.14); color: #d97706">
        <el-icon :size="18"><Collection /></el-icon>
      </div>
      <div class="stat-card-body">
        <div class="stat-card-label">当前页码</div>
        <div class="stat-card-value">{{ page }} / {{ totalPages }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-cards-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card-mini {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--glass-bg, rgba(255, 255, 255, 0.62));
  backdrop-filter: blur(16px) saturate(140%);
  -webkit-backdrop-filter: blur(16px) saturate(140%);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.7));
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: var(--shadow-md, 0 10px 30px rgba(30, 64, 175, 0.10));
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card-mini:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 38px rgba(30, 64, 175, 0.18);
}

.stat-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  flex-shrink: 0;
}

.stat-card-body {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.stat-card-label {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
  margin-bottom: 2px;
}

.stat-card-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text, #0f172a);
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 768px) {
  .stat-cards-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
