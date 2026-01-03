from util.storage import get_data_dir
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox

def resource_path(self, relative_path):
        base_path = Path(getattr(sys, '_MEIPASS', str(Path(__file__).parent.parent)))
        return base_path / relative_path
    
def apply_theme(self, theme_file="theme_nordic"):
    self.current_theme = theme_file
    theme_file = resource_path(self, f"themes/{theme_file}.qss")
    try:
        with open(theme_file, "r") as f:
            QApplication.instance().setStyleSheet(f.read())
        save_theme(self)
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to load theme: {e}")

def save_theme(self):
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    theme_file = data_dir / "current_theme.txt"
    try:
        with open(theme_file, "w") as f:
            f.write(str(self.current_theme))
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to save theme: {e}")

def apply_saved_theme(self):
    try:
        theme_file = get_data_dir() / "current_theme.txt"
        if not theme_file.exists():
            apply_theme(self, "theme_nordic")
            return
        
        with open(theme_file, "r") as f:
            theme_name = f.read().strip()
        if theme_name:
            apply_theme(self, theme_name)
        else:
            apply_theme(self, "theme_nordic")
    except Exception as e:
        apply_theme(self, "theme_nordic")
        QMessageBox.critical(self, "Error", f"Failed to save theme: {e}")