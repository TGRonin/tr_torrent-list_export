<script setup>
/**
 * 可点击标签列表组件
 * - 点击标签触发筛选
 * - 使用 Element Plus el-tag
 */
defineProps({
  tags: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["tag-click"]);

const tagTypes = ["", "success", "warning", "info", "danger"];

function getTagType(index) {
  return tagTypes[index % tagTypes.length];
}

function parseTags(tagsStr) {
  if (!tagsStr || tagsStr === "无标签") return [];
  return tagsStr.split(",").map((t) => t.trim()).filter(Boolean);
}

function handleTagClick(tag) {
  emit("tag-click", tag);
}
</script>

<template>
  <div class="tag-list">
    <el-tag
      v-for="(tag, index) in parseTags(tags)"
      :key="tag"
      :type="getTagType(index)"
      size="small"
      class="clickable-tag"
      @click="handleTagClick(tag)"
    >
      {{ tag }}
    </el-tag>
    <span v-if="!tags || tags === '无标签'" class="no-tag">-</span>
  </div>
</template>

<style scoped>
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.no-tag {
  color: #94a3b8;
  font-size: 12px;
}
</style>
