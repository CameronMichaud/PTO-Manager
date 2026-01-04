from PyQt5.QtWidgets import (
    QDialog, QFormLayout,
    QDateEdit, QDoubleSpinBox, QPushButton, QMessageBox
)
from PyQt5.QtCore import QDate


class PTOUsageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add PTO Usage")
        self.resize(350, 260)

        form = QFormLayout(self)

        self.start_date = QDateEdit(QDate.currentDate())
        self.start_date.setCalendarPopup(True)

        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)

        self.hours = QDoubleSpinBox()
        self.hours.setMaximum(24)
        self.hours.setValue(8)

        save = QPushButton("Save")
        save.clicked.connect(self.validate)

        form.addRow("Start Date", self.start_date)
        form.addRow("End Date", self.end_date)
        form.addRow("Hours Used", self.hours)
        form.addRow(save)

    def validate(self):
        if self.end_date.date() < self.start_date.date():
            QMessageBox.warning(self, "Invalid Range", "End date must be after start date.")
            return
        self.accept()

    def get_data(self):
        return {
            "start_date": self.start_date.date(),
            "end_date": self.end_date.date(),
            "hours": self.hours.value()
        }
