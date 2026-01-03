from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QDateEdit, QDoubleSpinBox,
    QRadioButton, QPushButton
)
from PyQt5.QtCore import QDate

class EmployeeDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Employee")
        self.resize(300, 260)
        self.build_ui()
        if data:
            self.load_data(data)

    def build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name = QLineEdit()
        self.hire = QDateEdit(QDate.currentDate())
        self.hire.setCalendarPopup(True)

        self.total_pto = QDoubleSpinBox()
        self.total_pto.setMaximum(1000)
        self.total_pto.setValue(120)

        self.carry = QDoubleSpinBox()
        self.carry.setMaximum(200)

        form.addRow("Name", self.name)
        form.addRow("Hire Date", self.hire)
        form.addRow("PTO hrs/yr", self.total_pto)
        form.addRow("Carryover", self.carry)

        save = QPushButton("Save")
        save.clicked.connect(self.accept)

        layout.addLayout(form)
        layout.addWidget(save)

    def load_data(self, d):
        self.name.setText(d["name"])
        self.hire.setDate(QDate.fromString(d["hire_date"], "yyyy-MM-dd"))
        self.total_pto.setValue(float(d["total_pto"]))
        self.carry.setValue(float(d["carryover"]))

    def get_data(self):
        return {
            "name": self.name.text(),
            "hire_date": self.hire.date().toString("yyyy-MM-dd"),
            "total_pto": self.total_pto.value(),
            "carryover": self.carry.value()
        }
