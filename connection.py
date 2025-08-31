import sys
from transmission_rpc import Client

# 配置Transmission的连接参数
HOST = "localhost"
PORT = 9091
USERNAME = "transmission"  # 如果没有认证，可设为None
PASSWORD = "password"      # 如果没有认证，可设为None

client = None # 初始化client为None

try:
    # 尝试连接到Transmission
    client = Client(host=HOST, port=PORT, username=USERNAME, password=PASSWORD)
    
    # 通过获取会话信息来测试连接
    session = client.get_session()
    
    # 如果成功，打印版本信息作为确认
    print("连接成功！")
    print(f"Transmission RPC 版本: {session.rpc_version}")
    print(f"Transmission 版本: {session.version}")
    
except Exception as e:
    print(f"连接失败: {e}")
    # 不在此处退出，以便main.py可以处理连接失败的情况
    # sys.exit(1)