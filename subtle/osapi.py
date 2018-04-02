import base64
import os
import sys
import zlib
from socket import gaierror
from xmlrpc.client import ServerProxy, ProtocolError
from subtle.components import TimedEvent
from subtle.types import SubResult
from web import log


class OSHandler(object):
    """"Provides the connection to and communication with the
    OpenSubtitles server using XML RPC"""

    version = '1'
    server_url = 'https://api.opensubtitles.org:443/xml-rpc'
    # Please do not change the user agent, nor use it in any other API
    user_agent = 'Subtle' + version

    def __init__(self):
        log.info("Welcome to Subtle!"
                 "Attempting to connect to OpenSubtitles...")
        try:
            self.xml_rpc = ServerProxy(OSHandler.server_url, allow_none=True)
            self.language = []
            self.user_name = None
            self.hash = None
            self.user_token = None
            self.__logged_in = False
            self.keep_alive_timer = TimedEvent(
                900, self._no_operation, autostart=False)
            self.keep_alive = False
            self.query_result = None
            self.server_info = self.xml_rpc.ServerInfo()
        except (gaierror, ProtocolError):
            # Throw exception and exit if we can't connect to OpenSubtitles
            log.exception("Error: Could not connect to OpenSubtitles.org")
            sys.exit(1)

    @property
    def logged_in(self):
        # Resets the timer that keeps the connection alive
        self.keep_alive_timer.reset()
        self.keep_alive = True
        return self.__logged_in

    @logged_in.setter
    def logged_in(self, value):
        # Start or stops the timer that keeps the connection alive
        self.__logged_in = value
        self.keep_alive_timer.start() if \
            value else self.keep_alive_timer.stop()

    def _extract_data(self, key):
        return self.query_result.get(key) if \
            self.query_result['status'].split()[0] == '200' else None

    def login(self):
        if not self.logged_in:
            log.info("Logging in...")
            try:
                self.query_result = self.xml_rpc.LogIn(
                                        self.user_name, self.hash,
                                        self.language, self.user_agent)
                if not self._extract_data('token'):
                    raise ValueError("Error: Login unsuccessful. "
                                     "Please check your login information"
                                     "and try again.")
                self.user_token = self._extract_data('token')
                self.language = \
                    (self._extract_data('data')['UserPreferedLanguages']) \
                    .split(",")

                log.info("""Login successful. Token set to "{t:s}","""
                         " preferred language for subtitles set to '{lang:s}'."
                         .format(t=self.user_token,
                                 lang=",".join(self.language)))
                self.query_result = None
                self.logged_in = True
            except ValueError as e:
                log.exception(e.args[0])
                sys.exit(1)
            except TimeoutError:
                # Throw exception if we can't connect to OpenSubtitles
                log.exception("Error: Could not connect to OpenSubtitles.org")
                sys.exit(1)

        else:
            log.info("Already logged in")

    def logout(self):
        log.info("Logging out...")
        if self.logged_in:
            try:
                self.query_result = self.xml_rpc.LogOut(self.user_token)
                if self._extract_data('status'):
                    self.logged_in = False
                    self.user_token = None
                    self.keep_alive = False
                    log.info("Successfully logged out."
                             " Thanks for using Subtle!")
                else:
                    log.error("Error: {}".format(self._extract_data('status')))
            except TimeoutError:
                # Throw exception if we can't connect to OpenSubtitles
                log.error("Error: Could not connect to OpenSubtitles.org")
                return
        else:
            log.info("Already logged out")

    def _no_operation(self):
        if self.__logged_in:
            if self.keep_alive:
                try:
                    self.keep_alive = False
                    self.query_result = \
                        self.xml_rpc.NoOperation(self.user_token)
                    if self._extract_data('status').split()[0] != '200':
                        self.logged_in = False
                        log.warn("Your session timed out, "
                                 "please use Login before doing anything else")
                    else:
                        log.info("Staying alive...")
                except TimeoutError:
                    # Throw exception if we can't connect to OpenSubtitles
                    log.error("Error: Could not connect to OpenSubtitles.org")
                    return
            else:
                self.logout()

    def get_video_info(self, video):
        if self.logged_in and video is not None:
            try:
                    # Send query and return result
                    self.query_result = self.xml_rpc.CheckMovieHash(
                        self.user_token, [video.file_hash])
                    if len(self._extract_data('data')[video.file_hash]) > 0:
                        data = self._extract_data('data')[video.file_hash]
                        video.imdb_id = data['MovieImdbID']
                        video.title = data['MovieName']
                        video.year = data['MovieYear']
                    else:
                        video.title = video.file_name

            except TimeoutError:
                # Catch exception if we can't connect to OpenSubtitles
                log.error("Error: Could not connect to OpenSubtitles.org")
                return None

            except TypeError:
                log.error("Error: Are you sure you're using a Video instance?")
                return None

    def search_subtitles(self, video, limit=500):
        if self.logged_in and video is not None and limit <= 500:
            try:
                log.info("Looking for subtitles for '{0}'..."
                         .format(video.file_name))
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

                request_params = \
                    [hash_params, imdb_params, tag_params,
                     file_params, folder_params]
                request_count = 0
                first_try = True

                # Try each param dictionary until we finda subtitle match
                while (first_try or len(self.query_result['data']) == 0) \
                        and request_count < 5:
                    first_try = False
                    self.query_result = \
                        self.xml_rpc.SearchSubtitles(
                            self.user_token,
                            [request_params[request_count]],
                            {'limit': limit})
                    request_count += 1

                # Return matching subs as SubResults grouped by language
                if len(self.query_result['data']) > 0:
                    results = dict()
                    for lang in self.language:
                        log.info(
                            "The following '{0}' subtitles are "
                            "available for '{1}':"
                            .format(lang, video.title))
                        log.info("=" * 10)
                        for sub in self._extract_data('data'):
                            if sub['SubLanguageID'] == lang:
                                if lang not in results:
                                    results[lang] = []
                                s = SubResult(video.id)
                                s.file_name = sub['SubFileName']
                                s.download_id = int(sub['IDSubtitleFile'])
                                s.lang_id = sub['ISO639']
                                s.language = sub['LanguageName']
                                s.rating = float(sub['SubRating'])
                                s.is_HD = bool(sub['SubHD'])
                                s.is_HI = bool(sub['SubHearingImpaired'])
                                s.download_count = int(sub['SubDownloadsCnt'])
                                s.fps = float(sub['MovieFPS'])
                                s.matched_by = sub['MatchedBy']
                                results[lang].append(s)
                                log.info(
                                    '{0:0>2}. {1} '
                                    '[[ ID: {2} - Download Count: {3} ]]'
                                    .format(
                                        (self._extract_data('data'))
                                        .index(sub) + 1,
                                        s.file_name, s.download_id,
                                        s.download_count))
                        results[lang].sort(
                            key=lambda x: x.download_count, reverse=True)
                        log.info('')
                    return results

                log.info('Sorry - could not find any matching subtitles')
                return None

            except TimeoutError:
                log.error('Error: Could not connect to OpenSubtitles.org')
                return None

            except TypeError:
                log.exception(
                             'Error: Are you sure you used a Video instance'
                             ' as a parameter?')
                return None

    def download_subtitle(self, video, sub_result):
        if self.logged_in and sub_result is not None:
            try:
                sub_id = sub_result.download_id
                self.query_result = self.xml_rpc.DownloadSubtitles(
                    self.user_token, [sub_id])
                sub = zlib.decompress(base64.b64decode(
                    self._extract_data('data')[0]['data']), 16 +
                    zlib.MAX_WBITS).decode('utf-8')
                sub_filename = "{path}.{lang}.{ext}".format(
                    path=os.path.join(video.directory, video.file_name[:-4]),
                    lang=sub_result.lang_id, ext='srt')
                sub_file = open(
                    sub_filename, 'w', encoding='utf-8', newline='')
                sub_file.write(sub)
                sub_file.close()

            except TimeoutError:
                log.error('Error: Could not connect to OpenSubtitles.org')

            except UnicodeDecodeError:
                log.error(
                    'Error: Could not decode downloaded subtitle to UTF-8'
                    ' character encoding')

            except TypeError:
                log.exception(
                    'Error: Are you sure you are using Video and SubResult'
                    ' instances as parameters?')
