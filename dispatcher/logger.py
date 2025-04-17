import json


def convert_missile_to_json(missile):
    js = vars(missile)
    js['status'] = js['status'].name
    js['missileType'] = js['missileType'].name
    return js


def convert_target_to_json(target):
    js = vars(target)
    js['status'] = js['status'].name
    for key in js['attachedMissiles'].keys():
        js['attachedMissiles'][key] = convert_missile_to_json(js['attachedMissiles'][key])
    return js


def convert_message_to_json(message):
    js = vars(message)
    for key in js.keys():
        if key == 'priority':
            js[key] = js[key].name
        elif key == 'recipient_id':
            js[key] = js[key].name
        elif key == 'missile':
            js[key] = convert_missile_to_json(js[key])
        elif key == 'missiles':
            js[key] = list(map(convert_missile_to_json, js[key]))
        elif key == 'target':
            js[key] = convert_target_to_json(js[key])
        elif key == 'detected_objects':
            js[key] = list(map(convert_target_to_json, js[key]))
    js = {type(message).__name__: js}
    return js

