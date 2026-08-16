# Python `transmission-rpc` 库专家级使用文档





### **引言**



`transmission-rpc` 是一个专为 Python 语言设计的模块，旨在实现对流行的 BitTorrent 客户端 Transmission 的远程程序调用（RPC）控制。它作为连接 Python 脚本与 Transmission 守护进程（daemon）之间的一座高效桥梁，使开发者和系统管理员能够以编程方式自动化、管理和监控其 BitTorrent 任务。该库将底层复杂的 HTTP 请求和 JSON-RPC 协议细节进行了高级封装，提供了一系列直观的 Python 对象，如 `Client`、`Torrent` 和 `Session`，极大地简化了远程控制的实施过程。该项目以 `trim21/transmission-rpc` 的形式在 GitHub 上托管，凭借其活跃的社区支持，能够兼容从 Transmission 2.40 到 4.1.0-beta.2 的广泛版本范围 1。

在评估和选择适用于特定任务的 RPC 库时，开发者可能会面临名称相似或功能重叠的库所带来的信息混淆。例如，`OpenMV Cam` 的 `rpc` 模块允许在微控制器之间执行远程 Python 调用 2；而在 

`JavaScript` 生态系统中，存在 `@brielov/transmission-rpc`  和 `transmission` 4 等库，它们同样用于与 Transmission 的 RPC API 进行交互。这些库虽然都涉及 RPC 概念，但其目标平台、功能集和实现语言各不相同。本报告将聚焦于 Python 语言的 

`transmission-rpc` 库，并深入剖析其与 Transmission BitTorrent 客户端的交互机制、核心功能、最佳实践以及重要的安全考量。通过这种明确的界定，旨在为用户提供一个精准、权威且无歧义的参考指南，以避免因选用错误依赖而带来的开发障碍。



### **第一章：环境准备与核心配置**





#### **1.1 Python `transmission-rpc` 库安装**



`transmission-rpc` 库的安装过程已从传统方式演变为现代化的包管理流程。在过去，例如在 2013 年，该模块的安装通常需要通过运行随源码附带的 `setup.py` 脚本来完成，有时还需要管理员权限 5。然而，现代 Python 开发已普遍采用 

`pip` 包管理器，该库的安装也已无缝集成到这一生态系统中。目前，推荐且最简便的安装方法是通过命令行执行 `pip install transmission-rpc` 1。

值得注意的是，由于该库在不同操作系统发行版上的打包方式各异，系统管理员在通过系统包管理器安装时可能会遇到不同的包名称。例如，在某些发行版中，包名可能为 `python-transmission-rpc-doc` 或 `py3-transmission-rpc`，这取决于 Python 版本和维护者的命名习惯 6。了解这种命名多样性对于确保在不同环境中正确部署至关重要。



#### **1.2 Transmission Daemon 核心配置**



在通过 `transmission-rpc` 库进行编程控制之前，必须确保目标 Transmission 守护进程（daemon）已正确配置以接受远程连接。所有相关的 RPC 设置都存储在 `settings.json` 配置文件中。该文件的常见位置包括 Linux 系统上的 `/etc/transmission-daemon/settings.json`。

以下是 `settings.json` 中几个关键的 RPC 参数及其功能：

- `"rpc-enabled"`: 一个布尔值，必须设置为 `true` 才能启用 RPC 功能。
- `"rpc-port"`: 指定 RPC 服务器监听的 TCP 端口，默认值为 `9091`。
- `"rpc-username"` 和 `"rpc-password"`: 用于基本的用户名和密码认证。如果 `rpc-authentication-required` 设置为 `true`，则客户端在连接时必须提供这些凭据。
- `"rpc-whitelist"` 和 `"rpc-whitelist-enabled"`: 一个 IP 地址白名单，仅允许列表中定义的客户端 IP 连接。默认情况下，白名单通常只包含 `127.0.0.1`（本地主机）。
- `"rpc-url"`: 定义了 RPC 接口的 URL 路径，默认值为 `/transmission/rpc`。

一份典型的 `settings.json` 配置片段可能如下所示 7：

JSON

