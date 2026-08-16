# tr_torrent-list_export

新增 Web UI 方案（Vue3 + Vite + FastAPI），支持 Docker 部署与本地配置持久化。配置通过 UI 进行读写，并保存至本地 JSON（可导入/导出）。

## 目录结构

- [`backend/app.py`](backend/app.py:1) FastAPI 后端
- [`backend/config.py`](backend/config.py:1) 配置读写
- [`config/config.json`](config/config.json:1) 本地配置文件（可持久化）
- [`frontend/src/App.vue`](frontend/src/App.vue:1) 前端页面
- [`frontend/src/styles/variables.css`](frontend/src/styles/variables.css:1) 主题样式

## 后端启动

```bash
pip install -r backend/requirements.txt
uvicorn backend.app:app --reload --port 8000
```

访问: `http://127.0.0.1:8000`

## 前端开发

```bash
cd frontend
npm install
npm run dev
```

Vite 代理 `/api` 到 `http://127.0.0.1:8000`。

## Docker

仅需映射容器内配置目录到本地持久化：

```bash
docker compose up --build
```

配置持久化目录：`./config` -> `/app/config`

## 说明

- 已移除 CSV 导出功能
- 配置走 UI 页面，不依赖环境变量
- 现代扁平化主题配色：天空蓝渐变背景、主色 #0EA5E9、辅助 #64748B、白色卡片 + 软阴影、点缀 #14B8A6、强调 #FCD34D
