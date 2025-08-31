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
    processed_torrents = defaultdict(lambda: {'labels': set(), 'total_size': None, 'maker': '未知'})

    for torrent in torrents:
        name = torrent.name
        labels = set(torrent.labels) if torrent.labels else set()
        total_size = torrent.total_size

        # 识别制作组
        maker = '未知'
        # 新规则：查找最后一个 '@' 或 '-'
        last_at_pos = name.rfind('@')
        last_dash_pos = name.rfind('-')

        # 确定哪个分隔符是最后一个
        separator_pos = max(last_at_pos, last_dash_pos)

        # 如果找到了分隔符，则提取其后的内容作为制作组
        if separator_pos != -1:
            potential_maker = name[separator_pos + 1:].strip()
            if potential_maker:
                maker = potential_maker

        # 合并信息
        processed_torrents[name]['labels'].update(labels)
        # 只有在尚未记录大小时才记录
        if processed_torrents[name]['total_size'] is None:
            processed_torrents[name]['total_size'] = total_size
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