```
{
  "rpc-enabled": true,
  "rpc-username": "user",
  "rpc-password": "transmission",
  "rpc-authentication-required": true,
  "rpc-bind-address": "0.0.0.0",
  "rpc-port": 9091,
  "rpc-url": "/transmission/rpc",
  "rpc-whitelist-enabled": true,
  "rpc-whitelist": "127.0.0.1,10.*.*.*"
}
```



#### **1.3 首次连接与验证**



在编写 Python 脚本之前，可以利用 `curl` 等命令行工具对 RPC 服务进行手动验证，以确认其可访问性。Transmission 的 RPC 协议包含一个防跨站请求伪造（CSRF）机制：客户端首次向 RPC 端点发起请求时，服务器会以 `HTTP 409 Conflict` 状态码响应，并在响应头中返回一个 `X-Transmission-Session-Id`。随后的所有请求都必须携带此头部，以证明其为合法会话的一部分 8。

以下是使用 `curl` 验证此机制的示例：

Bash

```
# 第一次请求，故意不带会话ID
$ curl -H 'X-Transmission-Session-Id: foo' -sI '{}' http://localhost:9091/transmission/rpc
HTTP/1.1 409 Conflict
Server: Transmission
X-Transmission-Session-Id: JL641xTn2h53UsN6bVa0kJjRBLA6oX1Ayl06AJwuhHvSgE6H
Date: Wed, 29 Nov 2017 21:37:41 GMT

# 第二次请求，携带从第一次响应中获取的会话ID
$ curl -H 'X-Transmission-Session-Id: JL641xTn2h53UsN6bVa0kJjRBLA6oX1Ayl06AJwuhHvSgE6H' \
       -d '{"method":"session-set","arguments":{"download-dir":"/home/user"}}' \
       -si http://localhost:9091/transmission/rpc
HTTP/1.1 200 OK
Server: Transmission
Content-Type: application/json; charset=UTF-8
Date: Wed, 29 Nov 2017 21:38:57 GMT
Content-Length: 36
```

`transmission-rpc` 库在内部会自动处理这一握手过程，因此开发者无需手动管理 `X-Transmission-Session-Id` 头部。然而，理解其工作原理对于诊断连接问题至关重要。尽管存在这种机制，但依赖其来保证安全是不足够的。在特定攻击情境下，例如 DNS 重绑定攻击，此机制可以被绕过，从而导致潜在的严重安全风险。这一重要议题将在本报告的后续章节中进行深入探讨。



### **第二章：核心概念与对象模型**





#### **2.1 `transmission-rpc` 库的对象抽象**



`transmission-rpc` 库通过将复杂的 RPC 协议调用抽象为面向对象的接口，极大地简化了开发工作。它主要围绕三个核心类进行设计：

- **`Client` 对象:** `Client` 类是库的入口点，负责建立和维护与 Transmission daemon 的连接。所有与 daemon 交互的方法，例如添加种子、获取种子列表、修改全局会话设置等，都是通过 `Client` 实例来调用的 9。
- **`Torrent` 对象:** `Torrent` 类封装了单个 BitTorrent 任务的所有属性和状态。当通过 `Client` 对象获取种子信息时，返回的便是 `Torrent` 对象列表。开发者可以通过访问这些对象的属性来获取任务的详细信息，如名称、下载进度、上传速度等 10。
- **`Session` 对象:** `Session` 类代表了 Transmission daemon 的全局会话设置。它包含了所有与客户端整体行为相关的参数，例如默认下载目录、全局限速、RPC 版本等。通过 `Client` 实例获取和修改会话设置时，操作的便是 `Session` 对象 10。



#### **2.2 属性命名转换：从 RPC 到 Python**



在处理 RPC 请求时，一个常见的设计挑战是底层协议的命名习惯与高层编程语言的惯例之间的不一致。Transmission 的 JSON-RPC 规范中，参数通常使用 `hyphen-case`（例如 `download-dir`、`peer-limit`）9。然而，在 Python 社区，

`PEP 8` 编码规范推荐使用 `underscore_case`（例如 `download_dir`）来命名变量和属性。

