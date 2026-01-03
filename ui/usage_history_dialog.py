from operator import add
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMenu, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt


class UsageHistoryDialog(QDialog):
    def __init__(self, id, employee_name, usage_records, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"PTO History — {employee_name}")
        self.resize(500, 300)

        self.employee_id = id
        self.employee = employee_name
        self.usage_records = usage_records

        self.build_ui()
        self.load_data()

    def build_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Date", "Hours", "ID"])
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_menu)
        self.table.setColumnHidden(2, True)
        self.table.setSortingEnabled(True)
        self.table.itemChanged.connect(self.cell_changed)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        close = QPushButton("Close")
        close.clicked.connect(self.accept)

        layout.addWidget(self.table)
        layout.addWidget(close)

    def load_data(self):
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)

        self.table.setRowCount(0)
        for usage in self.usage_records:
            if usage["employee_id"] == self.employee_id:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(usage["date"]))
                self.table.setItem(row, 1, QTableWidgetItem(str(usage["hours"])))
                self.table.setItem(row, 2, QTableWidgetItem(usage["id"]))

        self.table.blockSignals(False)
        self.table.setSortingEnabled(True)

        self.table.sortItems(0, Qt.DescendingOrder)
        self.table.setCurrentCell(-1, -1)

    def open_menu(self, pos):
        row = self.table.currentRow()
        if row < 0:
            return

        menu = QMenu()
        delete = menu.addAction("Delete Entry")
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action == delete:

            id = self.table.item(row, 2).text()
            self.usage_records[:] = [
                usage for usage in self.usage_records
                if usage["id"] != id
            ]
            self.load_data()

    def cell_changed(self, item):
        row = item.row()
        col = item.column()

        id_ = self.table.item(row, 2).text()
        new_date = self.table.item(row, 0).text()
        new_hours = self.table.item(row, 1).text()

        if col == 1:
            try:
                float(new_hours)
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Hours must be a number.")
                self.load_data()
                return

        for usage in self.usage_records:
            if usage["id"] == id_:
                usage["date"] = new_date
                usage["hours"] = new_hours
                break