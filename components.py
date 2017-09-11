from threading import Timer, Lock
import os
import struct


class timed_event(object):
    # Based on code from: https://stackoverflow.com/questions/2398661/schedule-a-repeating-event-in-python-3
    """
    A periodic task running in threading.Timers
    """

    def __init__(self, interval, action, *args, **kwargs):
        self._lock = Lock()
        self._timer = None
        self.action = action
        self.interval = interval
        self.args = args
        self.kwargs = kwargs
        self._stopped = True
        if kwargs.pop('autostart', True):
            self.start()

    def start(self, from_run=False):
        self._lock.acquire()
        if from_run or self._stopped:
            self._stopped = False
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self._lock.release()

    def _run(self):
        self.start(from_run=True)
        self.action(*self.args, **self.kwargs)

    def stop(self):
        self._lock.acquire()
        self._stopped = True
        self._timer.cancel()
        self._lock.release()

    def reset(self):
        if not self._stopped:
            self.stop()
            self.start()


def hash_file(name):
    # Source: http://trac.opensubtitles.org/projects<script%20type=/opensubtitles/wiki/HashSourceCodes
    try:

        longlongformat = '<q'  # little-endian long long
        bytesize = struct.calcsize(longlongformat)

        f = open(name, "rb")

        filesize = os.path.getsize(name)
        hash = filesize

        if filesize < 65536 * 2:
            return "SizeError"

        for x in range(65536 / bytesize):
            buffer = f.read(bytesize)
            (l_value,) = struct.unpack(longlongformat, buffer)
            hash += l_value
            hash = hash & 0xFFFFFFFFFFFFFFFF  # to remain as 64bit number

        f.seek(max(0, filesize - 65536), 0)
        for x in range(65536 / bytesize):
            buffer = f.read(bytesize)
            (l_value,) = struct.unpack(longlongformat, buffer)
            hash += l_value
            hash = hash & 0xFFFFFFFFFFFFFFFF

        f.close()
        returnedhash = "%016x" % hash
        return returnedhash

    except IOError:
        return "IOError"