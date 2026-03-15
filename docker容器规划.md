# Docker 容器规划

## 容器化目标
本项目的容器化目标是将前端 Vue 构建产物与后端 Python 服务解耦部署，保证在 Linux 环境中可重复构建与稳定运行，并保持与当前桌面端 Tauri 打包流程互不干扰。容器化侧重于 Web 形态的可部署服务与数据处理逻辑，不将 Windows NSIS 安装器打包纳入容器构建范围，以避免跨平台构建不可控因素。

## 项目组件概览
前端为 Vue 应用，入口逻辑集中在 [`frontend/src/App.vue`](frontend/src/App.vue:1)，构建由 Vite 完成，静态产物输出到 `frontend/dist`。后端为 Python 脚本与接口能力，核心数据处理逻辑位于 [`torrent_processor.py`](torrent_processor.py:1)，可与现有后端服务集成或作为独立服务运行。桌面端为 Tauri 应用，配置位于 [`desktop/src-tauri/tauri.conf.json`](desktop/src-tauri/tauri.conf.json:1)，打包目标已从 MSI 调整为 NSIS，构建依赖 Rust 工具链与系统级 Windows 打包环境。

## 推荐容器划分与镜像职责
将容器统一构建成一个镜像，使用 `docker-compose.yml` 作为编排入口，保证前端与后端在同一网络中协作，同时为本地配置与导出数据提供持久化挂载。

## 构建与运行流程
构建流程应先完成前端依赖安装与静态产物构建，再启动后端服务提供 API，最终由前端容器或独立静态服务器容器提供页面访问。对于 Tauri 桌面端构建，继续在宿主机 Windows 环境执行 `npm run build` 并触发 Rust 编译与打包，容器仅作为 Web 与后端服务部署载体。若需要在容器中执行 Node 构建，必须确保 Node 版本与 Vite 兼容，并固定依赖版本以规避构建不一致。

## 必要环境变量
后端容器需要提供 Transmission 连接与配置相关的环境变量，包含主机、端口、用户名、密码与可选的代理或超时配置，且应与已有配置文件路径兼容。前端容器不直接使用敏感环境变量，而是通过后端 API 提供配置读写能力，避免在镜像中固化密钥。若仍需前端构建期注入 API 地址，使用构建时环境变量并在构建日志中记录实际值以便追溯。

## 卷映射与产物位置
后端容器应映射配置目录与输出目录到宿主机，确保 `config/config.json` 能持久化。前端容器若以静态文件形式部署，将 `frontend/dist` 作为构建产物目录，并在运行时以只读方式挂载到 Web 服务器根目录。桌面端构建产物仍保留在 `desktop/src-tauri/target` 与安装器输出目录，避免与容器卷混用。

## 跨平台与 Windows NSIS 打包限制
NSIS 安装器仅支持 Windows 环境构建，且依赖系统工具链与图标资源配置，容器化并不能稳定替代本地 Windows 构建。Linux 容器中无法直接生成 Windows NSIS 安装器，替代方案是在 Windows 宿主机本地执行 Tauri 构建，同时容器仅提供 API 与前端构建能力。若必须实现 CI 打包，应使用 Windows Runner 或专用构建机，而非在 Linux Docker 中模拟。

## 面向后续对话的操作指引要点
后续指挥 agent 时应明确容器化范围仅覆盖 Web 前端与后端服务，桌面端构建与 NSIS 打包仍在 Windows 宿主机执行。指令需区分构建阶段与运行阶段，强调前端产物路径为 `frontend/dist`，后端配置目录为 `config/`，并保持对现有构建命令 `npm run build` 与 Rust 打包流程的独立描述，避免将 Tauri 打包混入容器构建步骤。