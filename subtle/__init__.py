from subtle.osapi import OSHandler
from debug import Debugger
from pathlib import Path
from collections import OrderedDict
import json
import bcrypt

os_handler = OSHandler()
config_exists = Path("config.json").is_file()
settings = None
update_settings = False

if config_exists:
    with open('config.json', 'r') as json_settings:
        settings = json.load(json_settings, object_pairs_hook=OrderedDict)
    if not settings["os_username"] or not settings["os_password"]:
        raise ValueError('OpenSubtitles credentials have not been set in config.json!')
    os_handler.user_name = settings["os_username"]

    if settings["salt"] and settings["password"].startswith(settings["salt"]):
        os_handler.salt = settings["salt"]
        os_handler.hashed_password = settings["os_password"]
    elif settings["salt"]:
        os_handler.salt = settings["salt"]
        os_handler.hashed_password = bcrypt.hashpw(settings["os_password"], os_handler.salt)
        settings["os_password"] = os_handler.hashed_password.decode('utf-8')
        update_settings = True
    else:
        password = settings["os_password"].encode('utf-8')
        os_handler.salt = bcrypt.gensalt()
        settings["salt"] = os_handler.salt.decode('utf-8')
        os_handler.hashed_password = bcrypt.hashpw(password, os_handler.salt)
        settings["os_password"] = os_handler.hashed_password.decode('utf-8')
        update_settings = True

    if update_settings:
        with open('config.json', 'w') as json_settings:
            json.dump(settings, json_settings)


os_handler.login(Debugger.user_name, Debugger.password)