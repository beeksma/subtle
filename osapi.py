from xmlrpc.client import ServerProxy, ProtocolError
from socket import gaierror
from components import TimedEvent, hash_file
from os import path
import hashlib
import sys


class OSHandler(object):
    """"Provides the connection to and communication with the OpenSubtitles server using XML RPC"""

    server_url = 'https://api.opensubtitles.org:443/xml-rpc'
    user_agent = 'OSTestUserAgentTemp'

    def __init__(self):
        print("\nWelcome to Subtle! Attempting to connect to OpenSubtitles...")
        try:
            self.xml_rpc = ServerProxy(OSHandler.server_url, allow_none=True)
            self.language = []
            self.user_token = None
            self.__logged_in = False
            self.keep_alive_timer = TimedEvent(900, self._no_operation, autostart=False)
            self.query_result = None
            self.server_info = self.xml_rpc.ServerInfo()
        except (gaierror, ProtocolError):  # Throw exception and exit if we can't connect to OpenSubtitles
            print("Error: Could not connect to OpenSubtitles.org")
            sys.exit(2)

    @property
    def logged_in(self):
        # Calling the 'logged_in' property will reset the timer that keeps the connection alive
        self.keep_alive_timer.reset()
        return self.__logged_in

    @logged_in.setter
    def logged_in(self, value):
        # Setting the 'logged_in' property will start or stop the timer that keeps the connection alive
        self.__logged_in = value
        self.keep_alive_timer.start() if value else self.keep_alive_timer.stop()

    def _extract_data(self, key):
        return self.query_result.get(key) if self.query_result['status'].split()[0] == '200' else None

    def login(self, username, password):
        if not self.logged_in:
            print("\nLogging in...")
            hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()
            try:
                self.query_result = self.xml_rpc.LogIn(username, hashed_password, self.language, self.user_agent)
                self.user_token = self._extract_data('token')
                self.language = (self._extract_data('data')['UserPreferedLanguages']).split(",")

                print("""Login successful. Token set to "{t:s}", preferred language for subtitles set to '{lang:s}'."""
                      .format(t=self.user_token, lang=",".join(self.language)))
                self.query_result = None
                self.logged_in = True
            except TypeError:
                    print("Error: Login unsuccessful. Please check your login information and try again.")
            except TimeoutError:  # Throw exception if we can't connect to OpenSubtitles
                print("Error: Could not connect to OpenSubtitles.org")
        else:
            print("Error: You're already logged in!")

    def logout(self):
        print("\nLogging out...")
        if self.logged_in:
            try:
                self.query_result = self.xml_rpc.LogOut(self.user_token)
                if self._extract_data('status'):
                    self.logged_in = False
                    self.user_token = None
                    print("Successfully logged out. Thanks for using Subtle!")
                else:
                    print("Error: {}".format(self._extract_data('status')))
            except TimeoutError:  # Throw exception if we can't connect to OpenSubtitles
                print("Error: Could not connect to OpenSubtitles.org")
                return
        else:
            print("Error: You can't be logged out as you're currently not logged in!")

    def _no_operation(self):
        if self.__logged_in:
            try:
                self.query_result = self.xml_rpc.NoOperation(self.user_token)
                if self._extract_data('status').split()[0] != '200':
                    self.logged_in = False
                    print("Your session timed out, please use Login before doing anything else")
                else:
                    print("Staying alive...")
            except TimeoutError:  # Throw exception if we can't connect to OpenSubtitles
                print("Error: Could not connect to OpenSubtitles.org")
                return

    def search_subtitles(self, video_filename, imdb_id=None, limit=500):
        if self.logged_in and video_filename is not None and limit <= 500:
            # try:
                # Get video info
                video = open(video_filename, "rb")
                file_base = path.basename(video_filename)
                file_size = path.getsize(video_filename)
                video_hash = hash_file(video, file_size)
                video.close()

                # Set params
                languages = ','.join(self.language)
                hash_params = \
                    {
                        'sublanguageid': languages,
                        'moviehash': video_hash,
                        'moviebytesize': str(file_size)
                    }

                imdb_params = \
                    {
                        'sublanguageid': languages,
                        'imdbid': imdb_id
                    }

                tag_params = \
                    {
                        'sublanguageid': languages,
                        'tag': file_base
                    }

                query_params = \
                    {
                        'sublanguageid': languages,
                        'query': path.splitext(file_base)[0]
                    }

                request_params = [hash_params, imdb_params, tag_params, query_params]
                request_count = 0
                first_try = True

                # Try each param dictionary until a subtitle match has been found or we have no more options
                while (first_try or len(self.query_result['data']) == 0) and request_count < 4:
                    first_try = False
                    self.query_result = self.xml_rpc.SearchSubtitles(self.user_token,
                                                                     [request_params[request_count]],
                                                                     {'limit': limit})
                    request_count += 1

                if len(self.query_result['data']) > 0:
                    print("\nThe following subtitles are available for '{0}':".format(file_base))
                    for result in self._extract_data('data'):
                        print('* ' + result['SubFileName'])
                    return self._extract_data('data')

                print('Sorry - could not find any matching subtitles')
                return None

            # except:
            #     return