`transmission-rpc` 库的设计巧妙地解决了这一问题。它在内部实现了自动的命名转换，将所有来自 RPC 调用的 `hyphen-case` 参数自动映射为 `Torrent` 和 `Session` 对象的 `underscore_case` 属性 9。例如，RPC 规范中的 

`download-dir` 字段在 Python 库中被映射为 `torrent.download_dir` 或 `session.download_dir` 属性。这种设计选择显著提升了库的易用性和代码可读性，使 Python 开发者能够使用他们熟悉的编程风格来操作 RPC 数据，减少了因命名不匹配而导致的常见错误。



#### **2.3 核心数据结构与属性详解**



`Torrent` 和 `Session` 对象提供了丰富的属性，用以反映 BitTorrent 任务和客户端会话的实时状态。以下表格详细列出了 `Torrent` 对象的部分关键属性，展示了 RPC 参数名与其对应的 Python 属性名之间的映射关系，并提供了简要描述。

| RPC 参数名          | Python 属性名         | 描述                                                    |
| ------------------- | --------------------- | ------------------------------------------------------- |
| `activityDate`      | `activity_date`       | 上次上传或下载活动的时间 10                             |
| `addedDate`         | `added_date`          | 种子首次被添加的日期 10                                 |
| `bandwidthPriority` | `bandwidth_priority`  | 传输的带宽优先级（-1=低，0=正常，1=高） 10              |
| `comment`           | `comment`             | 种子的注释 10                                           |
| `doneDate`          | `done_date`           | 种子下载完成的日期 10                                   |
| `downloadDir`       | `download_dir`        | 种子内容的下载目录 10                                   |
| `downloadLimit`     | `download_limit`      | 下载速度限制（单位：KiB/s） 9                           |
| `downloadLimitMode` | `download_limit_mode` | 下载限速模式（0=全局，1=独立，2=无限制） 10             |
| `eta`               | `eta`                 | 预计完成时间（单位：秒）。-1 表示不可用，-2 表示未知 10 |
| `files`             | `files`               | 包含每个文件信息的数组 10                               |
| `hashString`        | `hash_string`         | 种子的唯一哈希字符串 10                                 |
| `id`                | `id`                  | 会话中唯一的种子 ID 10                                  |
| `isPrivate`         | `is_private`          | 种子是否为私有 10                                       |
| `isStalled`         | `is_stalled`          | 种子是否已停滞（长时间空闲） 10                         |
| `magnetLink`        | `magnet_link`         | 种子的磁力链接 10                                       |
| `name`              | `name`                | 种子名称 10                                             |
| `peersConnected`    | `peers_connected`     | 已连接的 Peer 数量 10                                   |
| `percentDone`       | `percent_done`        | 下载进度（0.0 到 1.0） 10                               |
| `rateDownload`      | `rate_download`       | 当前下载速率（单位：bps） 10                            |
| `rateUpload`        | `rate_upload`         | 当前上传速率（单位：bps） 10                            |
| `recheckProgress`   | `recheck_progress`    | 重新校验进度（0.0 到 1.0） 10                           |
| `seedRatioLimit`    | `seed_ratio_limit`    | 种子分享率限制 9                                        |
| `sizeWhenDone`      | `size_when_done`      | 下载完成后种子的总大小（单位：字节） 10                 |
| `status`            | `status`              | 当前状态，如“下载中”、“做种中”或“已停止” 9              |
| `totalSize`         | `total_size`          | 种子的总大小（单位：字节） 10                           |
| `uploadLimit`       | `upload_limit`        | 上传速度限制（单位：KiB/s） 9                           |



### **第三章：基础用法与代码示例**





#### **3.1 建立连接**



与 Transmission daemon 的所有交互都始于 `Client` 对象的实例化。开发者需要提供 daemon 的地址和端口，如果配置了认证，还需要提供用户名和密码 9。为了增强安全性，建议使用环境变量而非将凭据硬编码到脚本中。

Python

