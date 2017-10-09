from subtle.osapi import OSHandler
from debug import Debugger


os_handler = OSHandler()
os_handler.login(Debugger.user_name, Debugger.password)
