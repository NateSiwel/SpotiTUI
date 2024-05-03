import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import time
import threading

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
 

class Display():
    def __init__(self, scr, spot):
        self.scr = scr
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.curs_set(0)
        
        self.main_win = curses.newwin(curses.LINES - 5, curses.COLS, 0, 0)
        self.main_win.clear()
        self.height, self.width = scr.getmaxyx()

        self.spot = spot    

    def get_command(self):
        self.command = ""
        win_height = 3
        win_width = self.width
        win_y = self.height - win_height
        win_x = 0
        self.command_win = curses.newwin(win_height, win_width, win_y, win_x)

        self.command_win.attron(curses.color_pair(1))
        self.command_win.attroff(curses.color_pair(1))

        self.command_win.border()
        curses.curs_set(1)

        start_x = 1
        start_y = 1
        max_width = win_width - 2  # Subtract 2 to account for the border

        prompt = " > "
        self.command_win.addstr(start_y, start_x, prompt, curses.color_pair(2))
        self.command_win.refresh()

        while True:
            max_width = win_width - 2
            key = self.command_win.getch()
            if key == curses.KEY_ENTER or key == ord('\n'):
                break
            elif key == curses.KEY_BACKSPACE or key == ord('\b') or key == 127:
                if len(self.command) > 0:
                    self.command = self.command[:-1]
            else:
                self.command += chr(key)

            self.command_win.border()  # Redraw the border

            self.command_win.addstr(start_y, start_x + len(prompt), " " * (20 - len(prompt)))

            # Truncate the command if it exceeds the maximum width
            display_command = self.command[-max_width+len(prompt):]

            self.command_win.addstr(start_y, start_x, prompt + display_command, curses.color_pair(2))
            self.command_win.refresh()

        curses.curs_set(0)

        return self.command

    def display_error(self, error_message):
        if error_message is None:
            return
        
        error_lines = (error_message + '\n\nPress any key to continue').split('\n')

        win_height = len(error_lines) + 2 
        win_width = self.width
        win_y = 0
        win_x = 0

        error_win = curses.newwin(win_height, win_width, win_y, win_x)
        error_win.attron(curses.color_pair(1))  # Use color pair 1 for error messages
        error_win.attroff(curses.color_pair(1))
        error_win.border()

        for i, line in enumerate(error_lines):
            error_win.addstr(1 + i, 2, line[:win_width - 4], curses.color_pair(1))

        error_win.refresh()
        error_win.getch()  # Wait for a key press before closing the error window
        error_win.clear()
        error_win.refresh()

    def show_currently_playing(self):
        dict = self.spot.get_currently_playing()
        if dict is None:
            return
        progress_ms = dict['progress_ms']
        is_playing = dict['is_playing']

        album_name = dict['item']['album']['name']
        album_art = dict['item']['album']['images'][0]

        artists_object = dict['item']['album']['artists']

        duration_ms = dict['item']['duration_ms']
        name = dict['item']['name']

        # Display the track name and artists
        self.main_win.delch(0, 0)
        self.main_win.addstr(0, 0, f"Now Playing: \"{name}\"", curses.color_pair(1))

        self.main_win.delch(1, 0)
        self.main_win.addstr(1, 0, f"Artists: {', '.join([artist['name'] for artist in artists_object])}", curses.color_pair(2))

        # Display the album name
        self.main_win.addstr(3, 0, f"Album: {album_name}", curses.color_pair(2))

        # Display the progress bar
        progress_percent = progress_ms / duration_ms
        progress_width = int(progress_percent * (curses.COLS - 15))
        self.main_win.delch(5, 0)
        self.main_win.addstr(5, 0, "Progress: [" + "=" * progress_width + ">" + " " * (curses.COLS - 15 -  progress_width) + "]", curses.color_pair(2))

        # Display the playback status
        status = "Playing" if is_playing else "Paused"

        self.main_win.delch(7, 0)
        self.main_win.addstr(7, 0, f"Status: {status}", curses.color_pair(2))

        self.main_win.refresh()

    def show_search(self, data):
        self.main_win.delch(12, 0)
        self.main_win.delch(13, 0)
        self.main_win.addstr(12, 0, "\n".join(
        song['name'] + " - " + ", ".join(artist['name'] for artist in song['artists'])
            for song in data['tracks']['items']
        ), curses.color_pair(2))
        self.main_win.refresh()


def main(scr):
    spot = Spotify()
    display = Display(scr, spot) 
    quit_flag = False
    curses.noecho()
    
    def handle_input():
        nonlocal quit_flag
        commands = {
            'quit': handle_quit,
            'pause': handle_pause,
            'play': handle_play,
            'search': handle_search
        }
        while not quit_flag:
            command = display.get_command().strip()

            if ' ' in command:
                cmd, params = command.split(' ', 1)
                cmd = cmd.strip()
                params = params.strip()
            else:
                cmd = command
                params = None

            if cmd in commands:
                if params is not None:
                    commands[cmd](params)
                else:
                    commands[cmd]()
            else:
                display.display_error(f"Unknown command: {cmd}")

    def handle_quit():
        nonlocal quit_flag
        quit_flag = True

    def handle_pause():
        ret = spot.pause_playback()
        clear_command_win()
        if ret is not None:
            display.display_error(ret)

    def handle_play(query=None):
        if query is None:
            ret = spot.start_playback()
            if ret is not None:
                display.display_error(ret)
            clear_command_win()
            return

        ret = spot.search(query)
        if ret is not None:
            if 'tracks' in ret:
                track_uri = ret['tracks']['items'][0]['uri']
                spot.start_playback(uris=[track_uri])
        return
        
    def handle_search(query):
        ret = spot.search(query)
        display.show_search(ret)
        clear_command_win()
                 

    def clear_command_win():
        display.command_win.clear()
        display.command_win.refresh()

    def update_screen():
        nonlocal quit_flag
        while not quit_flag:
            
            display.show_currently_playing()
            time.sleep(1) 

    update_thread = threading.Thread(target=update_screen) 
    input_thread = threading.Thread(target=handle_input)

    update_thread.start()
    input_thread.start()

    update_thread.join()
    input_thread.join()

if __name__ == '__main__':
    wrapper(main) 
