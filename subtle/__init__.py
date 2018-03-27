from subtle.osapi import OSHandler
from pathlib import Path
from collections import OrderedDict
from web import log, wz_log, logger, navigator
import sys
import json
import hashlib

os_handler = OSHandler()
config_exists = Path("config.json").is_file()
settings = None

if config_exists:
    try:
        with open('config.json', 'r') as json_settings:
            settings = json.load(json_settings, object_pairs_hook=OrderedDict)

        # Get OS credentials
        if not settings["os_username"] and \
           (not settings["os_password"] or not settings["hash"]):
            raise ValueError(
                'OpenSubtitles credentials have not been set in config.json!')
        os_handler.user_name = settings["os_username"]

        # Set hash if OS password is not blank
        if settings["os_password"]:
            os_handler.hash = hashlib.md5(settings["os_password"]
                                          .encode('utf-8')).hexdigest()
            settings["os_password"] = ""
            settings["hash"] = os_handler.hash
            with open('config.json', 'w') as json_settings:
                json.dump(settings, json_settings, indent=4)
        else:
            os_handler.hash = settings["hash"]

        # Enable verbose logging if debugging enabled
        if settings["debug"].lower() == 'yes':
            logger.setLevel(log.DEBUG)
            wz_log.setLevel(log.DEBUG)

        # Set root folder if valid directory
        if Path(settings["root"]).is_dir():
            navigator.root = settings["root"]

    except Exception as e:
        log.error(e.args[0])
        sys.exit(1)
else:
    raise ValueError("ERROR: 'config.json' is missing in root folder."
                     " Copy 'config.json.sample' to 'config.json', "
                     "add your OpenSubtitles credentials, and try again!")

os_handler.login()
