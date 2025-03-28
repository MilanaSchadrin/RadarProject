class LaunchController:
    def __init__(self):
        self._launchers=[]
    def update(self):
        pass
    def create(self, target):
        pass
    def status(self):
        for L in self._launchers:
            L.status()