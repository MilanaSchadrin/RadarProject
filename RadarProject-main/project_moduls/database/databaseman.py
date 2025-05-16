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
    def add_or_update_radar(self,
                              radar_id: int = None,
                              position: Tuple[float, float, float] = None,
                              max_targets: int = None,
                              angle: float = None,
                              range_val: float = None) -> int:

            if radar_id is None:

                self.cursor.execute(
                    """INSERT INTO radars
                    (pos_x, pos_y, pos_z, max_targets, angle_input, range_input)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (*position, max_targets, angle, range_val))
                radar_id = self.cursor.lastrowid
            else:

                updates = []
                params = []

                if position is not None:
                    updates.append("pos_x = ?, pos_y = ?, pos_z = ?")
                    params.extend(position)

                if max_targets is not None:
                    updates.append("max_targets = ?")
                    params.append(max_targets)

                if angle is not None:
                    updates.append("angle_input = ?")
                    params.append(angle)

                if range_val is not None:
                    updates.append("range_input = ?")
                    params.append(range_val)

                if updates:
                    params.append(radar_id)
                    query = f"""
                    UPDATE radars
                    SET {', '.join(updates)}
                    WHERE radar_id = ?
                    """
                    self.cursor.execute(query, params)

            self.conn.commit()
            return radar_id

    def add_or_update_launcher(self,
                                 launcher_id: int = None,
                                 position: Tuple[float, float, float] = None,
                                 missile_count: int = None,
                                 range1: int = None,
                                 velocity1: int = None,
                                 range2: int = None,
                                 velocity2: int = None) -> int:

            if launcher_id is None:

                self.cursor.execute(
                    """INSERT INTO launchers
                    (pos_x, pos_y, pos_z, cout_zur, dist_zur1, vel_zur1, dist_zur2, vel_zur2)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (*position, missile_count, range1, velocity1, range2, velocity2))
                launcher_id = self.cursor.lastrowid
            else:

                updates = []
                params = []

                if position is not None:
                    updates.append("pos_x = ?, pos_y = ?, pos_z = ?")
                    params.extend(position)

                if missile_count is not None:
                    updates.append("cout_zur = ?")
                    params.append(missile_count)

                if range1 is not None:
                    updates.append("dist_zur1 = ?")
                    params.append(range1)

                if velocity1 is not None:
                    updates.append("vel_zur1 = ?")
                    params.append(velocity1)

                if range2 is not None:
                    updates.append("dist_zur2 = ?")
                    params.append(range2)

                if velocity2 is not None:
                    updates.append("vel_zur2 = ?")
                    params.append(velocity2)

                if updates:
                    params.append(launcher_id)
                    query = f"""
                    UPDATE launchers
                    SET {', '.join(updates)}
                    WHERE launcher_id = ?
                    """
                    self.cursor.execute(query, params)

            self.conn.commit()
            return launcher_id

    def add_or_update_plane(self,
                              plane_id: int = None,
                              start_pos: Tuple[float, float, float] = None,
                              end_pos: Tuple[float, float, float] = None) -> int:
            if plane_id is None:

                self.cursor.execute(
                    """INSERT INTO planes
                    (start_x, start_y, start_z, end_x, end_y, end_z)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (*start_pos, *end_pos))
                plane_id = self.cursor.lastrowid
            else:

                updates = []
                params = []

                if start_pos is not None:
                    updates.append("start_x = ?, start_y = ?, start_z = ?")
                    params.extend(start_pos)

                if end_pos is not None:
                    updates.append("end_x = ?, end_y = ?, end_z = ?")
                    params.extend(end_pos)

                if updates:
                    params.append(plane_id)
                    query = f"""
                    UPDATE planes
                    SET {', '.join(updates)}
                    WHERE plane_id = ?
                    """
                    self.cursor.execute(query, params)

            self.conn.commit()
            return plane_id

    def add_or_update_cc(self,
                           cc_id: int = None,
                           position: Tuple[float, float, float] = None) -> int:

            if position is not None:
                    self.cursor.execute(
                        """UPDATE CC
                        SET pos_x = ?, pos_y = ?, pos_z = ?
                        WHERE cc_id = ?""",
                        (*position, cc_id))

            self.conn.commit()
            return cc_id
