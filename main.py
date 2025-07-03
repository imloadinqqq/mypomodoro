import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from db import conn

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(Path('./style.qss').read_text())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

    conn.close()
