from transmission_rpc import Client

# Transmission 连接配置（与项目现有配置保持一致）
HOST = "192.168.3.119"
PORT = 9091
USERNAME = "admin"
PASSWORD = "admin"

# 过滤条件与输出文件
TARGET_DOWNLOAD_DIR = "/download2/nsfw"
OUTPUT_FILE = "nsfw_name_comment.md"


def normalize_path(path: str) -> str:
    """统一路径格式，避免尾部斜杠导致匹配失败。"""
    if not path:
        return ""
    return path.rstrip("/")


def main() -> None:
    client = Client(
        host=HOST,
        port=PORT,
        username=USERNAME,
        password=PASSWORD,
    )

    torrents = client.get_torrents(arguments=["name", "comment", "downloadDir"])

    target = normalize_path(TARGET_DOWNLOAD_DIR)
    lines = []

    for torrent in torrents:
        download_dir = normalize_path(getattr(torrent, "download_dir", ""))
        if download_dir != target:
            continue

        name = (getattr(torrent, "name", "") or "").strip()
        comment = (getattr(torrent, "comment", "") or "").strip()

        # 按要求格式输出：[名称](注释)
        lines.append(f"[{name}]({comment})")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("".join(f"{line}\n\n" for line in lines))

    print(f"已导出 {len(lines)} 条记录到 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
