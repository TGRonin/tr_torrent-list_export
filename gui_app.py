import sys
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QHeaderView
)
from PyQt5.QtCore import Qt
from main import get_torrents_info_and_save_to_csv # 导入获取数据的方法

class TorrentViewerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transmission 种子列表查看器")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        # 主垂直布局
        main_layout = QVBoxLayout()

        # 标题
        title_label = QLabel("Transmission 种子列表")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # 表格显示区域
        self.table_widget = QTableWidget()
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers) # 禁止编辑
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows) # 整行选择
        self.table_widget.setAlternatingRowColors(True) # 交替行颜色
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # 列宽自动拉伸

        main_layout.addWidget(self.table_widget)

        # 刷新按钮
        refresh_button = QPushButton("刷新数据")
        refresh_button.setStyleSheet("padding: 10px; font-size: 16px; background-color: #4CAF50; color: white; border-radius: 5px;")
        refresh_button.clicked.connect(self.load_data)
        main_layout.addWidget(refresh_button)

        self.setLayout(main_layout)
        self.load_data() # 初始化时加载数据

    def load_data(self):
        # 调用 main.py 中的函数来获取并保存数据到CSV
        get_torrents_info_and_save_to_csv('torrent_details.csv')
        
        # 从CSV文件读取数据
        try:
            with open('torrent_details.csv', 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames
                data = list(reader)

            self.table_widget.setColumnCount(len(headers))
            self.table_widget.setHorizontalHeaderLabels(headers)
            self.table_widget.setRowCount(len(data))

            for row_idx, row_data in enumerate(data):
                for col_idx, header in enumerate(headers):
                    item = QTableWidgetItem(row_data.get(header, ""))
                    self.table_widget.setItem(row_idx, col_idx, item)
            print("数据已从CSV文件加载并显示。")
        except FileNotFoundError:
            print("错误: 'torrent_details.csv' 文件未找到。请确保已生成数据。")
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
        except Exception as e:
            print(f"加载CSV数据失败: {e}")
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TorrentViewerApp()
    window.show()
    sys.exit(app.exec_())