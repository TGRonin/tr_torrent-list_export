# Transmission-rpc（Python）使用文档

> 适用对象：希望用 Python 远程控制 Transmission（`transmission-daemon`）的开发者
>  依赖项目：[`Trim21/transmission-rpc`](https://github.com/Trim21/transmission-rpc) 与 Transmission 官方 RPC 规范
>  文档依据：官方 Sphinx 文档、GitHub README 与 Transmission RPC 规范。

------

## 1. 概览

`transmission-rpc` 是一个 Python3 库，用于通过 JSON-RPC 控制本机或远程的 Transmission 守护进程（`transmission-daemon`）。库内提供 `Client`、`Torrent`、`Session` 等对象以及常用操作（新增/查询/修改/移动/队列控制等）。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/))

- **推荐的种子标识**：建议使用种子的 `info_hash` 作为 ID（稳定且不会变化）。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))
- **与 RPC 版本**：部分参数仅在较新的 RPC 版本中可用（如 `labels`、`group` 等）；请参考 RPC 规范与文档中每个方法的说明。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))

------

## 2. 安装

```bash
pip install transmission-rpc
```

> 若你使用的是较新版本的 Transmission（4.x/5.x），请优先使用最新版 `transmission-rpc`。功能/参数支持以库文档与 RPC 规范为准。([GitHub](https://github.com/trim21/transmission-rpc), [transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))

------

## 3. 连接与初始化

### 3.1 最快上手

```python
from transmission_rpc import Client

c = Client(host="localhost", port=9091, username="transmission", password="password")
c.add_torrent("magnet:?xt=urn:btih:...")   # 直接添加磁力链接
```

或使用 `from_url` 一次性传入 URL：

```python
from transmission_rpc import from_url

c = from_url("http://127.0.0.1:9091/transmission/rpc")
```

> 注意：必须包含 **scheme**（`http://` 或 `https://`）；`127.0.0.1:9091` 不是有效 URL。`http://127.0.0.1` 与 `http://127.0.0.1/` 的 `path` 不同。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))

### 3.2 构造参数

```python
Client(
  protocol="http",           # 或 "https"
  username=None, password=None,
  host="127.0.0.1", port=9091,
  path="/transmission/rpc",
  timeout=30.0,
)
```

- `timeout` 可在实例化或调用方法时单独传入。
- `Client.rpc_version` / `semver_version` 已弃用，请改用 `Client.get_session().rpc_version` / `rpc_version_semver`。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))

------

## 4. 快速示例

### 4.1 添加种子/磁力/本地文件

```python
from transmission_rpc import Client
import requests
from pathlib import Path

c = Client(username="transmission", password="password")

# URL 或 magnet
c.add_torrent("https://example.com/a.torrent")
c.add_torrent("magnet:?xt=urn:btih:...")

# bytes 或文件对象
data = requests.get("https://example.com/a.torrent").content
c.add_torrent(data)

with open("a.torrent", "rb") as f:
    c.add_torrent(f)

# Path 也可，库会读取并自动做 base64 编码（无需手动提供 base64）
c.add_torrent(Path("a.torrent"))

# 常用可选参数
c.add_torrent(
  "magnet:?xt=urn:btih:...",
  download_dir="/data/downloads",
  files_wanted=[1, 2], files_unwanted=[0],
  paused=True,
  labels=["movies"],                 # RPC 17+
)
```

> `add_torrent` 支持 `http/https/magnet`、二进制内容、文件对象与 `Path`；**不支持** v4 中的 base64 字符串或 `file://` URL。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))

### 4.2 查询与过滤

```python
# 单个
t = c.get_torrent(0, arguments=["id", "name", "status", "rateDownload", "percentDone"])
print(t.id, t.name, t.status, t.rateDownload, t.percentDone)

# 批量
ts = c.get_torrents(arguments=["id", "name", "eta"])

# 最近活跃与已删除
active, removed = c.get_recently_active_torrents(arguments=["id", "name"])
```

> **性能提示**：只请求需要的字段能显著加快响应。例如 1500 个种子请求所有字段需 ~5s，而仅 6 个字段约 ~0.2s。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))

### 4.3 修改种子属性

```python
# 选择性下载、限速、标签、队列位置等
c.change_torrent(
  ids=[0, 1],
  files_wanted=[2,3], files_unwanted=[0,1],
  download_limited=True, download_limit=100,   # KB/s
  upload_limited=True,   upload_limit=50,      # KB/s
  labels=["urgent"],
  queue_position=0,
)
```

> 自 Transmission 4.0.0 起，`tracker_add`/`tracker_remove`/`tracker_replace` 已不推荐，宜使用 **`tracker_list`** 传入分层的 tracker 列表：
>  `[['https://a/announce','https://b/announce'], ['https://backup/announce']]`。 ([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))

### 4.4 移动数据与重命名路径

```python
# 移动数据到新目录
c.move_torrent_data(ids=0, location="/data/completed/", move=True)

# 重命名（仅对“单个”种子可调用；不是移动数据的方法）
new_path, new_name = c.rename_torrent_path(torrent_id=0, location="/data/completed", name="NewFolderName")
```

> 参见 RPC 规范的 *moving-a-torrent* 与 *renaming-a-torrent’s-path*。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))

### 4.5 启停/校验/重宣告

