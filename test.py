"""连接测试：验证 config/config.json（或 TRANSMISSION_* 环境变量）能否连上 Transmission。"""
import sys

import connection


def main():
    client = connection.get_client()
    if client is None:
        print("\n请检查以下可能的问题：")
        print("  1. 确保你的 Transmission daemon 正在运行。")
        print("  2. 检查 config/config.json 中的地址和端口是否正确。")
        print("  3. 如设置了认证，确保用户名和密码正确。", file=sys.stderr)
        return

    session = client.get_session()
    print("---------------------------------------")
    print("✅ 连接成功！")
    print(f"  - Transmission 版本: {session.version}")
    print(f"  - RPC 版本: {session.rpc_version}")
    print(f"  - 下载目录: {session.download_dir}")
    print("---------------------------------------")


if __name__ == "__main__":
    main()
