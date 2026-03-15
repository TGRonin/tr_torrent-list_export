import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from transmission_rpc import Client

from backend.config import load_env_overrides

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from torrent_processor import process_torrents
from backend.config import load_config, save_config

app = FastAPI(title="Transmission Torrent UI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConfigModel(BaseModel):
    host: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)
    username: Optional[str] = ""
    password: Optional[str] = ""


class TorrentsResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    filtered: int


def create_client(cfg: Dict[str, Any]) -> Client:
    return Client(
        host=cfg["host"],
        port=cfg["port"],
        username=cfg.get("username") or None,
        password=cfg.get("password") or None,
    )


def fetch_records() -> List[Dict[str, Any]]:
    cfg = load_config()
    try:
        client = create_client(cfg)
        return process_torrents(client)
    except Exception as exc:
        import traceback
        print("连接 Transmission 失败:\n", traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"连接 Transmission 失败: {exc}")


def apply_filters(
    records: List[Dict[str, Any]],
    search: str,
    label: str,
    maker: str,
) -> List[Dict[str, Any]]:
    search_text = (search or "").strip().lower()
    label_text = (label or "").strip()
    maker_text = (maker or "").strip()
    filtered: List[Dict[str, Any]] = []

    for row in records:
        name = str(row.get("名称", ""))
        tags = str(row.get("标签", ""))
        maker_value = str(row.get("制作组", ""))

        if search_text:
            if search_text not in name.lower() and search_text not in tags.lower():
                continue

        if label_text not in ("全部", ""):
            if label_text.lower() not in tags.lower():
                continue

        if maker_text not in ("全部", ""):
            if maker_value != maker_text:
                continue

        filtered.append(row)

    return filtered


def sort_records(records: List[Dict[str, Any]], sort: str, order: str) -> List[Dict[str, Any]]:
    sort_key_map = {
        "name": lambda r: str(r.get("名称", "")).lower(),
        "size": lambda r: int(r.get("原始文件大小") or 0),
        "label_count": lambda r: int(r.get("标签数量") or 0),
        "maker": lambda r: str(r.get("制作组", "")).lower(),
    }
    key_fn = sort_key_map.get(sort, sort_key_map["name"])
    reverse = (order or "").lower() == "desc"
    return sorted(records, key=key_fn, reverse=reverse)


@app.get("/api/torrents", response_model=TorrentsResponse)
async def get_torrents(
    search: str = "",
    label: str = "全部",
    maker: str = "全部",
    sort: str = Query("name", regex="^(name|size|label_count|maker)$"),
    order: str = Query("asc", regex="^(asc|desc)$"),
):
    records = fetch_records()
    filtered = apply_filters(records, search, label, maker)
    sorted_records = sort_records(filtered, sort, order)
    return TorrentsResponse(items=sorted_records, total=len(records), filtered=len(sorted_records))


@app.get("/api/filters")
async def get_filters():
    records = fetch_records()
    labels = set()
    makers = set()
    for row in records:
        tags = str(row.get("标签", ""))
        for tag in [t.strip() for t in tags.split(",") if t.strip()]:
            labels.add(tag)
        maker = str(row.get("制作组", "")).strip()
        if maker:
            makers.add(maker)
    return {
        "labels": sorted(labels),
        "makers": sorted(makers),
        "total": len(records),
    }


@app.get("/api/config")
async def get_config():
    cfg = load_config()
    overrides = load_env_overrides()
    cfg.update(overrides)
    return cfg


@app.post("/api/config")
async def update_config(payload: ConfigModel, test: bool = False):
    cfg = payload.dict()
    if test:
        try:
            client = create_client(cfg)
            client.get_session()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"连接测试失败: {exc}")
    return save_config(cfg)


@app.post("/api/config/import")
async def import_config(payload: ConfigModel):
    return save_config(payload.dict())


@app.get("/api/config/export")
async def export_config():
    return load_config()


dist_dir = ROOT / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")
