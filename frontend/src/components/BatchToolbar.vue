<script setup>
/**
 * 批量操作浮动工具栏
 * - 选中项 > 0 时从底部滑入显示
 * - 显示选中数量
 * - 操作：复制名称、复制完整信息、清除选择
 */
import { computed } from "vue";
import { ElMessage } from "element-plus";
import { CopyDocument, Document, Delete } from "@element-plus/icons-vue";

const props = defineProps({
  selectedItems: { type: Array, default: () => [] },
});

const emit = defineEmits(["clear-selection"]);

const count = computed(() => props.selectedItems.length);

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    ElMessage.success("已复制到剪贴板");
  } catch {
    // 降级方案
    const textarea = document.createElement("textarea");
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    ElMessage.success("已复制到剪贴板");
  }
}

function copyNames() {
  const names = props.selectedItems.map((r) => r["名称"]).join("\n");
  copyToClipboard(names);
}

function copyFullInfo() {
  const lines = props.selectedItems.map((r) => {
    return `名称: ${r["名称"]} | 大小: ${r["文件大小"]} | 制作组: ${r["制作组"] || "未知"} | 标签: ${r["标签"] || "无"}`;
  });
  copyToClipboard(lines.join("\n"));
}

function clearSelection() {
  emit("clear-selection");
}
</script>

<template>
  <transition name="toolbar-slide">
    <div v-if="count > 0" class="batch-toolbar">
      <div class="batch-toolbar-inner">
        <div class="batch-count">
          <span class="batch-count-num">{{ count }}</span>
          <span class="batch-count-label">项已选中</span>
        </div>

        <div class="batch-divider" />

        <el-button-group>
          <el-button :icon="CopyDocument" size="small" @click="copyNames">
            复制名称
          </el-button>
          <el-button :icon="Document" size="small" @click="copyFullInfo">
            复制完整信息
          </el-button>
        </el-button-group>

        <el-button
          :icon="Delete"
          size="small"
          type="danger"
          plain
          @click="clearSelection"
        >
          清除选择
        </el-button>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.batch-toolbar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 200;
}

.batch-toolbar-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(18px) saturate(150%);
  -webkit-backdrop-filter: blur(18px) saturate(150%);
  border-radius: 16px;
  padding: 12px 20px;
  box-shadow: 0 18px 48px rgba(30, 64, 175, 0.24);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.7));
}

.batch-count {
  display: flex;
  align-items: center;
  gap: 6px;
}

.batch-count-num {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  background: linear-gradient(135deg, var(--color-primary, #1e40af), var(--color-secondary, #3b82f6));
  color: #fff;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
}

.batch-count-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.batch-divider {
  width: 1px;
  height: 24px;
  background: #e2e8f0;
}

/* 滑入动画 */
.toolbar-slide-enter-active,
.toolbar-slide-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.toolbar-slide-enter-from,
.toolbar-slide-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(40px);
}
</style>
