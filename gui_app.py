import sys
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QHeaderView
)
from PyQt5.QtCore import Qt, QVariant
from main import get_torrents_info_and_save_to_csv # 导入获取数据的方法

class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, value, display_text=None):
        super().__init__(display_text if display_text is not None else str(value))
        self.value = value

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.value < other.value
        return super().__lt__(other)

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
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive) # 允许用户调整列宽
        self.table_widget.setSortingEnabled(True) # 启用排序

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
                data = list(reader)

            # 定义新的列顺序
            desired_headers = ['名称', '文件大小', '制作组', '标签数量', '标签']
            # 注意：'原始文件大小' 字段用于排序，但不显示在表格中
            
            self.table_widget.setColumnCount(len(desired_headers))
            self.table_widget.setHorizontalHeaderLabels(desired_headers)
            self.table_widget.setRowCount(len(data))

            for row_idx, row_data in enumerate(data):
                for col_idx, header in enumerate(desired_headers):
                    display_value = row_data.get(header, "")
                    if header == '文件大小':
                        # 使用原始文件大小进行排序，但显示格式化后的文件大小
                        original_size_str = row_data.get('原始文件大小', '0')
                        try:
                            original_size = int(original_size_str)
                        except ValueError:
                            original_size = 0 # 如果转换失败，默认为0
                        item = NumericTableWidgetItem(original_size, display_value)
                    elif header == '标签数量':
                        try:
                            numeric_value = int(display_value)
                            item = NumericTableWidgetItem(numeric_value, display_value)
                        except ValueError:
                            item = QTableWidgetItem(display_value)
                    else:
                        item = QTableWidgetItem(str(display_value)) # 确保所有数据都转换为字符串
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