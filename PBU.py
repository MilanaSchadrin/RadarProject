from typing import List, Dict, Any


class Point:
    """Класс для представления координат"""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"Point(x={self.x}, y={self.y})"


class Radar:
    """Класс радара"""
    def __init__(self, name: str, coordinates: Point):
        self.name = name
        self.coordinates = coordinates

    def __repr__(self) -> str:
        return f"Radar(name={self.name}, coordinates={self.coordinates})"



class PU:
    """Класс пусковой установки (PU)"""
    def __init__(self, name: str, coordinates: Point, missiles_count: int):
        self.name = name
        self.coordinates = coordinates
        self.missiles_count = missiles_count  # Количество доступных ракет

    def __repr__(self) -> str:
        return f"PU(name={self.name}, coordinates={self.coordinates}, missiles_count={self.missiles_count})"



class PBU:
    """Пункт боевого управления (ПБУ)"""
    def __init__(self, name: str, coordinates: Point, 
                 radar_params: List[Dict[str, Any]], 
                 pu_params: List[Dict[str, Any]]):
        """
        :param name: Название ПБУ
        :param coordinates: Координаты ПБУ
        :param radar_params: Список словарей с параметрами радаров
        :param pu_params: Список словарей с параметрами ПУ
        """
        self.name = name
        self.coordinates = coordinates
        self.radars: List[Radar] = [Radar(**params) for params in radar_params]
        self.pus: List[PU] = [PU(**params) for params in pu_params]

    def __repr__(self) -> str:
        return f"PBU(name={self.name}, coordinates={self.coordinates}, radars={self.radars}, pus={self.pus})"



# main()
pbu = PBU(
    name="Stepa",
    coordinates=Point(50, 100),
    radar_params=[
        {"name": "Radar-1", "coordinates": Point(20, 30)},
        {"name": "Radar-2", "coordinates": Point(40, 60)}
    ],
    pu_params=[
        {"name": "PU-1", "coordinates": Point(25, 35), "missiles_count": 5},
        {"name": "PU-2", "coordinates": Point(45, 65), "missiles_count": 3}
    ]
)

print(pbu)
