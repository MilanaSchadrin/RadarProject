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
    def __init__(self, obj_id, start, finish, speed: float = 300, time_step: float = 2, max_steps: int = None, status: bool = True):
        self.start = np.array(start) * 1000
        self.finish = np.array(finish) * 1000
        self.speed = speed * 1000 / 3600  # m/s
        self.status = status
        self.time_step = time_step

        direction = self.finish - self.start
        total_distance = np.linalg.norm(direction[:2])
        total_time = total_distance / self.speed
        steps_needed = int(total_time // time_step) + 1

        self.timeSteps = min(steps_needed, max_steps) if max_steps is not None else steps_needed
        super().__init__(obj_id, start, finish, speed)
        self.calculate_trajectory()

    def calculate_trajectory(self):
        direction = self.finish - self.start
        total_distance = np.linalg.norm(direction[:2])*1000
        #print(total_distance)
        total_time = total_distance / self.speed
        #print(total_time)

        flightHeight = np.clip((self.start[2] + self.finish[2]) / 2, 1000, 5000)
        climb_time = max(0.2 * total_time, 1e-6)
        cruise_time = max(0.6 * total_time, 1e-6)
        descend_time = max(0.2 * total_time, 1e-6)

        climb_end = climb_time
        cruise_end = climb_time + cruise_time
        descend_end = total_time

        self.trajectory = np.zeros((self.timeSteps, 3))

        for i in range(self.timeSteps):
            t = i * self.time_step
            dist = self.speed * t
            xy_progress = dist / total_distance if total_distance > 0 else 0
            x = self.start[0] + direction[0] * xy_progress
            y = self.start[1] + direction[1] * xy_progress

            if t <= climb_end:
                phase = t / climb_time
                z = self.start[2] + (flightHeight - self.start[2]) * phase
            elif t <= cruise_end:
                z = flightHeight
            elif t <= descend_end:
                phase = (t - cruise_end) / descend_time
                z = flightHeight + (self.finish[2] - flightHeight) * phase
            else:
                z = self.finish[2]

            self.trajectory[i] = [x, y, z/1000]
        #print(self.trajectory)

    def get_id(self):
        return super().get_id()

    def get_status(self):
        return self.status

    def killed(self):
        self.status = False

class Rocket(SkyObject):
    def __init__(self, obj_id, start, velocity, startTime, radius=20, time_step=5,timeSteps: int =250, status: bool = True):
        self.velocity = np.array(velocity[:3]) if len(velocity) > 3 else np.array(velocity)
        self.radius = radius
        self.killed = False
        self.startTime = startTime
        self.dragcoeff = 0
        self.gravity = -9.8
        self.time_step = time_step
        self.currentPos = np.array(start[:3])
        self.status = status # True - ракета обработалась в MissileController, False - надо запустить на бал. траекторию

        super().__init__(obj_id, start=start, finish=start, timeSteps=timeSteps, speed=0)
        self.lifePeriod = self.timeSteps - self.startTime
        self.currentTime = 1

    def rocket_step(self, velocity):
        #print(velocity)
        #print(self.status)
        if self.status:
            self.velocity = np.array(velocity[:3]) if len(velocity) > 3 else np.array(velocity)
            new_pos = self.currentPos + self.velocity*self.time_step
            #print('was here')
        else:
            direction = self.velocity.copy()
            x, y, z = self.currentPos

            x += direction[0] * self.time_step
            y += direction[1] * self.time_step
            if z < 1000:
                z += direction[2] * self.time_step
            else:
                z += direction[2] * self.time_step - 0.5 * abs(self.gravity) * self.time_step ** 2
                z = max(0, z)
            new_pos = np.array([x, y, z])
        self.currentPos = new_pos
        self.currentTime += 1
    
    def get_radius(self):
        return self.radius

    def get_startTime(self):
        return self.startTime

    def boom(self):
        self.killed = True

    def is_killed(self):
        return self.killed
    
    def get_currentPos(self):
        return tuple(self.currentPos[:3])
    
    def get_currentPosGUI(self):
        return tuple(self.currentPos[:3] / 1000)