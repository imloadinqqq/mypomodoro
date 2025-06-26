from PyQt6.QtCore import QTime, QTimer, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QWidget
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pomodororororo")

        # widgets
        self.timer_display = QLabel("25:00", self)
        self.font = QFont()
        self.font.setPointSize(24)
        self.timer_display.setFont(self.font)
        self.time = QTime(0, 25, 0)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_timer)

        # layout
        layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        layout.addWidget(self.timer_display,
                         alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.start_button)

        container = QWidget()
        container.setLayout(layout)
        container.setFixedSize(500, 200)
        self.setCentralWidget(container)

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_display)

    # start QTimer responsible for updating display
    def start_timer(self):
        if not self.timer.isActive():
            self.timer.start()

    def update_display(self):
        if self.time == QTime(0, 0, 0):
            self.timer.stop()
            self.timer_display.setText("Time's up!")
        else:
            self.time = self.time.addSecs(-1)
            self.timer_display.setText(self.time.toString("mm:ss"))
