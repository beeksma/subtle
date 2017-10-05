from threading import Timer, Lock
import struct


class TimedEvent(object):
    # Based on source from: https://stackoverflow.com/questions/2398661/schedule-a-repeating-event-in-python-3
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


def hash_file(file, file_size):
    # Based on source: http://trac.opensubtitles.org/projects<script%20type=/opensubtitles/wiki/HashSourceCodes
    try:

        long_long_format = '<q'  # little-endian long long
        byte_size = struct.calcsize(long_long_format)
        file_hash = file_size

        if file_size < 65536 * 2:
            return "SizeError"

        for x in range(65536 // byte_size):
            buffer = file.read(byte_size)
            (l_value,) = struct.unpack(long_long_format, buffer)
            file_hash += l_value
            file_hash = file_hash & 0xFFFFFFFFFFFFFFFF  # to remain as 64bit number

        file.seek(max(0, file_size - 65536), 0)
        for x in range(65536 // byte_size):
            buffer = file.read(byte_size)
            (l_value,) = struct.unpack(long_long_format, buffer)
            file_hash += l_value
            file_hash = file_hash & 0xFFFFFFFFFFFFFFFF

        file.close()
        returned_hash = "%016x" % file_hash
        return returned_hash

    except IOError:
        return "IOError"
