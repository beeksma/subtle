from flask import Flask
from web.types import Navigator
import logging as log
import os

# Set up logging
wz_log = log.getLogger('werkzeug')
wz_log.setLevel(log.ERROR)
log.basicConfig(level=log.WARN, filename="subtle.log", filemode="a+",
                format="%(asctime)-15s %(levelname)-8s %(message)s")
logger = log.getLogger()

# Run Subtle
root_location = os.path.abspath(os.sep)
app = Flask(__name__, static_url_path='/subtle')
app.config.from_object('flaskconf')
navigator = Navigator()
from web import views
