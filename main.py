"""CLI：导出种子列表为 CSV（Web UI 不含此功能，仅供命令行使用）。"""
import csv

import connection
import torrent_processor


def get_torrents_info_and_save_to_csv(filename='torrent_details.csv'):
    """
    获取Transmission中的种子列表，包括其标签、名称、制作组和文件大小，
    处理重复任务并归纳标签，然后保存到CSV文件。

    参数:
    filename: 保存CSV文件的名称 (默认: 'torrent_details.csv')
    """
    client = connection.get_client()
    if client is None:
        print("错误: 无法连接 Transmission，未导出。")
        return

    processed_torrents = torrent_processor.process_torrents(client)
    if not processed_torrents:
        print("没有获取到种子信息或处理失败。")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['名称', '文件大小', '原始文件大小', '制作组', '标签数量', '标签']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for torrent_info in processed_torrents:
            writer.writerow(torrent_info)

    print(f"成功将种子信息保存到 {filename}")


if __name__ == "__main__":
    get_torrents_info_and_save_to_csv()
