import curses

from tegmail import Event


class Interface(object):

    def __init__(self):
        self.on_key_event = Event()
        self.menu_box = None
        self.main_box = None
        self.info_box = None
        self._keys = {
            13: 'KEY_ENTER',
            127: 'KEY_BACKSPACE',
            258: 'KEY_DOWN',
            259: 'KEY_UP',
            260: 'KEY_LEFT',
            261: 'KEY_RIGHT',
        }

        self._init_curses()

    def _init_curses(self):
        self._stdscr = curses.initscr()
        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()
        curses.nonl()
        self._stdscr.keypad(True)
        self._stdscr.refresh()

        # set custom color pairs
        # TODO check COLORS for number of
        # supported pairs
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, -1, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_BLUE, -1)
        curses.init_pair(5, curses.COLOR_CYAN, -1)
        curses.init_pair(6, curses.COLOR_YELLOW, -1)
        curses.init_pair(7, curses.COLOR_MAGENTA, -1)

        self.menu_box = curses.newwin(1, curses.COLS, 0, 0)
        self.main_box = curses.newwin(curses.LINES - 2, curses.COLS, 1, 0)
        self.info_box = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)

        self.main_box.idlok(1)
        self.main_box.scrollok(True)

    def _exit_curses(self):
        curses.curs_set(1)
        curses.echo()
        curses.nocbreak()
        curses.nl()
        self._stdscr.keypad(False)
        curses.endwin()

    def _format_key(self, i):
        if i in self._keys:
            key = self._keys[i]
        else:
            key = chr(i)
        return key

    def update(self):
        getch = self._stdscr.getch()
        key = self._format_key(getch)

        self.on_key_event(key)

    def close(self):
        self._exit_curses()

    def clear(self, win=None):
        if not win:
            win = self.main_box

        win.erase()
        win.refresh()

    def print_text(self, text, win=None):
        if not win:
            win = self.main_box

        win.addstr(text)
        win.refresh()

    def get_cursor_pos(self, win=None):
        if not win:
            win = self.main_box

        return win.getyx()

    # move_cursor(y_direction)
    # move_cursor(y, x)
    def move_cursor(self, *args, **kwargs):
        if len(args) == 1:
            yx = self.main_box.getyx()
            y = yx[0] + args[0]
            x = yx[1]
        elif len(args) == 2:
            y = args[0]
            x = args[1]

        if (y < self.main_box.getbegyx()[0] - 1 or
                x > self.main_box.getmaxyx()[0] - 1):
            return

        self.main_box.chgat(curses.color_pair(1))
        self.main_box.move(y, x)
        self.main_box.chgat(curses.A_REVERSE)
        self.main_box.refresh()
