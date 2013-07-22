# -*- coding: utf-8 -*-
""" "THE BEER-WARE LICENSE" (Revision 42):
 * Matti Eiden <snaipperi@gmail.com> wrote this file. As long as you retain this notice you
 * can do whatever you want with this stuff. If we meet some day, and you think
 * this stuff is worth it, you can buy me a beer in return.
"""
import pygame, sys, time, socket
import celestialdata, kepler, views
from numpy import array, degrees

FONT = None

class System:
    def __init__(self):
        self.network = Network(self)
        self.display = None
        self.celestials = {}
        self.vessels = {}
        self.UT = 0
        self.temp = []
        
        f = open("celestial.txt","w")
        f.close()

    def parse(self,data):
        #print "PARSE:",data
        tok = data.split('\t')
        vType = tok[0]   # Type, should be V
        if vType == "V":
            vStatus = tok[1] # Status (flying, etc.)
            vPID = tok[2]    # Unique ID
            vT = tok[3]      # Game time
            self.UT = float(vT)
            
            vRV = tok[4]
            vMT = tok[5]     # Mission time
            vAcc =  tok[6]   # Acceleration magnitude
            vAlt = tok[7]    # Altitude
            vAnM = tok[8]    # Angular momentum
            vAnV = tok[9]    # Angular velocity
            vAtm = tok[10]    # Atmosphere density
            vGF  = tok[11]   # Gee force
            vGFi = tok[12]   # Geefore immediate
            vRAlt = tok[13]  # Height from surface (altitude?)
            vRAlt2 = tok[14] # Height from terrain (radar altimeter)
            vHor = tok[15]   # Horizontal surface spee d
            vLat = tok[16]   # Latitude
            vLon = tok[17]   # Longitude
            print "vlat",vLat
            print "vlon",vLon
            vOVel = tok[18]  # Orbital velocity
            vPQSAlt = tok[19]# PQS altitude ?
            vRBVel = tok[20] # RB velocity?
            vSPAcc = tok[21] # Specific accceleration
            vSVel = tok[22]  # Surface velocity (horizontal?)
            vSPrs = tok[23]  # Static pressure
            vTAlt = tok[24]  # Terrain altitude
            vVVel = tok[25]  # Vertical speed
            vDPrs = tok[26]  # Dynamic pressure (atm)
            vSPrs2 = tok[27] # Static pressure (atm)
            vTemp = tok[28]  # Temperature
            
            print "Status:",vStatus
            print "Velocity:",vSVel
            print "Altitude:",vAlt
            print "Pressure:",vSPrs
            print "Dynamic pressure:",vDPrs
            print "SAlt:",vRAlt
            print "TAlt:",vRAlt2
            if vStatus == "L" or vStatus == "S" or vStatus == "P" or vStatus == "F":
                vRef = tok[29]
            else:
                vRef = tok[29]
                vOEph = tok[30]
                vOSma = tok[31]
                VOEcc = tok[32]
                VOInc = tok[33]
                VOLAN = tok[34]
                VOAoP = tok[35]
                VOM0 = tok[36]
                
            rv = vRV.split(':')
            trv = [0.0,array([float(rv[0]), float(rv[1]), float(rv[2])]), array([float(rv[3]), float(rv[4]), float(rv[5])])]
            self.temp.append((vPID,trv))
            
            
        elif vType == "C":
            #print "Celestial data"
            f = open("celestial.txt","a")
            f.write(data + "\n")
            f.close()
            
            name = tok[1]
            ref = tok[2]
            rv = tok[3]
            mu = tok[4]
            radius = tok[5]
            SoI = tok[6]
            atm = tok[7]
            
            if name == "Sun":
                self.celestials[name] = celestialdata.Sun(mu=float(mu),radius=float(radius))
            else:
                if atm == "None":
                    atm = False
                else:
                    atm = float(atm)
                rv = rv.split(':')
                trv = [0.0,array([float(rv[0]), float(rv[1]), float(rv[2])]), array([float(rv[3]), float(rv[4]), float(rv[5])])]
                self.celestials[name] = celestialdata.Planet(self.celestials[ref],name,mu=float(mu),radius=float(radius),SoI=float(SoI),trv=trv,atm=atm)
                if name == "Eeloo":
                    self.display.viewPlot.draw()
                
            if name == "Kerbin":
                for vessel in self.temp:
                    self.vessels[vessel[0]] = celestialdata.Vessel(self.celestials["Kerbin"],vessel[0],trv=vessel[1])
                self.display.viewGroundTrack.draw()
            
            
            

