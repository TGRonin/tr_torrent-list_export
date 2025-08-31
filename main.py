import transmission_rpc
import csv
import connection # 导入connection模块


def get_torrents_info_and_save_to_csv(filename='torrent.csv'):
    """
    获取Transmission中的种子列表，包括其标签和名称，并保存到CSV文件。

    参数:
    filename: 保存CSV文件的名称 (默认: 'torrent.csv')
    """
    try:
        # 直接使用 connection.client
        client = connection.client

        if client is None:
            print("错误: Transmission客户端未成功连接。请检查connection.py中的配置。")
            return

        torrents = client.get_torrents(arguments=['name', 'labels'])

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['名称', '标签']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for torrent in torrents:
                name = torrent.name
                labels = ', '.join(torrent.labels) if torrent.labels else '无标签'
                writer.writerow({'名称': name, '标签': labels})

        print(f"成功将种子信息保存到 {filename}")

    except Exception as e:
        print(f"获取或保存种子信息失败: {e}")


def main():
    print("测试连接到Transmission...")
    
    # 移除对 test_transmission_connection 的调用，因为 connection.py 已经处理了连接
    # 示例1: 连接到本地Transmission (默认设置)
    # print("\n1. 连接到本地Transmission (localhost:9091):")
    # test_transmission_connection()
    
    # 示例2: 连接到远程Transmission
    # 取消注释并修改下面的代码以连接到远程Transmission
    # print("\n2. 连接到远程Transmission:")
    # test_transmission_connection(host='192.168.1.100', port=9091)
    
    # 示例3: 连接到需要认证的远程Transmission
    # 取消注释并修改下面的代码以连接到需要认证的远程Transmission
    # print("\n3. 连接到需要认证的远程Transmission:")
    # test_transmission_connection(host='192.168.1.100', port=9091, username='your_username', password='your_password')

    # 调用connection.py中的连接测试
    print("\n4. 调用connection.py进行连接测试:")
    # connection模块在导入时已经尝试连接，所以这里不需要额外的调用
    if connection.client:
        print("Transmission客户端已连接。")
    else:
        print("Transmission客户端未连接。请检查connection.py中的配置。")

    print("\n5. 获取Transmission种子列表并保存到CSV:")
    get_torrents_info_and_save_to_csv()


if __name__ == "__main__":
    main()