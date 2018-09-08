#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 28 00:22:55 2018

@author: loiccoyle
"""

#import sys
import os
import curses
import curses.panel
import signal
import locale
import time
import subprocess
import random
from chardet import detect
import numpy as np
from curses.textpad import Textbox, rectangle


locale.setlocale(locale.LC_ALL, '')


def ENCODING(x):
    '''gets the encoding'''
    return detect(x)['encoding']


SHIP_PATH = 'sprites/Ship.ascii'
INVADER_PATH = 'sprites/Invader.ascii'
PROJECTILE_PATH = 'sprites/Projectile.ascii'
PROJECTIL_INV_PATH = 'sprites/Projectile_inv.ascii'


SOUNDS = 'sounds/'
SHOOT_SOUND = SOUNDS + 'Shoot 2.wav'
BOOM_SOUND = SOUNDS + 'Explosion 2.wav'
HIT_SOUND = SOUNDS + 'Hit 1.wav'
SELECT_SOUND = SOUNDS + 'Select 1.wav'

SHOT_PATH = 'shot/'

TITLE_PATH = 'title/1'

COLOURS = {'white': 1,
           'red': 2,
           'blue': 3,
           'green': 4,
           'yellow': 5,
           'cyan': 6,
           'magenta': 7,
           'black': 8}


class Ship:
    '''
    Ship class, arguments :
       path: path to file to read ship from
       speed: how much to move per refresh
       uprate: limit how many times to refresh/s
       color: color of ship
       life: how many lifes (unused for now)
       rof: rate of fire
       shoot_sound: path to soudns file
    '''

    def __init__(self, path=None, x=0, y=0, speed=1, uprate=0.01, color='blue',
                 life=3, rof=1, shoot_sound=SHOOT_SOUND):
        self.x = x
        self.y = y
        self.color = color
        self.life = 3
        self.speed = speed
        self.uprate = uprate
        self.rof = rof
        self.last_move = 0
        self.last_shot = 0
        self.shoot_sound = shoot_sound
        if path is not None:
            self.LoadArray(path)

    def LoadArray(self, path):
        '''
        Laods the ship file into both lines array and char array
        '''
        lines = []
        with open(path, 'r', encoding='utf-8') as ship:
            for line in ship:
                lines.append(line.rstrip('\n'))
        self.lines = lines
        ship_array = np.chararray((len(lines), len(lines[0])), unicode=True)
        for i in range(ship_array.shape[0]):
            for j in range(ship_array.shape[1]):
                ship_array[i][j] = lines[i][j]
        self.charar = ship_array

    def Shape(self):
        '''
        returns the dimensions of the ship
        '''
        return self.charar.shape

    def MoveLeft(self):
        '''Moves left'''
        self.x = self.x - self.speed
        self.last_move = time.time()

    def MoveRight(self):
        '''Moves right'''
        self.x = self.x + self.speed
        self.last_move = time.time()

    def Moveable(self):
        '''returns true if the ship can move, false if not'''
        return time.time() - self.last_move > self.uprate

    def Shootable(self):
        '''returns true if the ship can shoot, false if not'''
        return time.time() - self.last_shot > self.rof


class Projectile:
    '''
    Class for the projectiles, arguments :
    speed: how much to move per refresh
    uprate: limit how many times to refresh/s
    color: color of projectile
    direction: projectile direction
    path: path of proctile file
    '''

    def __init__(self, x, y, speed=1, uprate=0.01, color='red', direction='up',
                 path=None):
        self.x = x
        self.y = y
        self.speed = speed
        self.color = color
        self.direction = direction
        self.uprate = uprate
        self.last_move = 0

        if path is not None:  # if a file is pecified, otherwise a simple box projectile
            self.LoadArray(path)
        else:
            self.lines = ['▀']
            charar = np.chararray((1, 1), unicode=True)
            charar[0, 0] = '▀'
            self.charar = charar

    def Draw(self):
        '''Draws the projectile to screen'''
        self.win = curses.newwin(
            self.Shape()[0] + 1,
            self.Shape()[1],
            self.y,
            self.x)
        self.panel = curses.panel.new_panel(self.win)
        for i in range(self.Shape()[0]):
            self.win.addstr(
                i, 0, self.lines[i], curses.color_pair(COLOURS[self.color]))

    def LoadArray(self, path):
        '''Laods the projectile path to array'''
        lines = []
        with open(path, 'r', encoding='utf-8') as inv:
            for line in inv:
                lines.append(line.rstrip('\n'))
        self.lines = lines
        proj_array = np.chararray((len(lines), len(lines[0])), unicode=True)
        for i in range(proj_array.shape[0]):
            for j in range(proj_array.shape[1]):
                proj_array[i][j] = lines[i][j]
        self.charar = proj_array

    def Move(self):
        '''Moves the projectile'''
        if self.direction == 'up':
            self.y = self.y - self.speed
        if self.direction == 'down':
            self.y = self.y + self.speed
        self.last_move = time.time()
        return self.x, self.y

    def Moveable(self):
        '''return true is projectile can move, false if not'''
        return time.time() - self.last_move > self.uprate

    def Shape(self):
        '''returns shape of prejectile'''
        return self.charar.shape


class Invader:
    '''
    Invader class, arguments :
       path: path to file to read ship from
       speed: how much to move per refresh
       uprate: limit how many times to refresh/s
       color: color of ship
       direction: direction of movement, left or right
       bottom: boolean true if the invader is at the bottom of a column, false
       otherwise
       rof: rate of fire
    '''
    def __init__(self, x=0, y=0, path=None, speed=1, uprate=0.1, color='red',
                 direction='right', bottom=False, rof=1):
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed
        self.direction = direction
        self.uprate = uprate
        self.last_move = 0
        self.alive = True
        self.bottom = bottom
        self.rof = rof
        if path is not None:
            self.LoadArray(path)
            self.win = curses.newwin(
                self.Shape()[0] + 1, self.Shape()[1], self.y, self.x)
            self.panel = curses.panel.new_panel(self.win)

    def LoadArray(self, path):
        '''
        Laods the ship file into both lines array and char array
        '''
        lines = []
        with open(path, 'r', encoding='utf-8') as inv:
            for line in inv:
                lines.append(line.rstrip('\n'))
        self.lines = lines
        inv_array = np.chararray((len(lines), len(lines[0])), unicode=True)
        for i in range(inv_array.shape[0]):
            for j in range(inv_array.shape[1]):
                inv_array[i][j] = lines[i][j]
        self.charar = inv_array

    def Shape(self):
        '''
        returns the dimensions of the ship
        '''
        return self.charar.shape

    def Move(self, fake=False):
        '''
        Moves the projectile if fake then don't update but return next coords
        '''
        if fake:
            if self.direction == 'left':
                return self.x - self.speed, self.y
            if self.direction == 'right':
                return self.x + self.speed, self.y
        else:
            if self.direction == 'left':
                self.x = self.x - self.speed
            if self.direction == 'right':
                self.x = self.x + self.speed
            self.last_move = time.time()

    def MoveDown(self):
        '''Moves the invader down'''
        self.y = self.y + 1
        self.last_move = time.time()

    def Moveable(self):
        '''returns true if can move, false otherwise'''
        return time.time() - self.last_move > self.uprate

    def ChangeDirection(self, direction):
        '''changes direction'''
        self.direction = direction

    def Shoot(self):
        '''shoots randomly, true if shoot'''
        thresh = self.rof*self.uprate #self.uprate / self.rof
#        np.random.seed(seed=int(time.time()))
        draw = np.random.uniform(0, 1)
        return draw < thresh

    def ChangeRate(self, delta):
        '''change the uprate'''
        new_rate = self.uprate - delta*self.uprate
        if new_rate < 0.016:
            pass
        else:
            self.uprate = new_rate


class Animation:
    '''
    Animation class, arguments:
        path: path to folder containing frames
        uprate: refresh rate
        frame: frame # currently at
        color: color of draw
    '''
    def __init__(self, x, y, path=None, uprate=0.2, frame=0, color='white'):
        self.x = x
        self.y = y
        self.uprate = uprate
        self.last_draw = 0
        self.frame = frame
        self.end = False
        self.color = color
        if path is not None:
            self.LoadArray(path)

    def LoadArray(self, path):
        '''
        Laods the ship file into both lines array and char array
        '''
        lines = []
        for file in os.listdir(path):
            frame = []
            with open(path + file, 'r', encoding='utf-8') as inv:
                for line in inv:
                    frame.append(line.rstrip('\n'))
            lines.append(frame)
        self.lines = lines
        self.draw = self.lines[0]
        self.win = curses.newwin(
            self.Shape()[0] + 1,
            self.Shape()[1],
            self.y,
            self.x)
        self.panel = curses.panel.new_panel(self.win)

    def Draw(self):
        '''draw logic, frame sequence'''
        if not self.end:
            self.draw = self.lines[self.frame]
            self.frame = self.frame + 1
            self.last_draw = time.time()
            if self.frame == len(self.lines):
                self.end = True

    def Drawable(self):
        '''returns true is drawalbe, false otherwise'''
        return time.time() - self.last_draw > self.uprate

    def Shape(self):
        '''returns the shape of the frame'''
        return (len(self.lines[0]), len(self.lines[0][0]))


class Menu:
    '''
    Menu class, arguments:
        text: text label written to screen
        functopn: function called when run
    '''
    def __init__(self, x, y, text=None, function=None):
        self.x = x
        self.y = y
        self.entries = []
        self.selected = 0
        self.spacing = 3
#        self.args = *args
        if text is not None:
            self.AddEntry(text, function)

    def MoveDown(self, sound=None):
        '''moves the selected entry down'''
        if self.selected + 1 < len(self.entries):
            self.selected = self.selected + 1
            if sound is not None:
                playsound(sound)

    def MoveUp(self, sound=None):
        '''moves the selected entry up'''
        if self.selected - 1 >= 0:
            self.selected = self.selected - 1
            if sound is not None:
                playsound(sound)

    def AddEntry(self, text, function=None):
        '''adds entry to menu'''
        dic = {'text': text, 'fun': function}
        self.entries.append(dic)

    def Run(self, sound=None):
        '''runs the function'''
        if self.entries[self.selected]['fun'] is not None:
            if sound is not None:
                playsound(sound)
            return self.entries[self.selected]['fun']()


class Fade:
    '''
    Fade class, arguments:
        path: path to file
        uprate: update rate
    '''
    def __init__(self, x, y, path, uprate=0.1):
        self.x = x
        self.y = y
        self.column = 0
        self.LoadArray(path)
        self.last_draw = 0
        self.uprate = uprate

    def LoadArray(self, path):
        '''
        Laods the ship file into both lines array and char array
        '''
        lines = []
        with open(path, 'r', encoding='utf-8') as inv:
            for line in inv:
                lines.append(line.rstrip('\n'))
        self.lines = lines
        self.draw = self.lines[0]
        self.win = curses.newwin(
            self.Shape()[0] + 1,
            self.Shape()[1],
            self.y,
            self.x)
        self.panel = curses.panel.new_panel(self.win)
        inv_array = np.chararray((len(lines), len(lines[0])), unicode=True)
        for i in range(inv_array.shape[0]):
            for j in range(inv_array.shape[1]):
                inv_array[i][j] = lines[i][j]
        self.charar = inv_array

    def Draw(self):
        '''moves one column'''
        self.last_draw = time.time()
        if self.column + 1 < len(self.lines[0]):
            self.column = self.column + 1

    def Drawable(self):
        '''return true if drawable, false oherwise'''
        return time.time() - self.last_draw > self.uprate

    def Shape(self):
        '''returns the shape of the array'''
        return (len(self.lines), len(self.lines[0]))


def Menu_exit():
    '''returns the exit game state'''
    return 'exit'


def Menu_play():
    '''returns the play game state'''
    return 'play'


def Menu_custom():
    '''returns the custom game state'''
    return 'custom'


def Menu_start():
    '''returns the start game state'''
    return 'start'


def playsound(sound):
    '''plays a sound through popen'''
    subprocess.Popen(['aplay', '-q', sound], shell=False,
                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)


def collision_detect(elem1, elem2):
    '''
    very rudimentary collision detection,  can be improved if > >
    '''
    for e1 in elem1:
        for e2 in elem2:
            # quicker but more annoying to do the x>x>x method
            if ((e1.x in range(e2.x, e2.x + e2.Shape()[1]) or
                 e1.x + e1.Shape()[1] - 1 in range(e2.x, e2.x + e2.Shape()[1])) and
                    (e1.y in range(e2.y, e2.y + e2.Shape()[0]) or
                     e1.y + e1.Shape()[0] - 1 in range(e2.y, e2.y + e2.Shape()[0]))):
                yield [e1, e2]


class GracefulKiller:
    '''
    catches Ctrl+C to clean exit especially to reset kbd rate
    '''
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


def RowApply(row, f):
    '''apply function f on a iteratable row'''
    for i in row:
        f(i)

def Shot_mvt(shot_tab,height,zorder='bottom'):

    for s in shot_tab:
        if s.Moveable():
            if s.y - s.speed < 0 or s.y + s.speed >= height - 1:
                s.win.erase()
                s.panel.hide()
                shot_tab.remove(s)
#                 stdscr.addstr(s.y, s.x, ' ', curses.color_pair(1))
                continue
            if zorder == 'bottom':
                s.panel.bottom()
            if zorder == 'top':
                s.panel.top()
            s.Move()
            s.panel.move(s.y, s.x)
    return shot_tab

def start(stdscr):
    '''
    title splash screen and start menu
    '''
    os.system('xset r rate 500')
    stdscr.clear()
    curses.start_color()
    stdscr.nodelay(1)
    curses.curs_set(0)

    height, width = stdscr.getmaxyx()
    stdscr.border()

    inmenu = True
    menu = Menu(width // 2, height // 2, text='Play', function=Menu_play)
    menu.AddEntry('Customize', function=Menu_custom)
    menu.AddEntry('Exit', function=Menu_exit)

    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    event = 0

    title = Fade(3, 3, TITLE_PATH, uprate=0.01)
    title.x = width // 2 - title.Shape()[1] // 2

    while inmenu:
        for j, i in enumerate(title.charar[:, title.column]):
            stdscr.addstr(title.y + j, title.x + title.column,
                          title.charar[j, title.column])
        if title.Drawable():
            title.Draw()

        if event == curses.KEY_DOWN:
            menu.MoveDown()
        if event == curses.KEY_UP:
            menu.MoveUp()
        if event == ord('\n'):
            #         stdscr.addstr(10, 10, 'm')
            out = menu.Run()
#         if out == 'play':
#            inmenu = False
#            state = out
#         if out == 'custom':
#            inmenu = False
#            state = out
#         if out == 'exit':
#            inmenu = False
#            state = out
            state = out
            inmenu = False

        for i, e in enumerate(menu.entries):
            if i == menu.selected:
                stdscr.addstr(
                    menu.y + menu.spacing * i,
                    menu.x,
                    e['text'],
                    curses.color_pair(3))
            else:
                stdscr.addstr(menu.y + menu.spacing * i, menu.x, e['text'])

        stdscr.refresh()
        event = stdscr.getch()
    return state


def custom(stdscr):
    '''
    custom menu screen
    '''
    curses.cbreak()
    stdscr.clear()
    curses.start_color()
    stdscr.nodelay(1)
    curses.curs_set(0)
    height, width = stdscr.getmaxyx()
    stdscr.border()
    inmenu = True
    menu_pos = (width // 10, height // 3)
    stdscr.addstr(menu_pos[1] - 3, menu_pos[0], '~= Assets =~')
    menu = Menu(menu_pos[0], menu_pos[1])

    event = 0

    ncols, nlines = width // 2 - 3, height - 4
    uly, ulx = 2, width // 2
    rectangle(stdscr, uly - 1, ulx - 1, uly + nlines, ulx + ncols)

    sprites = os.listdir('sprites/')
#   stdscr.addstr(2, 2, sprites[0])
    for spr in sprites:
        menu.AddEntry(spr)
    menu.AddEntry('< Back', function=Menu_start)

    while inmenu:
        if event == curses.KEY_DOWN:
            menu.MoveDown()
        if event == curses.KEY_UP:
            menu.MoveUp()
        if event == ord('\n'):
            out = menu.Run()
            if out == 'start':
                inmenu = False
                state = out
                break

            curses.curs_set(1)
            win = curses.newwin(nlines, ncols, uly, ulx)

            # instructions
            stdscr.addstr(uly - 2, ulx, 'Press Ctrl+g to leave editor')
            stdscr.refresh()
            file = 'sprites/' + menu.entries[menu.selected]['text']
            with open(file, 'r') as sprite:
                k = 0
                for line in sprite:
                    win.addstr(k, 0, line)
                    k += 1
            box = Textbox(win, insert_mode=False)
            content = box.edit()
#         content = box.gather()
            stdscr.addstr(2, 2, content)
            with open('test', 'w', encoding='utf-8') as out:
                out.write(content)

            # clears the instructions
            stdscr.addstr(uly - 2, ulx, '                            ')
            stdscr.border()

            del win
            stdscr.touchwin()
            stdscr.refresh()
#         rectangle.erase()
            curses.curs_set(0)

        for i, e in enumerate(menu.entries):
            if i == menu.selected:
                stdscr.addstr(
                    menu.y + menu.spacing * i,
                    menu.x,
                    e['text'],
                    curses.color_pair(3))
            else:
                stdscr.addstr(menu.y + menu.spacing * i, menu.x, e['text'])

        stdscr.refresh()
        event = stdscr.getch()

    return state


def play(stdscr):
    '''
    main game
    '''
    os.system('xset r rate 1')
    killer = GracefulKiller()

    k = 0
    score = 0

#    curses.halfdelay(1)
    curses.mousemask(True)
    curses.mouseinterval(5)
    curses.curs_set(0)

    # Clear and refresh the screen for a blank canvas
    stdscr.nodelay(1)
#    curses.halfdelay(3)

    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)

    # this is the background color I guess
    curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_BLACK)

    # color dict
    global COLOURS

    inv_colors = {v: k for k, v in COLOURS.items()}

    # Initialization
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    shots = []
    invaders = []
    animations = []
    invader_shots = []

    ship = Ship(path=SHIP_PATH, y=height - 4, speed=1, rof=0.5)
    w = curses.newwin(ship.Shape()[0], ship.Shape()[1] + 1, ship.y, ship.x)
    p = curses.panel.new_panel(w)
    for i in range(ship.Shape()[0]):
        w.addstr(i, 0, ship.lines[i], curses.color_pair(COLOURS[ship.color]))

    # Spawn invaders
    invaders = []
    n_rows = 4
    for row_i in range(n_rows):
        bottom = bool(row_i == n_rows - 1)
        y_row = 4 * row_i + 2
        row = []
        for col, x_inv in enumerate(range(0, width - 50, 7)):
            #    invaders.append(Invader(path=INVADER_PATH, x=50, y=5, speed=1, uprate=1))
            row.append(Invader(path=INVADER_PATH,
                               x=x_inv,
                               y=y_row,
                               speed=1,
                               uprate=0.1,
                               rof=1,
                               bottom=bottom,
                               color=inv_colors[(col) % 7 + 1]))
        invaders.append(row)
    for row in invaders:
        for inv in row:
            for i in range(inv.Shape()[0]):
                inv.win.addstr(
                    i, 0, inv.lines[i], curses.color_pair(COLOURS[inv.color]))

    # Loop where k is the last character pressed
    while k != ord('q'):
        if killer.kill_now: # if user ctrl+c then reset keyboard rate and leave
            os.system('xset r rate 500')
            break
        if k == curses.KEY_DOWN:
            pass
        elif k == curses.KEY_UP:
            pass
        elif k == curses.KEY_RIGHT and ship.Moveable():
            if ship.x + ship.Shape()[1] + ship.speed < width:
                ship.MoveRight()
                if animations:
                    for a in animations:
                        a.panel.move(a.y, ship.x + ship.Shape()
                                     [1] // 2 - a.Shape()[1] // 2)
        elif k == curses.KEY_LEFT and ship.Moveable():
            if ship.x - ship.speed >= 0:
                ship.MoveLeft()
                if animations:
                    for a in animations:
                        a.panel.move(a.y, ship.x + ship.Shape()
                                     [1] // 2 - a.Shape()[1] // 2)

        # Declaration of strings
        statusbarstr = "Press 'q' to exit | Score : {} | Lifes : {}".format(score,ship.life)

        # Render status bar
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(height - 1, 0, statusbarstr)
        stdscr.addstr(height - 1, len(statusbarstr), " " *
                      (width - len(statusbarstr) - 1))
        stdscr.attroff(curses.color_pair(3))

        # Shooting logic
        if k == curses.KEY_MOUSE and ship.Shootable():
            ship.last_shot = time.time()
#           _, mx, my, _, _ = curses.getmouse()
#           if bstate == curses.BUTTON1_PRESSED:
            playsound(ship.shoot_sound)
            temp_proj = Projectile(
                ship.x + ship.Shape()[1] // 2,
                ship.y,
                direction='up',
                speed=1,
                uprate=0.2,
                path=PROJECTILE_PATH)

            temp_proj.x = ship.x + \
                ship.Shape()[1] // 2 - temp_proj.Shape()[1] // 2
            temp_proj.y = ship.y - temp_proj.Shape()[0]
            temp_proj.Draw()

            shots.append(temp_proj)
            animations.append(
                Animation(
                    ship.x + 2,
                    ship.y - 2,
                    path=SHOT_PATH))

        shots = Shot_mvt(shots,height,zorder='top')
        invader_shots = Shot_mvt(invader_shots,height,zorder='bottom')

        for a in animations:
            if a.end:
                a.win.erase()
                a.panel.hide()
                animations.remove(a)
            else:
                if a.Drawable():
                    a.Draw()
                    a.panel.bottom()
                    for i in range(a.Shape()[0]):
                        a.win.addstr(
                            i, 0, a.draw[i], curses.color_pair(COLOURS[a.color]))

        # Invader movement logic
#        for row in invaders: # take the most left or right invader
        k = -1
        while True not in [i.alive for i in invaders[k]
                           ]:  # find row with at least one invader alive
            k = k - 1
        row = invaders[k]
        if row[0].direction == 'right':
            inv = row[-1]
        if row[0].direction == 'left':
            inv = row[0]
        i_x, i_y = inv.Move(fake=True)  # get the coords of next step
        if inv.Moveable():  # if above the 10
            if i_x <= 0 or i_x + \
                    inv.Shape()[1] >= width:  # left & right side detection
                if i_x <= 0:
                    for row in invaders:
                        RowApply(row, lambda x: x.ChangeDirection('right'))
                elif i_x + inv.Shape()[1] >= width:
                    for row in invaders:
                        RowApply(row, lambda x: x.ChangeDirection('left'))
                if i_y < height - 10:
                    for row in invaders:
                        RowApply(row, lambda x: x.MoveDown())

                # update rate
                for row in invaders:
                    RowApply(row, lambda x: x.ChangeRate(0.05))
                stdscr.addstr(0, 0, str(inv.uprate))
                playsound(HIT_SOUND)
            else:  # otherwise just move
                for row in invaders:
                    RowApply(row, lambda x: x.Move())

        for row in invaders:  # draw on new position
            for inv in row:
                inv.panel.move(inv.y, inv.x)
                # invader shooting
                if inv.bottom and inv.Moveable() and inv.alive and inv.Shoot():
                    temp_proj = Projectile(
                        0,
                        0,
                        direction='down',
                        speed=1,
                        uprate=0.2,
                        path=PROJECTIL_INV_PATH,
                        color=inv.color)
                    temp_proj.x = inv.x + \
                        inv.Shape()[1] // 2 - temp_proj.Shape()[1] // 2
                    temp_proj.y = inv.y + temp_proj.Shape()[0]
                    temp_proj.Draw()
                    invader_shots.append(temp_proj)
                    stdscr.addstr(10,10,str(len(invader_shots)))
        # collision detection
        # improvement: checking collision on dead invaders: done !
        for row_i, row in enumerate(invaders):
            row_alive_invaders =  [i for i in row if i.alive]
            if row_alive_invaders:
                collided = collision_detect(shots,row_alive_invaders)
                for element in collided:
                    if not element[1].alive:
                        continue
                    playsound(BOOM_SOUND)
                    element[1].win.erase()
                    element[1].panel.hide()
                    element[1].alive = False
                    score += 10
                    # this finds the new bottom invader
                    if element[1].bottom:
                        column = row.index(element[1])
                        for j,_ in enumerate(invaders):
                            if invaders[j][column].alive:
                                bottom_row = j
                        invaders[bottom_row][column].bottom = True
                        if column == 0:
                            stdscr.addstr(5, 0, str(bottom_row))
                    element[0].win.erase()
                    element[0].panel.hide()
                    shots.remove(element[0])
            else:
                invaders.remove(row)

        #Ship collision logic
        collided = collision_detect(invader_shots,[ship])
        for element in collided:
            element[1].life -= 1
            #here is trigger for death sequence
            element[0].win.erase()
            element[0].panel.hide()
            invader_shots.remove(element[0])


        p.move(ship.y, ship.x)
        curses.panel.update_panels()

        # Refresh the screen
        stdscr.refresh()
        # get next input
        k = stdscr.getch()
    return 'start'


def main():
    '''entry point'''
    state = 'start'
    while state != 'exit':
        if state == 'start':
            state = curses.wrapper(start)
        if state == 'custom':
            state = curses.wrapper(custom)
        if state == 'play':
            state = curses.wrapper(play)


if __name__ == "__main__":
    main()
    os.system('xset r rate 500')
