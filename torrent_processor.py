import re
from collections import defaultdict

def process_torrents(client):
    """
    获取Transmission中的种子列表，处理并返回包含文件大小、合并标签和制作组信息的列表。

    参数:
    client: 已连接的 Transmission RPC 客户端实例

    返回:
    一个字典列表，每个字典代表一个处理后的种子任务，包含 '名称', '文件大小', '原始文件大小', '制作组', '标签数量', '标签'。
    """
    if client is None:
        print("错误: Transmission客户端未成功连接。")
        return []

    torrents = client.get_torrents(arguments=['name', 'labels', 'totalSize'])

    # 要忽略的标签
    ignored_labels = {"IYUU自动转移", "IYUU自动辅种"}

    # 用于合并相同名称的种子
    processed_torrents = defaultdict(lambda: {'labels': set(), 'total_size': None, 'maker': '未知'})

    for torrent in torrents:
        name = torrent.name
        # 过滤掉指定的标签
        labels = {label for label in torrent.labels if label not in ignored_labels} if torrent.labels else set()
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
        sorted_labels = sorted(list(data['labels']))
        label_count = len(sorted_labels)
        result_list.append({
            '名称': name,
            '文件大小': format_size(data['total_size']),
            '原始文件大小': data['total_size'], # 添加原始文件大小
            '制作组': data['maker'],
            '标签数量': label_count,
            '标签': ', '.join(sorted_labels) if sorted_labels else '无标签',
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