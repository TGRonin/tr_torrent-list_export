<script setup>
/**
 * 数据统计仪表盘
 * - 4 个统计概览卡片
 * - 4 个 ECharts 图表（制作组 Top10、制作组存储占比、标签频次 Top10、文件大小分布）
 * - 制作组明细表格
 */
import { computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Refresh } from "@element-plus/icons-vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { BarChart, PieChart } from "echarts/charts";
import { GridComponent, TooltipComponent, LegendComponent } from "echarts/components";
import VChart from "vue-echarts";
import { useStats } from "../composables/useStats";

use([
  CanvasRenderer,
  BarChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
]);

const { stats, loading, error, fetchStats } = useStats();

/** 格式化字节数为可读单位 */
function formatBytes(bytes) {
  if (!bytes || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  let val = bytes;
  let idx = 0;
  while (val >= 1024 && idx < units.length - 1) {
    val /= 1024;
    idx++;
  }
  return `${val.toFixed(2)} ${units[idx]}`;
}

const totalSizeFormatted = computed(() =>
  formatBytes(stats.value?.total_size_bytes || 0)
);

/** 制作组 Top 10 柱状图配置 */
const makerBarOption = computed(() => {
  const top10 = (stats.value?.maker_stats || []).slice(0, 10);
  return {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: "3%", right: "5%", bottom: "3%", containLabel: true },
    xAxis: { type: "value", axisLine: { show: false } },
    yAxis: {
      type: "category",
      data: top10.map((m) => m.maker).reverse(),
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: "bar",
        data: top10.map((m) => m.count).reverse(),
        itemStyle: { color: "#1e40af", borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: "right", fontSize: 11 },
      },
    ],
  };
});

/** 制作组存储占比环形图配置 */
const makerDoughnutOption = computed(() => {
  const top10 = (stats.value?.maker_stats || []).slice(0, 10);
  const colors = [
    "#1e40af", "#3b82f6", "#0d9488", "#d97706", "#6366f1",
    "#0891b2", "#2563eb", "#059669", "#f59e0b", "#7c3aed",
  ];
  return {
    tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
    legend: {
      type: "scroll",
      orient: "vertical",
      right: 0,
      top: "center",
      textStyle: { fontSize: 11 },
    },
    series: [
      {
        type: "pie",
        radius: ["45%", "70%"],
        center: ["35%", "50%"],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 4 },
        label: { show: false },
        data: top10.map((m, i) => ({
          name: m.maker,
          value: m.size_bytes,
          itemStyle: { color: colors[i % colors.length] },
        })),
      },
    ],
  };
});

/** 标签频次 Top 10 柱状图配置 */
const labelBarOption = computed(() => {
  const top10 = (stats.value?.label_stats || []).slice(0, 10);
  return {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: "3%", right: "5%", bottom: "3%", containLabel: true },
    xAxis: {
      type: "category",
      data: top10.map((l) => l.label),
      axisLabel: { rotate: 30, fontSize: 11 },
    },
    yAxis: { type: "value", axisLine: { show: false } },
    series: [
      {
        type: "bar",
        data: top10.map((l) => l.count),
        itemStyle: { color: "#0d9488", borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: "top", fontSize: 11 },
      },
    ],
  };
});

/** 文件大小分布柱状图配置 */
const sizeDistOption = computed(() => {
  const dist = stats.value?.size_distribution || [];
  return {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: "3%", right: "5%", bottom: "3%", containLabel: true },
    xAxis: {
      type: "category",
      data: dist.map((d) => d.range),
      axisLabel: { fontSize: 11 },
    },
    yAxis: { type: "value", axisLine: { show: false } },
    series: [
      {
        type: "bar",
        data: dist.map((d) => d.count),
        itemStyle: { color: "#6366f1", borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: "top", fontSize: 11 },
      },
    ],
  };
});

/** 制作组明细表格数据 */
const makerTableData = computed(() => {
  const all = stats.value?.maker_stats || [];
  const totalSize = all.reduce((s, m) => s + m.size_bytes, 0);
  return all.map((m) => ({
    ...m,
    size_str: formatBytes(m.size_bytes),
    avg_size: formatBytes(m.count > 0 ? Math.round(m.size_bytes / m.count) : 0),
    pct: totalSize > 0 ? ((m.size_bytes / totalSize) * 100).toFixed(1) : "0.0",
  }));
});

