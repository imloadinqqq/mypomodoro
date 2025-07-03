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


def save_to_db(task, date, time, duration, reflection):
    c.execute("INSERT INTO history (task, date, time, duration, reflection) VALUES (?, ?, ?, ?, ?)",
              (task, date, time, duration, reflection))
    conn.commit()


def dump_history(output_file):
    with open(output_file, 'w') as f:
        for line in conn.iterdump():
            f.write(f"{line}\n")


def restore_from_backup(self, file):
    file_path = os.path.abspath(file)
    if not os.path.exists(file_path):
        raise FileExistsError(f"Could not find history backup: {file_path}")
        return False

    try:
        with open(file, 'r') as f:
            script = f.read()
        c.execute("DROP TABLE IF EXISTS history")
        conn.executescript(script)
        conn.commit()
        QMessageBox.information(self, "Restore Successful",
                                "History was restored from backup.")
        logging.info("History restored from SQL dump.")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
