<script setup>
/**
 * 设置页
 * - 连接配置表单（host、port、username、password）
 * - 保存并测试 / 仅保存 / 导出配置 / 导入配置
 * - 表单验证
 */
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Upload, Download, Check } from "@element-plus/icons-vue";
import { fetchJson } from "../api";

const formRef = ref(null);
const config = ref({
  host: "",
  port: 9091,
  username: "",
  password: "",
});
const loading = ref(false);

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

async function loadConfig() {
  try {
    const data = await fetchJson("/api/config");
    config.value = data;
  } catch (err) {
    ElMessage.error("加载配置失败: " + err.message);
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
      body: JSON.stringify(config.value),
    });
    config.value = data;
    if (test) {
      ElMessage.success("连接测试成功并已保存");
    } else {
      ElMessage.success("配置已保存");
    }
  } catch (err) {
    ElMessage.error(err.message || "保存失败");
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
    ElMessage.success("配置已导出");
  } catch (err) {
    ElMessage.error("导出失败: " + err.message);
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
      body: JSON.stringify(data),
    });
    config.value = saved;
    ElMessage.success("配置已导入");
  } catch (err) {
    ElMessage.error("导入失败: " + err.message);
  }
  // 重置 file input
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
            placeholder="可选"
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
        <el-upload
          :show-file-list="false"
          accept="application/json"
          style="display: inline-block"
        >
          <el-button :icon="Upload">
            导入配置
            <input
              type="file"
              accept="application/json"
              style="display: none"
              @change="importConfig"
            />
          </el-button>
        </el-upload>
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
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-strong, #1e3a8a);
}

.settings-intro p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary, #475569);
}
</style>
