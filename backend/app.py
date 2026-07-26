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
    page: int
    page_size: int
    total_pages: int


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
    exclude_labels: str = "",
) -> List[Dict[str, Any]]:
    search_text = (search or "").strip().lower()
    label_text = (label or "").strip()
    maker_text = (maker or "").strip()
    exclude_list = [t.strip().lower() for t in exclude_labels.split(",") if t.strip()]
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

        if exclude_list:
            tags_lower = tags.lower()
            if any(ex in tags_lower for ex in exclude_list):
                continue

        if maker_text not in ("全部", ""):
            if maker_value != maker_text:
                continue

        filtered.append(row)

    return filtered


def aggregate_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    聚合种子统计数据，返回仪表盘所需的各项指标。
    """
    total_count = len(records)
    total_size_bytes = sum(int(r.get("原始文件大小") or 0) for r in records)

    # 按制作组分组统计
    maker_map: Dict[str, Dict[str, Any]] = {}
    label_counter: Dict[str, int] = {}
    label_set = set()
    maker_set = set()

    for row in records:
        maker = str(row.get("制作组", "未知")).strip() or "未知"
        size = int(row.get("原始文件大小") or 0)
        if maker not in maker_map:
            maker_map[maker] = {"count": 0, "size_bytes": 0}
        maker_map[maker]["count"] += 1
        maker_map[maker]["size_bytes"] += size
        maker_set.add(maker)

        tags_str = str(row.get("标签", ""))
        for tag in [t.strip() for t in tags_str.split(",") if t.strip()]:
            label_counter[tag] = label_counter.get(tag, 0) + 1
            label_set.add(tag)

    # 制作组明细列表，按种子数降序
    maker_stats = sorted(
        [
            {
                "maker": k,
                "count": v["count"],
                "size_bytes": v["size_bytes"],
            }
            for k, v in maker_map.items()
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    # 标签频次列表，按次数降序
    label_stats = sorted(
        [{"label": k, "count": v} for k, v in label_counter.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    # 文件大小区间分布
    size_ranges = [
        ("<10MB", 10 * 1024 * 1024),
        ("10-100MB", 100 * 1024 * 1024),
        ("100MB-1GB", 1024 * 1024 * 1024),
        ("1-10GB", 10 * 1024 * 1024 * 1024),
        ("10-100GB", 100 * 1024 * 1024 * 1024),
        (">100GB", None),
    ]
    size_distribution = []
    for i, (label, upper) in enumerate(size_ranges):
        lower = size_ranges[i - 1][1] if i > 0 else 0
        count = 0
        for row in records:
            sz = int(row.get("原始文件大小") or 0)
            if upper is None:
                if sz > lower:
                    count += 1
            elif sz > lower and sz <= upper:
                count += 1
        size_distribution.append({"range": label, "count": count})

    return {
        "total_count": total_count,
        "total_size_bytes": total_size_bytes,
        "maker_count": len(maker_set),
        "label_count": len(label_set),
        "maker_stats": maker_stats,
        "label_stats": label_stats,
        "size_distribution": size_distribution,
    }


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
    exclude_labels: str = "",
    sort: str = Query("name", regex="^(name|size|label_count|maker)$"),
    order: str = Query("asc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    records = fetch_records()
    filtered = apply_filters(records, search, label, maker, exclude_labels)
    sorted_records = sort_records(filtered, sort, order)
    total_pages = max(1, (len(sorted_records) + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = sorted_records[start:end]
    return TorrentsResponse(
        items=page_items,
        total=len(records),
        filtered=len(sorted_records),
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@app.get("/api/stats")
async def get_stats():
    records = fetch_records()
    return aggregate_stats(records)


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
