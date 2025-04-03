import numpy as np
from typing import List, Dict
from skyobjects import Plane, Rocket
from messages import Message
from queue import PriorityQueue

def get_plane_trajectory_from_rocket(paires, rocket:Rocket):
        return paires.get(rocket.get_id()).get_trajectory()

def get_plane_id_from_rocket(paires, rocket:Rocket):
    return paires.get(rocket.get_id()).get_id()

class SkyEnv:
    def __init__(self, dispatcher, timeSteps:int=250):
        self.id = 6
        self.dispatcher = dispatcher
        self.planes = List[Plane] = []
        self.rockets: List[Rocket] = []
        self.pairs: Dict[int, Plane] = {} # {rocket id: plane}
        self.killedLastStep: List[int]
        self.timeSteps = timeSteps
        self.currentTime = 0


    def make_planes(self, plane_data):
        for data in plane_data:
            plane = Plane(*data)
            self.planes.append(plane)

    def check_if_in_radius(self, time, explosionPos, radius):
        collateralDamage = []
        for i in self.planes:
            i_trajectory = i.get_tragectory()
            i_id = i.get_id()
            if i.get_status()  == False:
                continue
            if time >= i_trajectory.shape[0]:
                continue
            position = i_trajectory(time)
            distance = np.linalg.norm(position - explosionPos)
            if distance <=radius:
                collateralDamage.append((i_id,position))
                i.killed()
                self.remove_plane(i.get_id())

        for i in self.rockets:
            i_trajectory = i.get_tragectory()
            i_id = i.get_id()
            i_startTime = i.get_startTime()
            if i.is_killed() == True:
                continue
            step = time - i_startTime
            if step < 0:
                continue
            position = i_trajectory(step)
            distance = np.linalg.norm(position - explosionPos)
            if distance <=radius:
                collateralDamage.append((i_id,position))
                i.boom()
                self.remove_rocket(i.get_id())
        return collateralDamage
    
    def check_collision(self, rocket:Rocket):
        collisionStep=None
        planetarjectory = get_plane_trajectory_from_rocket(self.pairs, rocket)
        rockettrajectory = rocket.get_trajectory()
        maxTime = min(planetarjectory.shape[0], rockettrajectory.shape[0]+rocket.get_startTime())
        for t in range(maxTime):
            if t<rocket.get_startTime():
                continue
            trIndex = t - rocket.get_startTime()
            positionPlane = planetarjectory[t]
            positionRocket = rockettrajectory[trIndex]
            distance = np.linalg.norm(positionPlane-positionRocket)
            if distance <= rocket.get_radius:
                collisionStep = t
                self.pairs.get(rocket.get_id()).get_id().killed()
                rocket.boom()
                collateralDamage = self.check_if_in_radius()
                data = (collisionStep,(rocket.get_id(),positionRocket),(get_plane_id_from_rocket(self.pairs,rocket),positionPlane),collateralDamage)
                message = Message('killed','HIGH',data)
                #нужно импортировать сообщения
                self.dispatcher.send_message(GUI, message)
                self.dispatcher.send_message(RadarController, message)
                self.remove_rocket(rocket.get_id())
                self.remove_plane(get_plane_id_from_rocket(self.pairs, rocket))

    
    def remove_plane(self, plane_id: int):
        self.planes = [p for p in self.planes if p.get_id() != plane_id]
    
    def add_rocket(self, rocket, target_id):
        self.rockets.append(rocket)
        message = Message('Rocket', 'STANDARD',(rocket.get_id(),rocket.get_trajectory()))
        self.dispatcher.send_message('GUI',message)
        self.dispatcher.send_message('RadarController',message)
        self.add_pair(rocket.get_id(),target_id)
    
    def remove_rocket(self, rocket_id: int):
        self.rockets = [r for r in self.rockets if r.get_id() != rocket_id]
        if rocket_id in self.pairs:
            self.delete_pair(rocket_id)
    
    def add_pair(self, rocket_id: int, plane_id:int):
        plane = [p for p in self.planes if p.get_id() == plane_id]
        self.pairs[rocket_id] = plane
    
    def delete_pair(self, rocket_id: int):
        if rocket_id in self.pairs:
            del self.pairs[rocket_id]

    def start(self):
        #сейчас только координаты начала и конца, потом добавть промежуточные точки
        stuff = self.dispatcher.get_start_data(self.id)
        n, *objects = stuff
        current_id = 600 
        for i in objects:
            current_id += 1
            coords, *v = objects
            if len(coords)==2:
                if v == None:
                    plane = Plane(current_id, coords[0], coords[1])
                    self.planes.append(plane)
                else:
                    plane = Plane(current_id, coords[0], coords[1], v)
                    self.planes.append(plane)
            else:
                pass
        data = []
        for j in self.planes:
            data.append((j.get_id(),j.get_trajectory()))
        message = Message('planes', 'STANDARD', data)
        self.dispatcher.send_message('GUI', message)
        self.dispatcher.send_message('RadarController', message)

    def update(self):
        if self.currentTime==0:
            self.start()
        else:
            messages = self.dispatcher.get_messages(self.id)
            while messages:
                data = messages.get()
                #вот тут может быть косяк
                rocket = Rocket(data[2].get_missileId(),data[2].get_launcherPos(),data[2].get_speed(),data[2].get_vector(), self.currentTime-1)
                self.add_rocket(rocket, data[1])
        for i in self.rockets:
            self.check_collision(i)
        self.currentTime+=1
            
                

