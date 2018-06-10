#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 28 00:22:55 2018

@author: loiccoyle
"""

import sys,os
import curses
import curses.panel
from chardet import detect
import numpy as np
import signal
import locale
import time
import subprocess

locale.setlocale(locale.LC_ALL, '')
encoding = lambda x: detect(x)['encoding']

ship_path        = 'Ship.ascii'
invader_path     = 'Invader.ascii'
projectile_path  = 'Projectile.ascii'
projectile_inv_path  = 'Projectile_inv.ascii'


sounds = 'sounds/'
shoot_sound = 'sounds/Shoot 2.wav'
boom_sound  = 'sounds/Explosion 2.wav' 
hit_sound   = 'sounds/Hit 1.wav'

shot_path = 'shot/'

title_path = 'title/1' 

class Ship:
   def __init__(self,path=None,x=0,y=0,speed=1,uprate=0.01,color='blue',life=3,rof=1,shoot_sound=shoot_sound):
      self.x         = x
      self.y         = y
      self.color     = color
      self.life      = 3
      self.speed     = speed
      self.uprate    = uprate
      self.rof       = rof
      self.last_move = 0
      self.last_shot = 0
      self.shoot_sound = shoot_sound
      if path != None :
         self.LoadArray(path)   
   def LoadArray(self,path):
      lines=[]
      with open(path,'r',encoding='utf-8') as ship :
         for line in ship:
            lines.append(line.rstrip('\n'))
      self.lines =lines      
      ship_array = np.chararray((len(lines),len(lines[0])),unicode=True)
      for i in range(ship_array.shape[0]):
         for j in range(ship_array.shape[1]):
            ship_array[i][j] = lines[i][j]      
      self.charar = ship_array
   def Shape(self):
      return self.charar.shape   
   def MoveLeft(self):
      self.x = self.x - self.speed
      self.last_move=time.time()
   def MoveRight(self):
      self.x = self.x + self.speed
      self.last_move=time.time()
   def Moveable(self):
      if time.time() - self.last_move > self.uprate : 
         return True
      else :
         return False
   def Shootable(self):
      if time.time() - self.last_shot > self.rof : 
         return True
      else :
         return False   
   

class Projectile:
   def __init__(self,x,y,speed=1,uprate=0.01,color='red',direction='up',path=None):
      self.x         = x
      self.y         = y
      self.speed     = speed
      self.color     = color
      self.direction = direction
      self.uprate    = uprate
      self.last_move = 0
      
      if path != None : # if a file is pecified, otherwise a simple box projectile
         self.LoadArray(path)
         
         
      else : 
         self.lines = ['▀']
         charar = np.chararray((1,1),unicode=True)
         charar[0,0] = '▀'
         self.charar = charar
#         self.win   = curses.newwin(self.Shape()[0]+1,self.Shape()[1],self.y,self.x)
#         self.panel = curses.panel.new_panel(self.win)
#         self.win.addstr(0,0,'▀',curses.color_pair(colors[self.color]))
         
   def Draw(self):
      self.win   = curses.newwin(self.Shape()[0]+1,self.Shape()[1],self.y,self.x)
      self.panel = curses.panel.new_panel(self.win)
      for i in range(self.Shape()[0]):
             self.win.addstr(i,0,self.lines[i],curses.color_pair(colors[self.color]))
             
   def LoadArray(self,path):
      lines=[]
      with open(path,'r',encoding='utf-8') as inv :
         for line in inv:
            lines.append(line.rstrip('\n'))
      self.lines =lines      
      proj_array = np.chararray((len(lines),len(lines[0])),unicode=True)
      for i in range(proj_array.shape[0]):
         for j in range(proj_array.shape[1]):
            proj_array[i][j] = lines[i][j]      
      self.charar = proj_array
   def Move(self):
      if self.direction == 'up':
         self.y=self.y-self.speed
      if self.direction == 'down':
         self.y=self.y+self.speed
      self.last_move = time.time()
      return self.x, self.y
   def Moveable(self):
      if time.time() - self.last_move > self.uprate : 
         return True
      else :
         return False
   def Shape(self):
      return self.charar.shape
      
   
class Invader:
   def __init__(self,x=0,y=0,path=None,speed=1,uprate=0.1,color='red',direction='right',bottom=False,rof=1):
      self.x         = x
      self.y         = y
      self.color     = color
      self.speed     = speed
      self.direction = direction
      self.uprate    = uprate
      self.last_move = 0
      self.alive     = True
      self.bottom    = bottom
      self.rof       = rof
      if path != None :
         self.LoadArray(path)
         self.win   = curses.newwin(self.Shape()[0]+1,self.Shape()[1],self.y,self.x)
         self.panel = curses.panel.new_panel(self.win)
   def LoadArray(self,path):
      lines=[]
      with open(path,'r',encoding='utf-8') as inv :
         for line in inv:
            lines.append(line.rstrip('\n'))
      self.lines =lines      
      inv_array = np.chararray((len(lines),len(lines[0])),unicode=True)
      for i in range(inv_array.shape[0]):
         for j in range(inv_array.shape[1]):
            inv_array[i][j] = lines[i][j]      
      self.charar = inv_array
   def Shape(self):
      return self.charar.shape
   def Move(self,fake=False):
      if fake :
         if self.direction == 'left':
            return self.x-self.speed,self.y
         if self.direction == 'right':
            return self.x+self.speed,self.y
      else :
         if self.direction == 'left':
            self.x=self.x-self.speed
         if self.direction == 'right':
            self.x=self.x+self.speed
         self.last_move = time.time()
#         return self.x, self.y
   def MoveDown(self):
      self.y = self.y + 1
      self.last_move = time.time()
   def Moveable(self):
      if time.time() - self.last_move > self.uprate : 
         return True
      else :
         return False
   def ChangeDirection(self,direction):
      self.direction=direction
   def Shoot(self):
      thresh = self.uprate/self.rof
      draw = np.random.uniform(0,1)
      if draw<thresh : 
         return True
      else : return False
   def ChangeRate(self,delta):
      self.uprate = self.uprate + delta
      
class Animation:
   def __init__(self,x,y,path=None,uprate=0.2,frame=0,color='white'):
      self.x      = x
      self.y      = y
      self.uprate = uprate
      self.last_draw = 0
      self.frame  = frame
      self.end    = False
      self.color  = color
      if path != None :
         self.LoadArray(path)
   def LoadArray(self,path):
      lines=[]
      for file in os.listdir(path):
         frame=[]
         with open(path+file,'r',encoding='utf-8') as inv :
            for line in inv:
               frame.append(line.rstrip('\n'))
         lines.append(frame)
      self.lines = lines
      self.draw  = self.lines[0]
      self.win   = curses.newwin(self.Shape()[0]+1,self.Shape()[1],self.y,self.x)
      self.panel = curses.panel.new_panel(self.win)
   def Draw(self):
      if not self.end: 
         self.draw = self.lines[self.frame]
         self.frame = self.frame + 1
         self.last_draw = time.time()
         if self.frame == len(self.lines) : self.end = True
   def Drawable(self):
      if time.time() - self.last_draw > self.uprate : 
         return True
      else :
         return False
   def Shape(self):
      return (len(self.lines[0]),len(self.lines[0][0]))
      

class Menu:
   def __init__(self,x,y,text=None,function=None):
      self.x=x
      self.y=y
      self.entries=[]
      self.selected=0
      self.spacing=3
#      self.args = *args
      if text != None:
         self.AddEntry(text,function)
   def MoveDown(self):
      if self.selected+1 < len(self.entries):
         self.selected = self.selected + 1
   def MoveUp(self):
      if self.selected-1 >= 0:
         self.selected = self.selected - 1
   def AddEntry(self,text,function=None):
      dic = {'text':text,'fun':function}
      self.entries.append(dic)
   def Run(self):
      if self.entries[self.selected]['fun'] != None :
         return self.entries[self.selected]['fun']()

class Fade :
   def __init__(self,x,y,path,uprate=0.1):
      self.x=x
      self.y=y
      self.column = 0
      self.LoadArray(path)
      self.last_draw = 0
      self.uprate = uprate
   def LoadArray(self,path):
      lines=[]
      with open(path,'r',encoding='utf-8') as inv :
         for line in inv:
            lines.append(line.rstrip('\n'))
      self.lines = lines
      self.draw  = self.lines[0]
      self.win   = curses.newwin(self.Shape()[0]+1,self.Shape()[1],self.y,self.x)
      self.panel = curses.panel.new_panel(self.win)
      inv_array = np.chararray((len(lines),len(lines[0])),unicode=True)
      for i in range(inv_array.shape[0]):
         for j in range(inv_array.shape[1]):
            inv_array[i][j] = lines[i][j]      
      self.charar = inv_array
   def Draw(self):
      self.last_draw = time.time()
      if self.column + 1 < len(self.lines[0]):
         self.column = self.column + 1
   def Drawable(self):
      if time.time() - self.last_draw > self.uprate : 
         return True
      else :
         return False
   def Shape(self):
      return (len(self.lines),len(self.lines[0]))

def Menu_exit():
   return 'exit'
def Menu_play():
   return 'play'

def playsound(sound):
   subprocess.Popen(['aplay','-q',sound],shell=False,stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL)

# very rudimentary collision detection, can be improved if > >
def collision_detect(elem1,elem2) :
   for e1 in elem1:
      for e2 in elem2:
         #quicker but more annoying to do the x>x>x method
         if ((e1.x in range(e2.x,e2.x+e2.Shape()[1]) or e1.x+e1.Shape()[1]-1 in range(e2.x,e2.x+e2.Shape()[1])) and
             (e1.y in range(e2.y,e2.y+e2.Shape()[0]) or e1.y+e1.Shape()[0]-1 in range(e2.y,e2.y+e2.Shape()[0]))):
            yield [e1,e2]
             
# catches Ctrl+C to clean exit especially to reset kbd rate
class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True

def RowApply(row,f):
   for i in row : 
      f(i)

def start(stdscr):
   stdscr.clear()
   curses.start_color()
   stdscr.nodelay(1)
   curses.curs_set(0)
   
   height, width = stdscr.getmaxyx()
   stdscr.border()
   
   inmenu = True
   menu = Menu(width//2,height//2,text='Play',function=Menu_play)
   menu.AddEntry('Customize')
   menu.AddEntry('Exit',function=Menu_exit)
   
   curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
   event = 0
   
   title = Fade(3,3,title_path,uprate=0.01)
   title.x = width//2 - title.Shape()[1]//2
   
   while inmenu :
      
      for j,i in enumerate(title.charar[:,title.column]):
         stdscr.addstr(title.y+j,title.x+title.column,title.charar[j,title.column])
      if title.Drawable():
         title.Draw()
      
      if event == curses.KEY_DOWN:
         menu.MoveDown()
      if event == curses.KEY_UP:
         menu.MoveUp()
      if event == ord('\n'):
#         stdscr.addstr(10,10,'m')
         out = menu.Run()
         if out == 'play' : inmenu = False ; state = out
         if out == 'custom' : inmenu = True ; state = out
         if out == 'exit' : inmenu = False ; state = out
      
      for i,e in enumerate(menu.entries) :
         if i == menu.selected:
            stdscr.addstr(menu.y+menu.spacing*i,menu.x,e['text'],curses.color_pair(3))
         else :
            stdscr.addstr(menu.y+menu.spacing*i,menu.x,e['text'])
      
      stdscr.refresh()
      event = stdscr.getch()
   return state

def play(stdscr):
    os.system('xset r rate 1')
    killer = GracefulKiller()
    
    k = 0
    
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
    curses.init_pair(1, curses.COLOR_WHITE,   curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED,     curses.COLOR_BLACK) 
    curses.init_pair(3, curses.COLOR_BLUE,    curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN,   curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW,  curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_CYAN,    curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    
    #this is the background color I guess
    curses.init_pair(8, curses.COLOR_BLACK,   curses.COLOR_BLACK)
    
    # color dict
    global colors
    colors = {'white'  :1,
              'red'    :2,
              'blue'   :3,
              'green'  :4,
              'yellow' :5,
              'cyan'   :6,
              'magenta':7,
              'black'  :8}
    inv_colors = {v: k for k, v in colors.items()}
    
    # Initialization
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    
    shots        = []
    invaders     = []
    animations   = []
    invader_shots = []
    
    ship = Ship(path=ship_path,y=height-4,speed=1,rof=0.5)
    w = curses.newwin(ship.Shape()[0],ship.Shape()[1]+1,ship.y,ship.x)
    p = curses.panel.new_panel(w)
    for i in range(ship.Shape()[0]):
       w.addstr(i,0,ship.lines[i],curses.color_pair(colors[ship.color]))
    
    
    #Spawn invaders
    invaders = []
    n_rows = 4
    for row_i in range(n_rows):
       if row_i == n_rows - 1 : bottom = True
       else : bottom = False
       y_row = 4*row_i+2
       row = []
       for col,x_inv in enumerate(range(0,width-50,7)):
   #    invaders.append(Invader(path=invader_path,x=50,y=5,speed=1,uprate=1))
          row.append(Invader(path=invader_path,x=x_inv,y=y_row,speed=1,uprate=0.1,
                             bottom=bottom,color=inv_colors[(col)%7+1]))
       invaders.append(row)
    for row in invaders :
       for inv in row :
          for i in range(inv.Shape()[0]):
             inv.win.addstr(i,0,inv.lines[i],curses.color_pair(colors[inv.color]))
              
    # Loop where k is the last character pressed
    while (k != ord('q')):
#        time.sleep(0.01)
        if killer.kill_now:
           os.system('xset r rate 500')
           break
        if k == curses.KEY_DOWN:pass
        elif k == curses.KEY_UP:pass
        elif k == curses.KEY_RIGHT and ship.Moveable() :
            if ship.x + ship.Shape()[1] + ship.speed < width :
               ship.MoveRight()
               if len(animations) > 0 :
                  for a in animations :
                     a.panel.move(a.y,ship.x+ship.Shape()[1]//2-a.Shape()[1]//2)
        elif k == curses.KEY_LEFT and ship.Moveable() :
            if ship.x - ship.speed >= 0 :
               ship.MoveLeft()
               if len(animations) > 0 :
                  for a in animations :
                     a.panel.move(a.y,ship.x+ship.Shape()[1]//2-a.Shape()[1]//2)
            
        # Declaration of strings
        statusbarstr = "Press 'q' to exit | STATUS BAR "

        # Centering calculations
#        start_x_keystr = int((width // 2) - (len(keystr) // 2) - len(keystr) % 2)
#        start_y = int((height // 2) - 2)

        # Render status bar
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(height-1, 0, statusbarstr)
        stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
        stdscr.attroff(curses.color_pair(3))

        # Shooting logic
        if k == curses.KEY_MOUSE and ship.Shootable() :
           ship.last_shot = time.time()
#           _,mx,my,_,_ = curses.getmouse()
#           stdscr.addstr(5,5,str(bstate))
#           if bstate == curses.BUTTON1_PRESSED :
#           shots.append(Projectile(mx,my,direction='up',speed=1,))))))))uprate=0.5))
           playsound(ship.shoot_sound)
           temp_proj = Projectile(ship.x+ship.Shape()[1]//2,ship.y,direction='up',
                                   speed=1,uprate=0.2,path=projectile_path)
           
           temp_proj.x = ship.x + ship.Shape()[1]//2 - temp_proj.Shape()[1]//2
           temp_proj.y = ship.y - temp_proj.Shape()[0]
           temp_proj.Draw()
           
           shots.append(temp_proj)
           animations.append(Animation(ship.x+2,ship.y-2,path=shot_path))
        

        for s in shots :
           if s.Moveable() :
              if s.y-s.speed < 0 or s.y + s.speed >= height-1:
                 s.win.erase()
                 s.panel.hide()
                 shots.remove(s)
#                 stdscr.addstr(s.y,s.x,' ',curses.color_pair(1))
                 continue
              s.panel.top()
              s.Move()
              s.panel.move(s.y,s.x)
              
        for s in invader_shots :
           if s.Moveable() :
              if s.y-s.speed < 0 or s.y + s.speed >= height-1:
                 s.win.erase()
                 s.panel.hide()
                 invader_shots.remove(s)
#                 stdscr.addstr(s.y,s.x,' ',curses.color_pair(1))
                 continue
              s.panel.bottom()
              s.Move()
              s.panel.move(s.y,s.x)

        for a in animations : 
          if a.end : 
             a.win.erase()
             a.panel.hide()
             animations.remove(a)
          else :
             if a.Drawable():
                a.Draw()
                a.panel.bottom()
                for i in range(a.Shape()[0]):
                   a.win.addstr(i,0,a.draw[i],curses.color_pair(colors[a.color]))


        # Invader movement logic
        for row in invaders :
           if row[0].direction == 'right':
              inv = row[-1]
           if row[0].direction == 'left':
              inv = row[0]
           i_x,i_y = inv.Move(fake=True)
           if i_y < height - 10 and inv.Moveable(): 
              if i_x <= 0 or i_x + inv.Shape()[1] >= width :
                 if i_x <= 0 :
   #                    inv.direction='right'
                    RowApply(row,lambda x : x.ChangeDirection('right'))
                    RowApply(row,lambda x : x.MoveDown())
   #                    inv.MoveDown()
                 elif i_x + inv.Shape()[1] >= width:
                    RowApply(row,lambda x : x.ChangeDirection('left'))
                    RowApply(row,lambda x : x.MoveDown())
                 
#                 for i in invaders:
#                    for j in i:
#                       j.ChangeRate(-0.005)
                 RowApply(row,lambda x : x.ChangeRate(-0.005))
                 stdscr.addstr(0,0,str(inv.uprate))
                 playsound(hit_sound)
              else:
                 RowApply(row,lambda x : x.Move())
#                    inv.Move()
        for row in invaders : 
           for inv in row :
              inv.panel.move(inv.y,inv.x)
              #invader shooting
              if inv.alive and inv.Shoot() and inv.bottom and inv.Moveable():
                 temp_proj = Projectile(0,0,direction='down',
                                   speed=1,uprate=0.2,path=projectile_inv_path,color=inv.color)
                 temp_proj.x = inv.x + inv.Shape()[1]//2 - temp_proj.Shape()[1]//2
                 temp_proj.y = inv.y + temp_proj.Shape()[0]
                 temp_proj.Draw()
                 invader_shots.append(temp_proj)
                 
                 
        #collision detection
        #improvement : checking collision on dead invaders
        for row_i,row in enumerate(invaders) : 
           collided = collision_detect(shots,row)
           for element in collided :
              if not element[1].alive : continue
              playsound(boom_sound)
              element[1].win.erase()
              element[1].panel.hide()
              element[1].alive = False
              #this finds the new bottom invader
              if element[1].bottom :
                 column = row.index(element[1])
                 for j in range(len(invaders)):
                    if invaders[j][column].alive : bottom_row = j
                 invaders[bottom_row][column].bottom = True
                 if column == 0: stdscr.addstr(5,0,str(bottom_row))
#                 while not invaders[row_i-1][column].alive : 
#                    row_i = row_i-1
#                 invaders[row_i-1][column].bottom=True

              # this removes invaders, creates non uniform row movement
#              row.remove(element[1])
#              if len(row) == 0 : invaders.remove(row)
              element[0].win.erase()
              element[0].panel.hide()
              shots.remove(element[0])
              
        p.move(ship.y,ship.x)
        curses.panel.update_panels()
        
        # Refresh the screen
        stdscr.refresh()
        # get next input
        k = stdscr.getch()

def main():
   state = 'start'
   if state == 'start' :
      state = curses.wrapper(start)
   if state == 'play' : 
      state = curses.wrapper(play)


if __name__ == "__main__":
   
   main()
   os.system('xset r rate 500')

   
