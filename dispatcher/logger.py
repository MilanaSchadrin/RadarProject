import json
from pathlib import Path
from datetime import datetime


class Logger:
    def __init__(self, log_path: Path):
        self.path = log_path

    @staticmethod
    def convert_missile_to_json(missile):
        js = vars(missile)
        js['status'] = js['status'].name
        js['missileType'] = js['missileType'].name
        return js

    @staticmethod
    def convert_target_to_json(target):
        js = vars(target)
        js['status'] = js['status'].name
        for key in js['attachedMissiles'].keys():
            js['attachedMissiles'][key] = Logger.convert_missile_to_json(js['attachedMissiles'][key])
        return js

    @staticmethod
    def convert_message_to_json(message):
        js = vars(message)
        for key in js.keys():
            if key == 'priority':
                js[key] = js[key].name
            elif key == 'recipient_id':
                js[key] = js[key].name
            elif key == 'missile':
                js[key] = Logger.convert_missile_to_json(js[key])
            elif key == 'missiles':
                js[key] = list(map(Logger.convert_missile_to_json, js[key]))
            elif key == 'target':
                js[key] = Logger.convert_target_to_json(js[key])
            elif key == 'detected_objects':
                js[key] = list(map(Logger.convert_target_to_json, js[key]))
        js = {type(message).__name__: js}
        return js

    def log(self, message, current_step):

        json_dir = self.path / "jsons"
        json_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%d_%m_%Y-%H:%M:%S")
        file_path = json_dir / f"{current_step}.json"
        data = {}
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
        data[timestamp] = self.convert_message_to_json(message)
        with open(file_path, "w") as f:
            json.dump(data, f)
    def finish(self, final_step):
        data = {}
        json_dir = self.path / "jsons"
        for i in range(final_step+1):
            file_path = json_dir / f"{final_step}.json"
            with open(file_path, 'r') as f:
                data[i] = json.load(f)
        with open(json_dir/'final_log.json', 'w') as f:
            json.dump(data, f)
