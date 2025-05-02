from typing import Tuple
import numpy as np

def vector(a,b):
    return np.array([a[0]-b[0],a[1]-b[1],a[2]-b[2]])

def distance(a,b):
    dist = vector(a,b)
    return np.linalg.norm(dist)

class SkyObject:
    def __init__(self, obj_id: int, start: Tuple[float, float, float], finish:Tuple[float, float, float],timeSteps: int =250, speed:float = 500):
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
    def __init__(self, obj_id, start, finish, speed: float = 500, time_step: float = 2, status: bool = True):
        self.start = np.array(start) * 1000
        self.finish = np.array(finish) * 1000
        self.speed = speed * 1000 / 3600
        self.status = status
        self.time_step = time_step
        direction = self.finish - self.start
        horizontal_distance = np.linalg.norm(direction[:2])
        total_time = horizontal_distance / self.speed
        self.timeSteps = int(total_time // time_step) + 1
        super().__init__(obj_id, start, finish, speed)
        
    def calculate_trajectory(self):
        direction = self.finish - self.start
        total_distance = np.linalg.norm(direction[:2])
        total_time = total_distance / self.speed
        steps_needed = int(total_time // self.time_step) + 1

        flightHeight = np.clip((self.start[2] + self.finish[2]) / 2, 1000, 5000)
        climb = 0.2
        cruise = 0.6
        descend = 0.2

        for i in range(self.timeSteps):
            progress = i / (self.timeSteps - 1)
            if progress <= climb:
                phase = progress / climb
                z = self.start[2] + (flightHeight - self.start[2]) * phase
                dist = progress * total_distance
            elif progress <= climb + cruise:
                phase = (progress - climb) / cruise
                z = flightHeight
                dist = climb * total_distance + phase * cruise * total_distance
            else:
                phase = (progress - (climb + cruise)) / descend
                z = flightHeight + (self.finish[2] - flightHeight) * phase
                dist = (climb + cruise) * total_distance + phase * descend * total_distance

            xy_progress = dist / total_distance if total_distance > 0 else 0
            x = self.start[0] + direction[0] * xy_progress
            y = self.start[1] + direction[1] * xy_progress
            self.trajectory[i] = [x, y, z]
        print(self.trajectory)

    def get_id(self):
        return super().get_id()

    def get_status(self):
        return self.status

    def killed(self):
        self.status = False

class Rocket(SkyObject):
    def __init__(self, obj_id, start, velocity, startTime, radius=20, time_step=5,timeSteps: int =250):
        self.velocity = np.array(velocity)
        self.radius = radius
        self.killed = False
        self.startTime = startTime
        self.dragcoeff = 0
        self.gravity = -9.8
        self.time_step = time_step
        self.currentPos = start

        super().__init__(obj_id, start, start, timeSteps)
        self.lifePeriod = self.timeSteps - self.startTime
        self.currentTime = 1

    def rocket_step(self, velocity):
        t = self.currentTime * self.time_step
        pos = self.currentPos
        if not np.allclose(velocity, 0):
            self.velocity = velocity
            self.currentPos = pos + velocity * t
            return 
        progress = self.currentTime / self.timeSteps
        self.currentTime +=1
        current_z = pos[2]
        if progress >= 0.8:
            t_fall = (self.time_step - int(0.875 * self.timeSteps)) * self.time_step
            z = current_z + 0.5 * self.gravity * t_fall**2
            self.currentPos = np.array([pos[0], pos[1], max(0, z)])
            return 
        elif current_z < 1000:
            z = current_z + 0.5 * 9.8 * t**2
            self.currentPos = np.array([pos[0], pos[1], min(z, 1000)])
            return
        else:
             self.currentPos = np.array([pos[0] + self.velocity[0] * t,pos[1] + self.velocity[1] * t,pos[2]])
             return
    
    def get_radius(self):
        return self.radius

    def get_startTime(self):
        return self.startTime

    def boom(self):
        self.killed = True

    def is_killed(self):
        return self.killed
    
    def get_currentPos(self):
        return super().get_currentPos()