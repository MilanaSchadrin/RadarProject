import sqlite3
from typing import List, Dict, Tuple, Union
#from common.commin import Point
import numpy as np
import os

class DatabaseManager:
    def __init__(self):
        self.db_name = 'skydb.db'
        self.db_folder ='database'
        self.db_path = os.path.join(self.db_folder,self.db_name)
        os.makedirs(self.db_folder, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def add_name(self, name):
        self.close()
        self.db_name = name if name.endswith('.db') else f"{name}.db"
        self.db_path = os.path.join(self.db_folder,self.db_name)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
    #add speed
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS planes (
                plane_id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_x REAL NOT NULL,
                start_y REAL NOT NULL,
                start_z REAL NOT NULL,
                end_x REAL NOT NULL,
                end_y REAL NOT NULL,
                end_z REAL NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS radars (
                radar_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pos_x REAL NOT NULL,
                pos_y REAL NOT NULL,
                pos_z REAL NOT NULL,
                max_targets INTEGER NOT NULL,
                range_input REAL NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS launchers (
                launcher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pos_x REAL NOT NULL,
                pos_y REAL NOT NULL,
                pos_z REAL NOT NULL,
                cout_zur INTEGER NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS CC (
                cc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pos_x REAL NOT NULL,
                pos_y REAL NOT NULL,
                pos_z REAL NOT NULL
            )
        """)

        self.conn.commit()

    def add_plane(self, 
                 start: Tuple[float, float, float], 
                 end: Tuple[float, float, float]) -> None:
        self.cursor.execute(
            """INSERT INTO planes 
            (start_x, start_y, start_z, end_x, end_y, end_z)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (*start, *end))
        self.conn.commit()

    def add_radar(self,
                 position: Tuple[float, float, float],
                 max_targets: int,
                 range_input: float) -> None:
        self.cursor.execute(
            """INSERT INTO radars 
            (pos_x, pos_y, pos_z, max_targets,range_input)
            VALUES (?, ?, ?, ?,?)""",
            (*position, max_targets, range_input))
        self.conn.commit()

    def add_launcher(self,
                    position: Tuple[float, float, float],
                    cout_zur : int) -> None:
        self.cursor.execute(
            """INSERT INTO launchers 
            (pos_x, pos_y, pos_z, cout_zur)
            VALUES ( ?, ?, ?, ?)""",
            (*position, cout_zur))
        self.conn.commit()

    def add_cc(self,
              position: Tuple[float, float, float]) -> None:
        self.cursor.execute(
            """INSERT INTO CC 
            (pos_x, pos_y, pos_z)
            VALUES ( ?, ?, ?)""",
            (position[0], position[1], position[2]))
        self.conn.commit()

    def load_planes(self) -> Dict[int, Dict[str, np.ndarray]]:
        #{plane_id: {'start': np.array, 'end': np.array}}
        self.cursor.execute("SELECT * FROM planes")
        planes = {}
        for row in self.cursor.fetchall():
            plane_id, sx, sy, sz, ex, ey, ez = row
            planes[plane_id] = {
                'start': np.array([sx, sy, sz], dtype=np.float32),
                'end': np.array([ex, ey, ez], dtype=np.float32)}
        return planes
    
    def load_radars(self) -> Dict[int, Dict[str, Union[np.ndarray, int, float]]]:
        self.cursor.execute("SELECT * FROM radars")
        radars = {}
        for row in self.cursor.fetchall():
            radar_id, px, py, pz, max_t, range_ = row
            radars[radar_id] = {
                'position': (px, py, pz),
                'max_targets': max_t,
                'range_input': range_}
        return radars

    def load_launchers(self) -> Dict[int, Dict[str, Union[np.ndarray, int]]]:
        self.cursor.execute("SELECT * FROM launchers")
        launchers = {}
        for row in self.cursor.fetchall():
            launcher_id, px, py, pz, count  = row
            launchers[launcher_id] = {
                'position': (px, py, pz),
                'cout_zur': count}
        return launchers
    
    def load_cc(self) -> Dict[int, Dict[str, np.ndarray]]:
        self.cursor.execute("SELECT * FROM CC")
        cc = {}
        for row in self.cursor.fetchall():
            cc_id, px, py, pz = row
            cc[cc_id] = {
                'position': (px, py, pz)}
        return cc
    def update_radar_position(self, radar_id: int, new_position: Tuple[float, float, float]) -> None:
        self.cursor.execute(
            """UPDATE radars 
            SET pos_x = ?, pos_y = ?, pos_z = ?
            WHERE radar_id = ?""",
            (*new_position, radar_id))
        self.conn.commit()

    def update_radar_range(self, radar_id: int, new_range: float) -> None:
        self.cursor.execute(
            """UPDATE radars 
            SET range_input = ?
            WHERE radar_id = ?""",
            (new_range, radar_id))
        self.conn.commit()

    def update_launcher_position(self, launcher_id: int, new_position: Tuple[float, float, float]) -> None:
        self.cursor.execute(
            """UPDATE launchers 
            SET pos_x = ?, pos_y = ?, pos_z = ?
            WHERE launcher_id = ?""",
            (*new_position, launcher_id))
        self.conn.commit()

    def update_launcher_missile_count(self, launcher_id: int, new_count: int) -> None:
        self.cursor.execute(
            """UPDATE launchers 
            SET missile_count = ?
            WHERE launcher_id = ?""",
            (new_count, launcher_id))
        self.conn.commit()

    def clear_table(self, table_name: str) -> None:
        if table_name in ['planes', 'radars', 'launchers', 'CC']:
            self.cursor.execute(f"DELETE FROM {table_name}")
            self.conn.commit()

    def delete_row(self, table_name: str, row_id: int) -> None:
        if table_name in ['planes', 'radars', 'launchers', 'CC']:
            self.cursor.execute(f"DELETE FROM {table_name} WHERE {table_name[:-1]}_id = ?", (row_id,))
            self.conn.commit()

    def close(self) -> None:
        self.conn.close()
    