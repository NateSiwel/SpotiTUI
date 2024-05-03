import curses
from curses import wrapper
import time
import threading
from spotify import Spotify
from display import Display
from spotipy import SpotifyException

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
            
            try: 
                display.show_currently_playing()
                time.sleep(1) 
            except SpotifyException as e:
                display.display_error(str(e))


    update_thread = threading.Thread(target=update_screen) 
    input_thread = threading.Thread(target=handle_input)

    update_thread.start()
    input_thread.start()

    update_thread.join()
    input_thread.join()

if __name__ == '__main__':
    wrapper(main) 
