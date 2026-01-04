import csv
from datetime import date, datetime
import os
import shutil
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSystemTrayIcon, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMenu, QDateEdit, QComboBox, QMessageBox, QHeaderView, QFileDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QDate

from ui.employee_dialog import EmployeeDialog
from ui.pto_usage_dialog import PTOUsageDialog
from ui.usage_history_dialog import UsageHistoryDialog
from ui.vacation_dialog import PTOVacationDialog
from util.pto_calc import calculate_pto, calculate_used_pto
from util.storage import load_csv, save_csv, employees_file, usage_file, get_data_dir

from pathlib import Path
import uuid
from util.theme import apply_theme, apply_saved_theme, save_theme, resource_path


class PTOManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PTO Manager")
        self.resize(900, 485)
        self.tray = QSystemTrayIcon(QIcon(str(resource_path(self, "icon.ico"))), self)
        self.setWindowIcon(QIcon(str(resource_path(self, "icon.ico"))))

        self.backup_data()
        self.employees = load_csv(employees_file())
        self.employee_dict = {}

        for emp in self.employees:
            # Make an ID if none (old csv)
            if "id" not in emp or not emp["id"]:
                emp["id"] = str(uuid.uuid4())
            # Map all employees by ID
            self.employee_dict[emp["id"]] = emp

        self.pto_usage = load_csv(usage_file())
        self.pto_usage_dict = {}

        for usage in self.pto_usage:
            # Make an ID if none (old csv)
            if "id" not in usage or not usage["id"]:
                usage["id"] = str(uuid.uuid4())

            # Map all usage records by ID
            employee_id = usage["employee_id"]
            self.pto_usage_dict.setdefault(employee_id, []).append(usage)

        self.build_ui()
        apply_saved_theme(self)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)
        self.refresh_table()

    def build_ui(self):
        layout = QVBoxLayout(self)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search employees...")
        self.search.textChanged.connect(self.filter_table)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Name",
            "Hire Date",
            "Yearly PTO",
            "Carryover",
            "Accrued PTO",
            "Used PTO",
            "Available PTO",
            "ID"
        ])
        self.table.setColumnHidden(7, True)  # Hide ID column
        self.table.itemChanged.connect(self.cell_changed)
        self.table.verticalHeader().setDefaultSectionSize(52)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSortingEnabled(True)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_menu)

        self.horizon = QDateEdit(QDate.currentDate())
        self.horizon.setAlignment(Qt.AlignCenter)
        self.horizon.setCalendarPopup(True)
        self.horizon.dateChanged.connect(self.as_of_changed)

        add_btn = QPushButton("Add Employee")
        add_btn.clicked.connect(self.add_employee)

        layout.addWidget(self.search)
        layout.addWidget(self.horizon)
        layout.addWidget(self.table)
        layout.addWidget(add_btn)

        self.search.setFocus()

    def refresh_table(self, horizon=None):
        try:
            if horizon is None: 
                horizon = self.horizon.date().toPyDate()
            text = self.search.text()
            self.horizon.date().toPyDate()
            self.table.blockSignals(True) # Stops cellChanged from firing
            self.table.setSortingEnabled(False)

            self.table.setRowCount(0)
            for emp in self.employees:
                self.add_row(emp, horizon)

            self.table.setSortingEnabled(True)
            self.table.blockSignals(False)
            self.filter_table(text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh table: {e}")

    def as_of_changed(self):

        new_date = self.horizon.date().toPyDate()
        self.refresh_table(new_date)

    def add_row(self, emp, horizon=None):
        row = self.table.rowCount()
        self.table.insertRow(row)

        accrued = calculate_pto(emp, horizon)
        usage = self.pto_usage_dict.get(emp["id"], [])
        used = calculate_used_pto(emp["id"], usage, horizon)
        carryover = float(emp["carryover"])
        available = accrued + carryover - used

        values = [
            emp["name"],
            emp["hire_date"],
            emp["total_pto"],
            emp["carryover"],
            accrued,
            used,
            available,
            emp["id"]
        ]

        for col, value in enumerate(values):
            item = QTableWidgetItem(str(round(value, 2) if isinstance(value, float) else value))

            if col >= 2 and col < 7:
                item = QTableWidgetItem(str(round(value, 2) if isinstance(value, float) else value))
                item.setData(Qt.EditRole, float(value))
            if col > 3:
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)

            if col == 6 and available < 0:
                item.setBackground(QColor("#AC4646"))
                item.setForeground(QColor("#FFFFFF"))
            elif col == 6 and available >= 40 and available < 80:
                item.setBackground(QColor("#4CB12A"))
                item.setForeground(QColor("#FFFFFF"))
            elif col == 6 and available >= 80:
                item.setBackground(QColor("#195D15"))
                item.setForeground(QColor("#FFFFFF"))

            self.table.setItem(row, col, item)

    def add_employee(self):
        dlg = EmployeeDialog(self)
        if dlg.exec_():
            data = dlg.get_data()
            data["id"] = str(uuid.uuid4())
            self.employees.append(data)
            self.employee_dict[data["id"]] = data
            self.save_all()
            self.refresh_table()

    def edit_employee(self, row):
        id = self.table.item(row, 7).text()
        emp = self.employee_dict[id]
        dlg = EmployeeDialog(self, emp)
        if dlg.exec_():
            new_data = dlg.get_data()
            new_data["id"] = id

            self.employee_dict[id].update(new_data)
            self.save_all()
            self.refresh_table()

    def delete_employee(self, row):
        id = self.table.item(row, 7).text()
        reply = QMessageBox.warning( 
            self, "Confirm Delete", 
            f"Are you sure you want to delete employee '{self.table.item(row, 0).text()}'?", 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No )
        if reply == QMessageBox.Yes:
            self.employees = [employee for employee in self.employees if employee["id"] != id]
            self.employee_dict.pop(id, None)
            self.pto_usage = [usage for usage in self.pto_usage if usage["employee_id"] != id]
            self.pto_usage_dict.pop(id, None)
            self.save_all()
            self.refresh_table()

    def add_vacation(self, row):
        id = self.table.item(row, 7).text()
        emp = self.employee_dict[id]

        dlg = PTOVacationDialog(self, self.horizon.date())
        if dlg.exec_():
            data = dlg.get_data()

            if data["count_weekends"]:
                days = self.get_all_days( data["start_date"], data["end_date"] )
            else:
                days = self.get_weekdays( data["start_date"], data["end_date"] )

            for day in days:
                usage = {
                    "id": str(uuid.uuid4()),
                    "employee_id": id,
                    "employee": emp["name"],
                    "date": day.toString("yyyy-MM-dd"),
                    "hours": data["hours"]
                }

                self.pto_usage.append(usage)
                self.pto_usage_dict.setdefault(id, []).append(usage)

            self.save_all()
            self.refresh_table()

    def add_pto_usage(self, row):
        id = self.table.item(row, 7).text()
        emp = self.employee_dict[id]

        dlg = PTOUsageDialog(self, self.horizon.date())
        if dlg.exec_():
            data = dlg.get_data()

            usage = {
                "id": str(uuid.uuid4()),
                "employee_id": id,
                "employee": emp["name"],
                **data
            }

            self.pto_usage.append(usage)
            self.pto_usage_dict.setdefault(id, []).append(usage)

            self.save_all()
            self.refresh_table()

    def get_weekdays(self, start_date, end_date):
        weekdays = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.dayOfWeek() <= 5:
                weekdays.append(current_date)
            current_date = current_date.addDays(1)
        return weekdays
    def get_all_days(self, start_date, end_date):
        days = []
        current_date = start_date
        while current_date <= end_date:
            days.append(current_date)
            current_date = current_date.addDays(1)
        return days

    def backup_data(self):
        try:
            if not employees_file().exists() and not usage_file().exists():
                return
            self.kill_backups(keep=40)
            backup_dir = get_data_dir() / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            emp_backup = backup_dir / f"pto_employees_backup_{timestamp}.csv"
            usage_backup = backup_dir / f"pto_usage_backup_{timestamp}.csv"

            shutil.copy(employees_file(), emp_backup)
            shutil.copy(usage_file(), usage_backup)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to backup data: {e}")
    
    def kill_backups(self, keep=40):
        try:
            backup_dir = get_data_dir() / "backups"
            if not backup_dir.exists():
                return

            emp_backups = sorted(backup_dir.glob("pto_employees_backup_*.csv"), key=os.path.getmtime)
            usage_backups = sorted(backup_dir.glob("pto_usage_backup_*.csv"), key=os.path.getmtime)

            for backups in [emp_backups, usage_backups]:
                while len(backups) > keep:
                    old_backup = backups.pop(0)
                    old_backup.unlink()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to clean up backups in {backup_dir}: {e}")

    def save_all(self):
        save_csv(
            employees_file(),
            self.employees,
            ["id", "name", "hire_date", "total_pto", "carryover"]
        )
        save_csv(
            usage_file(),
            self.pto_usage,
            ["id", "employee_id", "employee", "date", "hours"]
        )

    def cell_changed(self, item):
        row = item.row()
        col = item.column()
        new_value = item.text()

        # Map table columns to employee dict keys
        keys = ["name", "hire_date", "total_pto", "carryover"]

        # Only columns 0–4 are editable employee fields
        if col < len(keys):
            key = keys[col]

            try:
                if key == "hire_date":
                    QDate.fromString(new_value, "yyyy-MM-dd")
                    if not QDate.fromString(new_value, "yyyy-MM-dd").isValid():
                        raise ValueError("Invalid date format")
                
                elif key in ["total_pto", "carryover"]:
                    if new_value is None or new_value.strip() == "":
                        raise ValueError("Value cannot be empty")
                    float(new_value)

            except ValueError as e:
                #QMessageBox.critical(self, "Error", f"Invalid value for {key}: {e}")
                
                old_value = self.employees[row][key]
                item.setText(str(old_value))

                return

            # Save
            #self.employees[row][key] = new_value
            id = self.table.item(row, 7).text()
            self.employee_dict[id][key] = new_value
            self.save_all()
            self.refresh_table()

    def open_menu(self, pos):
        row = self.table.currentRow()
        if row < 0:
            return

        menu = QMenu()
        edit = menu.addAction("Edit Employee")
        usage = menu.addAction("Add PTO Usage")
        vacation = menu.addAction("Add Vacation")
        history = menu.addAction("View PTO History")
        delete = menu.addAction("Delete Employee")

        # REMOVE PTO
        menu.addSeparator()
        remove_pto_menu = menu.addMenu("Delete Old PTO")
        delete_emp_year = remove_pto_menu.addAction("Delete Old PTO")
        delete_all_year = remove_pto_menu.addAction("Delete Old PTO (All)")
        # DATA
        data_menu = menu.addMenu("Data")
        export_csv = data_menu.addAction("Export PTO CSVs")
        import_csv = data_menu.addAction("Import PTO CSVs")
        export_ = data_menu.addAction("Export App Data")
        import_ = data_menu.addAction("Import App Data")

        # THEMES
        theme_menu = menu.addMenu("Themes")

        dark_theme = theme_menu.addAction("Dark Theme")
        nordic_theme = theme_menu.addAction("Nordic Theme")
        royal_red_theme = theme_menu.addAction("Red Theme")
        cyan_theme = theme_menu.addAction("Cyan Theme")
        dark_blue_theme = theme_menu.addAction("Dark Blue Theme")
        radianse_theme_dark = theme_menu.addAction("Radianse Dark Theme")
        radianse_theme_light = theme_menu.addAction("Radianse Light Theme")

        action = menu.exec_(self.table.mapToGlobal(pos))
        current_year = date.today().year

        if action == edit:
            self.edit_employee(row)
        elif action == usage:
            self.add_pto_usage(row)
        elif action == vacation:
            self.add_vacation(row)
        elif action == history:
            id = self.table.item(row, 7).text()
            name = self.table.item(row, 0).text()
            dlg = UsageHistoryDialog(id, name, self.pto_usage, self)
            dlg.exec_()
            self.update_pto_usage()
            self.save_all()
            self.refresh_table()
        elif action == delete_emp_year:
            emp_id = self.table.item(row, 7).text()  # selected employee
            reply = QMessageBox.warning(
                self,
                "Confirm Delete",
                f"Delete all PTO entries before {current_year} for {self.table.item(row, 0).text()}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.pto_usage = [
                    usage for usage in self.pto_usage
                    if not (usage["employee_id"] == emp_id and int(usage["date"][:4]) < current_year)
                ]
                self.update_pto_usage()
                self.save_all()
                self.refresh_table()
        elif action == delete_all_year:
            reply = QMessageBox.warning(
            self,
            "Confirm Delete",
            f"Delete all PTO entries before {current_year} for all employees?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.pto_usage = [
                    usage for usage in self.pto_usage
                    if int(usage["date"][:4]) >= current_year
                ]
                self.update_pto_usage()
                self.save_all()
                self.refresh_table()
        elif action == delete:
            self.delete_employee(row)
        elif action == export_csv:
            self.export_csv()
        elif action == export_:
            self.export_data()
        elif action == import_:
            self.import_data()
        elif action == import_csv:
            self.import_csv_directory()

        elif action == dark_theme:
            apply_theme(self, "theme_dark")
        elif action == nordic_theme:
            apply_theme(self, "theme_nordic")
        elif action == royal_red_theme:
            apply_theme(self, "theme_red")
        elif action == radianse_theme_dark:
            apply_theme(self, "theme_radianse_dark")
        elif action == radianse_theme_light:
            apply_theme(self, "theme_radianse_light")
        elif action == dark_blue_theme:
            apply_theme(self, "theme_dark_blue")
        elif action == cyan_theme:
            apply_theme(self, "theme_cyan")

    def filter_table(self, text):
        text = text.lower()

        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            if name_item:
                name = name_item.text().lower()
                self.table.setRowHidden(row, text not in name)
    
    def update_pto_usage(self):
        self.pto_usage_dict = {}

        for usage in self.pto_usage:
            emp_id = usage.get("employee_id")
            if not emp_id:
                continue
            self.pto_usage_dict.setdefault(emp_id, []).append(usage)

    def export_data(self):
        source = get_data_dir()
        source.mkdir(parents=True, exist_ok=True)

        target_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            str(Path.home())
        )
        if not target_dir:
            return
        
        files = ["pto_employees.csv", "pto_usage.csv"]

        for file in files:
            source_file = source / file
            dir_out = Path(target_dir) / file

            if source_file.exists():
                try:
                    shutil.copy(source_file, dir_out)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export {file}: {e}")
                    return

        QMessageBox.information(self, "Export Complete", f"Files exported successfully to {target_dir}.")

    def export_csv(self):
        try:
            source = get_data_dir()
            source.mkdir(parents=True, exist_ok=True)

            target_dir = QFileDialog.getExistingDirectory(
                self,
                "Select Export Directory",
                str(Path.home())
            )
            if not target_dir:
                return
            num_emps = 0
            for emp_id, record in self.pto_usage_dict.items():
                filename = os.path.join(target_dir, f"pto_usage_{record[0]['employee']}.csv")
                with open(filename, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["employee", "date", "hours"])

                    for usage in record:
                        writer.writerow([usage["employee"], usage["date"], usage["hours"]])
                num_emps += 1

            QMessageBox.information(self, "Export Complete", f"{num_emps} PTO sheets exported successfully to {target_dir}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export CSV files: {e}")

    def get_employee_id(self, employee_name):
        for emp in self.employees:
            if emp["name"] == employee_name:
                return emp["id"]
        
        new_id = str(uuid.uuid4())
        self.employee_dict[new_id] = {
            "id": new_id,
            "name": employee_name,
            "hire_date": QDate.currentDate().toString("yyyy-MM-dd"),
            "total_pto": "0",
            "carryover": "0"
        }
        self.employees.append(self.employee_dict[new_id])
        return new_id

    def import_data(self):
        try:
            target_dir = get_data_dir()
            target_dir.mkdir(parents=True, exist_ok=True)

            source_dir = QFileDialog.getExistingDirectory(
                self,
                "Select Import Directory",
                str(Path.home())
            )
            if not source_dir:
                return

            source_dir = Path(source_dir)
            files = ["pto_employees.csv", "pto_usage.csv"]

            for file in files:
                if not (source_dir / file).exists():
                    QMessageBox.critical(self, "Error", f"File {file} not found in selected directory.")
                    return
            try:
                for file in files:
                    shutil.copy(source_dir / file, target_dir / file)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import data: {e}")
                return
            
            QMessageBox.information(self, "Import Complete", "Files imported successfully.")

            self.employees = load_csv(employees_file())
            self.employee_dict = {emp["id"]: emp for emp in self.employees}

            self.pto_usage = load_csv(usage_file())
            self.update_pto_usage()

            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import data: {e}")
    
    def import_csv_directory(self):
        try:
            directory = QFileDialog.getExistingDirectory(
                self,
                "Select Directory CSV Files"
            )
            if not directory:
                return

            imported = 0

            for filename in os.listdir(directory):
                if not filename.lower().endswith(".csv"):
                    continue

                path = os.path.join(directory, filename)

                with open(path, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)

                    if not {"employee", "date", "hours"}.issubset(reader.fieldnames):
                        QMessageBox.warning(
                            self,
                            "Invalid CSV",
                            f"CSV file {filename} not formatted correctly: employee, date, hours."
                        )
                        continue

                    rows = list(reader)
                    if not rows:
                        continue

                    employee_name = rows[0]["employee"]
                    employee_id = self.get_employee_id(employee_name)

                    for row in rows:
                        usage = {
                            "id": str(uuid.uuid4()),
                            "employee_id": employee_id,
                            "employee": employee_name,
                            "date": row["date"],
                            "hours": float(row["hours"])
                        }

                        self.pto_usage.append(usage)
                        self.pto_usage_dict.setdefault(employee_id, []).append(usage)
                        imported += 1

            self.save_all()
            self.refresh_table()

            QMessageBox.information(
                self,
                "Import Complete",
                f"Imported {imported} PTO entries successfully."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import CSV files: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PTOManager()
    window.show()
    sys.exit(app.exec_())

