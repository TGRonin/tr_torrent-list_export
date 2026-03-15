import sys
import csv
from typing import List, Dict, Set

from PySide6.QtCore import Qt, QSortFilterProxyModel, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QComboBox,
    QTableView,
    QFileDialog,
    QMessageBox,
    QStatusBar,
)

import connection
import torrent_processor


HEADERS = ["名称", "文件大小", "原始文件大小", "制作组", "标签数量", "标签"]


class TorrentFilterProxy(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.search_text = ""
        self.label_filter = "全部"
        self.maker_filter = "全部"

    def set_search_text(self, text: str):
        self.search_text = text.strip().lower()
        self.invalidateFilter()

    def set_label_filter(self, label: str):
        self.label_filter = label
        self.invalidateFilter()

    def set_maker_filter(self, maker: str):
        self.maker_filter = maker
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        if model is None:
            return False

        def data_by_header(header: str) -> str:
            try:
                col = HEADERS.index(header)
                return str(model.index(source_row, col, source_parent).data() or "")
            except ValueError:
                return ""

        name = data_by_header("名称").lower()
        tags = data_by_header("标签").lower()
        maker = data_by_header("制作组")

        if self.search_text:
            if self.search_text not in name and self.search_text not in tags:
                return False

        if self.label_filter not in ("全部", ""):
            if self.label_filter.lower() not in tags:
                return False

        if self.maker_filter not in ("全部", ""):
            if maker != self.maker_filter:
                return False

        return True


class TorrentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Transmission 种子列表 - PySide6")
        self.resize(1000, 700)

        self.model = QStandardItemModel()
        self.proxy = TorrentFilterProxy()
        # 使用用户角色的数值进行排序，避免文件大小按字符串排序
        self.proxy.setSortRole(Qt.UserRole)
        self.proxy.setSourceModel(self.model)

        self._init_ui()
        self.load_data()

    def _init_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()

        # 顶部过滤与动作区域
        controls_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索名称/标签")
        self.search_input.textChanged.connect(self.proxy.set_search_text)
        controls_layout.addWidget(QLabel("搜索:"))
        controls_layout.addWidget(self.search_input)

        self.label_combo = QComboBox()
        self.label_combo.addItem("全部")
        self.label_combo.currentTextChanged.connect(self.proxy.set_label_filter)
        controls_layout.addWidget(QLabel("标签:"))
        controls_layout.addWidget(self.label_combo)

        self.maker_combo = QComboBox()
        self.maker_combo.addItem("全部")
        self.maker_combo.currentTextChanged.connect(self.proxy.set_maker_filter)
        controls_layout.addWidget(QLabel("制作组:"))
        controls_layout.addWidget(self.maker_combo)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_data)
        controls_layout.addWidget(self.refresh_btn)

        self.export_btn = QPushButton("导出当前视图")
        self.export_btn.clicked.connect(self.export_current_view)
        controls_layout.addWidget(self.export_btn)

        controls_layout.addStretch(1)

        main_layout.addLayout(controls_layout)

        # 表格
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnHidden(HEADERS.index("原始文件大小"), True)
        main_layout.addWidget(self.table)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # 状态栏
        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel()
        status.addWidget(self.status_label)

    def load_data(self):
        try:
            client = connection.client
            if client is None:
                self._show_error("Transmission 未连接，请检查 connection.py 配置。")
                return

            records = torrent_processor.process_torrents(client)
            self._populate_model(records)
            self._update_filters(records)
            self._update_status(records)
        except Exception as exc:
            self._show_error(f"加载数据失败: {exc}")

    def _populate_model(self, records: List[Dict]):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(HEADERS)

        for row in records:
            items = []
            for header in HEADERS:
                value = row.get(header, "")
                item = QStandardItem(str(value))
                # 数值列用于排序
                if header == "文件大小":
                    # 使用原始字节大小作为排序依据，确保 12GB > 500MB
                    try:
                        item.setData(int(row.get("原始文件大小", 0) or 0), Qt.UserRole)
                    except ValueError:
                        item.setData(0, Qt.UserRole)
                elif header in ("原始文件大小", "标签数量"):
                    try:
                        item.setData(int(row.get(header, 0) or 0), Qt.UserRole)
                    except ValueError:
                        item.setData(0, Qt.UserRole)
                items.append(item)
            self.model.appendRow(items)

        # 隐藏原始大小列
        self.table.setColumnHidden(HEADERS.index("原始文件大小"), True)
        self.table.resizeColumnsToContents()

    def _update_filters(self, records: List[Dict]):
        labels: Set[str] = set()
        makers: Set[str] = set()

        for row in records:
            tags = row.get("标签", "")
            for tag in [t.strip() for t in tags.split(',') if t.strip()]:
                labels.add(tag)
            maker = row.get("制作组", "")
            if maker:
                makers.add(maker)

        current_label = self.label_combo.currentText()
        current_maker = self.maker_combo.currentText()

        self.label_combo.blockSignals(True)
        self.label_combo.clear()
        self.label_combo.addItem("全部")
        for label in sorted(labels):
            self.label_combo.addItem(label)
        if current_label in labels or current_label == "全部":
            self.label_combo.setCurrentText(current_label)
        self.label_combo.blockSignals(False)

        self.maker_combo.blockSignals(True)
        self.maker_combo.clear()
        self.maker_combo.addItem("全部")
        for maker in sorted(makers):
            self.maker_combo.addItem(maker)
        if current_maker in makers or current_maker == "全部":
            self.maker_combo.setCurrentText(current_maker)
        self.maker_combo.blockSignals(False)

    def _update_status(self, records: List[Dict]):
        self.status_label.setText(f"总数: {len(records)} | 过滤后: {self.proxy.rowCount()}")

    def export_current_view(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出当前视图", "torrent_view.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                visible_headers = [h for h in HEADERS if h != "原始文件大小"]
                writer.writerow(visible_headers)

                for row in range(self.proxy.rowCount()):
                    row_data = []
                    for header in visible_headers:
                        col = HEADERS.index(header)
                        index = self.proxy.index(row, col)
                        row_data.append(self.proxy.data(index))
                    writer.writerow(row_data)
            self.statusBar().showMessage(f"已导出: {path}", 5000)
        except Exception as exc:
            self._show_error(f"导出失败: {exc}")

    def _show_error(self, message: str):
        QMessageBox.critical(self, "错误", message)
        self.statusBar().showMessage(message, 5000)


def main():
    app = QApplication(sys.argv)
    window = TorrentWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
