import PyQt5
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QAction, QMenu, QSystemTrayIcon
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QCoreApplication, QPoint, QObject, QThread, pyqtSignal,QTimer, QEvent
import random
import sys
import time
from math import cos, sin, atan2
import os 
import pyautogui
import mouse
import configparser

from win32api import GetMonitorInfo, MonitorFromPoint

'''TO - DO
- fix sliding bug and code in proper friction
- port variables over to config file
- change all global variables to OOP (maybe)

'''

monitor_info = GetMonitorInfo(MonitorFromPoint((0,0)))
monitor_area = monitor_info.get("Monitor")
work_area = monitor_info.get("Work")


impath = os.getcwd()+'\\animations'
idle = impath+'\\idle.png'
dleft = impath+'\\dragleft.png'
dright = impath+'\\dragright.png'
dfleft = impath +'\\dragfarleft.png'
dfright = impath+'\\dragfarright.png'
walkleft = [impath+'\\{}.png'.format(i) for i in 'run1 run2 run3'.split()]
walkright = [impath+'\\{}.png'.format(i) for i in 'run4 run5 run6'.split()]
fall = impath+'\\fall.png'
jump = [impath+'\\{}.png'.format(i) for i in 'jump1 jump2 jump3'.split()]

cycle = 0 #frame 0
action = 0
animlength = 0
frame = idle

#projectile motion
startingpos = (0,0)
cursorpos = (0,0)
xvelocity = 0
yvelocity = 0
angle = 0
t = 1
acceleration = 0

#sizing
monitorwidth, monitorheight = pyautogui.size()
taskbarheight = monitor_area[3]-work_area[3]
ground = monitorheight-taskbarheight-120

def readConfig():
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(os.getcwd()+'\\config.ini')
    configDict = dict(config._sections)
    for section in configDict.keys():
        for key in configDict[section].keys():
            if configDict[section][key] == 'True':
                configDict[section][key] = True
            if configDict[section][key]=='False':
                configDict[section][key] = False
    print(configDict)
    return configDict

    

def writeConfig(configDict):
    config = configparser.ConfigParser()
    config.optionxform = str
    for section in configDict.keys():
        config.add_section(section)
        for key in configDict[section].keys():
            config.set(section, key, str(configDict[section][key]))

        with open(os.getcwd()+'\\config.ini', 'w') as f:
            config.write(f)


def animate(cycle,frames):
    if cycle < len(frames)-1:
        cycle+=1
    else:
        cycle = 0
    frame = frames[cycle]
    return cycle,frame

def getAngle(x,y):
    return atan2(-y,x)

