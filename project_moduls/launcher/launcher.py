import random
from dispatcher.enums import *
from dispatcher.messages import CCLaunchMissile, LaunchertoSEMissileLaunched,LaunchertoCCMissileLaunched
from dispatcher.dispatcher import Dispatcher
from missile.Missile import Missile, MissileType,MISSILE_TYPE_CONFIG
from radar.Target import Target
from typing import Tuple

def dir(A, B):
    return (B[0]-A[0], B[1]-A[1], B[2]-A[2])

def dist(A, B):
    return ((B[0]-A[0])**2+(B[1]-A[1])**2+(B[2]-A[2])**2)**0.5

def renormalize(ovect, length):
    olength = dist((0, 0, 0), ovect)
    scale = length / olength
    return (ovect[0] * scale, ovect[1] * scale, ovect[2] * scale)

class Launcher:
    def __init__(self, ctrl, id, coord, silos, missile_speed1, damage_radius1, missile_speed2, damage_radius2):
        self.ctrl=ctrl
        self.id=id
        self.coord: Tuple[float, float, float] =coord
        self.silo_num=silos
        self._silos=[1]*silos
        self.missile_speed_first = missile_speed1
        self.damage_radius_first = damage_radius1
        self.missile_speed_second = missile_speed2
        self.damage_radius_second = damage_radius2

    def launch(self, target):
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
        velocity = renormalize(dir(self.coord, target.currentCoords), speed)
        time = MISSILE_TYPE_CONFIG[type]["currLifeTime"]
        M = Missile(
        missileID= missile_id, 
        missileType=type,
        currentCoords=start_coords,
        velocity=velocity,
        currLifeTime = time ,
        damageRadius = radius)
        self.ctrl.acknowledge(target.targetId, M)
        target.attachMissile(M)

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
        D=10**10
        k=0
        closest_launcher = min(
            (l for l in self._launchers if l.available_missiles() > 0),
            key=lambda l: dist(l.coord, target.currentCoords),
            default=None
        )
        if closest_launcher:
            closest_launcher.launch(target)

    def status(self):
        for L in self._launchers:
          print("Available missiles in launcher", L.id, ":", L.available_missiles())