from PyQt6.QtCore import QTime, QTimer, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QWidget
)
import logging
import sqlite3

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
    c.execute("INSERT INTO history (task, date, time, duration) VALUES, (?, ?, ?, ?)",
              (task, date, time, duration))
    conn.commit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pomodororororo")

        # widgets
        self.timer_display = QLabel()
        self.font = QFont()
        self.font.setPointSize(24)
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

        # layout
        layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        layout.addWidget(self.timer_display,
                         alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.start_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.break_button)
        layout.addWidget(self.new_session_button)
        layout.addWidget(self.skip_break_button)

        container = QWidget()
        container.setLayout(layout)
        container.setFixedSize(500, 200)
        self.setCentralWidget(container)

        # init timer
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_display)

        self.reset_ui()

    # start QTimer responsible for updating display

    def start_timer(self):
        if not self.timer.isActive():
            self.timer.start()
            self.hide_elements()

    def pause_timer(self):
        if self.timer.isActive():
            self.timer.stop()
            self.hide_elements()

    def reset_ui(self):
        self.timer_display.setText("25:00")
        self.start_button.show()
        self.pause_button.hide()
        self.new_session_button.hide()
        self.break_button.hide()
        self.skip_break_button.hide()

        self.time = QTime(0, 25, 0)

    # avoid unnecessary UI components
    def hide_elements(self):
        if self.timer.isActive():
            self.start_button.hide()
            self.pause_button.show()
        else:
            self.pause_button.hide()
            self.start_button.show()

    def update_display(self):
        if self.time == QTime(0, 0, 0):
            self.timer.stop()
            self.timer_display.setText("Time's up!")
            logging.info("Task complete")
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