def getDisplacement(oldx,oldy):
    gravity = 0.5 #placeholder
    global startingpos #x,y
    global xvelocity
    global yvelocity
    global angle
    global t
    global monitorwidth
    global ground
    if startingpos[0] > monitorwidth-64:
        startingpos = (monitorwidth-64, startingpos[1])
        

    x = startingpos[0] + xvelocity*t*cos(angle)
    y = startingpos[1] - yvelocity*t*sin(angle) + 0.5*gravity*(t**2)

    t+=1
    if x < -10: #left wall bounce
        if angle >0:
            angle = 3.14 - angle 
        else:
            angle = -3.14+angle
        x = -10
        startingpos = (x,y)
        xvelocity *= 0.7
        yvelocity*=0.7

        t= min(3,t//2)
        x = startingpos[0] + xvelocity*t*cos(angle)
        y = startingpos[1] - yvelocity*t*sin(angle) + 0.5*gravity*(t**2)

    
    if x >= monitorwidth-64: #half of sprite width
        if angle >0:
            angle = 3.14 - angle 
        else:
            angle = -3.14+angle
        x = monitorwidth-64-10
        startingpos = (x,y)
        xvelocity *= 0.7
        yvelocity*=0.7
        t=min(3, t//2)
        x = startingpos[0] + xvelocity*t*cos(angle)
        y = startingpos[1] - yvelocity*t*sin(angle) + 0.5*gravity*(t**2)
        



    if y > ground:
        y = ground

    if y <-10000: #anti yeet into space measure
        startingpos = (x,-100)
        t = 1
        angle = -3.14/2
    if y <-100:
        t+=2

    return (x,y)

def getJumpHeight(): #x,y
    #0 means going up
    #1 means going down
    global startingpos 
    global t
    global cursorpos
    #a(x-h)^2+k
    #h = x
    #k = y
    k = cursorpos[1]
    h = cursorpos[0] - startingpos[0]
    a = -k/(h**2)
    t1 = t-k 


    #get t of max point
    #get in terms of parabolic equation
    #x = h+-sqrt(t/a), where - is upwards and + is downwards
    #jump to right
    if cursorpos[0] > startingpos[0]:
        if t1<0: #going up
            x = h-(t1/a)**0.5 + startingpos[0]
            y = t1+k
            t+= max(-t1*0.05, 1)
        else: #going down
            t2 = k-t
            y = t2 + k 
            x = h+(t2/a)**0.5 + startingpos[0]
            t+= max(-t2*0.025,1)
    else: #jump to left
        if t1<0: #going up
            x = h+(t1/a)**0.5 + startingpos[0]
            y = t1+k
            t+= max(-t1*0.05, 1)
        else: #going down
            t2 = k-t
            y = t2 + k 
            x = h-(t2/a)**0.5 + startingpos[0]
            t+= max(-t2*0.025,1)
        
    #might need to add a constant based on starting position of randy
    #y = t+k
    #return coordinates
    #print(x,y)
    y = round(startingpos[1] - y)
    global ground
    if y > ground:
        y = ground
    if x < -10:
        x = -10
    global monitorwidth 
    if x > monitorwidth -84:
        x = monitorwidth-84

    return (x,y)


class DesktopPet(QWidget):
    def __init__(self, parent = None, **kwargs):
        super(DesktopPet,self).__init__(parent)
        self.setWindowFlags(
            self.windowFlags() |
            Qt.FramelessWindowHint|
            Qt.WindowStaysOnTopHint|
            Qt.SubWindow|
            Qt.WindowMinimizeButtonHint)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()



        self.setGeometry(10,10,128,128)
        self.image = QLabel(self)
        self.image.setPixmap(QPixmap(idle))

        global monitorwidth 
        global ground 
        self.move(monitorwidth*0.6,ground)



        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showMenu)


        oldPos = QPoint()

        #settings
        self.config = readConfig()
        self.settings = self.config["SETTINGS"]

        #flags/variables
        self.stealingCursor = False #if is stealing cursor

        #info storage
        self.cursorhistory = [(0,0),0]


        self.timer = QTimer()
        self.timer.timeout.connect(self.RandyAction)
        self.timer.start(0.1)

        self.yeettimer = QTimer()
        self.yeettimer.timeout.connect(self.Yeet)

        self.leaptimer = QTimer()
        self.leaptimer.timeout.connect(self.Leap)

        self.cursorcam = QTimer()
        self.cursorcam.timeout.connect(self.captureCursor)
        self.cursorcam.start(1000)

        #self.installEventFilter(self)


    #def eventFilter(self, source, event):
        #return super(DesktopPet, self).eventFilter(source, event)


    def showMenu(self,event):
        menu = QMenu()
        menu.clear()


        if self.settings["walk"] == False:
            walk = menu.addAction("Be free!")
        else:
            walk = menu.addAction("Sit still!")
        
        cursorcatch = menu.addAction("Catch my cursor!")

        settingsMenu = menu.addMenu("Settings")
        
        if self.settings["gravity"] == True:
            gravity = settingsMenu.addAction("Disable Gravity")
        else:
            gravity = settingsMenu.addAction("Enable Gravity")

        if self.settings["cursorTheft"] == False:
            cursortheft = settingsMenu.addAction("Enable cursor stealing")
        else:
            cursortheft = settingsMenu.addAction("Disable cursor stealing")
        

        quit_action = menu.addAction("Quit")
        debug = menu.addAction("Debug")
        action = menu.exec_(self.mapToGlobal(event))

        if action == quit_action:
            #run offscreen
            self.settings["ongoingAction"] = True
            finished = False
            imageset = False
            global cycle
            global frame
            x = self.x()
            if x > monitorwidth//2: #right
                while x <= monitorwidth+100:
                    cycle, frame = animate(cycle,walkright)
                    x+=10
                    time.sleep(0.03)
                    self.image.setPixmap(QPixmap(frame))
                    self.repaint()
                    self.move(x, self.y())
                finished = True
            
            else:
                while x >= -100:
                    cycle, frame = animate(cycle,walkleft)
                    x-=10
                    time.sleep(0.03)
                    self.image.setPixmap(QPixmap(frame))
                    self.repaint()
                    self.move(x, self.y())
                finished = True

            #quit
            if finished:
                QCoreApplication.instance().quit()

        if action == cursorcatch:
            self.settings["ongoingAction"] = True
            self.leaptimer.start(1000)

        if action== gravity:
            self.settings["gravity"] = not self.settings["gravity"]
            writeConfig(self.config)
            if self.settings["gravity"] == True:
                self.settings["ongoingAction"] = True
                self.image.setPixmap(QPixmap(fall))
                self.repaint()
                global startingpos 
                startingpos = (self.x(),self.y())
                self.Yeet()

        if action == walk:
            self.settings["walk"] = not self.settings["walk"]
            self.image.setPixmap(QPixmap(idle))
            self.repaint()
            writeConfig(self.config)

        if action == cursortheft:
            self.settings["cursorTheft"] = not self.settings["cursorTheft"]
            writeConfig(self.config)

        if action == debug:
            pass 


    def mousePressEvent(self,event):
        self.oldPos = event.globalPos()
        if event.buttons() == Qt.LeftButton:
            #SOMEHOW this is needed so he doesn't freak out when you click on him
            global xvelocity 
            global yvelocity
            global startingpos
            xvelocity = 0 
            yvelocity=0
            startingpos = (self.x(),self.y()) 


            self.settings["ongoingAction"] = True
            self.yeettimer.stop()
    
    def mouseMoveEvent(self,event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos()-self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()


            global angle
            #global t
            global startingpos
            global xvelocity
            global yvelocity

            angle = getAngle(delta.x(),delta.y())
            xvelocity = abs(delta.x())
            yvelocity = abs(delta.y())

            #t = 1
            startingpos = (self.x(),self.y()) 

            

            if delta.x() <-2:
                self.image.setPixmap(QPixmap(dfleft))
            elif delta.x() < 0:
                self.image.setPixmap(QPixmap(dleft))
            elif delta.x() >2:
                self.image.setPixmap(QPixmap(dfright))
            else:
                self.image.setPixmap(QPixmap(dright))

    def mouseReleaseEvent(self,event):
        #self.settings["ongoingAction"] = False
        global t
        t=1
        if self.settings["ongoingAction"] == True:
            if self.settings["gravity"]:
                self.image.setPixmap(QPixmap(fall))
                self.repaint()
                self.Yeet()
            else:
                self.settings["ongoingAction"] = False
                self.image.setPixmap(QPixmap(idle))
                self.repaint()
                self.RandyAction()


    def Yeet(self):
        global ground
        if self.y() <ground and self.settings["ongoingAction"]:
            x,y = getDisplacement(self.x(),self.y())
            self.move(x,y)
            global t
            self.yeettimer.start(50/t+10)
        else:
            self.yeettimer.stop()
            self.image.setPixmap(QPixmap(fall))
            self.repaint()
            for i in range(5):
                x,y = getDisplacement(self.x(), self.y())
                if y!= ground:
                    y= ground
                if x - self.x() > 0:
                    x += min((x-self.x())*0.05*i, 10-i)
                else:
                    x += max((x-self.x())*0.05*i, i-10)
                self.move(x,y)
                time.sleep(0.02*5/t)
            if self.y() != ground:
                self.Yeet()

            self.settings["ongoingAction"] = False
            self.image.setPixmap(QPixmap(idle))
            self.repaint()
            self.RandyAction()

    def Leap(self): #only works for gravity enabled
        global t
        global startingpos 
        global cursorpos
        global ground
        global monitorheight

        if self.y()!=ground or t == 1 or t ==2 or t ==3:
            if t ==1: #play the first two frames
                startingpos = (self.x(), self.y())
                cursorpos = pyautogui.position()
                cursorpos = (cursorpos[0], monitorheight - cursorpos[1])
                self.image.setPixmap(QPixmap(jump[0]))
                self.repaint()
                t+=1
                self.leaptimer.setInterval(100)
            elif t == 2:
                self.image.setPixmap(QPixmap(jump[1]))
                self.repaint()
                t+=1    
            else:
                self.image.setPixmap(QPixmap(jump[2]))
                self.repaint()
                x,y = getJumpHeight()
                self.move(x,y)
                currentcursorpos = pyautogui.position()
                if currentcursorpos[0]+32 > x \
                    and currentcursorpos[0]<x+128\
                    and currentcursorpos[1]+32 > y\
                    and currentcursorpos[1]<y+128:

                    self.stealingCursor= True

                if self.stealingCursor == True and self.settings["cursorTheft"] == True:
                    mouse.move(x+64,y+64)
                self.leaptimer.setInterval(1)



        else:
            self.stealingCursor = False
            self.settings["ongoingAction"] = False 
            self.cursorhistory[1] = 0
            t = 1
            self.image.setPixmap(QPixmap(idle))
            self.repaint()
            self.leaptimer.stop()
            self.RandyAction()


    def captureCursor(self):
        #print(self.settings)
        cursorpos = pyautogui.position()
        if self.cursorhistory[0] == cursorpos:
            self.cursorhistory[1]+=1 #add 1 second to timer
        else:
            self.cursorhistory[0] = cursorpos  
            self.cursorhistory[1] = 0     #reset if cursor moves      


    def getRandyAction(self):
        if not self.settings["walk"]:
            return 0
        choices = [i for i in range(4)]
        if self.x() > 1408: #on the right
            choices.remove(2)
        elif self.x() <128: #on the left
            choices.remove(1)

        if self.y() < pyautogui.position()[1] or self.cursorhistory[1] <60: #if above cursor
            choices.remove(3)

        action = random.choice(choices)
        return action

    def RandyAction(self):
        if not self.settings["ongoingAction"] and self.settings["walk"]:
            global frame
            global animlength
            global action
            global cycle
            frame = idle
            x = self.x()
            if action == 0:
                animlength+=0.5

            elif action == 1:
                if x < 128:
                    animlength+=20
                else:
                    cycle, frame = animate(cycle, walkleft)
                    x-=10
                    animlength +=1

            elif action == 2:
                if x > 1408:
                    animlength+=20
                else:
                    cycle, frame = animate(cycle,walkright)
                    x+=10
                    animlength+=1
            
            elif action == 3:
                self.settings["ongoingAction"] = True
                self.leaptimer.start(0.1)
                animlength+=20


            time.sleep(0.05)
            if animlength >= 20:
                animlength = 0
                action = self.getRandyAction()
            self.image.setPixmap(QPixmap(frame))
            self.move(x, self.y())
        


class MainApp(QApplication):
    def __init__(self, args):
        super(MainApp, self).__init__(args)
        self.trayicon = QSystemTrayIcon(QIcon(impath + "\\randyicon.ico"))
        self.trayicon.show()

        self.menu = QMenu()
        self.trayicon.setContextMenu(self.menu)
        reset_action = self.menu.addAction("Reset Position", lambda: self.widget.move(monitorwidth*0.6,ground))
        quit_action = self.menu.addAction("Force Quit", lambda: QCoreApplication.instance().quit())



        self.widget = DesktopPet()
        self.widget.show()







if __name__ == '__main__':
    app = MainApp(sys.argv)


    sys.exit(app.exec_())
