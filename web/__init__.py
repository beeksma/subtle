from flask import Flask
from web.types import Navigator

app = Flask(__name__)
app.config.from_object('config')
navigator = Navigator()
from web import views
