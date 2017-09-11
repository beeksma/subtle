from xmlrpc.client import ServerProxy
from socket import gaierror
import os
import struct
import hashlib
import sys


class OSHandler(object):
    """"The connection to the OpenSubtitles server using XML RPC"""

    server_url = 'https://api.opensubtitles.org:443/xml-rpc'
    user_agent = 'OSTestUserAgentTemp'

    def __init__(self):
        print("\nWelcome to Subtle! Attempting to connect to OpenSubtitles...")
        try:
            self.xml_rpc = ServerProxy(OSHandler.server_url, allow_none=True)
            self.language = None
            self.user_token = None
            self.query_result = None
            self.server_info = self.xml_rpc.ServerInfo()
        except gaierror:  # Throw exception and exit if we can't connect to OpenSubtitles
            print("Error: Could not connect to OpenSubtitles.org")
            sys.exit(2)

    def _extract_data(self, key):
        return self.query_result.get(key) if self.query_result.get('status').split()[0] == '200' else None

    def login(self, username, password):
        print("\nLogging in...")
        hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()
        try:
            self.query_result = self.xml_rpc.LogIn(username, hashed_password, self.language, self.user_agent)
            self.user_token = self._extract_data('token')
            self.language = self._extract_data('data')['UserPreferedLanguages']

            print("""Login successful. Token set to "{token:s}", preferred language for subtitles set to '{lang:s}'."""
                  .format(token=self.user_token, lang=self.language))
            self.query_result = None
        except TypeError:
                print("Error: Login unsuccessful. Please check your login information and try again.")
        except TimeoutError:  # Throw exception if we can't connect to OpenSubtitles
            print("Error: Could not connect to OpenSubtitles.org")

    def logout(self):
        print("\nLogging out...")
        if isinstance(self.user_token, str):
            try:
                self.query_result = self.xml_rpc.LogOut(self.user_token)
                if self._extract_data('status'):
                    print("Successfully logged out. Thanks for using Subtle!")
                else:
                    print("Error: {}".format(self._extract_data('status')))
            except TimeoutError:  # Throw exception if we can't connect to OpenSubtitles
                print("Error: Could not connect to OpenSubtitles.org")
                return
        else:
            print("Error: You can't be logged out as you're not logged in!")


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
