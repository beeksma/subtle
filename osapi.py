from xmlrpc.client import ServerProxy
import struct, os, hashlib

class OSConnection(object):
    """"The connection to the OpenSubtitles server using XML RPC"""

    server_url ='https://api.opensubtitles.org:443/xml-rpc'
    user_agent = 'OSTestUserAgentTemp'


    def __init__(self):
        self.xml_rpc = ServerProxy(OSConnection.server_url, allow_none=True)
        self.language = None
        self.user_token = None
        self.query_result = None
        self.server_info = self.xml_rpc.ServerInfo()

    def _extract_data(self, key):
        return self.query_result.get(key) if self.query_result.get('status').split()[0] else None


    def Login(self, username, password):
        hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()
        self.query_result = self.xml_rpc.LogIn(username, hashed_password, self.language, self.user_agent)
        if self.query_result is not None:
            self.user_token = self._extract_data('token')
            self.language = self._extract_data('data')['UserPreferedLanguages']
            print(self.query_result)
            print ("Login successful. Token set to '{0}', language set to '{1}'.".format(self.user_token, self.language))
            self.query_result = None
        else:
            print("Login unsuccessful. Please check your login information and try again.")



def hashFile(name):
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

    except(IOError):
        return "IOError"

