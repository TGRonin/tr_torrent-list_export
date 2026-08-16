"""Transmission 连接工具（供根目录 CLI 脚本复用）。

凭据统一从 backend.config 读取（config/config.json，可用 TRANSMISSION_* 环境变量覆盖），
不再硬编码；连接按需建立，导入本模块不会发起网络请求。
"""
from typing import Optional

from transmission_rpc import Client

from backend.config import load_config


def get_client() -> Optional[Client]:
    """按当前配置创建 Transmission 客户端；失败时打印错误并返回 None。"""
    cfg = load_config()
    try:
        client = Client(
            host=cfg["host"],
            port=cfg["port"],
            username=cfg.get("username") or None,
            password=cfg.get("password") or None,
        )
        session = client.get_session()
        print(f"连接成功: {cfg.get('host')}:{cfg.get('port')}（RPC 版本 {session.rpc_version}）")
        return client
    except Exception as e:
        print(f"连接 Transmission 失败（{cfg.get('host')}:{cfg.get('port')}）: {e}")
        print("请检查 config/config.json 或 TRANSMISSION_* 环境变量。")
        return None
