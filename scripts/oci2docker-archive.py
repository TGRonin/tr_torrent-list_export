"""把 OCI 布局归档（containerd 存储下 docker save 的输出）重组为传统 Docker 归档。

传统归档结构：manifest.json + <config>.json + <layerid>/layer.tar(|VERSION) + repositories，
其中层目录名 = DiffID = sha256(未压缩 layer.tar)，与镜像 config 的 rootfs.diff_ids 一一对应。

纯本地确定性操作：无网络、无守护进程依赖；tar/gzip 条目固定 mtime 与顺序，输出可复现。

用法：
  python scripts/oci2docker-archive.py 输入.tar[.gz] 输出.tar.gz [--tag repo:tag]

--tag 缺省时尝试读取归档内 io.containerd.image.name 注解。
"""
import argparse
import gzip
import hashlib
import io
import json
import os
import sys
import tarfile
import tempfile
from pathlib import Path

# OCI / Docker 媒体类型关键字
GZIP_LAYER_TYPES = ("tar+gzip", "tar.gzip")
PLAIN_LAYER_TYPES = ("rootfs.diff.tar",)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob_path(blobs_dir: Path, digest: str) -> Path:
    algo, hexval = digest.split(":", 1)
    if algo != "sha256":
        raise SystemExit(f"不支持的摘要算法: {digest}")
    return blobs_dir / algo / hexval


def load_blob_bytes(blobs_dir: Path, digest: str) -> bytes:
    p = blob_path(blobs_dir, digest)
    if not p.exists():
        raise SystemExit(f"blob 缺失: {digest}")
    return p.read_bytes()


def is_gzip(data: bytes) -> bool:
    return data[:2] == b"\x1f\x8b"


def pick_image_manifest(index: dict, blobs_dir: Path) -> tuple[bytes, str]:
    """从 index.json 选中目标镜像 manifest 字节与其摘要。

    支持顶层为 manifest list / image index（按 linux/amd64 选取并排除
    attestation 子清单），或直接为 image manifest。
    """
    desc = index["manifests"][0]
    mt = desc.get("mediaType", "")
    tag = (desc.get("annotations") or {}).get("io.containerd.image.name", "")

    if "manifest.list" in mt or "image.index" in mt:
        chosen = None
        for child in json.loads(load_blob_bytes(blobs_dir, desc["digest"])).get("manifests", []):
            ann = child.get("annotations") or {}
            if ann.get("vnd.docker.reference.type"):
                continue  # attestation / 附属清单
            plat = child.get("platform") or {}
            if plat.get("os") == "linux" and plat.get("architecture") == "amd64":
                chosen = child
                break
        if chosen is None:
            raise SystemExit("manifest list 中未找到 linux/amd64 镜像清单")
        tag = tag or (chosen.get("annotations") or {}).get("io.containerd.image.name", "")
        desc = chosen

    return load_blob_bytes(blobs_dir, desc["digest"]), tag


def open_any_tar(path: Path):
    """按魔数自动识别 tar / tar.gz 打开。"""
    with open(path, "rb") as f:
        head = f.read(2)
    if head == b"\x1f\x8b":
        return tarfile.open(path, "r:gz")
    return tarfile.open(path, "r:")


def deterministic_info(name: str, size: int, mode: int = 0o644):
    info = tarfile.TarInfo(name)
    info.size = size
    info.mode = mode
    info.mtime = 0
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    return info


