from flask import render_template
from web import app
from subtle.types import Video
from subtle import os_handler
from debug import Debugger


@app.route('/')
@app.route('/index')
def index():
    v = Video(Debugger.video)
    os_handler.get_video_info(v)
    results = os_handler.search_subtitles(v)

    return render_template("index.html",
                           title='Results',
                           video=v,
                           results=results)
