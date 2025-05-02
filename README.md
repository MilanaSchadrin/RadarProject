# Проект по курсу "Технология разработки ПО", 2025 г. 
## Цель проекта: Разработка компьютерной имитационной модели ЗРС
### Состав команды: студенты МФТИ, 4 курс, Б03-113
<hr />
   
| Фамилия Имя           | Модуль                                  |           Github                  |
|----------------------|------------------------------------------|------------------------------------------|
| Голова Анна          | Модель радиолокатора| GolovaAnna|
| Киселёва Светлана    | Модуль визуализации результатов                    | ssssveta |
| Ошметков Степан      | Модель ПБУ| Razakys|
| Сергиенко Сергей     | Модель ПУ | BolshoiQuq|
| Сибирцев Иван        | Модель Диспетчер     | Shtrulpex|
| Шадрина Милана       | Модель воздушной обстановки | MilanaSchadrin |

## Архитектура
### Проект построен на событийно-ориентированной архитектуре (EDA) с централизованным управлением и основывается на трёх основных принципах.

1. **Разделение ответственности**

   * Четкое разделение модулей по функциям:
    
      * ControlCenter (принятие решений)
      * Radar (обнаружение)
      * Launcher (атака)
      * SkyEnv (моделирование физики)
       
   * Каждый модуль инкапсулирует свою логику и общается только через единый для всех Dispatcher

2. **Событийно-ориентированная модель**

   * Вся система работает на асинхронных сообщениях
   * Состояние системы изменяется через цепочку событий
   * Dispatcher выступает как центральная шина сообщений, обеспечивая слабую связанность
    
3. **Иерархия управления**

   * Вертикальное управление: ПБУ координирует радары и ПУ
   * Горизонтальная изоляция: Радары и ПУ не знают друг о друге
     
### Использованные архитектурные паттерны:

 * Mediator (Dispatcher как посредник)
 * Observer (подписка на события)
 * Strategy (алгоритмы приоритизации целей)
 * Facade (ControlCenter как единая точка входа)
   
>Диаграммы классов и процессов  - [UML диаграммы](https://drive.google.com/file/d/1NRzsn4hVriHqQKuGoWiO6pbLNernI-Td/view?usp=sharing)
### Структура репозитория
```
- docs/ документация
- project_moduls/ проект
  - common/ общие данные
     - commin.py
  - controlcenter/ модуль ПБУ
     - ControlCenter.py
  - database/ хранение и обработка бд
     - databaseman.py
     - skydb.db -
  - dispatcher/ модуль Диспетчер
     - dispatcher.py
     - enums.py
     - logger.py
     - messages.py
  - launcher/ модуль ПУ
     - launcher.py
  - logs/ хранение логов симуляций
  - missile/ модуль ЗУР
     - Missile.py
     - MissileController.py
  - radar/ модуль РЛС
     - Radar.py
     - RadarController.py
     - Target.py
  - skyenv/ модуль ВО
     - skyenv.py
     - skyobjects.py
  - testing/ тесты
     - modul_cc_ra_la.py
     - modul_skyenv.py
  - vizualization/ UI
     - pictures/
     - data_collector_for_visual.py
     - map_class.py
     - map_window.py
     - parametr_window.py
     - start_page.py
  - main.py
  - simulation.py
```

### Настройка окружения
```
pip install -r docs/requirements.txt
```

## Документация
[Документация по проекту](https://github.com/MilanaSchadrin/RadarProject/blob/main/docs/Docs.pdf)

>**Используемые Ресурсы**
>
>![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
>![Qt](https://img.shields.io/badge/Qt-%23217346.svg?style=for-the-badge&logo=Qt&logoColor=white)
>![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
