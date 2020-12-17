import sqlite3
import os.path

CREATE_SQL = "create table record_download(rid TEXT PRIMARY KEY);"


class TimoRecordDB:
    def __init__(self, db_path):
        need_create = not os.path.exists(db_path)
        self.conn = sqlite3.connect(db_path)
        if need_create:
            cursor = self.conn.cursor()
            cursor.executescript(CREATE_SQL)
            self.conn.commit()

    def isDownloaded(self, rid):
        cursor = self.conn.execute(
            "select count(rid) from record_download where rid = ?", (rid,))
        return cursor.fetchone()[0] != 0

    def markDownload(self, rid):
        self.conn.execute(
            "insert into record_download(rid) values (?)", (rid,))
        self.conn.commit()
