import re
from collections import defaultdict

def process_torrents(client):
    """
    获取Transmission中的种子列表，处理并返回包含文件大小、合并标签和制作组信息的列表。

    参数:
    client: 已连接的 Transmission RPC 客户端实例

    返回:
    一个字典列表，每个字典代表一个处理后的种子任务，包含 '名称', '标签', '制作组', '文件大小'。
    """
    if client is None:
        print("错误: Transmission客户端未成功连接。")
        return []

    torrents = client.get_torrents(arguments=['name', 'labels', 'totalSize'])

    # 用于合并相同名称的种子
    processed_torrents = defaultdict(lambda: {'labels': set(), 'total_size': 0, 'maker': '未知'})

    for torrent in torrents:
        name = torrent.name
        labels = set(torrent.labels) if torrent.labels else set()
        size_when_done = torrent.total_size

        # 识别制作组
        maker = '未知'
        match_at = re.search(r'@([^-\s]+)', name) # 匹配 @ 后面的内容直到 - 或空格
        match_dash = re.search(r'-([^-@\s]+)', name) # 匹配 - 后面的内容直到 @ 或空格

        if match_at:
            maker = match_at.group(1).strip()
        elif match_dash:
            maker = match_dash.group(1).strip()

        # 合并信息
        processed_torrents[name]['labels'].update(labels)
        processed_torrents[name]['total_size'] += size_when_done
        processed_torrents[name]['maker'] = maker # 假设制作组对于相同名称的种子是相同的，或者取第一个识别到的

    result_list = []
    for name, data in processed_torrents.items():
        result_list.append({
            '名称': name,
            '标签': ', '.join(sorted(list(data['labels']))) if data['labels'] else '无标签',
            '制作组': data['maker'],
            '文件大小': format_size(data['total_size'])
        })
    return result_list

def format_size(size_bytes):
    """
    将字节数格式化为更易读的单位 (B, KB, MB, GB, TB)。
    """
    if size_bytes is None:
        return "N/A"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB" # 理论上不会到PB，但以防万一