from xmlrpc.client import ServerProxy, ProtocolError
from socket import gaierror
from components import TimedEvent
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

    def __del__(self, exc_type, exc_val, exc_tb):
        if self.logged_in:
            try:
                self.logout()
            except (gaierror, ProtocolError):  # Throw exception and exit if we can't connect to OpenSubtitles
                print("Error: Could not connect to OpenSubtitles.org")
                sys.exit(2)

    @property
    def logged_in(self):
        self.keep_alive_timer.reset()
        return self.__logged_in

    @logged_in.setter
    def logged_in(self, value):
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
                    print("Your session timed out, please use Login before doing anything else")
                else:
                    print("Staying alive...")
            except TimeoutError:  # Throw exception if we can't connect to OpenSubtitles
                print("Error: Could not connect to OpenSubtitles.org")
                return
