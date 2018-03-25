from flask import Flask
from web.types import Navigator

app = Flask(__name__)
app.config.from_object('flaskconf')
navigator = Navigator()
from web import views
