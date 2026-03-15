# Docker 化部署（单镜像）

本文档严格遵循 [`docker容器规划.md`](docker容器规划.md:1) 的约束：仅容器化 Web 前端与后端，桌面端与 NSIS 打包不进入容器流程。

## 目录结构与职责

- 前端：Vue + Vite，构建产物输出到 `frontend/dist`。
- 后端：FastAPI，静态挂载 `frontend/dist` 并提供 `/api` 接口。
- 配置持久化：`config/config.json` 通过卷映射持久化。

## 前端构建期 API 配置说明

前端在浏览器中默认使用同域访问（`/api`），由 FastAPI 同容器提供静态页面与 API 服务，因此无需额外反向代理。

构建期可通过 `VITE_API_BASE` 指定 API 基地址（例如在非同域部署时）。该值会被注入到前端构建产物中：

- 默认值为空字符串（同域）。
- 若需要外部 API：在构建时传入 `VITE_API_BASE=http://localhost:8000`（或你的真实地址）。

实现逻辑在 [`frontend/src/desktop.js`](frontend/src/desktop.js:1)：
- 先读取 `?port=`（桌面端兼容逻辑）。
- 若无 `port`，则使用 `import.meta.env.VITE_API_BASE`。

## 环境变量

参考示例：[`/.env.example`](.env.example:1)

- `TR_CONFIG_DIR`：后端配置目录（容器内路径）。
- `TRANSMISSION_HOST/PORT/USERNAME/PASSWORD`：Transmission 连接信息，容器启动时会写入或更新 `config/config.json`。
- `VITE_API_BASE`：前端构建期 API 地址（默认空字符串）。

> 注意：敏感信息仅存储在后端配置文件中，前端不直接读取敏感变量。

## Dockerfile 与 Compose

- 多阶段构建：前端 build + 后端运行。
- 端口：`8000` 对外暴露。
- 前端静态资源由 FastAPI 挂载：`/` -> `frontend/dist`。

关键文件：
- [`Dockerfile`](Dockerfile:1)
- [`docker-compose.yml`](docker-compose.yml:1)
- [`scripts/entrypoint.sh`](scripts/entrypoint.sh:1)

## 一键启动

```bash
# 构建并启动（前端 + 后端）
docker compose up --build
```

启动后访问：
- 前端：`http://localhost:8000/`
- API：`http://localhost:8000/api`

## 卷映射

`docker-compose.yml` 中已映射：

```yaml
volumes:
  - ./config:/app/config
```

配置文件持久化路径：`config/config.json`

## 运行流程

1. 前端在构建阶段生成 `frontend/dist`。
2. 后端容器启动时执行 [`scripts/entrypoint.sh`](scripts/entrypoint.sh:1)：
   - 将 `TRANSMISSION_*` 环境变量写入 `config/config.json`（若提供）。
   - 启动 `uvicorn` 提供 API 与静态页面。

## 备注（桌面端）

桌面端仍需在宿主机 Windows 上执行 `npm run build` 与 Tauri/Rust 打包流程，容器仅用于 Web 前端与后端部署。
