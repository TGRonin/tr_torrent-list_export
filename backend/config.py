from pathlib import Path
import json
import os
from typing import Dict, Any

# 默认配置不含任何真实地址与凭据，首次运行后在设置页（或环境变量）填写
DEFAULT_CONFIG = {
    "host": "",
    "port": 9091,
    "username": "",
    "password": "",
}


def load_env_overrides() -> Dict[str, Any]:
    host = os.getenv("TRANSMISSION_HOST")
    port = os.getenv("TRANSMISSION_PORT")
    username = os.getenv("TRANSMISSION_USERNAME")
    password = os.getenv("TRANSMISSION_PASSWORD")
    overrides: Dict[str, Any] = {}
    if host:
        overrides["host"] = host
    if port:
        try:
            overrides["port"] = int(port)
        except ValueError:
            pass
    if username is not None and username != "":
        overrides["username"] = username
    if password is not None and password != "":
        overrides["password"] = password
    return overrides


def get_config_path() -> Path:
    override_dir = os.getenv("TR_CONFIG_DIR")
    if override_dir:
        config_dir = Path(override_dir)
    else:
        root = Path(__file__).resolve().parents[1]
        config_dir = root / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"


def load_config() -> Dict[str, Any]:
    """只读文件，并在内存中叠加环境变量覆盖；绝不写盘。

    写盘只发生在用户显式保存（save_config）时，避免：
    - 临时环境变量覆盖被永久化到文件；
    - 用户已保存的配置被环境变量覆盖回滚；
    - 每次请求重写文件造成竞态。
    """
    path = get_config_path()
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                cfg = json.load(f)
        except json.JSONDecodeError:
            cfg = DEFAULT_CONFIG.copy()
    else:
        # 文件不存在时仅返回默认配置副本，不自动创建文件
        cfg = DEFAULT_CONFIG.copy()
    # 环境变量仅在本次内存结果中生效，不落盘
    cfg.update(load_env_overrides())
    return cfg


def save_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    path = get_config_path()
    with path.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return cfg
