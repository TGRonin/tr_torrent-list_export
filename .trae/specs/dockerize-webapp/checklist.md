* [x] docker-compose.yml 通过 env\_file 加载 `.env` 并透传 TRANSMISSION\_\* 环境变量

* [x] docker-compose.yml 保留 config 卷映射与 TR\_CONFIG\_DIR，配置可持久化

* [x] Dockerfile 前端阶段复制 package-lock.json 并使用 npm ci

* [x] Dockerfile 后端阶段与 entrypoint 逻辑保持可运行

* [x] README.docker.md 引用 frontend/src/api/index.js（无死链）且开发端口为 5173

* [x] README.docker.md 包含复制 .env.example 为 .env 的步骤

* [x] `docker compose config` 语法校验通过（本机未安装 Docker，无法执行实际 build/up）

* [ ] `docker compose up` 后 <http://localhost:8000/> 返回前端页面（需在有 Docker 的环境执行）

* [ ] <http://localhost:8000/api/config> 返回 JSON 配置（需在有 Docker 的环境执行）

