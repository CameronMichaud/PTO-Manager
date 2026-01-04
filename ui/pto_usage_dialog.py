from PyQt5.QtWidgets import (
    QDialog, QFormLayout,
    QDateEdit, QDoubleSpinBox, QPushButton, QMessageBox, QVBoxLayout, QCheckBox
)
from PyQt5.QtCore import QDate

class PTOUsageDialog(QDialog):
    def __init__(self, parent=None, horizon_date=None):
        super().__init__(parent)
        
        if horizon_date is None:
            horizon_date = QDate.currentDate()
            
        self.setWindowTitle("Add PTO Usage")
        self.resize(350, 100)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.date = QDateEdit(horizon_date)
        self.date.setCalendarPopup(True)

        self.hours = QDoubleSpinBox()
        self.hours.setMaximum(24)
        self.hours.setValue(8)

        save = QPushButton("Save")
        save.clicked.connect(self.accept)

        form.addRow("Date", self.date)
        form.addRow("Hours", self.hours)

        layout.addLayout(form)
        layout.addWidget(save)

    def get_data(self):
        return {
            "date": self.date.date().toString("yyyy-MM-dd"),
            "hours": self.hours.value()
        }
