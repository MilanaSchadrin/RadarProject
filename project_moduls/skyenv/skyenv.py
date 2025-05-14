import numpy as np
from typing import List, Dict
from skyenv.skyobjects import SkyObject, Plane, Rocket
from dispatcher.messages import SEKilled,SEKilledGUI,SEAddRocket,SEAddRocketToRadar,RocketUpdate,SEStarting,CCToSkyEnv,ToGuiRocketInactivated,LaunchertoSEMissileLaunched
from dispatcher.dispatcher import Dispatcher
from dispatcher.enums import *
from queue import PriorityQueue
from missile.Missile import MissileStatus
import math

def get_plane_trajectory_from_rocket(paires, rocket:Rocket):
        keys = paires.get(rocket.get_id())
        return keys.get_trajectory()

def get_plane_id_from_rocket(paires, rocket:Rocket):
    plane = paires.get(rocket.get_id())
    return plane.get_id()

class SkyEnv:
    def __init__(self, dispatcher:Dispatcher, timeSteps:int=250):
        self.id = 6
        self.dispatcher = dispatcher
        self.planes : List[Plane] =[]
        self.rockets: Dict[int, Rocket] = {} #{rocket id: rocket}
        self.pairs: Dict[int, Plane] = {} # {rocket id: plane}
        self.killedLastStep: List[int]
        self.timeSteps = timeSteps
        self.currentTime = 0
        self.to_remove = set()
        self.stuff = []

    def make_planes(self, plane_data):
        for data in plane_data:
            plane = Plane(*data)
            self.planes.append(plane)

    def check_if_in_radius(self, explosionPos, radius):
        collateralDamage = []
        explosionPos = np.array(explosionPos)
        for i in self.planes:
            i_trajectory = i.get_trajectory()
            i_id = i.get_id()
            if i.get_status()  == False:
                continue
            position = np.array(i_trajectory[self.currentTime-1])
            distance = np.linalg.norm(position - explosionPos)
            if distance <=radius:
                collateralDamage.append((i_id, position))
                i.killed()
                self.to_remove.add(('plane', i_id))
        for rocket_id, rocket in list(self.rockets.items()):
            if rocket.is_killed():
                continue  
            position = np.array(rocket.get_currentPos())
            distance = np.linalg.norm(position - explosionPos)
            if distance <= radius:
                collateralDamage.append((rocket_id, position))
                rocket.boom()
                self.to_remove.add(('rocket', rocket_id))
        return collateralDamage
    
    def check_collision(self, rocket:Rocket):
        if rocket.get_id() not in self.pairs or rocket.is_killed():
            return
        plane = self.pairs[rocket.get_id()]
        if plane.get_status() == False:  # Plane already lost
            return
        planetarjectory = get_plane_trajectory_from_rocket(self.pairs, rocket)
        positionRocket = np.array(rocket.get_currentPos())
        positionPlane = np.array(planetarjectory[self.currentTime-1])* 1000
        pos_rocket_2d = positionRocket[:2]
        pos_plane_2d = positionPlane[:2]
        #print(positionPlane, positionRocket)
        distance = np.linalg.norm(positionPlane-positionRocket)
        dx = positionRocket[0] - positionPlane[0]
        dy = positionRocket[1] - positionPlane[1]

        if abs(dx)  <= rocket.get_radius() or abs(dy)  <= rocket.get_radius():
            print(rocket.get_radius())
            plane.killed
            rocket.boom()
            print(positionRocket[0],positionRocket[1],positionPlane[0],positionPlane[1])
            print('I made boom')
            print(self.currentTime)
            collateralDamage = self.check_if_in_radius(positionRocket, rocket.get_radius())
            message = SEKilledGUI(Modules.GUI, Priorities.SUPERHIGH,rocket.get_id(),positionRocket/1000,rocket.get_radius(),get_plane_id_from_rocket(self.pairs,rocket),positionPlane/1000, collateralDamage)
            self.dispatcher.send_message(message)
            message = SEKilled(Modules.RadarMain, Priorities.HIGH,rocket.get_id(),positionRocket,get_plane_id_from_rocket(self.pairs,rocket),positionPlane, collateralDamage)
            self.dispatcher.send_message(message)
            self.to_remove.add(('plane', plane.get_id()))
            self.to_remove.add(('rocket', rocket.get_id()))

    def remove_plane(self, plane_id: int):
        self.planes = [p for p in self.planes if p.get_id() != plane_id]

    def cleanup(self):
        for obj_type, obj_id in self.to_remove:
            if obj_type == 'plane':
                self.planes = [p for p in self.planes if p.get_id() != obj_id]
            elif obj_type == 'rocket':
                if obj_id in self.rockets:
                    del self.rockets[obj_id]
                if obj_id in self.pairs:
                    del self.pairs[obj_id]
        
        self.to_remove.clear()
    
    def add_rocket(self, rocket, missile, target_id):
        self.rockets[rocket.get_id()] = rocket
        message = SEAddRocket(Modules.GUI, Priorities.HIGH,rocket.get_id(),rocket.get_currentPosGUI())
        self.dispatcher.send_message(message)
        print(rocket.get_id(),rocket.get_currentPosGUI(),self.currentTime)
        message = SEAddRocketToRadar(Modules.RadarMain,Priorities.SUPERHIGH,target_id, missile, rocket.get_currentPos())
        self.dispatcher.send_message(message)
        self.add_pair(rocket.get_id(),target_id)
    
    def remove_rocket(self, rocket_id: int):
        if rocket_id in self.rockets:
            del self.rockets[rocket_id]
        if rocket_id in self.pairs:
            self.delete_pair(rocket_id)
    
    def add_pair(self, rocket_id: int, plane_id:int):
        plane = next((p for p in self.planes if p.get_id() == plane_id), None)
        if plane is not None:
            self.pairs[rocket_id] = plane
    
    def delete_pair(self, rocket_id: int):
        if rocket_id in self.pairs:
            del self.pairs[rocket_id]

    def start(self,db):
        self.dispatcher.register(Modules.SE)
        #сейчас только координаты начала и конца, потом добавть промежуточные точки
        #засунуть это всё в make_planes
        planesData = db.load_planes()
        current_id = 600 
        for plane_id, plane_info in planesData.items():
            current_id += 1
            coords=[1,2]
            v=None
            if len(coords)==2:
                if v == None:
                    plane = Plane(current_id, plane_info['start'],plane_info['end'],self.timeSteps)
                    self.planes.append(plane)
                else:
                    plane = Plane(current_id, plane_info['start'],plane_info['end'],self.timeSteps, v)
                    self.planes.append(plane)
            else:
                pass
        data = {} #all planes in this period
        for j in self.planes:
            data[j.get_id()] = j.get_trajectory()
            #print(data[j.get_id()])
        message = SEStarting(recipient_id=Modules.GUI,
                             priority=Priorities.LOW,
                             planes=data)
        
        self.dispatcher.send_message(message)
        for j in self.planes:
            data[j.get_id()] = j.get_trajectory()*1000
            #print(data[j.get_id()])
        messagetoRadar = SEStarting(recipient_id=Modules.RadarMain,
                                    priority=Priorities.SUPERLOW,
                                    planes=data)
        self.dispatcher.send_message(messagetoRadar)

    def update(self):
        messages = []
        message_queue = self.dispatcher.get_message(Modules.SE)
        while not message_queue.empty():
            messages.append(message_queue.get())
        for priority, message in messages:
            if isinstance(message,LaunchertoSEMissileLaunched):
                targetId = message.targetId
                miss = message.missile
                scaled_coords = np.array(miss.currentCoords)
                rocket = Rocket(
                    obj_id=miss.missileID,
                    start=scaled_coords,
                    velocity=miss.velocity,
                    startTime=self.currentTime,
                    radius=miss.damageRadius,
                    time_step=2,              
                    timeSteps=self.timeSteps   )
                #print(miss.velocity)
                self.stuff.append(miss.currentCoords)
                self.add_rocket(rocket,miss,targetId)
            elif isinstance(message,CCToSkyEnv):
                rocketsCC = message.missiles
                #print(rocketsCC)
                #print(self.rockets)
                for missile in rocketsCC:
                    # изменение статуса ракете
                    if missile.missileID in self.rockets:
                        if missile.status == MissileStatus.AUTOMATIC:
                            self.rockets[missile.missileID].status = False
                        else:
                            self.rockets[missile.missileID].status = True


                    if missile.currLifeTime <=0 and missile.missileID in self.rockets: 
                        self.rockets[missile.missileID].boom()
                        message = ToGuiRocketInactivated(Modules.GUI, Priorities.SUPERLOW, missile.missileID)
                        self.dispatcher.send_message(message)
                        self.to_remove.add(('rocket', missile.missileID))
                        #self.check_if_in_radius(self, self.rockets[missile.missileID].get_currentPos(),self.rockets[missile.missileID].get_radius())
                    if missile.missileID in self.rockets:
                        self.rockets[missile.missileID].rocket_step(missile.velocity)
                        message = RocketUpdate(Modules.GUI, Priorities.SUPERLOW, missile.missileID,self.rockets[missile.missileID].get_currentPosGUI())
                        self.stuff.append(self.rockets[missile.missileID].get_currentPos())
                        self.dispatcher.send_message(message)
                        message = RocketUpdate(Modules.RadarMain, Priorities.LOW, missile.missileID,self.rockets[missile.missileID].get_currentPos())
                        self.dispatcher.send_message(message)
        for rocket_id, rocket in list(self.rockets.items()):
            self.check_collision(rocket)
        for rocket_id, rocket in list(self.rockets.items()):
            if rocket.is_killed():
                self.to_remove.add(('rocket', rocket_id))
        self.cleanup()
        self.currentTime+=1
            
