import csv
import os
import platform
from pathlib import Path


def get_data_dir():
    system = platform.system()
    if system == "Windows":
        appdata = Path(os.getenv("APPDATA"))
        if appdata is not None:
            return appdata / "PTO Manager Files"
        return Path.home() / "AppData" / "Roaming" / "PTO Manager Files"
    return Path.home() / "PTO Manager Files"


def employees_file():
    return get_data_dir() / "pto_employees.csv"


def usage_file():
    return get_data_dir() / "pto_usage.csv"


def load_csv(path):
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def save_csv(path, rows, headers):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
