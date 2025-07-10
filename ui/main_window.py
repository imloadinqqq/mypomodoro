from PyQt6.QtCore import QTime, QTimer, Qt, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QBoxLayout,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QMainWindow,
    QPushButton,
    QWidget,
    QLineEdit,
    QMessageBox,
    QInputDialog
)
from PyQt6.QtMultimedia import QSoundEffect
import logging
from datetime import datetime, timedelta
from db import save_to_db, restore_from_backup, dump_history, c, conn


logging.basicConfig(
    filename='app.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# allow user to play focus music
class MusicWindow(QMainWindow):
    WINDOW_WIDTH = 500
    WINDOW_HEIGHT = 300

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music")
        self.song_location = ""

        # Display song list from /music directory

    def playback_song(self, song_location):
        # play & pause
        pass

    # change song_location and return
    def select_song(self):
        # change location logic
        return self.song_location


class HistoryWindow(QMainWindow):
    def __init__(self, history_rows, parent=None):
        WINDOW_WIDTH = 500
        WINDOW_HEIGHT = 300

        super().__init__(parent)
        self.setWindowTitle("History")

        self.delete_history_button = QPushButton("Erase All History")
        self.delete_history_button.clicked.connect(self.delete_history)

        self.delete_selection_button = QPushButton("Delete Selected")
        self.delete_selection_button.clicked.connect(self.delete_selection)

        self.save_history_button = QPushButton("Save History")
        self.save_history_button.clicked.connect(
            lambda: dump_history(self, "history_dump.sql"))

        self.restore_history_button = QPushButton("Restore History")
        self.restore_history_button.clicked.connect(
            lambda: self.reload_after_restore()
        )

        self.layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.view_reflection)
        for row in history_rows:
            self.list_widget.addItem(
                f"{row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
        container = QWidget()
        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(self.delete_history_button)
        self.layout.addWidget(self.delete_selection_button)
        self.layout.addWidget(self.restore_history_button)
        self.layout.addWidget(self.save_history_button)
        container.setLayout(self.layout)
        container.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
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
            task, date, time, duration, reflection = self.split_row(item)

        c.execute("""
            DELETE FROM history
            WHERE task = ? AND date = ? AND time = ? AND duration = ? AND reflection = ?
        """, (task, date, time, duration, reflection))

        logging.info(f"Task: {task} | {date} | {time} | {duration} deleted")

        conn.commit()

        self.list_widget.takeItem(self.list_widget.row(item))

    def reload_after_restore(self):
        success = restore_from_backup(self, "./history_dump.sql")
        if success:
            self.list_widget.clear()
            c.execute("SELECT * FROM history ORDER BY id DESC")
            rows = c.fetchall()
            for row in rows:
                self.list_widget.addItem(
                    f"{row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
            logging.info("UI refreshed after history restore.")

    def view_reflection(self, item: QListWidgetItem):
        task, date, time, duration, reflection = self.split_row(item)
        msg = QMessageBox(self)
        msg.setWindowTitle("Reflection")
        if reflection != "":
            msg.setText("Reflection for selected task:")
            msg.setInformativeText(reflection)
        else:
            msg.setText("No Reflection for selected task")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def split_row(self, item):
        text = item.text()
        text_sep = text.split(" | ")

        return text_sep


class MainWindow(QMainWindow):
    def __init__(self):
        WINDOW_WIDTH = 600
        WINDOW_HEIGHT = 300
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

        self.sound = QSoundEffect()
        self.sound.setSource(QUrl.fromLocalFile("./complete.wav"))
        self.sound.setLoopCount(1)
        self.sound.setVolume(1.0)

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

        self.open_music_player_button = QPushButton("Music Player")
        self.open_music_player_button.clicked.connect(self.open_player)

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
        layout.addWidget(self.open_music_player_button)

        task_layout = QHBoxLayout()
        task_layout.addWidget(QLabel("Task Name:"))
        task_layout.addWidget(self.task)
        task_layout.addWidget(self.submit_task_button)

        layout.addLayout(task_layout)

        container = QWidget()
        container.setLayout(layout)
        container.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setCentralWidget(container)

        # init timer
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_display)

        self.reset_ui()

    # start QTimer responsible for updating display

    def start_timer(self):
        if self.is_task():
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
        self.task_display.clear()

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
            QTimer.singleShot(1000, self.play_sound)
            logging.info("Task complete")

            end_time = datetime.now()
            duration = end_time - \
                self.start_time if self.start_time else timedelta(minutes=25)

            task_name = self.task.text() or "Unnamed Task"
            relfection = self.reflection_prompt()
            save_to_db(
                task_name,
                end_time.strftime('%Y-%m-%d'),
                end_time.strftime('%H:%M:%S'),
                str(duration),
                relfection
            )

            self.start_button.hide()
            self.pause_button.hide()
            self.break_button.show()
            self.reset_timer_button.hide()
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
        history_window = HistoryWindow(rows, self)
        history_window.show()

    def submit_task_name(self):
        text = self.task.text()
        self.task_display.setText(f"Current Task: {text}")

    def reset_timer(self):
        if self.time != QTime(0, 25, 0):
            self.timer.stop()
            self.reset_ui()
            logging.info("Time Reset")

    def reflection_prompt(self):
        text, ok = QInputDialog.getText(
            self,
            "Reflection Prompt",
            "Write a reflection for this session."
        )

        if ok and text:
            QMessageBox.information(
                self, "Good session!",  "Return to main window.")
        elif ok:
            QMessageBox.warning(self, "Empty", "You didn't write anything.")

        return text

    def is_task(self):
        print(self.task_display.text())
        if self.task_display.text() == "Current Task: " or self.task_display.text() == "":
            QMessageBox.warning(self, "Task is Empty",
                                "Please enter a task before starting the timer!")
            return False
        return True

    def play_sound(self):
        print("Loaded:", self.sound.isLoaded())
        self.sound.play()
        QTimer.singleShot(500, lambda: print(
            "Playing:", self.sound.isPlaying()))

    def open_player(self):
        print("Opening music player")
        music_window = MusicWindow()
        music_window.show()
