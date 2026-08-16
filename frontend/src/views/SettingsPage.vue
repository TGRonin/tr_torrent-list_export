<script setup>
/**
 * 设置页
 * - 连接配置表单（host、port、username、password）
 * - 保存并测试 / 仅保存 / 导出配置 / 导入配置
 * - 密码不回显：已设置时留空表示保持不变（keep_password）
 * - 后端启用 TR_API_TOKEN 后，401 时显示 Token 输入区
 */
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Upload, Download, Check } from "@element-plus/icons-vue";
import { fetchJson, setApiToken } from "../api";

const formRef = ref(null);
const fileInput = ref(null);
const config = ref({
  host: "",
  port: 9091,
  username: "",
  password: "",
});
const loading = ref(false);

/** 后端是否已存有密码（密码不回显，留空保持不变） */
const hasPassword = ref(false);

/** 401 时的 API Token 输入 */
const showTokenInput = ref(false);
const tokenInput = ref("");

const rules = {
  host: [
    { required: true, message: "请输入 Transmission 地址", trigger: "blur" },
  ],
  port: [
    { required: true, message: "请输入端口号", trigger: "blur" },
    {
      type: "number",
      min: 1,
      max: 65535,
      message: "端口范围 1-65535",
      trigger: "blur",
    },
  ],
};

/** 401 时展示 Token 输入区；返回是否已处理 */
function handleAuthError(err) {
  if (err && err.status === 401) {
    showTokenInput.value = true;
    return true;
  }
  return false;
}

function saveToken() {
  if (!tokenInput.value.trim()) {
    ElMessage.warning("请输入 Token");
    return;
  }
  setApiToken(tokenInput.value.trim());
  tokenInput.value = "";
  showTokenInput.value = false;
  ElMessage.success("Token 已保存，正在重新加载...");
  loadConfig();
}

async function loadConfig() {
  try {
    const data = await fetchJson("/api/config");
    config.value = {
      host: data.host || "",
      port: data.port || 9091,
      username: data.username || "",
      password: "",
    };
    hasPassword.value = !!data.has_password;
  } catch (err) {
    if (!handleAuthError(err)) {
      ElMessage.error("加载配置失败: " + err.message);
    }
  }
}

async function saveConfig(test = false) {
  if (!formRef.value) return;

  try {
    await formRef.value.validate();
  } catch {
    ElMessage.warning("请检查表单填写");
    return;
  }

  loading.value = true;
  try {
    const data = await fetchJson(`/api/config?test=${test ? "true" : "false"}`, {
      method: "POST",
      body: JSON.stringify({
        host: config.value.host,
        port: config.value.port,
        username: config.value.username,
        password: config.value.password,
        // 密码框留空且原本已有密码时，保持已存密码不变
        keep_password: hasPassword.value && !config.value.password,
      }),
    });
    config.value.password = "";
    hasPassword.value = !!data.has_password;
    if (test) {
      ElMessage.success("连接测试成功并已保存");
    } else {
      ElMessage.success("配置已保存");
    }
  } catch (err) {
    if (!handleAuthError(err)) {
      ElMessage.error(err.message || "保存失败");
    }
  } finally {
    loading.value = false;
  }
}

async function exportConfig() {
  try {
    const data = await fetchJson("/api/config/export");
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "config.json";
    link.click();
    URL.revokeObjectURL(link.href);
    ElMessage.success("配置已导出（不含密码）");
  } catch (err) {
    if (!handleAuthError(err)) {
      ElMessage.error("导出失败: " + err.message);
    }
  }
}

async function importConfig(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  try {
    const text = await file.text();
    const data = JSON.parse(text);
    const saved = await fetchJson("/api/config/import", {
      method: "POST",
      body: JSON.stringify({
        host: data.host,
        port: data.port,
        username: data.username || "",
        password: data.password || "",
        // 导入文件不含密码（新导出格式）时，保留当前已保存的密码
        keep_password: !data.password,
      }),
    });
    config.value = {
      host: saved.host || "",
      port: saved.port || 9091,
      username: saved.username || "",
      password: "",
    };
    hasPassword.value = !!saved.has_password;
    ElMessage.success("配置已导入");
  } catch (err) {
    if (!handleAuthError(err)) {
      ElMessage.error("导入失败: " + err.message);
    }
  }
  // 重置 file input，允许再次选择同一文件
  event.target.value = "";
}

onMounted(loadConfig);
</script>

<template>
  <div class="settings-page">
    <div class="panel">
      <div class="settings-intro">
        <h3>Transmission RPC 连接</h3>
        <p>填写服务器地址与凭据，保存后即可读取种子数据。</p>
      </div>

      <!-- Token 输入区：后端启用 TR_API_TOKEN 后返回 401 时显示 -->
      <div v-if="showTokenInput" class="token-panel">
        <el-alert
          title="此服务已启用 API 鉴权，请输入访问 Token（TR_API_TOKEN）"
          type="warning"
          show-icon
          :closable="false"
        />
        <div class="token-input-row">
          <el-input
            v-model="tokenInput"
            type="password"
            show-password
            placeholder="API Token"
            @keyup.enter="saveToken"
          />
          <el-button type="primary" @click="saveToken">保存并重试</el-button>
        </div>
      </div>

      <el-form
        ref="formRef"
        :model="config"
        :rules="rules"
        label-position="top"
        class="settings-form"
      >
        <el-form-item label="服务器地址" prop="host">
          <el-input
            v-model="config.host"
            placeholder="例如: 192.168.3.119"
          />
        </el-form-item>

        <el-form-item label="端口" prop="port">
          <el-input-number
            v-model="config.port"
            :min="1"
            :max="65535"
            controls-position="right"
          />
        </el-form-item>

        <el-form-item label="用户名" prop="username">
          <el-input v-model="config.username" placeholder="可选" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="config.password"
            type="password"
            show-password
            :placeholder="hasPassword ? '已设置，留空保持不变' : '可选'"
          />
        </el-form-item>
      </el-form>

      <div class="settings-actions">
        <el-button
          type="primary"
          :icon="Check"
          :loading="loading"
          @click="saveConfig(true)"
        >
          保存并测试
        </el-button>
        <el-button
          type="success"
          :loading="loading"
          @click="saveConfig(false)"
        >
          仅保存
        </el-button>
        <el-button :icon="Download" @click="exportConfig">
          导出配置
        </el-button>
        <input
          ref="fileInput"
          type="file"
          accept="application/json"
          style="display: none"
          @change="importConfig"
        />
        <el-button :icon="Upload" @click="fileInput && fileInput.click()">
          导入配置
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 700px;
}

.settings-intro {
  margin-bottom: 20px;
}

.settings-intro h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-strong, #1e3a8a);
}

.settings-intro p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary, #475569);
}

.token-panel {
  margin-bottom: 20px;
}

.token-input-row {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
</style>
