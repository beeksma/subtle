from flask import render_template
from web import app
from subtle.types import Video
from subtle import os_handler
from debug import Debugger


@app.route('/home')
@app.route('/')
def index():
    greeting = "Hello and welcome to Subtle!"

    return render_template("index.html",
                           title='Welcome to Subtle',
                           greeting=greeting)


@app.route('/results')
def get_result(sort_by="download_count", desc=True):
    v = Video(Debugger.video)
    os_handler.get_video_info(v)

    results = os_handler.search_subtitles(v)
    for lang in results:
        results[lang].sort(key=lambda x: getattr(x, sort_by), reverse=desc)

    return render_template("results.html",
                           title='Results',
                           video=v,
                           results=results)
