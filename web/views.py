from flask import render_template, url_for, redirect, request, flash
from web import app
from subtle.types import Video
from subtle import os_handler
from debug import Debugger
from web.types import SubtitleQuery
from web import navigator
import os

current_query = None


@app.route('/home')
@app.route('/')
def home():
    greeting = "Hello and welcome to Subtle!"

    return render_template("index.html",
                           title='Welcome to Subtle',
                           greeting=greeting)


@app.route('/results')
def get_result():
    sort_by = request.args.get('sort_by', default="download_count", type=str)
    desc = True if request.args.get('desc', default="True", type=str) == "True" else False
    global current_query

    if current_query is None:
        current_query = SubtitleQuery(Video(Debugger.video))
        os_handler.get_video_info(current_query.Video)
        current_query.Results = os_handler.search_subtitles(current_query.Video)

    for lang in current_query.Results:
        current_query.Results[lang].sort(key=lambda x: getattr(x, sort_by), reverse=desc)

    return render_template("results.html",
                           title='Results',
                           video=current_query.Video,
                           sort_by=sort_by,
                           is_desc=desc,
                           order="Ascending" if not desc else "Descending",
                           results=current_query.Results)


@app.route('/browse')
def select_video():
    path = request.args.get('dir', default=navigator.path, type=str)
    if path in 'parent':
        path = navigator.parent
    dirs = os.listdir(os.path.join(navigator.path, path))

    return render_template("browse.html",
                           title='Select a video',
                           directories=dirs,
                           path=navigator.path,
                           not_root=(path != navigator.root))


@app.route('/download/<lang>/<int:download_id>', methods=['POST'])
def download_subtitle(lang, download_id):
    global current_query
    if current_query is not None:
        sub = next(s for s in current_query.Results[lang] if s.download_id == download_id)
        os_handler.download_subtitle(current_query.Video, sub)
        flash(str.format("Downloading {s.file_name}...", s=sub))
    return redirect(url_for('get_result'))
