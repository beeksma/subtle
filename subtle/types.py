import os
from subtle.components import hash_file


class Video(object):
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