```
import transmissionrpc
from os import getenv

# 连接到默认地址和端口（localhost:9091），无需认证
client = transmissionrpc.Client()

# 连接到指定地址和端口，并进行认证
TR_HOST = getenv("TR_HOST", "192.168.1.100")
TR_PORT = int(getenv("TR_PORT", 9091))
TR_USER = getenv("TR_USER", "username")
TR_PASS = getenv("TR_PASS", "password")

try:
    auth_client = transmissionrpc.Client(
        address=TR_HOST,
        port=TR_PORT,
        user=TR_USER,
        password=TR_PASS
    )
    print("成功连接到 Transmission daemon。")
except transmissionrpc.TransmissionError as e:
    print(f"连接失败：{e}")
```



#### **3.2 种子管理：添加与移除**



`transmission-rpc` 提供了多种方式来添加新种子，以及灵活的移除选项。

**添加种子**

可以使用 `client.add_uri()` 方法通过磁力链接或 `.torrent` 文件的 URL 来添加种子。该方法还支持其他可选参数，如 `download_dir` 来指定下载路径，以及 `paused` 参数来控制是否在添加后立即开始下载 9。

Python

```
# 通过磁力链接添加种子
magnet_uri = "magnet:?xt=urn:btih:..."
new_torrent = auth_client.add_uri(magnet_uri, download_dir="/mnt/data/downloads", paused=False)
print(f"已添加种子：{new_torrent.name}，ID：{new_torrent.id}")

# 通过.torrent文件URL添加种子
torrent_url = "http://example.com/some_torrent_file.torrent"
new_torrent = auth_client.add_uri(torrent_url)
print(f"已从URL添加种子：{new_torrent.name}")
```

**移除种子**

`client.remove()` 方法用于从 Transmission 列表中移除种子。一个重要的参数是 `delete_data`，如果设置为 `True`，该方法将在移除种子的同时删除所有相关的本地数据文件，否则只移除列表中的记录 9。

Python

```
# 获取所有已停止的种子ID
stopped_torrents = [t.id for t in auth_client.get_torrents() if t.status == 'stopped']

if stopped_torrents:
    # 移除所有已停止的种子，但不删除本地数据
    auth_client.remove(stopped_torrents, delete_data=False)
    print(f"已移除 {len(stopped_torrents)} 个已停止的种子。")
```



#### **3.3 状态查询与信息获取**



要获取一个或多个种子的详细信息，可以使用 `client.get_torrents()` 或 `client.get_torrent()` 方法 9。

Python

```
# 获取所有种子
all_torrents = auth_client.get_torrents()

print("所有当前种子:")
for torrent in all_torrents:
    print(f"ID: {torrent.id}, 名称: {torrent.name}, 进度: {torrent.percent_done * 100:.2f}%, "
          f"下载速率: {torrent.rate_download / 1024:.2f} KiB/s [10]")

# 通过ID获取特定种子
torrent_id_to_check = 1
try:
    specific_torrent = auth_client.get_torrent(torrent_id_to_check)
    print(f"\n种子 ID {specific_torrent.id} 的磁力链接：{specific_torrent.magnet_link} [10]")
except transmissionrpc.TransmissionError:
    print(f"\n未找到 ID 为 {torrent_id_to_check} 的种子。")
```



#### **3.4 种子操作**



`transmission-rpc` 库提供了多种方法来控制种子的状态和行为，例如启动、停止或重新校验数据 9。

Python

```
# 启动所有已停止的种子
stopped_ids = [t.id for t in auth_client.get_torrents() if t.status == 'stopped']
if stopped_ids:
    auth_client.start(stopped_ids)
    print(f"已启动 {len(stopped_ids)} 个种子。")

# 停止ID为2和5的种子
auth_client.stop()

# 对ID为3的种子进行重新校验
auth_client.verify()

# 强制对ID为4的种子重新公告
auth_client.reannounce(4)
```



#### **3.5 批量操作与过滤**



一个高效的编程实践是利用库对批量操作的支持。相比于通过循环对每个种子进行单独的 RPC 调用，将多个种子 ID 组成列表传递给一个方法可以显著减少网络延迟和服务器负载。`transmission-rpc` 的大多数核心方法，如 `start()`、`stop()` 和 `remove()`，都接受一个 ID 或哈希字符串的列表作为参数，从而实现了高效的批量操作 9。



