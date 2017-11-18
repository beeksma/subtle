import os
import uuid
from subtle.components import hash_file


class Video(object):
    id = uuid.uuid1()
    title = ''
    full_path = ''
    file_size = 0
    file_hash = None
    imdb_id = 0
    year = ''

    @property
    def file_name(self):
        if len(self.full_path) > 0:
            return os.path.basename(self.full_path)
        else:
            return None

    @property
    def directory(self):
        if len(self.full_path) > 0:
            return os.path.dirname(self.full_path)
        else:
            return None

    def __init__(self, path):
        try:
            self.full_path = path
            self.file_size = os.path.getsize(self.full_path)
            video_file = open(self.full_path, "rb")
            self.file_hash = hash_file(video_file, self.file_size)
            video_file.close()

        except OSError as e:
            if e.args[0] == 2:  # Catch exception if path does not exist
                print("Error: Could not find the specified file")
            elif e.args[0] == 22:  # Catch exception if path is not a valid filename
                print("Error: Invalid argument specified - please use the full file path")
            else:
                print("Error: Could not open the specified file")


class SubResult(object):
    file_name = ''
    video_id = None
    is_HI = False
    is_HD = False
    rating = -1.0
    download_id = ''
    download_count = -1
    fps = 0.0
    language = ''
    lang_id = ''
    matched_by = ''

    def __init__(self, video_id):
        if type(video_id) is uuid.UUID:
            self.video_id = video_id
        else:
            raise TypeError('Error: The provided video_id is not a valid unique identifier')

    def __str__(self):
        return self.file_name
