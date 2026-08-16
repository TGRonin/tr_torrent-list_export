<script setup>
/**
 * 分页控件组件
 * - 使用 el-pagination
 * - 支持页码切换和每页条数切换
 */
defineProps({
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 50 },
});

const emit = defineEmits(["update:page", "update:pageSize", "size-change"]);

function handleCurrentChange(val) {
  emit("update:page", val);
}

function handleSizeChange(val) {
  emit("update:pageSize", val);
  // 额外抛出独立的 size-change 事件，供父组件统一处理
  // “更新 pageSize -> 静默重置 page 为 1 -> 单次请求”
  emit("size-change", val);
}
</script>

<template>
  <div class="pagination-bar">
    <el-pagination
      :current-page="page"
      :page-size="pageSize"
      :page-sizes="[20, 50, 100, 200]"
      :total="total"
      layout="total, sizes, prev, pager, next, jumper"
      background
      @current-change="handleCurrentChange"
      @size-change="handleSizeChange"
    />
  </div>
</template>
