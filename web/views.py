from flask import render_template, url_for, redirect
from web import app
from subtle.types import Video
from subtle import os_handler
from debug import Debugger
from web.types import SubtitleQuery


current_query = None

@app.route('/home')
@app.route('/')
def home():
    greeting = "Hello and welcome to Subtle!"

    return render_template("index.html",
                           title='Welcome to Subtle',
                           greeting=greeting)


@app.route('/results')
def get_result(sort_by="download_count", desc=True):
    global current_query
    current_query = SubtitleQuery(Video(Debugger.video))
    os_handler.get_video_info(current_query.Video)

    current_query.Results = os_handler.search_subtitles(current_query.Video)
    for lang in current_query.Results:
        current_query.Results[lang].sort(key=lambda x: getattr(x, sort_by), reverse=desc)

    return render_template("results.html",
                           title='Results',
                           video=current_query.Video,
                           results=current_query.Results)


@app.route('/download/<lang>/<int:download_id>')
def download_subtitle(lang, download_id):
    global current_query
    if current_query is not None:
        sub = next(s for s in current_query.Results[lang] if s.download_id == download_id)
        os_handler.download_subtitle(current_query.Video, sub)
    return redirect(url_for('home'))
