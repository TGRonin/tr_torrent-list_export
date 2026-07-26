<script setup>
/**
 * 筛选栏组件（精简版）
 * - 标签筛选下拉
 * - 制作组筛选下拉
 * - 排除标签多选下拉
 * - 刷新按钮
 * 搜索框已迁移至 QuickSearch 组件
 */
import { PriceTag, User, Remove, Refresh } from "@element-plus/icons-vue";

defineProps({
  label: { type: String, default: "全部" },
  maker: { type: String, default: "全部" },
  excludeLabels: { type: Array, default: () => [] },
  labels: { type: Array, default: () => [] },
  makers: { type: Array, default: () => [] },
});

const emit = defineEmits([
  "update:label",
  "update:maker",
  "update:excludeLabels",
  "refresh",
]);
</script>

<template>
  <div class="filter-bar">
    <el-select
      :model-value="label"
      placeholder="标签筛选"
      :prefix-icon="PriceTag"
      class="filter-select"
      @update:model-value="(val) => emit('update:label', val)"
    >
      <el-option label="全部标签" value="全部" />
      <el-option
        v-for="item in labels"
        :key="item"
        :label="item"
        :value="item"
      />
    </el-select>

    <el-select
      :model-value="maker"
      placeholder="制作组筛选"
      :prefix-icon="User"
      class="filter-select"
      filterable
      @update:model-value="(val) => emit('update:maker', val)"
    >
      <el-option label="全部制作组" value="全部" />
      <el-option
        v-for="item in makers"
        :key="item"
        :label="item"
        :value="item"
      />
    </el-select>

    <el-select
      :model-value="excludeLabels"
      placeholder="排除标签"
      :prefix-icon="Remove"
      class="filter-select"
      multiple
      collapse-tags
      collapse-tags-tooltip
      clearable
      filterable
      @update:model-value="(val) => emit('update:excludeLabels', val)"
    >
      <el-option
        v-for="item in labels"
        :key="item"
        :label="item"
        :value="item"
      />
    </el-select>

    <el-button type="primary" :icon="Refresh" @click="emit('refresh')">
      刷新
    </el-button>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-select {
  min-width: 160px;
  flex: 1;
  max-width: 260px;
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
  }

  .filter-select {
    width: 100%;
    max-width: unset;
    min-width: unset;
  }
}
</style>