def convert(src: Path, dst: Path, tag_override: str | None) -> None:
    # 工作目录可用 OCI2DOCKER_TMPDIR 指定（如系统盘空间不足时放到其他盘）
    workdir = os.environ.get("OCI2DOCKER_TMPDIR") or None
    with tempfile.TemporaryDirectory(prefix="oci2docker-", dir=workdir) as tmp:
        tmp_dir = Path(tmp)
        with open_any_tar(src) as tf:
            tf.extractall(tmp_dir)  # 归档来自本机 docker save，可信输入

        blobs_dir = tmp_dir / "blobs"
        layout = tmp_dir / "oci-layout"
        if not layout.exists() or not blobs_dir.exists():
            raise SystemExit("输入不是 OCI 布局归档（缺少 oci-layout/blobs）")

        index = json.loads((tmp_dir / "index.json").read_text(encoding="utf-8"))
        manifest_bytes, ann_tag = pick_image_manifest(index, blobs_dir)
        manifest = json.loads(manifest_bytes)

        tag = tag_override or ann_tag
        if not tag:
            raise SystemExit("无法确定镜像标签，请用 --tag repo:tag 指定")
        repo, _, repo_tag = tag.rpartition(":")
        if not repo or not repo_tag:
            raise SystemExit(f"标签格式应为 repo:tag，得到: {tag}")

        config_digest = manifest["config"]["digest"]
        config_hex = config_digest.split(":", 1)[1]
        config_bytes = load_blob_bytes(blobs_dir, config_digest)
        config = json.loads(config_bytes)
        diff_ids = config["rootfs"]["diff_ids"]

        layers = manifest.get("layers") or manifest.get("fsLayers") or []
        if len(layers) != len(diff_ids):
            raise SystemExit(f"层数不匹配: manifest {len(layers)} vs config {len(diff_ids)}")

        layer_entries: list[tuple[str, bytes]] = []
        for i, (layer_desc, diff_id) in enumerate(zip(layers, diff_ids)):
            data = load_blob_bytes(blobs_dir, layer_desc["digest"])
            mt = layer_desc.get("mediaType", "")
            if any(k in mt for k in GZIP_LAYER_TYPES) or is_gzip(data):
                data = gzip.decompress(data)
            actual = sha256_hex(data)
            expected = diff_id.split(":", 1)[1]
            if actual != expected:
                raise SystemExit(f"第 {i} 层哈希不匹配: 实际 {actual} != config 声明 {expected}")
            layer_id = actual
            layer_entries.append((f"{layer_id}/layer.tar", data))
            print(f"  layer {i}: {layer_id[:16]}… 校验通过")

        top_layer_id = diff_ids[-1].split(":", 1)[1]

        with open(dst, "wb") as raw_out:
            gz = gzip.GzipFile(filename="", mode="wb", fileobj=raw_out, mtime=0)
            with tarfile.open(fileobj=gz, mode="w") as out:
                # 固定写入顺序：层 → config → manifest.json → repositories
                for name, data in layer_entries:
                    out.addfile(deterministic_info(name, len(data)), io.BytesIO(data))
                    out.addfile(deterministic_info(f"{name.rsplit('/', 1)[0]}/VERSION", 4),
                                io.BytesIO(b"1.0\n"))
                out.addfile(deterministic_info(f"{config_hex}.json", len(config_bytes)),
                            io.BytesIO(config_bytes))
                manifest_json = json.dumps(
                    [{
                        "Config": f"{config_hex}.json",
                        "RepoTags": [f"{repo}:{repo_tag}"],
                        "Layers": [name for name, _ in layer_entries],
                    }],
                    separators=(",", ":"),
                ).encode()
                out.addfile(deterministic_info("manifest.json", len(manifest_json)),
                            io.BytesIO(manifest_json))
                repositories = json.dumps(
                    {repo: {repo_tag: top_layer_id}}, separators=(",", ":")
                ).encode()
                out.addfile(deterministic_info("repositories", len(repositories)),
                            io.BytesIO(repositories))
            gz.close()

        print(f"已生成传统 Docker 归档: {dst}")
        print(f"  镜像标签: {repo}:{repo_tag}")
        print(f"  层数: {len(layer_entries)}, 顶层: {top_layer_id[:16]}…")


def main() -> None:
    parser = argparse.ArgumentParser(description="OCI 布局归档 → 传统 Docker 归档")
    parser.add_argument("src", type=Path)
    parser.add_argument("dst", type=Path)
    parser.add_argument("--tag", help="输出镜像标签 repo:tag（缺省用归档内注解）")
    args = parser.parse_args()
    convert(args.src, args.dst, args.tag)


if __name__ == "__main__":
    main()
