from PyQt5.QtWidgets import (
    QDialog, QFormLayout,
    QDateEdit, QDoubleSpinBox, QPushButton
)
from PyQt5.QtCore import QDate


class PTOUsageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add PTO Usage")

        form = QFormLayout(self)

        self.date = QDateEdit(QDate.currentDate())
        self.date.setCalendarPopup(True)

        self.hours = QDoubleSpinBox()
        self.hours.setMaximum(24)
        self.hours.setValue(8)

        save = QPushButton("Save")
        save.clicked.connect(self.accept)

        form.addRow("Date", self.date)
        form.addRow("Hours Used", self.hours)
        form.addRow(save)

    def get_data(self):
        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "hours": self.hours.value()
        }
