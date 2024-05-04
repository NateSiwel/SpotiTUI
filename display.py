import curses
from art import *
import re
import time

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

    def clear_command_window(self):
        y, x = self.command_win.getyx()
        self.main_win.move(y, x)
        self.main_win.clrtoeol()


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

            self.command_win.border() 

            self.command_win.addstr(start_y, start_x + len(prompt), " " * (max_width - len(prompt)))

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
        name = re.sub(r'[-(\[].*', '', name)

        # Display the track name and artists
        song_name = text2art(name).splitlines()

        name_height = 1
        name_width = max(len(i) for i in song_name)
        if (name_width > self.width):
            name_width = len(name)
            song_name = name
            for y in range(6):
                self.main_win.move(y+1, 0)
                self.main_win.clrtoeol()
                name_height += 1 
            self.main_win.addstr((name_height//2)-1, ((self.width - name_width)//2), song_name)
        else:
            for y, line in enumerate(song_name, name_height):
                self.main_win.move(y, 0)
                self.main_win.clrtoeol()
                self.main_win.addstr(y, ((self.width - name_width)//2), line)
                name_height += 1

        self.main_win.move(name_height + 1, 0)
        self.main_win.clrtoeol()
        self.main_win.addstr(name_height + 1, 0, f"Artists: {', '.join([artist['name'] for artist in artists_object])}", curses.color_pair(2))

        # Display the album name
        self.main_win.move(name_height + 3, 0)
        self.main_win.clrtoeol()
        self.main_win.addstr(name_height + 3, 0, f"Album: {album_name}", curses.color_pair(2))

        # Display the progress bar
        progress = progress_ms / duration_ms
        bar_width = self.width - 10
        filled_blocks = int(progress * bar_width)
        progress_bar = "█" * filled_blocks + "░" * (bar_width - filled_blocks)
        elapsed_str = time.strftime("%M:%S", time.gmtime(progress_ms // 1000))
        remaining_str = time.strftime("%M:%S", time.gmtime((duration_ms - progress_ms) // 1000))

        self.main_win.move(name_height + 5, 0)
        self.main_win.clrtoeol()
        self.main_win.addstr(name_height + 5, 5, f"[{progress_bar}]")
        self.main_win.addstr(name_height + 6, 5, f"{elapsed_str} / {remaining_str}")
        self.main_win.addstr(name_height + 5, 1, "♪")

        # Display the playback status
        status = "Playing" if is_playing else "Paused"
        self.main_win.move(name_height + 8, 0)
        self.main_win.clrtoeol()
        self.main_win.addstr(name_height + 8, 0,status, curses.color_pair(2))

        self.main_win.refresh()

    def show_search(self, data):
        self.main_win.delch(12, 0)
        self.main_win.delch(13, 0)
        self.main_win.addstr(12, 0, "\n".join(
        song['name'] + " - " + ", ".join(artist['name'] for artist in song['artists'])
            for song in data['tracks']['items']
        ), curses.color_pair(2))
        self.main_win.refresh()
