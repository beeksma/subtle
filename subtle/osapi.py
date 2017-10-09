import base64
import hashlib
import os
import sys
import zlib
from socket import gaierror
from xmlrpc.client import ServerProxy, ProtocolError
from subtle.components import TimedEvent
from subtle.types import SubResult


class OSHandler(object):
    """"Provides the connection to and communication with the OpenSubtitles server using XML RPC"""

    version = '1'
    server_url = 'https://api.opensubtitles.org:443/xml-rpc'
    user_agent = 'Subtle' + version  # Please do not change this value, nor use it in any other API

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

    def get_video_info(self, video):
        if self.logged_in and video is not None:
            try:
                    # Send query and return result
                    self.query_result = self.xml_rpc.CheckMovieHash(self.user_token, [video.file_hash])
                    if len(self._extract_data('data')[video.file_hash]) > 0:
                        data = self._extract_data('data')[video.file_hash]
                        video.imdb_id = data['MovieImdbID']
                        video.title = data['MovieName']
                        video.year = data['MovieYear']
                        return video
                    else:
                        raise ValueError("Sorry, couldn't find any matches")

            except TimeoutError:  # Catch exception if we can't connect to OpenSubtitles
                print("Error: Could not connect to OpenSubtitles.org")
                return None

            except TypeError:
                print("Error: Are you sure you used a Video instance as a parameter?")
                return None

    def search_subtitles(self, video, limit=500):
        if self.logged_in and video is not None and limit <= 500:
            try:
                print("\nLooking for subtitles for '{0}'...".format(video.file_name))
                # Set params
                languages = ','.join(self.language)
                hash_params = \
                    {
                        'sublanguageid': languages,
                        'moviehash': video.file_hash,
                        'moviebytesize': str(video.file_size)
                    }

                imdb_match = video.imdb_id if video.imdb_id is not 0 else None
                imdb_params = \
                    {
                        'sublanguageid': languages,
                        'imdbid': imdb_match
                    }

                tag_params = \
                    {
                        'sublanguageid': languages,
                        'tag': video.file_name
                    }

                file_params = \
                    {
                        'sublanguageid': languages,
                        'query': os.path.splitext(video.file_name)[0]
                    }

                folder_params = \
                    {
                        'sublanguageid': languages,
                        'query': os.path.basename(video.directory)
                    }

                request_params = [hash_params, imdb_params, tag_params, file_params, folder_params]
                request_count = 0
                first_try = True

                # Try each param dictionary until a subtitle match has been found or we have no more options
                while (first_try or len(self.query_result['data']) == 0) and request_count < 5:
                    first_try = False
                    self.query_result = self.xml_rpc.SearchSubtitles(self.user_token,
                                                                     [request_params[request_count]],
                                                                     {'limit': limit})
                    request_count += 1

                # In case we find matching subtitles, return them as SubResult instances grouped by language
                if len(self.query_result['data']) > 0:
                    results = dict()
                    for lang in self.language:
                        print("\nThe following '{0}' subtitles are available for '{1}':"
                              .format(lang, video.file_name))
                        print("=" * 10)
                        for sub in self._extract_data('data'):
                            if sub['SubLanguageID'] == lang:
                                if lang not in results:
                                    results[lang] = []
                                s = SubResult(video.id)
                                s.file_name = sub['SubFileName']
                                s.download_id = sub['IDSubtitleFile']
                                s.lang_id = sub['ISO639']
                                s.language = sub['LanguageName']
                                s.rating = float(sub['SubRating'])
                                s.is_HD = bool(sub['SubHD'])
                                s.is_HI = bool(sub['SubHearingImpaired'])
                                s.download_count = int(sub['SubDownloadsCnt'])
                                s.fps = float(sub['MovieFPS'])
                                s.matched_by = sub['MatchedBy']
                                results[lang].append(s)
                                print('{0:0>2}. {1} [[ ID: {2} - Download Count: {3} ]]'
                                      .format((self._extract_data('data')).index(sub) + 1,
                                              s.file_name, s.download_id, s.download_count))
                        print('')
                    return results

                print('Sorry - could not find any matching subtitles')
                return None

            except TimeoutError:
                print('Error: Could not connect to OpenSubtitles.org')
                return None

            except TypeError:
                print("Error: Are you sure you used a Video instance as a parameter?")
                return None

    def download_subtitle(self, video, sub_result):
        if self.logged_in and sub_result is not None:
            try:
                sub_id = sub_result.download_id
                self.query_result = self.xml_rpc.DownloadSubtitles(self.user_token, [sub_id])
                sub = zlib.decompress(base64.b64decode(self._extract_data('data')[0]['data']), 16 +
                                      zlib.MAX_WBITS).decode('utf-8')
                sub_filename = "{path}.{lang}.{ext}".format(
                    path=os.path.join(video.directory, video.file_name[:-4]),
                    lang=sub_result.lang_id, ext='srt')
                sub_file = open(sub_filename, 'w', encoding='utf-8', newline='')
                sub_file.write(sub)
                sub_file.close()

            except TimeoutError:
                print('Error: Could not connect to OpenSubtitles.org')

            except UnicodeDecodeError:
                print('Error: Could not decode downloaded subtitle to UTF-8 character encoding')

            except TypeError:
                print("Error: Are you sure you are using Video and SubResult instances as parameters?")
