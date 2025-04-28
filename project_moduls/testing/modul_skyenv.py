import pytest
import numpy as np
from typing import Tuple
from unittest.mock import MagicMock, patch
from skyenv.skyenv import  Plane, Rocket, SkyEnv, Dispatcher

@pytest.fixture
def basic_plane():
    return Plane(1, (0, 0, 0), (1000, 1000, 100), 250)

@pytest.fixture
def basic_rocket():
    return Rocket(1, (0, 0, 0), [10, 10, 10], 0, 100, 20)

@pytest.fixture
def sky_env():
    dispatcher = MagicMock(spec=Dispatcher)
    return SkyEnv(dispatcher)

class TestPlane:
    def test_initialization(self, basic_plane):
        plane = basic_plane
        assert plane.get_status() is True
        assert plane.trajectory.shape == (250, 3)

    def test_killed(self, basic_plane):
        plane = basic_plane
        plane.killed()
        assert plane.get_status() is False

    def test_trajectory_shape(self, basic_plane):
        plane = basic_plane
        assert plane.get_trajectory().shape == (250, 3)

    def test_trajectory_climbing(self, basic_plane):
        plane = basic_plane
        trajectory = plane.get_trajectory()
        assert trajectory[0][2] < trajectory[10][2]

class TestRocket:
    def test_initialization(self, basic_rocket):
        rocket = basic_rocket
        assert rocket.get_id() == 1
        assert rocket.get_radius() == 20
        assert rocket.is_killed() is False
        assert rocket.trajectory.shape == (100, 3)

    def test_boom(self, basic_rocket):
        rocket = basic_rocket
        rocket.boom()
        assert rocket.is_killed() is True

class TestSkyEnv:
    def test_initialization(self, sky_env):
        assert sky_env.id == 6
        assert isinstance(sky_env.dispatcher, Dispatcher)
        assert sky_env.planes == []
        assert sky_env.rockets == {}
        assert sky_env.pairs == {}

    def test_make_planes(self, sky_env):
        plane_data = [(1, (0, 0, 0), (100, 100, 100), 250)]
        sky_env.make_planes(plane_data)
        assert len(sky_env.planes) == 1
        assert sky_env.planes[0].get_id() == 1

    def test_add_rocket(self, sky_env):
        dispatcher = sky_env.dispatcher
        rocket = MagicMock()
        rocket.get_id.return_value = 1
        rocket.get_startTime.return_value = 0
        rocket.get_trajectory.return_value = np.zeros((100, 3))
        
        missile = MagicMock()
        target_id = 1
        
        sky_env.add_rocket(rocket, missile, target_id)
        
        assert 1 in sky_env.rockets
        dispatcher.send_message.assert_called()

    def test_check_collision(self, sky_env):
        plane = Plane(1, (0, 0, 0), (100, 100, 100), 250)
        sky_env.planes.append(plane)
        
        rocket = Rocket(2, (0, 0, 0), [1, 1, 1], 0, 250, 100) 
        sky_env.rockets[2] = rocket
        sky_env.pairs[2] = plane
        
        sky_env.check_collision(rocket)

        assert plane.get_status() is False
        assert rocket.is_killed() is True
        sky_env.dispatcher.send_message.assert_called()

    def test_check_if_in_radius(self, sky_env):
        plane1 = Plane(1, (0, 0, 0), (100, 100, 100), 250)
        plane2 = Plane(2, (50, 50, 50), (150, 150, 150), 250)
        sky_env.planes.extend([plane1, plane2])
        
        explosion_pos = np.array([25, 25, 25])
        radius = 100
        time = 10
        
        collateral = sky_env.check_if_in_radius(time, explosion_pos, radius)
        
        assert len(collateral) >= 1 
        assert plane1.get_status() is False or plane2.get_status() is False

    def test_cleanup(self, sky_env):
        sky_env.to_remove.add(('plane', 1))
        sky_env.to_remove.add(('rocket', 1))

        plane = Plane(1, (0, 0, 0), (100, 100, 100), 250)
        sky_env.planes.append(plane)
        
        rocket = MagicMock()
        rocket.get_id.return_value = 1
        sky_env.rockets[1] = rocket
        sky_env.pairs[1] = plane
        
        sky_env.cleanup()
        
        assert len(sky_env.planes) == 0
        assert len(sky_env.rockets) == 0
        assert len(sky_env.pairs) == 0
        assert len(sky_env.to_remove) == 0