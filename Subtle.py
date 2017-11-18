#!flask/bin/python
from web import app
from subtle import os_handler


try:
    app.run(debug=True)
finally:
    os_handler.logout()
