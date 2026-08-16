"""分析种子列表的制作组识别情况"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import re
from collections import Counter

import connection

# 连接
client = connection.get_client()
if client is None:
    sys.exit(1)
torrents = client.get_torrents(arguments=['name', 'labels', 'totalSize'])

print(f"总共获取到 {len(torrents)} 个种子\n")

# 先看看所有种子的名称，特别关注制作组识别
ignored_labels = {"IYUU自动转移", "IYUU自动辅种"}

names = []
for t in torrents:
    raw_labels = set(t.labels) if t.labels else set()
    is_queen = any("皇后" in label for label in raw_labels)
    if is_queen:
        continue
    names.append(t.name)

print(f"过滤后剩余 {len(names)} 个种子\n")

# 用当前的 torrent_processor 识别制作组
from torrent_processor import process_torrents
results = process_torrents(client)

# 统计制作组分布
maker_counter = Counter()
unknown_names = []
for r in results:
    maker = r['制作组']
    maker_counter[maker] += 1
    if maker == '未知':
        unknown_names.append(r['名称'])

print("=== 制作组分布 ===")
for maker, count in maker_counter.most_common():
    print(f"  {maker}: {count}")

print(f"\n=== 未识别制作组的种子 ({len(unknown_names)} 个) ===")
for name in unknown_names:
    print(f"  {name}")

# 分析未识别种子的命名模式
print("\n=== 未识别种子的命名模式分析 ===")
bracket_patterns = Counter()
dash_patterns = Counter()
at_patterns = Counter()

for name in unknown_names:
    # 检查方括号前缀
    if name.startswith('['):
        end = name.find(']')
        if end > 1:
            bracket_patterns[name[1:end]] += 1
    
    # 检查 @ 分隔
    if '@' in name:
        parts = name.split('@')
        at_patterns[parts[-1][:30]] += 1
    
    # 检查 - 分隔 (最后一个)
    last_dash = name.rfind('-')
    if last_dash > 0:
        tail = name[last_dash+1:].strip()
        dot_pos = tail.find('.')
        if dot_pos > 0:
            tail = tail[:dot_pos]
        dash_patterns[tail[:30]] += 1

print("\n方括号前缀分布:")
for p, c in bracket_patterns.most_common(20):
    print(f"  [{p}]: {c}")

print("\n@ 后缀分布:")
for p, c in at_patterns.most_common(20):
    print(f"  @{p}: {c}")

print("\n- 后缀分布:")
for p, c in dash_patterns.most_common(30):
    print(f"  -{p}: {c}")
