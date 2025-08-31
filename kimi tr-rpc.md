# Python 语言下 Transmission-RPC 使用文档

> 文档版本：v1.0  
> 最后更新：2025-08-31  
> 适用范围：transmission-rpc ≥ 4.x，Transmission ≥ 2.40

---

## 1. 简介

`transmission-rpc` 是一个用 Python 3 编写的第三方库，它对 Transmission 提供的 JSON-RPC 协议进行封装，使开发者可以在 **不直接处理 HTTP/JSON 细节** 的情况下，方便地完成以下任务：

- 添加/删除/暂停/恢复种子  
- 实时查询任务状态、做种信息、文件列表  
- 修改全局或单种上传/下载速率、做种比率等设置  
- 远程管理 Transmission 实例（本地或公网）

支持 Transmission **2.40–4.0.6** 对应的 RPC 14–17 版本，后续版本也能工作，但新特性可能缺失。

---

## 2. 安装

```bash
pip install -U transmission-rpc
```

如需开发或调试，可使用源码安装：

```bash
git clone https://github.com/Trim21/transmission-rpc.git
cd transmission-rpc
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
```

---

## 3. 快速上手

### 3.1 建立连接

```python
from transmission_rpc import Client

client = Client(
    host='localhost',
    port=9091,
    username='transmission',
    password='password',
    timeout=30
)
```

> 如未指定 host / port / username / password，库会依次读取环境变量  
> `TR_HOST`、`TR_PORT`、`TR_USER`、`TR_PASS`。

### 3.2 添加种子

```python
# 1. 通过磁力链
magnet = "magnet:?xt=urn:btih:e84213a794f3ccd890382a54a64ca68b7e925433&dn=ubuntu-18.04.1-desktop-amd64.iso"
client.add_torrent(magnet)

# 2. 通过 .torrent 文件 URL
torrent_url = "https://github.com/trim21/transmission-rpc/raw/v4.1.0/tests/fixtures/iso.torrent"
client.add_torrent(torrent_url, download_dir='/data/downloads')

# 3. 通过二进制内容
import requests
r = requests.get(torrent_url)
client.add_torrent(r.content)
```

### 3.3 查询任务

```python
# 获取全部种子列表
torrents = client.get_torrents()
for t in torrents:
    print(t.id, t.name, t.percent_done * 100, '%')

# 根据 ID 或 hash 精确查询
t = client.get_torrent(1)          # 按 Transmission 内部 ID
t = client.get_torrent('abcd1234') # 按 info-hash
```

### 3.4 修改任务

```python
# 设置单种上传限速（单位 KiB/s）
client.change_torrent(
    t.hashString,
    upload_limited=True,
    upload_limit=100
)

# 排除/选中部分文件
files = t.get_files()
unwant = [f.id for f in files if f.name.endswith('.txt')]
high   = [f.id for f in files if f.name.endswith('.mkv')]
client.change_torrent(
    t.hashString,
    files_unwanted=unwant,
    priority_high=high
)
```

---

## 4. 进阶用法

### 4.1 批量控制

```python
# 暂停所有做种完成的任务
for t in client.get_torrents():
    if t.status == 'seeding' and t.percent_done == 1.0:
        client.stop_torrent(t.id)
```

### 4.2 移动数据目录

```python
client.move_torrent_data(
    t.hashString,
    location='/mnt/usb/completed'
)
```

### 4.3 会话级配置

```python
session = client.get_session()
print('当前全局上传限速:', session.upload_limit)

client.set_session(
    alt_speed_enabled=True,
    alt_speed_up=50,
    alt_speed_down=400
)
```

### 4.4 自定义超时与重试

```python
from transmission_rpc import Client, TransmissionTimeoutError

try:
    client = Client(timeout=5)
    client.get_torrents()
except TransmissionTimeoutError:
    print("Transmission 连接超时")
```

---

## 5. 数据模型速查

| 对象        | 常用属性示例                                                 |
| ----------- | ------------------------------------------------------------ |
| **Torrent** | id, name, hashString, percent_done, status, totalSize, uploadRatio, files... |
| **File**    | id, name, size, completed, priority, wanted                  |
| **Session** | download_dir, upload_limit, peer_port, rpc_version...        |

状态枚举（`Status`）：

- `STOPPED = 0`
- `CHECK_WAIT = 1`
- `CHECK = 2`
- `DOWNLOAD_WAIT = 3`
- `DOWNLOAD = 4`
- `SEED_WAIT = 5`
- `SEED = 6`

---

## 6. 常见错误码与排查

| 异常类型                 | 触发场景 & 解决思路                                          |
| ------------------------ | ------------------------------------------------------------ |
| TransmissionAuthError    | 用户名/密码错误；检查 `settings.json` 里的 `rpc-username` / `rpc-password` |
| TransmissionConnectError | 地址/端口不通；确认 daemon 已启动，且监听 `0.0.0.0`          |
| TransmissionTimeoutError | 网络延迟或 daemon 无响应；增大 `timeout` 或检查日志          |
| HTTP 409                 | CSRF Token 失效；库已自动重试，无需手动处理                  |
| HTTP 403 Forbidden       | IP 白名单限制；关闭 `rpc-whitelist-enabled` 或添加白名单     |

---

## 7. 与 Transmission 官方 RPC 规范的对照

| transmission-rpc 方法     | 对应官方 RPC 方法 | 额外说明                     |
| ------------------------- | ----------------- | ---------------------------- |
| `Client.add_torrent()`    | `torrent-add`     | 自动处理 base64、CSRF        |
| `Client.get_torrents()`   | `torrent-get`     | 支持用 `arguments` 过滤字段  |
| `Client.change_torrent()` | `torrent-set`     | Python 变量名用 `_` 替换 `-` |
| `Client.get_session()`    | `session-get`     | 返回 Session 对象            |
| `Client.set_session()`    | `session-set`     | 同上                         |

完整官方规范：[Transmission RPC Spec](https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md) 。

---

## 8. 最小可运行示例（完整脚本）

```python
#!/usr/bin/env python3
"""
transmission_rpc_demo.py
"""
import os
from transmission_rpc import Client

def main():
    client = Client()  # 使用环境变量连接
    torrent_url = "magnet:?xt=urn:btih:e84213a794f3ccd890382a54a64ca68b7e925433&dn=ubuntu-18.04.1-desktop-amd64.iso"
    t = client.add_torrent(torrent_url, download_dir=os.getenv('TR_DOWNLOAD_DIR', '/tmp'))
    print(f"已添加任务：{t.name} (ID={t.id})")

if __name__ == '__main__':
    main()
```

运行前设置环境变量：

```bash
export TR_HOST=192.168.1.100
export TR_PORT=9091
export TR_USER=admin
export TR_PASS=secret
python transmission_rpc_demo.py
```

---

## 9. 参考资料与社区

- PyPI 项目页：https://pypi.org/project/transmission-rpc/  
- 在线文档：https://transmission-rpc.readthedocs.io/  
- GitHub 仓库：https://github.com/Trim21/transmission-rpc  
- Transmission 官方 RPC 规范：https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md  

---

> **许可证**  
> `transmission-rpc` 自身采用 MIT 许可证。