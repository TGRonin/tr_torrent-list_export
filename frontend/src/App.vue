<script setup>
import { computed, onMounted, ref } from "vue";
import { fetchJson } from "./api";

const activeTab = ref("list");
const search = ref("");
const label = ref("全部");
const maker = ref("全部");
const sortKey = ref("");
const sortDir = ref("");

const items = ref([]);
const total = ref(0);
const filtered = ref(0);
const labels = ref([]);
const makers = ref([]);
const loading = ref(false);
const error = ref("");

const config = ref({
  host: "",
  port: 9091,
  username: "",
  password: ""
});
const configMessage = ref("");

const loadFilters = async () => {
  const data = await fetchJson("/api/filters");
  labels.value = data.labels || [];
  makers.value = data.makers || [];
  total.value = data.total || 0;
};

const loadTorrents = async () => {
  loading.value = true;
  error.value = "";
  try {
    const params = new URLSearchParams({
      search: search.value,
      label: label.value,
      maker: maker.value
    });
    const data = await fetchJson(`/api/torrents?${params.toString()}`);
    items.value = data.items || [];
    total.value = data.total || 0;
    filtered.value = data.filtered || 0;
  } catch (err) {
    error.value = err.message || "加载失败";
  } finally {
    loading.value = false;
  }
};

const loadConfig = async () => {
  const data = await fetchJson("/api/config");
  config.value = data;
};

const saveConfig = async (test) => {
  configMessage.value = "";
  try {
    const data = await fetchJson(`/api/config?test=${test ? "true" : "false"}` , {
      method: "POST",
      body: JSON.stringify(config.value)
    });
    config.value = data;
    configMessage.value = test ? "连接测试成功并已保存" : "配置已保存";
  } catch (err) {
    configMessage.value = err.message || "保存失败";
  }
};

const exportConfig = async () => {
  const data = await fetchJson("/api/config/export");
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "config.json";
  link.click();
};

const importConfig = async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  const text = await file.text();
  const data = JSON.parse(text);
  const saved = await fetchJson("/api/config/import", {
    method: "POST",
    body: JSON.stringify(data)
  });
  config.value = saved;
  configMessage.value = "配置已导入";
};

const isSorted = (key) => sortKey.value === key;
const nextSortDir = (key) => {
  if (sortKey.value !== key) return "asc";
  if (sortDir.value === "asc") return "desc";
  if (sortDir.value === "desc") return "";
  return "asc";
};

const toggleSort = (key) => {
  const nextDir = nextSortDir(key);
  sortKey.value = nextDir ? key : "";
  sortDir.value = nextDir;
};

const sortIndicator = (key) => {
  if (!isSorted(key) || !sortDir.value) return "↕";
  return sortDir.value === "asc" ? "▲" : "▼";
};

const toNumber = (value) => {
  if (value === null || value === undefined || value === "") return Number.NEGATIVE_INFINITY;
  if (typeof value === "number") return value;
  const cleaned = String(value).replace(/[^\d.]/g, "");
  const parsed = Number.parseFloat(cleaned);
  return Number.isFinite(parsed) ? parsed : Number.NEGATIVE_INFINITY;
};

const toString = (value) => (value === null || value === undefined ? "" : String(value));

const sortedItems = computed(() => {
  const data = items.value.map((item, index) => ({ item, index }));
  if (!sortKey.value || !sortDir.value) return data.map((entry) => entry.item);
  const dir = sortDir.value === "asc" ? 1 : -1;
  const sorted = data.sort((a, b) => {
    if (sortKey.value === "size" || sortKey.value === "label_count") {
      const rawKey = sortKey.value === "size" ? "原始文件大小" : "标签数量";
      const fallbackKey = sortKey.value === "size" ? "文件大小" : "标签数量";
      const aVal = toNumber(a.item[rawKey] ?? a.item[fallbackKey]);
      const bVal = toNumber(b.item[rawKey] ?? b.item[fallbackKey]);
      if (aVal !== bVal) return (aVal - bVal) * dir;
      return a.index - b.index;
    }
    const aText = toString(a.item[sortKey.value === "name" ? "名称" : "制作组"]);
    const bText = toString(b.item[sortKey.value === "name" ? "名称" : "制作组"]);
    const cmp = aText.localeCompare(bText, "zh", { numeric: true, sensitivity: "base" });
    if (cmp !== 0) return cmp * dir;
    return a.index - b.index;
  });
  return sorted.map((entry) => entry.item);
});

