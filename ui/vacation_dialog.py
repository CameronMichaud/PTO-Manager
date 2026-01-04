from PyQt5.QtWidgets import (
    QDialog, QFormLayout,
    QDateEdit, QDoubleSpinBox, QPushButton, QMessageBox, QVBoxLayout, QCheckBox
)
from PyQt5.QtCore import QDate

class PTOVacationDialog(QDialog):
    def __init__(self, parent=None, horizon_date=None):
        super().__init__(parent)
        
        if horizon_date is None:
            horizon_date = QDate.currentDate()
            
        self.setWindowTitle("Add PTO Usage")
        self.resize(350, 260)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.start_date = QDateEdit(horizon_date)
        self.start_date.setCalendarPopup(True)

        self.end_date = QDateEdit(horizon_date)
        self.end_date.setCalendarPopup(True)

        self.hours = QDoubleSpinBox()
        self.hours.setMaximum(24)
        self.hours.setValue(8)

        self.count_weekends = QCheckBox("Count Weekends")
        self.count_weekends.setChecked(False)

        save = QPushButton("Save")
        save.clicked.connect(self.validate)

        form.addRow("Start Date", self.start_date)
        form.addRow("End Date", self.end_date)
        form.addRow("Hours/Day", self.hours)
        form.addRow(self.count_weekends)

        layout.addLayout(form)
        layout.addWidget(save)

    def validate(self):
        if self.end_date.date() < self.start_date.date():
            QMessageBox.warning(self, "Invalid Range", "End date must be after start date.")
            return 1
        self.accept()

    def get_data(self):
        return {
            "start_date": self.start_date.date(),
            "end_date": self.end_date.date(),
            "hours": self.hours.value(),
            "count_weekends": self.count_weekends.isChecked()
        }
