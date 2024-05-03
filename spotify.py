import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

class Spotify():
    def __init__(self):
        self.sp =  spotipy.Spotify(auth_manager=SpotifyOAuth(
                                          client_id=os.getenv('SPOTIPY_CLIENTID'),
                                          client_secret=os.getenv('SPOTIPY_CLIENTSECRET'),
                                          redirect_uri="http://localhost:3000",
                                          scope=["user-read-playback-state", "user-modify-playback-state"]))

    def get_currently_playing(self):
        results = self.sp.currently_playing()
        return results

    def pause_playback(self):
        try:
            self.sp.pause_playback()
        except spotipy.SpotifyException as e:
            return str(e)
        return None
    
    def start_playback(self, uris=None):
        try:
            if uris is None:
                self.sp.start_playback()
            else:
                self.sp.start_playback(uris=uris)
        except spotipy.SpotifyException as e:
            return str(e)
        return None
    
    def search(self,search):
        try:
            ret = self.sp.search(search)
        except spotipy.SpotifyException as e:
            return str(e)
        return ret 
 

