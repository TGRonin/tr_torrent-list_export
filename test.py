import sys
from transmission_rpc import Client

# 替换为你的 Transmission daemon 连接信息
# 如果没有设置用户名和密码，请将 USER 和 PASSWORD 留空或删除
HOST = '192.168.4.142'
PORT = 9091
USER = 'admin'     # 替换为你的用户名
PASSWORD = 'admin' # 替换为你的密码

try:
    client = Client(
        host=HOST,
        port=PORT,
        username=USER,
        password=PASSWORD,
        timeout=10, # 设置连接超时时间，单位为秒
    )
    
    # 获取会话信息
    # 这一操作会触发实际的连接。如果连接成功，会返回一个 Session 对象。
    # 如果失败（如认证失败、连接超时），会抛出异常。
    session_stats = client.get_session()

    # 如果代码执行到这里，说明连接已成功
    print("---------------------------------------")
    print("✅ 连接成功！")
    print(f"  - Transmission 版本: {session_stats.version}")
    print(f"  - RPC 版本: {session_stats.rpc_version}")
    print(f"  - 下载目录: {session_stats.download_dir}")
    print("---------------------------------------")

except Exception as e:
    # 捕获所有可能的异常，如连接失败、认证错误等
    print("---------------------------------------")
    print("❌ 连接失败！")
    print(f"  - 错误信息: {e}", file=sys.stderr)
    print("---------------------------------------")
    print("\n请检查以下可能的问题：")
    print("  1. 确保你的 Transmission daemon 正在运行。")
    print(f"  2. 检查你提供的地址 ({HOST}) 和端口 ({PORT}) 是否正确。")
    print("  3. 如果 Transmission 设置了用户名和密码，请确保你在代码中提供了正确的认证信息。")