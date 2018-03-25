from subtle.osapi import OSHandler
from pathlib import Path
from collections import OrderedDict
import json
import hashlib

os_handler = OSHandler()
config_exists = Path("config.json").is_file()
settings = None

if config_exists:
    with open('config.json', 'r') as json_settings:
        settings = json.load(json_settings, object_pairs_hook=OrderedDict)
    if not settings["os_username"] and \
       (not settings["os_password"] or not settings["hash"]):
        raise ValueError(
            'OpenSubtitles credentials have not been set in config.json!')
    os_handler.user_name = settings["os_username"]

    if settings["os_password"]:
        os_handler.hash = hashlib.md5(settings["os_password"]
                                      .encode('utf-8')).hexdigest()
        settings["os_password"] = ""
        settings["hash"] = os_handler.hash
        with open('config.json', 'w') as json_settings:
            json.dump(settings, json_settings, indent=4)
    else:
        os_handler.hash = settings["hash"]

os_handler.login()