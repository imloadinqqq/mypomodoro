import sqlite3
import os
import requests_cache
from requests_cache.backends import SQLiteCache
from PyQt6.QtWidgets import QMessageBox
import logging

conn = sqlite3.connect('history.db')
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        date DATE NOT NULL,
        time TIME NOT NULL,
        duration TIME NOT NULL,
        reflection TEXT
    )
""")
conn.commit()

print("Working directory:", os.getcwd())
print("Using database at:", os.path.abspath("history.db"))


def save_to_db(task, date, time, duration, reflection):
    c.execute("INSERT INTO history (task, date, time, duration, reflection) VALUES (?, ?, ?, ?, ?)",
              (task, date, time, duration, reflection))
    conn.commit()


def dump_history(self, output_file):
    reply = QMessageBox.question(
        self,
        "Confirm Dump",
        "Do you want to dump the database history?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )

    if reply == QMessageBox.StandardButton.Yes:
        with open(output_file, 'w') as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")
        QMessageBox.information(
            self, "Success", "Database successfully saved!")


def restore_from_backup(self, file):
    file_path = os.path.abspath(file)
    if not os.path.exists(file_path):
        QMessageBox.critical(self, "File Not Found",
                             f"Could not find backup file at: {file_path}")
        return False

    try:
        with open(file, 'r') as f:
            script = f.read()

        if "CREATE TABLE history" not in script:
            QMessageBox.critical(
                self, "Invalid Backup", "The backup file does not contain the history table schema.")
            return False

        c.execute("DROP TABLE IF EXISTS history")
        conn.executescript(script)
        conn.commit()

        QMessageBox.information(
            self, "Restore Successful", "History was restored from backup.")
        logging.info("History restored from SQL dump.")
        return True

    except Exception as e:
        logging.error(f"Restore failed: {e}")
        QMessageBox.critical(self, "Restore Failed", f"Error: {e}")
        return False


def dump_history(self, output_file):
    reply = QMessageBox.question(
        self,
        "Confirm Dump",
        "Do you want to dump the database history?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )

    if reply == QMessageBox.StandardButton.Yes:
        with open(output_file, 'w') as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")

        QMessageBox.information(
            self, "Success", "Database successfully saved!")
        logging.info("History dump written to %s", output_file)
