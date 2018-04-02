from flask import render_template, url_for, redirect, request, flash
from web import app
from subtle.types import Video
from subtle import os_handler
from web.types import SubtitleQuery
from web import navigator
import os

current_query = None
current_video_path = None


@app.route('/home')
@app.route('/')
def home():
    greeting = "Hello and welcome to Subtle!"

    return render_template("index.html",
                           title='Welcome to Subtle',
                           greeting=greeting,
                           no_results=current_query is None)


@app.route('/results')
def get_result():
    sort_by = request.args.get('sort_by', default="download_count", type=str)
    desc = True \
        if request.args.get('desc', default="True", type=str) == "True" \
        else False
    global current_query

    if current_video_path is None:
        flash("Please select a video file first!", 'info')
        return redirect(url_for('browse'))
    elif current_query is None:
        current_query = SubtitleQuery(Video(current_video_path))
        os_handler.get_video_info(current_query.Video)
        current_query.Results = os_handler.search_subtitles(
            current_query.Video)

    for lang in current_query.Results:
        current_query.Results[lang].sort(
            key=lambda x: getattr(x, sort_by), reverse=desc)

    return render_template("results.html",
                           title='Results',
                           video=current_query.Video,
                           sort_by=sort_by,
                           is_desc=desc,
                           order="Ascending" if not desc else "Descending",
                           results=current_query.Results,
                           no_results=current_query is None)


@app.route('/browse')
def browse():
    try:
        os_handler.login()
        path = request.args.get('dir', default=-2, type=int)
        if path is -2:
            path = navigator.root
        elif path is -1:
            path = navigator.parent
        else:
            path = navigator.dirs[int(path)]
        navigator.path = os.path.join(navigator.path, path)
        navigator.dirs = sorted([d for d in os.listdir(navigator.path)
                                if os.path.isdir(
                                    os.path.join(navigator.path, d)) and
                                not d.startswith('.')])
        supported_extensions = ('.mkv', '.avi', '.mp4')
        navigator.files = sorted([f for f in os.listdir(navigator.path)
                                 if os.path.isfile(
                                     os.path.join(navigator.path, f)) and
                                 f.endswith(supported_extensions)])

        return render_template("browse.html",
                               title='Select a video',
                               directories=navigator.dirs,
                               files=navigator.files,
                               path=navigator.path,
                               no_results=current_query is None,
                               not_root=(path != navigator.root))
    except IndexError:
        flash("Something went wrong, please try again", 'error')
        return redirect(url_for('browse'))


@app.route('/select')
def select():
    os_handler.login()
    file_id = request.args.get('file', type=int)
    global current_video_path
    new_video_path = os.path.join(navigator.path, navigator.files[file_id])
    if os.path.isfile(new_video_path):
        current_video_path = new_video_path
        global current_query
        current_query = None
        return redirect(url_for('get_result'))
    else:
        current_video_path = None
        flash("Error: could not open the selected file. Please try again.",
              'error')
        return redirect(url_for('browse'))


@app.route('/download/<lang>/<int:download_id>', methods=['POST'])
def download_subtitle(lang, download_id):
    os_handler.login()    
    global current_query
    if current_query is not None:
        sub = next(
                s for s in current_query.Results[lang] if
                s.download_id == download_id)
        os_handler.download_subtitle(current_query.Video, sub)
        flash(str.format("Downloading {s.file_name}...", s=sub), 'success')
    return redirect(url_for('get_result'))