```python
c.start_torrent([0,1], bypass_queue=False)
c.stop_torrent(0)
c.verify_torrent(0)
c.reannounce_torrent(0)  # 向 tracker 重新汇报
```

> `start_all()` 会按队列顺序启动全部种子。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))

### 4.6 队列操作

```python
c.queue_top(0)
c.queue_up(0)
c.queue_down(0)
c.queue_bottom(0)
```

> 对应 RPC 规范中的队列移动请求。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))

------

## 5. 会话（Session）与统计

```python
from transmission_rpc import Client

c = Client()
s = c.get_session()
print(s.download_dir, s.rpc_version, s.rpc_version_semver)

# 修改会话参数（setter 已移除，使用 Client.set_session）
c.set_session(download_dir="/data/downloads", speed_limit_down=2048, speed_limit_down_enabled=True)

# 会话统计
stats = c.get_session_stats()
print(stats.active_torrent_count, stats.download_speed)
```

- `Session` 的属性名与 RPC 规范字段一致，但将连字符 `-` **改为** 下划线 `_`（例如 `download-dir` → `download_dir`）。
- **重要**：`Session` 属性的直接 setter 已被移除，必须使用 `Client.set_session(...)`。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/session.html))

------

## 6. `Torrent` 对象与常用字段

```python
t = c.get_torrent(0)
print(t.id, t.hashString, t.name, t.status, t.rateDownload, t.rateUpload)

# 访问文件、tracker、状态等
files = t.get_files()             # -> List[FileStat]
trackers = t.trackers             # -> List[Tracker]
status = t.status                 # -> Enum: downloading/seeding/stopped 等
```

> 字段与枚举详见文档的 `Torrent`/`Status`/`FileStat`/`Tracker`/`TrackerStats` 等章节。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/))

------

## 7. 错误处理

常见异常（均在 `transmission_rpc.error`）：

- `TransmissionError`：泛化的通信错误（提供 `response`/`rawResponse` 等调试信息）。
- `TransmissionAuthError`：用户名或密码错误。
- `TransmissionConnectError`：无法连接至守护进程。
- `TransmissionTimeoutError`：请求超时。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/errors.html))

示例：

```python
from transmission_rpc import Client
from transmission_rpc.error import TransmissionAuthError, TransmissionConnectError

try:
    c = Client(username="u", password="p")
    c.get_torrents()
except TransmissionAuthError:
    print("认证失败：请检查用户名/密码")
except TransmissionConnectError:
    print("连接失败：请检查 host/port 与防火墙")
```

------

## 8. 参数命名与 RPC 规范对照

- Python 代码中的关键字参数一律使用 **下划线**，库会自动转换为 RPC 所需的 **连字符**。
	- 例：`download_dir="/path"` → RPC 中为 `"download-dir": "/path"`。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/))
- `torrent-id` 的传参既可用整数 ID，也可使用 `info_hash`（推荐）。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))
- Transmission 的完整 RPC 字段、会话参数与方法定义详见官方 `rpc-spec.md`。([GitHub](https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md))

------

## 9. 进阶与实践建议

- **仅取所需字段**：对大量种子进行查询时，务必通过 `arguments=[...]` 限定字段以获得更好的响应时间。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))
- **Tracker 管理（4.0+）**：优先使用 `tracker_list`（分层列表）维护 tracker 组，避免使用已弃用的 `tracker_add/remove/replace`。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))
- **移动 vs. 重命名**：移动数据请用 `move_torrent_data`；重命名路径（单个种子）用 `rename_torrent_path`，二者语义不同。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))
- **URL 规范**：务必包含协议方案（`http/https`），并注意有无尾随斜杠会影响默认 `path`。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))

------

## 10. 常见任务代码片段速查

**暂停/继续全部：**

```python
c.stop_torrent([t.id for t in c.get_torrents()])
c.start_all()
```

**限速（会话级）：**

```python
c.set_session(speed_limit_down_enabled=True, speed_limit_down=2048)
c.set_session(speed_limit_up_enabled=True,   speed_limit_up=1024)
```

**按后缀筛文件并设优先级：**

```python
t = c.get_torrent(0)
mp4_ids = [f.id for f in t.get_files() if f.name.endswith(".mp4")]
txt_ids = [f.id for f in t.get_files() if f.name.endswith(".txt")]
c.change_torrent(t.hashString, priority_high=mp4_ids, priority_low=txt_ids)
```

**把完成品移动到归档目录：**

```python
t = c.get_torrent(0)
c.move_torrent_data(t.hashString, location="/data/archive/")
```

以上片段均来自官方示例与方法说明的组合与改写。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/))

------

## 11. 参考

- Transmission 官方 RPC 规范（字段/方法权威定义）：`docs/rpc-spec.md`。([GitHub](https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md))
- `transmission-rpc` 官方文档（完整 API 与示例）：Client / Torrent / Session / Errors 页面。([transmission-rpc.readthedocs.io](https://transmission-rpc.readthedocs.io/en/v7.0.11/client.html))
- `Trim21/transmission-rpc` 仓库首页（兼容性、版本说明等）：README。([GitHub](https://github.com/trim21/transmission-rpc))

------

> 本文档为 `.md` 版本，可直接放入你的项目 Wiki 或仓库。若需要我根据你的 Transmission 版本/部署方式（本机、Docker、反向代理、HTTPS、自签证书等）生成更贴合的示例与最佳实践，我可以在此基础上补充一份“部署与安全篇”。