### **第四章：高级应用与最佳实践**





#### **4.1 全局会话与限速管理**



`Session` 对象是管理 Transmission 客户端全局设置的接口。它允许开发者获取和修改如默认下载目录、全局限速和备用限速模式等参数。

Python

```
# 获取全局会话信息
session = auth_client.get_session()

print("当前全局下载目录:", session.download_dir)
print(f"RPC 版本: {session.rpc_version} ")
print(f"全局下载限速: {session.speed_limit_down} KiB/s")
print(f"全局下载限速是否启用: {session.speed_limit_down_enabled}")

# 启用全局下载限速并设置为100 KiB/s
auth_client.set_session(speed_limit_down_enabled=True, speed_limit_down=100)
print("\n已将全局下载限速设置为 100 KiB/s。")
```



#### **4.2 错误处理与调试**



在与远程 RPC 服务交互时，妥善的错误处理是确保脚本健壮性的关键。`transmission-rpc` 库定义了两种主要的异常类型 10：

- `transmissionrpc.TransmissionError`: 当与 Transmission 通信时发生一般性错误时抛出。
- `transmissionrpc.HTTPHandlerError`: 当 HTTP 请求本身发生错误（例如，404 Not Found 或 500 Internal Server Error）时抛出。

一个稳健的脚本应该使用 `try...except` 块来捕获这些潜在的异常，从而优雅地处理连接失败、认证失败或其他通信问题。

Python

```
try:
    auth_client.get_torrents()
except transmissionrpc.HTTPHandlerError as e:
    print(f"HTTP 请求错误：URL={e.url}, 状态码={e.code}, 消息={e.message} [10]")
except transmissionrpc.TransmissionError as e:
    print(f"通信错误：{e}")
```

当遇到难以诊断的问题时，查看库内部的 HTTP 请求和响应详情是至关重要的。`transmission-rpc` 库集成了 Python 的标准 `logging` 模块，开发者可以通过简单的配置来启用详细的调试日志。将日志级别设置为 `DEBUG` 后，库将打印出完整的 RPC 请求（包括头部和数据）和服务器响应，这是解决复杂问题的终极手段 11。

Python

```
import logging
import transmissionrpc

logging.getLogger('transmissionrpc').setLevel(logging.DEBUG)

# 再次运行代码，将看到详细的通信日志
try:
    auth_client.get_torrents()
except Exception as e:
    print(f"发生错误：{e}")
```



#### **4.3 异步与并发编程**



`transmission-rpc` 库本身是同步的，这意味着当一个方法被调用时，它会阻塞主线程，直到从 Transmission daemon 接收到响应。在简单的脚本中这通常不是问题，但在需要高并发或在 Web 服务等非阻塞环境中（如 `asyncio`）使用时，这种同步行为可能会导致性能瓶颈。

为了将同步库集成到异步框架中，可以利用 `asyncio` 的 `run_in_executor` 方法。该方法能够在单独的线程池或进程池中运行同步函数，从而避免阻塞主事件循环。通过这种方式，即使是处理大量的种子或频繁的 RPC 调用，也能确保应用程序的响应能力和并发性能。



### **第五章：深入故障排除与安全考量**





#### **5.1 常见连接问题诊断**



在开发或部署过程中，开发者可能会遇到各种连接问题。以下是一个针对常见错误的系统化诊断流程：

- **`Connection Refused`:** 这是最常见的错误，通常表示客户端无法在指定的 IP 地址和端口上与 Transmission daemon 建立连接。诊断步骤包括：

	1. 确认 Transmission daemon 服务正在运行。

	2. 使用 `telnet` 或 `netstat` 命令验证 RPC 端口 `9091` 是否在监听 12。例如，

		`netstat -alpn | grep 9091` 可以显示哪个进程正在监听该端口。

	3. 检查客户端连接的 IP 地址 (`localhost`、`127.0.0.1` 或 `0.0.0.0`) 是否与 daemon 实际绑定的 IP 匹配 13。如果 daemon 仅绑定到 

		`127.0.0.1`，那么从远程连接会失败。

