from pathlib import Path
import json
import os
from typing import Dict, Any

DEFAULT_CONFIG = {
    "host": "192.168.3.119",
    "port": 9091,
    "username": "admin",
    "password": "admin",
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
    path = get_config_path()
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                cfg = json.load(f)
        except json.JSONDecodeError:
            cfg = DEFAULT_CONFIG.copy()
    else:
        cfg = DEFAULT_CONFIG.copy()
    overrides = load_env_overrides()
    if overrides:
        cfg.update(overrides)
        save_config(cfg)
    elif not path.exists():
        save_config(cfg)
    return cfg


def save_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    path = get_config_path()
    with path.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return cfg
