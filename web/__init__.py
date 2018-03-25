from flask import Flask
from web.types import Navigator
import logging as log

wz_log = log.getLogger('werkzeug')
wz_log.setLevel(log.ERROR)
log.basicConfig(level=log.DEBUG, filename="subtle.log", filemode="a+",
                format="%(asctime)-15s %(levelname)-8s %(message)s")

app = Flask(__name__)
app.config.from_object('flaskconf')
navigator = Navigator()
from web import views
