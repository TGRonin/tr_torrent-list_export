/**
 * 解析 API 基地址
 * - Tauri 桌面端通过 ?port=xxxx 查询参数传入
 * - 开发环境由 Vite 代理，无需指定
 * - 可通过 VITE_API_BASE 环境变量覆盖
 */
function resolveApiBase() {
  const params = new URLSearchParams(window.location.search);
  const port = params.get("port");
  if (port) {
    return `http://127.0.0.1:${port}`;
  }
  return import.meta.env.VITE_API_BASE || "";
}

/**
 * 通用 JSON 请求封装
 */
export async function fetchJson(url, options = {}) {
  const base = resolveApiBase();
  const res = await fetch(`${base}${url}`, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "请求失败");
  }
  return res.json();
}
