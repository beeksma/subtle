from xmlrpc.client import ServerProxy, ProtocolError
from socket import gaierror
from components import TimedEvent, hash_file
import os
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

    def get_video_info(self, video_filename):
        if self.logged_in and video_filename is not None:
            try:
                    # Get video info
                    video_info = dict()
                    video = open(video_filename, "rb")
                    video_info['dir'] = os.path.dirname(video_filename)
                    video_info['base'] = os.path.basename(video_filename)
                    video_info['size'] = os.path.getsize(video_filename)
                    video_info['hash'] = hash_file(video, video_info['size'])
                    video.close()

                    # Send query and return result
                    self.query_result = self.xml_rpc.CheckMovieHash(self.user_token, [video_info['hash']])
                    video_info['match'] = self._extract_data('data')[video_info['hash']] \
                        if len(self._extract_data('data')[video_info['hash']]) > 0 else None
                    return video_info

            except TimeoutError:  # Catch exception if we can't connect to OpenSubtitles
                print("Error: Could not connect to OpenSubtitles.org")
                return None

            except OSError as e:
                if e.args[0] == 2:  # Catch exception if video_filename does not exist
                    print("Error: Could not find the specified file")
                elif e.args[0] == 22:  # Catch exception if video_filename is not a valid filename
                    print("Error: Invalid argument specified - please use the full file path")
                else:
                    print("Error: Could not open the specified file")
                return None

    def search_subtitles(self, video_info, limit=500):
        if self.logged_in and video_info is not None and limit <= 500:
            try:
                # Set params
                languages = ','.join(self.language)
                hash_params = \
                    {
                        'sublanguageid': languages,
                        'moviehash': video_info['hash'],
                        'moviebytesize': str(video_info['size'])
                    }

                imdb_match = video_info['match']['MovieImdbID'] if video_info['match'] is not None else None
                imdb_params = \
                    {
                        'sublanguageid': languages,
                        'imdbid': imdb_match
                    }

                tag_params = \
                    {
                        'sublanguageid': languages,
                        'tag': video_info['base']
                    }

                query_params = \
                    {
                        'sublanguageid': languages,
                        'query': os.path.splitext(video_info['base'])[0]
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
                    for lang in self.language:
                        print("\nThe following '{0}' subtitles are available for '{1}':"
                              .format(lang, video_info['base']))
                        for sub in self._extract_data('data'):
                            if sub['SubLanguageID'] == lang:
                                print('{0}. '.format((self._extract_data('data')).index(sub) + 1) + sub['SubFileName'])
                    return self._extract_data('data')

                print('Sorry - could not find any matching subtitles')
                return None

            except TimeoutError:
                print('Error: Could not connect to OpenSubtitles.org')
                return None