- **`HTTP 403 Forbidden`:** 此错误通常是由 RPC 配置问题引起的。最可能的原因是客户端的 IP 地址不在 `rpc-whitelist` 白名单中 14，或者 

	`rpc-authentication-required` 为 `true` 但提供的用户名或密码不正确。

- **`settings.json` 配置不生效:** 在某些 Linux 环境中，简单地编辑 `settings.json` 并重启服务可能无法加载新配置。这通常是因为存在其他配置冲突或相关软件包（如 `transmission-cli` 或 `transmission-common`）导致的问题。根据一些用户报告，解决此问题的有效方法是彻底清除相关的 Transmission 包（`transmission-daemon`、`transmission-cli` 和 `transmission-common`），然后重新安装 14。



#### **5.2 安全漏洞与防御**



依赖 `rpc-authentication-required` 和 `X-Transmission-Session-Id` 头部来保护 Transmission RPC 服务是不够的，因为它存在一个已知的 DNS 重绑定漏洞 8。

**DNS 重绑定攻击原理**

攻击者可以利用此漏洞绕过浏览器的同源策略，从而向本地的 Transmission daemon 发送恶意 RPC 请求。攻击过程通常如下：

1. 用户访问一个由攻击者控制的恶意网站。
2. 该网站包含一个隐藏的 `iframe`，加载一个由攻击者控制的子域名，例如 `attack.attacker.com`。
3. 攻击者精心配置其 DNS 服务器，使 `attack.attacker.com` 的 DNS 解析结果在短时间内交替返回一个公共 IP（由攻击者控制）和本地回环地址 `127.0.0.1` 8。
4. 浏览器首次解析到公共 IP，加载恶意 JavaScript 代码。当 DNS 缓存过期后，浏览器再次解析该域名，此时得到 `127.0.0.1`。
5. 由于同源策略是以域名而非 IP 地址为基础的，此时浏览器仍认为它在与 `attack.attacker.com` 通信，从而被允许向 `127.0.0.1:9091` 发送 `XMLHttpRequest`，并能够读取服务器响应头部（包括 `X-Transmission-Session-Id`）。

**潜在危害与防御措施**

攻击者可以利用这一漏洞向本地 daemon 发送恶意 RPC 请求，例如修改 `download-dir` 以覆盖用户的 `.bashrc` 文件，或者启用 `script-torrent-done-enabled` 并指定一个恶意脚本，从而导致远程代码执行（RCE）8。

为了有效防御此类攻击，仅依赖认证和会话 ID 是不够的。建议采取以下更严格的防御措施：

- **严格限制 `rpc-whitelist`:** 将 RPC 服务限制在受信任的 IP 地址范围内。对于本地控制，仅允许 `127.0.0.1`。
- **绑定到特定接口:** 在 `settings.json` 中，将 `rpc-bind-address` 明确设置为 `127.0.0.1`，而不是通配符 `0.0.0.0`，以确保 RPC 服务仅从本地回环接口可访问。
- **使用 SSH 隧道:** 如果需要从远程网络访问，建议使用 SSH 隧道作为一种更安全的替代方案。这可以将远程端口安全地转发到本地回环接口，从而避免将 RPC 服务直接暴露在公共网络上。



### **附录：API 完整参考**



本附录提供了 `transmission-rpc` 库中核心类、方法和属性的详细参考，作为开发和故障排除的快速查阅指南。



#### **A.1 `Client` 类方法**



`Client` 类是所有 RPC 调用的主要接口。核心方法包括：

