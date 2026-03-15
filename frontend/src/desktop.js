export function resolveApiBase() {
  const params = new URLSearchParams(window.location.search);
  const port = params.get("port");
  if (port) {
    return `http://127.0.0.1:${port}`;
  }
  const buildBase = import.meta.env.VITE_API_BASE || "";
  return buildBase;
}
