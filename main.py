import transmission_rpc
import csv
import connection # 导入connection模块
import torrent_processor # 导入新的 torrent_processor 模块


def get_torrents_info_and_save_to_csv(filename='torrent_details.csv'):
    """
    获取Transmission中的种子列表，包括其标签、名称、制作组和文件大小，
    处理重复任务并归纳标签，然后保存到CSV文件。

    参数:
    filename: 保存CSV文件的名称 (默认: 'torrent_details.csv')
    """
    try:
        client = connection.client

        if client is None:
            print("错误: Transmission客户端未成功连接。请检查connection.py中的配置。")
            return

        # 使用 torrent_processor 处理种子信息
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

    except Exception as e:
        print(f"获取或保存种子信息失败: {e}")


def main():
    print("测试连接到Transmission...")
    
    # connection模块在导入时已经尝试连接，所以这里不需要额外的调用
    print("\n4. 调用connection.py进行连接测试:")
    if connection.client:
        print("Transmission客户端已连接。")
    else:
        print("Transmission客户端未连接。请检查connection.py中的配置。")

    print("\n5. 获取Transmission种子列表并保存到CSV:")
    get_torrents_info_and_save_to_csv()


if __name__ == "__main__":
    main()