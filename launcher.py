import random

def dir(A, B):
    return (B[0]-A[0], B[1]-A[1], B[2]-A[2])

def dist(A, B):
    return ((B[0]-A[0])**2+(B[1]-A[1])**2+(B[2]-A[2])**2)**0.5

class Launcher:
    def __init__(self, ctrl, id, coord, silos):
        self.ctrl=ctrl
        self.id=id
        self.coord=coord
        self.silo_num=silos
        self._silos=[1]*silos

    def launch(self, target):
        i=0
        while self._silos[i]==0:
            i+=1
        self._silo[i]=0
        M=Missile("active", random.randint(0, 1000), self.coord,
                  dir(self.coord, target.currentPosition), 100.0, self.coord)
        self.ctrl.acknowledge(target.targetID, M)
        target.add_missilesFollow(M)

    def status(self):
        print("Launcher", self.id, "status:")
        for i in range(self.silo_num):
            if self._silos[i]==1:
                print("Silo", i, "status: full")
            else:
                print("Silo", i, "status: empty")

class LaunchController:
    def __init__(self, dispatcher, launchers, lchr_coords):
        self._dispatcher = dispatcher
        self.lchr_num = launchers
        self._launchers = []
        for i in range(launchers):
            self._launchers.append(Launcher(self, i, lchr_coords[i], 4))

    def update(self):
        messages = self._dispatcher.get_message(Modules.ControlCenter)
        for message in messages:
            if isinstance(message, CCLaunchMissile):
                self.create(message.target)
        
    def acknowledge(self, targetID, missile):
        self._dispatcher.send_message(LaunchertoSEMissileLaunched(SkyEnv, STANDARD, targetID, missile))
        self._dispatcher.send_message(LaunchertoCCMissileLaunched(ControlCenter, STANDARD, missile))

    def create(self, target):
        D=10**10
        k=0
        for i in range(self.lchr_num):
            d=dist(self._launchers[i].coord, target.currentPosition)
            if (d<D):
                D=d
                k=i
        self._launchers[k].launch(target)

    def status(self):
        print("LauncherController status:")
        for L in self._launchers:
            L.status()