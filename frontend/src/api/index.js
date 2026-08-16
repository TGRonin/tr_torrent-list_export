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

/** 请求超时时间（毫秒） */
const REQUEST_TIMEOUT = 15000;

/**
 * 通用 JSON 请求封装
 * - 携带已保存的 API Token（后端设置 TR_API_TOKEN 时必需）
 * - 15 秒超时，防止请求无限挂起
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
  try {
    const res = await fetch(`${base}${url}`, {
      ...options,
      headers,
      // 调用方自带 signal 时不覆盖，否则启用 15s 超时
      signal: options.signal || AbortSignal.timeout(REQUEST_TIMEOUT),
    });
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
    return await res.json();
  } catch (err) {
    // AbortSignal.timeout 超时抛出 TimeoutError（旧实现为 AbortError）
    if (err && (err.name === "TimeoutError" || err.name === "AbortError")) {
      throw new Error("请求超时，请检查后端服务");
    }
    throw err;
  }
}
