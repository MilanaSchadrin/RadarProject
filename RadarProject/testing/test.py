import numpy as np
from skyenv.skyenv import SkyEnv
from skyenv.skyobjects import Plane, Rocket
from dispatcher.dispatcher import Dispatcher

def test_skyenv_functions():
    # Создаем mock Dispatcher
    dispatcher = Dispatcher()
    
    # Создаем экземпляр SkyEnv с 250 шагами времени
    sky_env = SkyEnv(dispatcher, timeSteps=250)
    sky_env.currentTime = 3  # Устанавливаем текущее время на 3 шаг
    
    # Создаем тестовые самолеты (вылетели на 1 шаге)
    plane1 = Plane(1, start=(0, 0, 0), finish=(10000, 10000, 0), speed=200)
    plane2 = Plane(2, start=(5000, 5000, 0), finish=(15000, 15000, 0), speed=200)
    sky_env.planes = [plane1, plane2]
    
    # Создаем тестовые ракеты (вылетели на 3 шаге)
    rocket1 = Rocket(101, start=(0, 0, 0), velocity=(100, 100, 100), startTime=3, radius=200)
    rocket2 = Rocket(102, start=(5400, 5400, 0), velocity=(100, 100, 100), startTime=3, radius=100)
    sky_env.rockets = {101: rocket1, 102: rocket2}
    
    # Создаем пары ракета-самолет
    sky_env.pairs = {101: plane1, 102: plane2}
    #print(plane1.get_trajectory())
    #print(rocket1.get_trajectory())
    
    print("=== Тестирование check_collision ===")
    for time_step in range(1, 250):
        sky_env.currentTime = time_step
        print(f"\n--- Шаг времени: {time_step} ---")
        
        # Проверяем столкновения для каждой ракеты
        for rocket_id, rocket in list(sky_env.rockets.items()):
            if rocket.is_killed():
                continue
                
            print(f"\nПроверка ракеты {rocket_id}")
            print(f"Время запуска: {rocket.get_startTime()}")
            
            # Проверяем столкновение только если ракета уже стартовала
            if time_step >= rocket.get_startTime():
                sky_env.check_collision(rocket)
                print(f"Статус: {'уничтожена' if rocket.is_killed() else 'активна'}")

if __name__ == "__main__":
    test_skyenv_functions()