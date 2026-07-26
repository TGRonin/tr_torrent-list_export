# 在 Docker 上运行本项目 Spec

## Why
用户希望将本项目（Transmission 种子列表导出/查看 Web 应用）在 Docker 上运行。项目已存在基础 Docker 配置，但存在若干缺口（compose 未加载 `.env`、依赖锁定缺失、默认配置含硬编码敏感信息、文档细节偏差），需要修复缺口并给出清晰、可复现的运行方案。

## What Changes
- 修复 `docker-compose.yml`：显式加载 `.env` 文件（`env_file`），并将 `TRANSMISSION_*` 环境变量透传到容器，使 `.env.example` 配置真正生效。
- 优化 `Dockerfile`：复制 `package-lock.json` 并使用 `npm ci` 保证前端依赖可复现；后端安装保持不变。
- 校正 `README.docker.md` 中与代码不一致的细节（前端开发端口应为 `5173`，文件引用 `frontend/src/api/index.js` 而非不存在的 `desktop.js`）。
- 验证并跑通 `docker compose up --build`，确认前端页面与 `/api` 接口在 `http://localhost:8000` 正常访问。
- 不改动应用业务逻辑；不容器化桌面端（Tauri/PySide），遵循 [docker容器规划.md](docker容器规划.md) 的约束。

## Impact
- Affected specs: 容器化部署（Web 前端 + 后端单镜像）
- Affected code:
  - [Dockerfile](Dockerfile)
  - [docker-compose.yml](docker-compose.yml)
  - [scripts/entrypoint.sh](scripts/entrypoint.sh)（仅验证，预计不改）
  - [README.docker.md](README.docker.md)
  - [.env.example](.env.example)（仅验证/补充说明）

## ADDED Requirements

### Requirement: Compose 加载环境变量
系统 SHALL 在 `docker-compose.yml` 中通过 `env_file` 加载项目根目录 `.env`，并将 `TRANSMISSION_HOST/PORT/USERNAME/PASSWORD`、`TR_CONFIG_DIR` 透传到容器，使用户复制 `.env.example` 为 `.env` 后配置即可生效。

#### Scenario: 通过 .env 配置 Transmission 连接
- **WHEN** 用户复制 `.env.example` 为 `.env` 并填写 `TRANSMISSION_HOST` 等变量后执行 `docker compose up --build`
- **THEN** 容器启动时 [entrypoint.sh](scripts/entrypoint.sh) 将这些变量写入 `/app/config/config.json`，前端 `/api/config` 返回对应连接信息

### Requirement: 前端依赖可复现构建
系统 SHALL 在 Dockerfile 前端构建阶段复制 `package-lock.json` 并使用 `npm ci`，以保证依赖版本可复现。

#### Scenario: 可复现的前端构建
- **WHEN** 执行 `docker compose build`
- **THEN** 前端依赖依据 `package-lock.json` 精确安装，`npm run build` 成功生成 `frontend/dist`

### Requirement: 一键运行 Web 应用
系统 SHALL 支持通过单条命令 `docker compose up --build` 启动，暴露端口 `8000`，由 FastAPI 同时提供前端静态页面（`/`）与 API（`/api`）。

#### Scenario: 启动后可访问
- **WHEN** 容器成功启动
- **THEN** 访问 `http://localhost:8000/` 返回前端页面，访问 `http://localhost:8000/api/config` 返回 JSON 配置

### Requirement: 文档与代码一致
系统 SHALL 使 `README.docker.md` 中的关键引用与实际代码一致（前端 API 解析逻辑位于 [frontend/src/api/index.js](frontend/src/api/index.js)，开发端口为 `5173`）。

#### Scenario: 文档指向真实文件
- **WHEN** 用户按 `README.docker.md` 查阅前端 API 配置逻辑
- **THEN** 文档指向存在的文件与正确端口，无死链

## MODIFIED Requirements
（无：现有 entrypoint 与静态挂载逻辑保持不变）

## REMOVED Requirements
（无）
