import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle
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
                                          scope="user-read-playback-state"))

    def get_currently_playing(self):
        results = self.sp.currently_playing()
        return results

    
class Display():
    def __init__(self, scr):
        self.scr = scr 
        self.scr.clear()
    
    def show_currently_playing(self,dict):
        progress_ms = dict['progress_ms'] 
        is_playing = dict['is_playing']

        album_name = dict['item']['album']['name']
        album_art = dict['item']['album']['images'][0]

        artists_object = dict['item']['album']['artists']

        duration_ms = dict['item']['duration_ms']
        name = dict['item']['name']
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)

        self.scr.addstr(8, 0, f"\"{name}\" by {', '.join([artist['name'] for artist in artists_object])} is currently playing", curses.color_pair(1))

        self.scr.refresh()
        self.scr.getkey()

    def run(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)

        curses.noecho()
        self.scr.refresh()

        editwin = curses.newwin(5, 30, 2, 1)
        rectangle(self.scr, 1, 0, 1+5+1, 1+30+1)
        self.scr.refresh()

        box = Textbox(editwin)
        box.edit()
        message = box.gather()

        self.scr.addstr(8, 0, f"{message}", curses.color_pair(1))
        self.scr.getkey()



def main(scr):
    spot = Spotify()
    currently_playing_ret = spot.get_currently_playing()
    display = Display(scr) 
    #display.run()
    
    display.show_currently_playing(currently_playing_ret)
       

if __name__ == '__main__':
    wrapper(main) 
