/**
 * 解析 API 基地址
 * - 默认同域访问（开发环境由 Vite 代理 /api）
 * - 可通过 VITE_API_BASE 环境变量覆盖
 */
function resolveApiBase() {
  return import.meta.env.VITE_API_BASE || "";
}

const TOKEN_KEY = "tr_api_token";

export function getApiToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setApiToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

/**
 * 通用 JSON 请求封装
 * - 携带已保存的 API Token（后端设置 TR_API_TOKEN 时必需）
 * - 非 2xx 时解析 FastAPI 的 {"detail": "..."} 为可读错误，并挂载 status
 */
export async function fetchJson(url, options = {}) {
  const base = resolveApiBase();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  const token = getApiToken();
  if (token) {
    headers["X-Api-Token"] = token;
  }
  const res = await fetch(`${base}${url}`, { ...options, headers });
  if (!res.ok) {
    const text = await res.text();
    let message = text;
    try {
      message = JSON.parse(text).detail || text;
    } catch {
      // 非 JSON 响应体，原样使用
    }
    const err = new Error(message || "请求失败");
    err.status = res.status;
    throw err;
  }
  return res.json();
}
