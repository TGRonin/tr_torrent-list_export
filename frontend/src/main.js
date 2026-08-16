import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./styles/variables.css";

// Element Plus 的组件/指令/样式（含 ElMessage 等 API 及其样式）
// 由 vite.config.js 中的 unplugin-auto-import + unplugin-vue-components
// （ElementPlusResolver）按需注入，此处不再全量引入与注册图标。
const app = createApp(App);

app.use(router);
app.mount("#app");
