from typing import Tuple
import numpy as np

def vector(a,b):
    return np.array([a[0]-b[0],a[1]-b[1],a[2]-b[2]])

def distance(a,b):
    dist = vector(a,b)
    return np.linalg.norm(dist)

class SkyObject:
    def __init__(self, obj_id: int, start: Tuple[float, float, float], finish:Tuple[float, float, float], speed:float = 500, timeSteps: int =250):
        self.id = obj_id
        self.currentPos = start
        self.start = start
        self.finish = finish
        self.timeSteps = timeSteps
        self.trajectory = np.zeros((self.timeSteps, 3))
        self.currentTime = 0
        self.speed = speed
        self.calculate_trajectory()
    
    def calculate_trajectory(self):
        directionVector = vector(self.start, self.finish)
        distances = distance(directionVector)
        directionVector = directionVector/distances
        time = distances/self.speed
        timeStep = time/(self.timeSteps-1)
        for i in range(self.timeSteps):
            self.trajectory[i]=np.array([self.start[0],self.start[1],self.start[2]])+i*timeStep*self.speed*directionVector

    def get_id(self):
        return self.id
    
    def get_currentPos(self):
        return self.currentPos
    
    def get_speed(self):
        return self.speed
    
    def get_trajectory(self):
        return self.trajectory
    
    def update(self):
        self.currentTime+=1
        self.currentPos=self.trajectory[self.currentTime]
        

class Plane(SkyObject):
    def __init__(self,obj_id, start, finish, speed:float = 500, timeSteps:int =250, status:bool = True):
        super().__init__( obj_id, start, finish, speed, timeSteps)
        self.status = status
        self.trajectory = np.zeros((self.timeSteps, 3))
        self.points=[]
        self.calculate_trajectory(self.start,self.finish)

    def calculate_trajectory(self):
        #добавить не 2 точки, а произвольное количество
        if self.points == []:
            pass
        flightHeight = np.clip((self.start[2] + self.finish[2])/2, 5000, 10000)#min и max flight
        direction = vector(self.start, self.finish)
        totalDistance = np.linalg.norm(direction[:2])#только горизонтальное расстояние
        pDirection = direction/np.linalg.norm(direction)# для чего я это добавила?

        climb = 0.2 
        cruise = 0.6 
        descend = 0.2

        for i in range(self.timeSteps):
            progress = i/(self.timeSteps-1)
            if progress<=climb:
                phase = progress/climb
                z = self.start[2] + (flightHeight - self.start[2])*phase
                dist = progress*totalDistance
            elif progress<=climb+cruise:
                phase = (progress-climb)/cruise
                z = flightHeight
                dist = climb * totalDistance + phase * cruise * totalDistance
            else:
                phase=(progress - (climb + cruise)) / descend
                z = flightHeight + (self.finish[2] - flightHeight) * phase
                dist = (climb + cruise) * totalDistance + phase * descend*totalDistance

            xy_progress = dist / totalDistance
            x = self.start[0] + direction[0] * xy_progress
            y = self.start[1] + direction[1] * xy_progress
            self.trajectory[i] = [x, y, z]

    def get_status(self):
        return self.status
    
    def killed(self):
        self.status=False

class Rocket(SkyObject):
    def __init__(self, obj_id, start, speed, dirVector, startTime,timeSteps:int=250,radius:int=20, life_period:int=250):
        super().__init__( obj_id, start, speed, timeSteps)
        self.radius = radius
        self.lifePeriod = life_period
        self.killed = False
        self.dirVector = dirVector
        self.timeSteps = timeSteps
        self.startTime = startTime
        self.tarjectory = None
        self.calculate_trajectory()

    def calculate_trajectory(self):
        direction = self.dirVector / np. np.linalg.norm(self.dirVector)
        stepDisplacement = self.speed * direction
        self.trajectory = np.zeros((self.timeSteps-self.startTime + 1, 3))
        self.trajectory[0] = self.start
        for step in range(1,self.timeSteps-self.startTime+1):
            self.trajectory[step] = self.trajectory[step - 1] + stepDisplacement

    def get_radius(self):
        return self.radius
    
    def get_startTime(self):
        return self.startTime
    
    def boom(self):
        self.killed=True

    def is_killed(self):
        return self.killed
    
    def get_trajectory(self):
        return super().get_trajectory()