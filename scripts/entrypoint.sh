#!/usr/bin/env sh
set -eu

# 配置目录写权限预检：卷挂载目录属主不匹配时给出明确修复提示，而非启动后静默失败
CONFIG_DIR="${TR_CONFIG_DIR:-/app/config}"
if ! (touch "$CONFIG_DIR/.write_test" 2>/dev/null && rm -f "$CONFIG_DIR/.write_test"); then
  echo "错误: 配置目录不可写: $CONFIG_DIR" >&2
  echo "修复: 在宿主机对挂载目录执行 chown -R 1000:1000 <config目录> 后重启容器" >&2
  exit 1
fi

if [ -n "${TRANSMISSION_HOST:-}" ]; then
  python - <<'PY'
import json
import os
from pathlib import Path

config_dir = Path(os.getenv("TR_CONFIG_DIR", "/app/config"))
config_dir.mkdir(parents=True, exist_ok=True)
config_path = config_dir / "config.json"

cfg = {}
if config_path.exists():
    try:
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        cfg = {}

host = os.getenv("TRANSMISSION_HOST")
port = os.getenv("TRANSMISSION_PORT")
username = os.getenv("TRANSMISSION_USERNAME")
password = os.getenv("TRANSMISSION_PASSWORD")

if host:
    cfg["host"] = host
if port:
    try:
        cfg["port"] = int(port)
    except ValueError:
        pass
if username is not None and username != "":
    cfg["username"] = username
if password is not None and password != "":
    cfg["password"] = password

config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
PY
fi

exec uvicorn backend.app:app --host 0.0.0.0 --port 8000
