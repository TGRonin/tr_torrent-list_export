#!/usr/bin/env sh
set -eu

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
