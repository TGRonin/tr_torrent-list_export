# Docker 化部署（单镜像）

本文档描述 Web 前端与后端的容器化部署（单镜像）。

## 目录结构与职责

- 前端：Vue + Vite，构建产物输出到 `frontend/dist`。
- 后端：FastAPI，静态挂载 `frontend/dist` 并提供 `/api` 接口。
- 配置持久化：`config/config.json` 通过卷映射持久化。

## 前端构建期 API 配置说明

前端在浏览器中默认使用同域访问（`/api`），由 FastAPI 同容器提供静态页面与 API 服务，因此无需额外反向代理。

构建期可通过 `VITE_API_BASE` 指定 API 基地址（例如在非同域部署时）。该值会被注入到前端构建产物中：

- 默认值为空字符串（同域）。
- 若需要外部 API：在构建时传入 `VITE_API_BASE=http://localhost:8000`（或你的真实地址）。

实现逻辑在 [`frontend/src/api/index.js`](frontend/src/api/index.js:1)：
- 默认使用 `import.meta.env.VITE_API_BASE`（默认空字符串，走同域 `/api`）。

## 环境变量

参考示例：[`/.env.example`](.env.example:1)

- `TR_CONFIG_DIR`：后端配置目录（容器内路径）。
- `TRANSMISSION_HOST/PORT/USERNAME/PASSWORD`：Transmission 连接信息，容器启动时会写入或更新 `config/config.json`。
- `VITE_API_BASE`：前端构建期 API 地址（默认空字符串）。
- `TR_API_TOKEN`：配置 API 访问令牌（可选）。设置后，`/api/config` 相关接口（读取/保存/导入/导出）要求请求携带 `X-Api-Token` 请求头；留空则不鉴权。前端在"连接设置"页遇到 401 时会提示输入 Token 并保存在浏览器本地。

> 注意：敏感信息仅存储在后端配置文件中，前端不直接读取敏感变量。配置 API 不会返回密码明文（仅返回 `has_password` 标记）；"导出配置"生成的文件不含密码，导入此类文件时将保留当前已保存的密码。

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
# 1) 准备环境变量（可选，用于预置 Transmission 连接信息）
cp .env.example .env   # 然后按需修改 .env 中的 TRANSMISSION_* 配置

# 2) 构建并启动（前端 + 后端）
docker compose up --build
```

> `docker-compose.yml` 已通过 `env_file` 加载根目录 `.env`（文件不存在时不报错），并将 `TRANSMISSION_*` 变量透传到容器，由 [`scripts/entrypoint.sh`](scripts/entrypoint.sh:1) 写入 `config/config.json`。

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
