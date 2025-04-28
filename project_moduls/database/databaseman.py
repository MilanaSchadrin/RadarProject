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
                radar_id INTEGER PRIMARY KEY,
                pos_x REAL NOT NULL,
                pos_y REAL NOT NULL,
                pos_z REAL NOT NULL,
                max_targets INTEGER NOT NULL,
                angle_input REAL NOT NULL,
                range_input REAL NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS launchers (
                launcher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pos_x REAL NOT NULL,
                pos_y REAL NOT NULL,
                pos_z REAL NOT NULL,
                cout_zur INTEGER NOT NULL,
                dist_zur1 INTEGER NOT NULL,
                vel_zur1  INTEGER NOT NULL,
                dist_zur2 INTEGER NOT NULL,
                vel_zur2 INTEGER NOT NULL
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
                 angle_input : float,
                 range_input: float) -> None:
        self.cursor.execute(
            """INSERT INTO radars 
            (pos_x, pos_y, pos_z, max_targets, angle_input, range_input)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (*position, max_targets, angle_input, range_input))
        self.conn.commit()

    def add_launcher(self,
                    position: Tuple[float, float, float],
                    cout_zur : int,
                    dist_zur1:int,
                    vel_zur1:int,
                    dist_zur2:int,
                    vel_zur2:int) -> None:
        self.cursor.execute(
            """INSERT INTO launchers 
            (pos_x, pos_y, pos_z, cout_zur, dist_zur1, vel_zur1, dist_zur2, vel_zur2)
            VALUES ( ?, ?, ?, ?, ?, ?, ?, ?)""",
            (*position, cout_zur,dist_zur1,vel_zur1,dist_zur2,vel_zur2))
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
   #{radar_id: {'position': np.array,'max_targets': int,'angle_input': float,'range_input': float}}
        self.cursor.execute("SELECT * FROM radars")
        radars = {}
        for row in self.cursor.fetchall():
            radar_id, px, py, pz, max_t, angle, range_ = row
            radars[radar_id] = {
                'position': (px, py, pz),
                'max_targets': max_t,
                'angle_input': angle,
                'range_input': range_}
        return radars

    def load_launchers(self) -> Dict[int, Dict[str, Union[np.ndarray, int]]]:
    # {launcher_id: {'position': np.array,'cout_zur': int,'dist': int,'velocity_zur': int}}
        self.cursor.execute("SELECT * FROM launchers")
        launchers = {}
        for row in self.cursor.fetchall():
            launcher_id, px, py, pz, count, dist_zur1, vel_zur1, dist_zur2, vel_zur2  = row
            launchers[launcher_id] = {
                'position': (px, py, pz),
                'cout_zur': count,
                'dist_zur1': dist_zur1,
                'vel_zur1': vel_zur1,
                'dist_zur2': dist_zur2,
                'vel_zur2': vel_zur2}
        return launchers
    
    def load_cc(self) -> Dict[int, Dict[str, np.ndarray]]:
        self.cursor.execute("SELECT * FROM CC")
        cc = {}
        for row in self.cursor.fetchall():
            cc_id, px, py, pz = row
            cc[cc_id] = {
                'position': (px, py, pz)}
        return cc

    def close(self) -> None:
        self.conn.close()
    