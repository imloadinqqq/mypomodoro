from PyQt6.QtCore import QTime, QTimer, Qt, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QBoxLayout,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QLabel,
    QMainWindow,
    QPushButton,
    QWidget,
    QLineEdit,
    QMessageBox
)
from PyQt6.QtMultimedia import QSoundEffect
import logging
import sqlite3
from datetime import datetime, timedelta

logging.basicConfig(
    filename='app.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

conn = sqlite3.connect('history.db')
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        date DATE NOT NULL,
        time TIME NOT NULL,
        duration TIME NOT NULL
    )
""")
conn.commit()


def save_to_db(task, date, time, duration):
    c.execute("INSERT INTO history (task, date, time, duration) VALUES (?, ?, ?, ?)",
              (task, date, time, duration))
    conn.commit()


class SecondWindow(QMainWindow):
    def __init__(self, history_rows, parent=None):
        super().__init__(parent)
        self.setWindowTitle("History")

        self.delete_history_button = QPushButton("Erase All History")
        self.delete_history_button.clicked.connect(self.delete_history)

        self.delete_selection_button = QPushButton("Delete Selected")
        self.delete_selection_button.clicked.connect(self.delete_selection)

        self.layout = QVBoxLayout()
        self.list_widget = QListWidget()
        for row in history_rows:
            self.list_widget.addItem(
                f"{row[1]} | {row[2]} | {row[3]} | {row[4]}")
        container = QWidget()
        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(self.delete_history_button)
        self.layout.addWidget(self.delete_selection_button)
        container.setLayout(self.layout)
        container.setFixedSize(400, 200)
        self.setCentralWidget(container)

    def delete_history(self):
        msgBox = QMessageBox()
        msgBox.setText("You are about to delete all history!")
        msgBox.setInformativeText("Do you want to wipe your history?")
        msgBox.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msgBox.setDefaultButton(QMessageBox.StandardButton.Yes)
        ret = msgBox.exec()
        if ret == QMessageBox.StandardButton.Yes:
            try:
                c.execute("DELETE FROM history")
                conn.commit()
                self.list_widget.clear()
                logging.info("All history deleted.")
            except Exception as e:
                logging.error(f"Failed to delete history: {e}")
                QMessageBox.critical(
                    self, "Error", "Could not delete history.")

    def delete_selection(self):
        selected_item = self.list_widget.selectedItems()

        if not selected_item:
            return

        for item in selected_item:
            text = item.text()
            text_sep = text.split(" | ")

        task, date, time, duration = text_sep

        c.execute("""
            DELETE FROM history
            WHERE task = ? AND date = ? AND time = ? AND duration = ?
        """, (task, date, time, duration))

        conn.commit()

        self.list_widget.takeItem(self.list_widget.row(item))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pomodororororo")
        self.start_time = None
        self.task = QLineEdit()
        self.task.setFixedWidth(200)
        self.history = list()

        # widgets
        self.task_display = QLabel()
        self.timer_display = QLabel()
        self.font = QFont()
        self.font.setPointSize(72)
        self.timer_display.setFont(self.font)

        # buttons
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_timer)

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_timer)

        self.break_button = QPushButton("Break")
        self.break_button.clicked.connect(self.start_break)

        self.new_session_button = QPushButton("Study")
        self.new_session_button.clicked.connect(self.reset_ui)

        self.skip_break_button = QPushButton("Skip")
        self.skip_break_button.clicked.connect(self.skip_break)

        self.show_history_button = QPushButton("Show History")
        self.show_history_button.clicked.connect(self.show_history)

        self.submit_task_button = QPushButton("Submit")
        self.submit_task_button.clicked.connect(self.submit_task_name)

        self.reset_timer_button = QPushButton("Reset Timer")
        self.reset_timer_button.clicked.connect(self.reset_timer)

        # layouts
        layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        layout.addWidget(self.task_display,
                         alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.timer_display,
                         alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.start_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.reset_timer_button)
        layout.addWidget(self.break_button)
        layout.addWidget(self.new_session_button)
        layout.addWidget(self.skip_break_button)
        layout.addWidget(self.show_history_button)

        task_layout = QHBoxLayout()
        task_layout.addWidget(QLabel("Task Name:"))
        task_layout.addWidget(self.task)
        task_layout.addWidget(self.submit_task_button)

        layout.addLayout(task_layout)

        container = QWidget()
        container.setLayout(layout)
        container.setFixedSize(600, 250)
        self.setCentralWidget(container)

        # init timer
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_display)

        self.reset_ui()

    # start QTimer responsible for updating display

    def start_timer(self):
        if not self.timer.isActive():
            self.task.setDisabled(True)
            self.start_time = datetime.now()
            self.timer.start()
            self.hide_elements()

    def pause_timer(self):
        if self.timer.isActive():
            self.task.setEnabled(True)
            self.timer.stop()
            self.hide_elements()

    def reset_ui(self):
        self.timer_display.setText("25:00")
        self.start_button.show()
        self.pause_button.hide()
        self.reset_timer_button.show()
        self.new_session_button.hide()
        self.break_button.hide()
        self.skip_break_button.hide()
        self.show_history_button.show()

        self.task.setEnabled(True)

        self.time = QTime(0, 25, 0)

    # avoid unnecessary UI components
    def hide_elements(self):
        if self.timer.isActive():
            self.start_button.hide()
            self.pause_button.show()
            self.show_history_button.hide()
        else:
            self.pause_button.hide()
            self.start_button.show()
            self.show_history_button.show()

    def update_display(self):
        if self.time == QTime(0, 0, 0):
            self.timer.stop()
            self.timer_display.setText("Time's up!")
            logging.info("Task complete")

            end_time = datetime.now()
            duration = end_time - \
                self.start_time if self.start_time else timedelta(minutes=25)

            task_name = self.task.text() or "Unnamed Task"
            save_to_db(
                task_name,
                end_time.strftime('%Y-%m-%d'),
                end_time.strftime('%H:%M:%S'),
                str(duration)
            )

            self.start_button.hide()
            self.pause_button.hide()
            self.break_button.show()
            self.new_session_button.show()
        else:
            self.time = self.time.addSecs(-1)
            self.timer_display.setText(self.time.toString("mm:ss"))

    # start 5 min break
    def start_break(self):
        self.time = QTime(0, 5, 0)
        self.start_timer()
        self.update_display()
        self.break_button.hide()
        self.new_session_button.hide()
        self.skip_break_button.show()

    def skip_break(self):
        if self.timer.isActive():
            self.timer.stop()
        logging.info("Break skipped")
        self.reset_ui()

    def show_history(self):
        c.execute(
            "SELECT * FROM history ORDER BY id DESC"
        )
        rows = c.fetchall()
        second = SecondWindow(rows, self)
        second.show()

    def submit_task_name(self):
        text = self.task.text()
        self.task_display.setText(f"Current Task: {text}")

    def reset_timer(self):
        if self.time != QTime(0, 25, 0):
            self.timer.stop()
            self.reset_ui()
            logging.info("Time Reset")
