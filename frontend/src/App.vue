<script setup>
/**
 * 根布局组件（明亮玻璃拟态 · 侧边栏版）
 * - 左侧固定玻璃侧边栏：品牌 + 导航 + 连接状态
 * - 右侧主内容区：动态标题顶部条 + RouterView
 */
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { List, Setting, DataAnalysis } from "@element-plus/icons-vue";

const router = useRouter();
const route = useRoute();

const activeMenu = computed(() => route.name || "list");

/** 导航项配置 */
const navItems = [
  { name: "list", label: "列表视图", icon: List, title: "种子列表", sub: "浏览、搜索与批量管理" },
  { name: "dashboard", label: "数据统计", icon: DataAnalysis, title: "数据统计", sub: "制作组、标签与存储分析" },
  { name: "settings", label: "连接设置", icon: Setting, title: "连接设置", sub: "配置 Transmission RPC 连接" },
];

/** 当前页标题信息 */
const current = computed(
  () => navItems.find((i) => i.name === activeMenu.value) || navItems[0]
);

function go(name) {
  if (name !== activeMenu.value) router.push({ name });
}
</script>

<template>
  <div class="app-shell">
    <!-- 侧边栏 -->
    <aside class="app-sidebar">
      <div class="sidebar-brand">
        <span class="sidebar-logo">
          <el-icon :size="22"><DataAnalysis /></el-icon>
        </span>
        <span class="sidebar-brand-text">
          <span class="sidebar-brand-title">Torrent Manager</span>
          <span class="sidebar-brand-sub">Transmission 控制台</span>
        </span>
      </div>

      <nav class="sidebar-nav">
        <span class="sidebar-nav-label">导航</span>
        <div
          v-for="item in navItems"
          :key="item.name"
          class="nav-item"
          :class="{ 'is-active': item.name === activeMenu }"
          role="button"
          :tabindex="0"
          @click="go(item.name)"
          @keyup.enter="go(item.name)"
        >
          <span class="nav-icon">
            <el-icon><component :is="item.icon" /></el-icon>
          </span>
          <span>{{ item.label }}</span>
        </div>
      </nav>

      <div class="sidebar-footer">
        <span class="status-dot"></span>在线数据源
        <br />
        实时读取 Transmission 种子信息
      </div>
    </aside>

    <!-- 主内容 -->
    <main class="app-main">
      <div class="main-topbar">
        <div>
          <h1>{{ current.title }}</h1>
          <div class="topbar-sub">{{ current.sub }}</div>
        </div>
        <div class="status-chip">
          <span class="badge"><span class="status-dot"></span>在线数据</span>
        </div>
      </div>

      <router-view />
    </main>
  </div>
</template>