onMounted(async () => {
  await loadConfig();
  await loadFilters();
  await loadTorrents();
});
</script>

<template>
  <div class="app-shell">
    <header class="header">
      <h1>Transmission 种子列表</h1>
      <div class="status-chip">
        <span class="badge">在线数据</span>
        <span>总数 {{ total }} / 过滤后 {{ filtered }}</span>
      </div>
    </header>

    <nav class="nav-tabs">
      <button :class="{ active: activeTab === 'list' }" @click="activeTab = 'list'">
        列表视图
      </button>
      <button :class="{ active: activeTab === 'settings' }" @click="activeTab = 'settings'">
        连接设置
      </button>
    </nav>

    <section v-if="activeTab === 'list'">
      <div class="panel">
        <div class="filters">
          <input
            class="input"
            v-model="search"
            placeholder="搜索名称 / 标签"
            @input="loadTorrents"
          />
          <select v-model="label" @change="loadTorrents">
            <option>全部</option>
            <option v-for="item in labels" :key="item" :value="item">{{ item }}</option>
          </select>
          <select v-model="maker" @change="loadTorrents">
            <option>全部</option>
            <option v-for="item in makers" :key="item" :value="item">{{ item }}</option>
          </select>
          <button class="button" @click="loadTorrents">刷新</button>
        </div>
      </div>

      <div class="panel">
        <div class="table-wrapper">
          <table class="table">
            <colgroup>
              <col class="col-name" />
              <col class="col-size" />
              <col class="col-maker" />
              <col class="col-count" />
              <col class="col-tags" />
            </colgroup>
            <thead>
              <tr>
                <th class="sortable" @click="toggleSort('name')">
                  <span>名称</span>
                  <span class="sort-indicator" :class="{ active: isSorted('name') }">{{ sortIndicator('name') }}</span>
                </th>
                <th class="sortable" @click="toggleSort('size')">
                  <span>文件大小</span>
                  <span class="sort-indicator" :class="{ active: isSorted('size') }">{{ sortIndicator('size') }}</span>
                </th>
                <th class="sortable" @click="toggleSort('maker')">
                  <span>制作组</span>
                  <span class="sort-indicator" :class="{ active: isSorted('maker') }">{{ sortIndicator('maker') }}</span>
                </th>
                <th class="sortable" @click="toggleSort('label_count')">
                  <span>标签数量</span>
                  <span class="sort-indicator" :class="{ active: isSorted('label_count') }">{{ sortIndicator('label_count') }}</span>
                </th>
                <th>标签</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="5">加载中...</td>
              </tr>
              <tr v-if="error">
                <td colspan="5">{{ error }}</td>
              </tr>
              <tr v-for="row in sortedItems" :key="row['名称']">
                <td class="cell-name">{{ row['名称'] }}</td>
                <td class="cell-size">{{ row['文件大小'] }}</td>
                <td class="cell-maker">{{ row['制作组'] }}</td>
                <td class="cell-count">{{ row['标签数量'] }}</td>
                <td class="cell-tags">
                  <div class="tags-grid">
                    <span
                      v-for="tag in row['标签'].split(',').map(t => t.trim()).filter(Boolean)"
                      :key="tag"
                      class="tag"
                    >{{ tag }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section v-else>
      <div class="panel">
        <div class="settings-grid">
          <div class="form-row">
            <label>Transmission Host</label>
            <input class="input" v-model="config.host" placeholder="192.168.3.119" />
          </div>
          <div class="form-row">
            <label>端口</label>
            <input class="input" type="number" v-model.number="config.port" />
          </div>
          <div class="form-row">
            <label>用户名</label>
            <input class="input" v-model="config.username" />
          </div>
          <div class="form-row">
            <label>密码</label>
            <input class="input" type="password" v-model="config.password" />
          </div>
        </div>
        <div style="display:flex; gap:12px; margin-top:16px; flex-wrap:wrap;">
          <button class="button" @click="saveConfig(true)">保存并测试</button>
          <button class="button secondary" @click="saveConfig(false)">仅保存</button>
          <button class="button ghost" @click="exportConfig">导出配置</button>
          <label class="button ghost" style="cursor:pointer;">
            导入配置
            <input type="file" accept="application/json" style="display:none" @change="importConfig" />
          </label>
        </div>
        <p class="helper" style="margin-top:12px;">{{ configMessage }}</p>
      </div>
    </section>

    <footer class="footer">现代扁平化界面 · 云端存储风格配色</footer>
  </div>
</template>