- `add_torrent(data, **kwargs)`: 通过 base64 编码的 `.torrent` 文件数据添加种子。
- `add_uri(uri, **kwargs)`: 通过 URI（如磁力链接或 HTTP/FTP URL）添加种子。
- `change_torrent(ids, **kwargs)`: 批量修改一个或多个种子的参数。
- `get_torrents(ids=None, arguments=None)`: 获取一个或多个种子的信息。如果 `ids` 为空，则获取所有种子。
- `get_session()`: 获取全局会话 `Session` 对象。
- `set_session(**kwargs)`: 设置全局会话参数。
- `remove(ids, delete_data=False)`: 移除种子。
- `start(ids)`: 启动种子。
- `stop(ids)`: 停止种子。
- `verify(ids)`: 校验种子数据。
- `locate(ids, location)`: 告知 Transmission 种子数据的新位置。
- `move(ids, location)`: 移动种子数据到新位置。
- `blocklist_update()`: 更新 Blocklist。



#### **A.2 `Torrent` 类属性与方法**



`Torrent` 对象封装了种子信息。其属性与 RPC 字段一一对应，并遵循 Python 的命名约定。

| RPC 参数名         | Python 属性名       | 数据类型 | 描述                                                 |
| ------------------ | ------------------- | -------- | ---------------------------------------------------- |
| `activityDate`     | `activity_date`     | `int`    | 上次上传或下载活动的时间 10                          |
| `addedDate`        | `added_date`        | `int`    | 种子首次被添加的日期 10                              |
| `announceResponse` | `announce_response` | `str`    | Tracker 的公告消息 10                                |
| `downloadDir`      | `download_dir`      | `str`    | 种子内容的下载目录 10                                |
| `downloadLimit`    | `download_limit`    | `int`    | 下载速度限制（单位：KiB/s） 10                       |
| `eta`              | `eta`               | `int`    | 预计剩余完成时间（单位：秒） 10                      |
| `files`            | `files`             | `list`   | 包含文件对象的列表 10                                |
| `hashString`       | `hash_string`       | `str`    | 种子的唯一哈希字符串 10                              |
| `id`               | `id`                | `int`    | 会话中唯一的种子 ID 10                               |
| `isStalled`        | `is_stalled`        | `bool`   | 种子是否已停滞 10                                    |
| `magnetLink`       | `magnet_link`       | `str`    | 种子的磁力链接 10                                    |
| `name`             | `name`              | `str`    | 种子名称 10                                          |
| `percentDone`      | `percent_done`      | `float`  | 下载进度（0.0-1.0） 10                               |
| `rateDownload`     | `rate_download`     | `int`    | 当前下载速率（单位：bps） 10                         |
| `rateUpload`       | `rate_upload`       | `int`    | 当前上传速率（单位：bps） 10                         |
| `status`           | `status`            | `str`    | 当前状态（如 'downloading', 'seeding', 'stopped'） 9 |
| `totalSize`        | `total_size`        | `int`    | 种子的总大小（单位：字节） 10                        |
| `uploadLimit`      | `upload_limit`      | `int`    | 上传速度限制（单位：KiB/s） 10                       |



#### **A.3 `Session` 类属性**



`Session` 对象代表全局会话设置。其属性同样来自 RPC 规范，并进行了命名转换。

- `download_dir`: 默认下载目录
- `download_dir_free_space`: 下载目录的可用空间（单位：字节）
- `rpc_version`: 当前 RPC 版本
- `rpc_version_minimum`: 所支持的最小 RPC 版本
- `speed_limit_down_enabled`: 全局下载限速是否启用
- `speed_limit_up_enabled`: 全局上传限速是否启用
- `seed_ratio_limit`: 全局分享率限制
- `alt_speed_enabled`: 备用限速模式是否启用
- `utp_enabled`: UTP 协议是否启用



#### **A.4 `File` 类属性**



在 `Torrent` 对象内部，`files` 属性是一个文件对象列表，每个对象都包含了关于单个文件的详细信息 9。

- `name`: 文件名 9
- `size`: 文件大小（单位：字节） 9
- `completed`: 已完成的字节数 9
- `priority`: 文件优先级（'high'、'normal' 或 'low'） 9
- `selected`: 是否被选中下载 9



#### **A.5 状态码与常量**



`Torrent` 对象的 `status` 属性可以返回以下状态码，这些状态码在编写基于种子状态的自动化逻辑时非常有用 9：

- `check pending`：等待校验
- `checking`：正在校验
- `downloading`：下载中
- `seeding`：做种中
- `stopped`：已停止