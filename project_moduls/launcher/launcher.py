import random
from dispatcher.enums import *
from dispatcher.messages import CCLaunchMissile, LaunchertoSEMissileLaunched,LaunchertoCCMissileLaunched
from dispatcher.dispatcher import Dispatcher
from missile.Missile import Missile, MissileType,MISSILE_TYPE_CONFIG
from radar.Target import Target
from typing import Tuple
from missile.MissileController import *

def dir(A, B):
    return (B[0]-A[0], B[1]-A[1], B[2]-A[2])

def dist(A, B):
    return ((B[0]-A[0])**2+(B[1]-A[1])**2+(B[2]-A[2])**2)**0.5

def plane_sep(vect, A, B):
    D=dir(A, B)
    return D[0]*vect[0]+D[1]*vect[1]+D[2]*vect[2]

def renormalize(ovect, length):
    olength = dist((0, 0, 0), ovect)
    scale = length / olength
    return (ovect[0] * scale, ovect[1] * scale, ovect[2] * scale)

class Launcher:
    def __init__(self, ctrl, id, coord, silos):
        self.ctrl=ctrl
        self.id=id
        self.coord: Tuple[float, float, float] =coord
        self.silo_num=silos
        self._silos=[1]*silos

    def launch(self, target, time_step):
        available_silo = None
        for i in range(self.silo_num):
            if self._silos[i] == 1:
                available_silo = i
                break
        if available_silo is None:
            return  # handle appropriatel
        self._silos[available_silo] = 0
        start_coords = (self.coord[0]*1000, self.coord[1]*1000, self.coord[2]*1000)

        if available_silo<=self.silo_num//2:
            type=MissileType.TYPE_1
        else:
            type=MissileType.TYPE_2

        speed = MISSILE_TYPE_CONFIG[type]["speed"]
        radius = MISSILE_TYPE_CONFIG[type]["damageRadius"]

        missile_id = self.ctrl.generate_missile_id()
        velocity = renormalize(dir(start_coords, target.currentCoords), speed)
        time = MISSILE_TYPE_CONFIG[type]["currLifeTime"]
        M = Missile(
        missileID= missile_id, 
        missileType=type,
        currentCoords=start_coords,
        velocity=velocity,
        currLifeTime = time ,
        damageRadius = radius)
        interception_point = calculate_interception_point(target, M)
        change_velocity(interception_point, M)
        calc_lifetime(interception_point, M, time_step)
        self.ctrl.acknowledge(target.targetId, M)
        target.attachMissile(M)
        target.gotMissile = True

    def available_missiles(self):
        return sum(self._silos)

class LaunchController:
    def __init__(self, dispatcher):
        self._dispatcher = dispatcher
        self._launchers = []
        self._missile_counter = 700 
        self._used_ids = set()
        self.lchr_num = len(self._launchers)

    def generate_missile_id(self):
        while True:
            new_id = str(self._missile_counter)
            self._missile_counter += 1
            if new_id not in self._used_ids:
                self._used_ids.add(new_id)
                return new_id

    def get_launchers(self):
        return self._launchers
    
    def add_launcher(self, launcher: Launcher):
        """Добавляет пусковую установку под управление контроллера"""
        self._launchers.append(launcher)

    def update(self):
        self._launchers = [l for l in self._launchers if l.available_missiles() > 0]
        message_queue = self._dispatcher.get_message(Modules.LauncherMain)
        messages = []
        while not message_queue.empty():
            messages.append(message_queue.get())
        for priority, message in messages:
            if isinstance(message, CCLaunchMissile):
                self.create(message.target)
        
    def acknowledge(self, targetID, missile):
        print('I made missile ',missile.missileID)
        self._dispatcher.send_message(LaunchertoSEMissileLaunched(Modules.SE, Priorities.SUPERHIGH, targetID, missile))
        self._dispatcher.send_message(LaunchertoCCMissileLaunched(Modules.ControlCenter, Priorities.SUPERHIGH, missile))

    def create(self, target):
        if not self._launchers:
            return
        min_dist = float('inf')
        selected_launcher = None

        for launcher in self._launchers:
            if launcher.available_missiles() > 0:
                launcher_coords = tuple(x * 1000 for x in launcher.coord)
                d = dist(launcher_coords, target.currentCoords)
                if d < min_dist:
                    min_dist = d
                    selected_launcher = launcher

        if selected_launcher:
            print(f"Chosen launcher {selected_launcher.id} (distance: {int(min_dist)})")
            selected_launcher.launch(target, self._dispatcher.time_step)

    def status(self):
        for L in self._launchers:
          print("Available missiles in launcher", L.id, ":", L.available_missiles())