class Display:
    def __init__(self,system,width=800,height=600):
        pygame.init()
        
        self.font = pygame.font.Font("unispace.ttf",12)
        views.FONT = self.font
        global FONT
        FONT = self.font
        
        
        self.system = system
        self.system.display = self
        
        self.basewidth = width
        self.baseheight = height
        
        self.window = pygame.display.set_mode((self.basewidth, self.baseheight),pygame.RESIZABLE)
        
        # The monitor is always 800x600, 4:3
        self.monitor = pygame.Surface((self.basewidth,self.baseheight))
        self.scaledmonitor = pygame.Surface((self.basewidth, self.baseheight))
        
        self.viewGroundTrack = views.GroundTrack(self,(800,300))
        self.viewPlot = views.Plot(self,(400,300))
        self.viewData = views.MainMenu(self,(400,300))
        
        self.focus = None
        
        self.transformWidth = self.basewidth
        self.transformHeight = self.baseheight
        self.transformCenterWidth = 0
        self.transformCenterHeight = 0
        self.lastTick = time.time()
        
        self.x = 30
        
        #self.font = pygame.font.match_font("consolas")
        #self.font = pygame.font.Font(self.font,12)
        
        self.icon = pygame.image.load("icon.png")
        pygame.display.set_icon(self.icon)
        pygame.display.set_caption("KSP Mission Control")
        
        self.map_kerbin = pygame.image.load("maps/kerbin.png")
        self.viewGroundTrack.blit(self.map_kerbin,(0,0))
        
        self.render_data()
        
        
    
    def recalculate_transforms(self):
        ''' Calculates window stretching to maintain aspect ratio '''
        sw = float(self.window.get_width())
        sh = float(self.window.get_height())
        
        if sw/sh >= 1.333333333:
            self.transformHeight = int(sh)
            self.transformWidth = int(640 * (sh / 480.0))
        else:
            self.transformWidth = int(sw)
            self.transformHeight = int(480 * (sw / 640))
        
        self.transformCenterWidth = int((sw-self.transformWidth)/2)
        self.transformCenterHeight = int((sh-self.transformHeight)/2)
            
    def render_groundTrack(self):
        self.viewGroundTrack.fill((0,0,0))
        self.viewGroundTrack.blit(self.map_kerbin,(0,0))
        
    def render_data(self):
        #self.viewData.fill((0,0,0))
        pass
        
        #self.viewData.blit(cstr1,(0,0))
        #self.viewData.testButton()
        
        
    def getRpos(self,pos):
        ''' Get relative position in the 800x600 window '''
        print pos
        x = int((pos[0] - self.transformCenterWidth) / float(self.window.get_width()) * 800)
        y = int((pos[1] - self.transformCenterHeight)/ float(self.window.get_height()) * 600)
        print (x,y)
        return (x,y)
        
    def getCanvas(self,rpos):
        x,y = rpos
        if x < 400 and y < 300:
            return (self.viewPlot,(x,y))
        elif x >= 400 and y < 300:
            return (self.viewData,(x-400,y))
        else:
            return (self.viewGroundTrack,(x,y-300))
        
        
    def mainloop(self):
        ''' Mainloop. Attempts to stay at 20fps '''
        
        while True:
            self.monitor.fill((255,255,255))

            self.monitor.blit(self.viewPlot,(0,0))
            self.monitor.blit(self.viewData,(400,0))
            self.monitor.blit(self.viewGroundTrack,(0,300))
            
            # Event categories that should be post-processed
            postprocess_clicks = []
            postprocess_motion = []
            
            
            for event in pygame.event.get():
                
                if event.type == pygame.MOUSEMOTION:
                    postprocess_motion.append(event)
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    postprocess_clicks.append(event)
                
                # In case of window resize, calculate new window requirements to maintain 4:3 aspect ratio
                elif event.type == pygame.VIDEORESIZE:
                    self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    self.recalculate_transforms()
                    self.scaledmonitor = pygame.Surface((self.transformWidth,self.transformHeight))                
                
                
                elif event.type in (pygame.QUIT, pygame.KEYDOWN):
                    sys.exit()
                    
                # Button click hilight event (used to dehilight)
                elif event.type == pygame.USEREVENT+1:
                    if event.canvas.activeButton:
                        event.canvas.activeButton.render(event.canvas,True)
                    
            for event in postprocess_motion:
                canvas,rpos = self.getCanvas(self.getRpos(event.pos))
                canvas.motion(rpos)
                
                # Defocus old canvas
                if canvas != self.focus:
                    if self.focus:
                        self.focus.defocus()
                    self.focus = canvas
                    
            for event in postprocess_clicks:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    canvas,rpos = self.getCanvas(self.getRpos(event.pos))
                    canvas.click(rpos)
                    
            self.system.network.recv()
            
            self.window.fill((0,0,0))
            pygame.transform.scale(self.monitor,(self.transformWidth,self.transformHeight),self.scaledmonitor)
            
            self.window.blit(self.scaledmonitor,(self.transformCenterWidth,self.transformCenterHeight))
            
            pygame.display.flip()
            #print self.window.get_size()
            
            newtick = time.time() 
            sleep = 0.05-(newtick-self.lastTick)
            #print "fps:",1/(newtick-self.lastTick)
            if sleep>0:    
                time.sleep(sleep)
            else:
                print "Warning: lagging"
            self.lastTick = time.time()
    
class Network:
    def __init__(self,system):
        self.socket = None
        self.buffer = ''
        self.system = system
        
    def connect(self):
        self.socket = socket.socket()
        try:
            self.socket.connect(("192.168.1.13",11211))
        except socket.error:
            self.socket = None
            
    def recv(self):
        if self.socket:
            self.socket.setblocking(False)
            while True:
                try:
                    buf = self.socket.recv(1024)
                except socket.error:
                    break
                
                if len(buf) == 0:
                    break
                else:
                    tok  = (self.buffer + buf).split(';')
                    self.buffer = ''
                    if len(tok) == 1:
                        self.buffer = tok[0]
                        continue
                    else:
                        if len(tok[-1]) != 0:
                            self.buffer = tok.pop()
                        else:
                            tok.pop()
                    for t in tok:
                        self.system.parse(t)
            self.socket.setblocking(True)
        
                
                
        
if __name__ == '__main__':
    s = System()
    d = Display(s)
    d.mainloop()