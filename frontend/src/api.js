import { resolveApiBase } from "./desktop";

export async function fetchJson(url, options = {}) {
  const base = resolveApiBase();
  const res = await fetch(`${base}${url}`, {
    headers: {
      "Content-Type": "application/json"
    },
    ...options
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "请求失败");
  }
  return res.json();
}
