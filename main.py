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
            'search': handle_search,
            'skip': handle_skip,
            'queue': add_to_queue,
            'mix': mix 
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
        display.clear_command_window()
        ret = spot.pause_playback()
        if ret is not None:
            display.display_error(ret)

    def handle_play(query=None):
        display.clear_command_window()
        if query is None:
            ret = spot.start_playback()
            if ret is not None:
                display.display_error(ret)
            return

        ret = spot.search(query)
        if ret is not None:
            if 'tracks' in ret:
                track_uri = ret['tracks']['items'][0]['uri']
                spot.start_playback(uris=[track_uri])
        return
        
    def handle_search(query):
        display.clear_command_window()
        ret = spot.search(query)
        display.show_search(ret)

    def handle_skip():
        display.clear_command_window()
        ret = spot.next_track()
        if ret is not None:
            display.display_error(ret)
 
    def add_to_queue(query):
        display.clear_command_window()
        ret = spot.search(query)
        if ret is not None:
            if 'tracks' in ret:
                track_uri = ret['tracks']['items'][0]['uri']
                spot.add_to_queue(uri=track_uri)

    def mix(query):
        display.clear_command_window()
        uri = spot.search(query)['tracks']['items'][0]['uri']
        ret = spot.recommendations(seed_tracks=[uri])
        track_uris = [track['uri'] for track in ret['tracks']]
        if uri not in track_uris:
            track_uris.append(uri)
        offset = {"uri": uri}
        spot.start_playback(uris=track_uris, offset=offset)
        
        


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
