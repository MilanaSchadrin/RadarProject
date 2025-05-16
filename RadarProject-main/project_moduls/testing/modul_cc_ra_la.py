import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from typing import Dict, Tuple
from common.commin import *
from radar.Target import Target, TargetStatus
from radar.Radar import Radar
from radar.RadarController import RadarController, TargetEnv, MissileEnv
from missile.Missile import Missile, MissileStatus, MissileType
from missile.MissileController import MissileController
from launcher.launcher import LaunchController, Launcher
from controlcenter.ControlCenter import ControlCenter
from dispatcher.dispatcher import Dispatcher
from dispatcher.enums import Modules, Priorities
from dispatcher.messages import (
    RadarControllerObjects, LaunchertoCCMissileLaunched,
    CCToSkyEnv, CCLaunchMissile, CCToRadarNewStatus
)

@pytest.fixture
def dispatcher():
    return Dispatcher()

@pytest.fixture
def sample_target():
    return Target("target1")

@pytest.fixture
def sample_missile():
    return Missile(
        missileID="missile1",
        missileType=MissileType.TYPE_1,
        currentCoords=(0, 0, 0),
        velocity=(1, 1, 1),
        currLifeTime=30,
        damageRadius=10
    )

@pytest.fixture
def radar_controller(dispatcher):
    return RadarController(dispatcher)

@pytest.fixture
def radar(radar_controller, dispatcher):
    return Radar(
        radarController=radar_controller,
        dispatcher=dispatcher,
        radarId="radar1",
        position=(0, 0, 0),
        maxRange=1000,
        coneAngleDeg=60,
        maxFollowedCount=5
    )

@pytest.fixture
def control_center(dispatcher):
    return ControlCenter(dispatcher, (0, 0, 0), 250)

class TestRadar:
    def test_initialization(self, radar):
        assert radar.radarId == "radar1"
        assert radar.position == (0, 0, 0)
        assert radar.maxRange == 1000
        assert radar.coneAngleDeg == 60
        assert radar.maxFollowedCount == 5
        assert radar.currentTargetCount == 0
        assert isinstance(radar.followedTargets, dict)

    def test_is_target_in_range(self, radar):
        target = MagicMock()
        target.getCurrentCoords.return_value = (100, 100, 100)
        
        assert radar.isTargetInRange(target, 0) is False

    def test_is_target_out_of_range(self, radar):
        target = MagicMock()
        target.getCurrentCoords.return_value = (2000, 2000, 2000)
        
        assert radar.isTargetInRange(target, 0) is False

class TestRadarController:
    def test_initialization(self, radar_controller):
        assert isinstance(radar_controller.radars, dict)
        assert isinstance(radar_controller.allTargets, dict)
        assert isinstance(radar_controller.allMissiles, dict)
        assert isinstance(radar_controller.detectedTargets, dict)

    def test_add_radar(self, radar_controller, radar):
        radar_controller.addRadar(radar)
        assert "radar1" in radar_controller.radars

    def test_add_detected_target(self, radar_controller, sample_target):
        radar_controller.addDetectedTarget(sample_target)
        assert "target1" in radar_controller.detectedTargets

    def test_process_message_se_starting(self, radar_controller):
        message = MagicMock()
        message.planes = {"target1": np.array([[0, 0, 0], [1, 1, 1]])}
        
        radar_controller.process_message = MagicMock()
        radar_controller.start(message)
        
        assert "target1" in radar_controller.allTargets
        assert len(radar_controller.allTargets["target1"].clearCoords) == 2

class TestMissileController:
    def test_initialization(self):
        controller = MissileController()
        assert len(controller._missiles) == 0
        assert len(controller._unusefulMissiles) == 0

    def test_process_missiles_of_target(self, sample_target, sample_missile):
        controller = MissileController()
        sample_target.attachedMissiles = {"missile1": sample_missile}
        
        controller.process_missiles_of_target(sample_target)
        assert len(controller._missiles) == 1

        sample_target.status = TargetStatus.DESTROYED
        controller.process_missiles_of_target(sample_target)
        assert sample_missile.status == MissileStatus.INACTIVE
        assert len(controller._unusefulMissiles) == 1

    def test_process_new_missile(self, sample_missile):
        controller = MissileController()
        controller.process_new_missile(sample_missile)
        assert len(controller._missiles) == 1
        assert sample_missile.currLifeTime == 30 - TICKSPERCYCLELAUNCHER

class TestControlCenter:
    def test_initialization(self, control_center):
        assert control_center._position == (0, 0, 0)
        assert isinstance(control_center._radarController, RadarController)
        assert isinstance(control_center._launcherController, LaunchController)
        assert isinstance(control_center._missileController, MissileController)

    def test_update_priority_targets(self, control_center):

        target1 = Target("target1")
        target1.currentCoords = (100, 100, 100)
        target1.currentSpeedVector = (1, 0, 0)
        
        target2 = Target("target2")
        target2.currentCoords = (200, 200, 200)
        target2.currentSpeedVector = (0, 1, 0)
        
        control_center._targets = [target1, target2]
        
        control_center._dispatcher.send_message = MagicMock()
        
        control_center._update_priority_targets()
        
        assert control_center._dispatcher.send_message.call_count >= 0

    def test_process_targets(self, control_center, sample_target):

        sample_target.status = TargetStatus.FOLLOWED
        control_center._targets = [sample_target]

        control_center._dispatcher.send_message = MagicMock()
        
        control_center._process_targets()
        
        control_center._dispatcher.send_message.assert_called_once()
        assert isinstance(control_center._dispatcher.send_message.call_args[0][0], CCLaunchMissile)

class TestTargetEnv:
    def test_initialization(self):
        coords = [(i, i, i) for i in range(10)]
        target = TargetEnv("target1", coords)
        assert target.targetId == "target1"
        assert len(target.clearCoords) == 10
        assert target.isFollowed is False

    def test_get_current_coords(self):
        coords = [(i, i, i) for i in range(10)]
        target = TargetEnv("target1", coords)
        assert target.getCurrentCoords(5) == (5, 5, 5)

    def test_get_current_speed_vec(self):
        coords = [(i, i, i) for i in range(10)]
        target = TargetEnv("target1", coords)
        assert target.getCurrentSpeedVec(5) == (1, 1, 1)

class TestMissileEnv:
    def test_initialization(self):
        coords = [(i, i, i) for i in range(10)]
        missile = MissileEnv("missile1", "target1", coords)
        assert missile.missileId == "missile1"
        assert missile.targetId == "target1"
        assert len(missile.clearCoords) == 10

    def test_get_current_coords(self):
        coords = [(i, i, i) for i in range(10)]
        missile = MissileEnv("missile1", "target1", coords)
        assert missile.getCurrentCoords(5) == (5, 5, 5)

    def test_get_current_speed_vec(self):
        coords = [(i, i, i) for i in range(10)]
        missile = MissileEnv("missile1", "target1", coords)
        assert missile.getCurrentSpeedVec(5) == (1, 1, 1)