async function handleRefresh() {
  await fetchStats();
  if (!error.value) {
    ElMessage.success("统计数据已刷新");
  }
}

onMounted(fetchStats);
</script>

<template>
  <div class="dashboard-page" v-loading="loading">
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      closable
      style="margin-bottom: 16px"
    />

    <!-- 顶栏 -->
    <div class="dashboard-header">
      <div class="dashboard-heading">
        <h3>种子数据总览</h3>
        <span class="dashboard-sub">制作组、标签与存储的可视化分析</span>
      </div>
      <el-button
        type="primary"
        :icon="Refresh"
        :loading="loading"
        @click="handleRefresh"
      >
        刷新
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: rgba(30, 64, 175, 0.14); color: #1e40af">
            T
          </div>
          <div class="stat-label">总种子数</div>
          <div class="stat-value">{{ stats?.total_count ?? 0 }}</div>
          <div class="stat-sub">去重后合并种子</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: rgba(59, 130, 246, 0.14); color: #3b82f6">
            D
          </div>
          <div class="stat-label">总存储量</div>
          <div class="stat-value">{{ totalSizeFormatted }}</div>
          <div class="stat-sub">所有种子文件大小之和</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: rgba(13, 148, 136, 0.14); color: #0d9488">
            M
          </div>
          <div class="stat-label">制作组数</div>
          <div class="stat-value">{{ stats?.maker_count ?? 0 }}</div>
          <div class="stat-sub">已识别的发布组</div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: rgba(217, 119, 6, 0.14); color: #d97706">
            L
          </div>
          <div class="stat-label">标签种类</div>
          <div class="stat-value">{{ stats?.label_count ?? 0 }}</div>
          <div class="stat-sub">不重复标签总数</div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <div class="panel">
          <h4 class="chart-title">制作组种子数 Top 10</h4>
          <v-chart
            v-if="stats"
            class="chart-canvas"
            :option="makerBarOption"
            autoresize
          />
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="panel">
          <h4 class="chart-title">制作组存储占比</h4>
          <v-chart
            v-if="stats"
            class="chart-canvas"
            :option="makerDoughnutOption"
            autoresize
          />
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="panel">
          <h4 class="chart-title">标签使用频次 Top 10</h4>
          <v-chart
            v-if="stats"
            class="chart-canvas"
            :option="labelBarOption"
            autoresize
          />
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="panel">
          <h4 class="chart-title">文件大小分布</h4>
          <v-chart
            v-if="stats"
            class="chart-canvas"
            :option="sizeDistOption"
            autoresize
          />
        </div>
      </el-col>
    </el-row>

    <!-- 制作组明细表 -->
    <div class="panel">
      <h4 class="chart-title">制作组明细</h4>
      <el-table
        :data="makerTableData"
        stripe
        border
        style="width: 100%"
        max-height="400"
      >
        <el-table-column prop="maker" label="制作组" min-width="160" />
        <el-table-column prop="count" label="种子数" width="100" align="right" />
        <el-table-column prop="size_str" label="总大小" width="120" align="right" />
        <el-table-column prop="avg_size" label="平均大小" width="120" align="right" />
        <el-table-column label="占比" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.pct }}%</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.dashboard-heading h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-strong, #1e3a8a);
  margin: 0;
}

.dashboard-sub {
  font-size: 12px;
  color: var(--text-secondary, #475569);
}

.stat-row {
  margin-bottom: 4px;
}

.stat-card {
  background: var(--glass-bg, rgba(255, 255, 255, 0.62));
  backdrop-filter: blur(16px) saturate(140%);
  -webkit-backdrop-filter: blur(16px) saturate(140%);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.7));
  border-radius: 16px;
  padding: 20px;
  box-shadow: var(--shadow-md, 0 10px 30px rgba(30, 64, 175, 0.10));
  margin-bottom: 16px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 38px rgba(30, 64, 175, 0.18);
}

.stat-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  font-family: var(--font-mono, monospace);
  margin-bottom: 10px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary, #64748b);
  margin-bottom: 6px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--text-strong, #1e3a8a);
  font-family: var(--font-mono, monospace);
  font-variant-numeric: tabular-nums;
}

.stat-sub {
  font-size: 11px;
  color: var(--text-muted, #94a3b8);
  margin-top: 6px;
}

.chart-title {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-strong, #1e3a8a);
}

.chart-canvas {
  width: 100%;
  height: 280px;
}
</style>
