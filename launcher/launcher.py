import random
from dispatcher.enums import *
from dispatcher.messages import CCLaunchMissile, LaunchertoSEMissileLaunched,LaunchertoCCMissileLaunched
from dispatcher.dispatcher import Dispatcher
from missile.Missile import Missile, MissileType
from radar.Target import Target

def dir(A, B):
    return (B[0]-A[0], B[1]-A[1], B[2]-A[2])

def dist(A, B):
    return ((B[0]-A[0])**2+(B[1]-A[1])**2+(B[2]-A[2])**2)**0.5

def renormalize(ovect, length):
    vect=ovect.copy()
    olength=dist((0, 0, 0), ovect)
    vect[0]*=(length/olength)
    vect[1]*=(length/olength)
    vect[2]*=(length/olength)
    return vect

class Launcher:
    def __init__(self, ctrl, id, coord, silos):
        self.ctrl=ctrl
        self.id=id
        self.coord: Tuple[float, float, float] =coord
        self.silo_num=silos
        self._silos=[1]*silos
        self.current_id = 700

    def launch(self, target):
        available_silo = None
        i=0
        for i in range(self.silo_num):
            available_silo=i
            break
        if available_silo is None:
            return  # handle appropriatel
        self._silos[available_silo] = 0
        start_coords = (self.coord[0], self.coord[1], self.coord[2])

        if available_silo<=self.silo_num//2:
            type=MissileType.TYPE_1
        else
            type=MissileType.TYPE_2

        velocity = renormalize(dir(self.coord, target.currentCoords), MISSILE_TYPE_CONFIG[type]["speed"])
        M = Missile(
        missileID=str(self.current_id),
        missileType=type,
        currentCoords=start_coords,
        velocity=velocity)
        self.current_id+=1
        self.ctrl.acknowledge(target.targetId, M)
        target.attachMissile(M)

    def available_missiles(self):
        k=0
        for i in range(self.silo_num):
            k+=self._silos[i]
        return k

class LaunchController:
    def __init__(self, dispatcher):
        self._dispatcher = dispatcher
        self._launchers = []
        self.launchers_num = len(self._launchers)

    def get_launchers(self):
        return self._launchers
    
    def add_launcher(self, launcher: Launcher):
        """Добавляет пусковую установку под управление контроллера"""
        self._launchers.append(launcher)

    def update(self):
        for L in self._launchers.copy():
            if L.available_missiles==0:
                self._launchers.remove(L)

        message_queue = self._dispatcher.get_message(Modules.LauncherMain)
        messages = []
        while not message_queue.empty():
            messages.append(message_queue.get())
        for priority, message in messages:
            if isinstance(message, CCLaunchMissile):
                self.create(message.target)
        
    def acknowledge(self, targetID, missile):
        self._dispatcher.send_message(LaunchertoSEMissileLaunched(Modules.SE, Priorities.STANDARD, targetID, missile))
        self._dispatcher.send_message(LaunchertoCCMissileLaunched(Modules.ControlCenter, Priorities.STANDARD, missile))

    def create(self, target):
        D=10**10
        k=0
        for i in range(self.launchers_num):
            if self._launchers[i].silo_num>=0:
                d=dist(self._launchers[i].coord, target.currentPosition)
                if (d<D):
                    D=d
                    k=i
        self._launchers[k].launch(target)

    def status(self):
        for L in self._launchers:
            print("Available missiles in launcher", L.id, ":", L.available_missiles())