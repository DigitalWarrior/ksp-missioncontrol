""" "THE BEER-WARE LICENSE" (Revision 42):
 * Matti Eiden <snaipperi@gmail.com> wrote this file. As long as you retain this notice you
 * can do whatever you want with this stuff. If we meet some day, and you think
 * this stuff is worth it, you can buy me a beer in return.
"""

from numpy import sin, sinh, arcsin, cos, cosh, arccos, tan, arctan , pi, nan
from numpy import sign, sqrt, cross, log, array, dot, degrees, radians, inf
from numpy.linalg import norm

PI2 = pi * 2

class Orbit:
    ''' This class provides orbit prediction '''
    
    def __init__(self,parent,**kwargs):
        ''' 
        kwargs needs to contain currently trv (time, pos, vel)
        Calculating from elements is not available yet
        '''
        self.parent = parent
        self.mu = parent.mu
        
        if "elements" in kwargs:
            self.recalculateFromElements(kwargs["elements"])
        elif "trv" in kwargs:
            self.recalculateFromTRV(kwargs["trv"])
        else:
            raise AttributeError
        
        
        
        
    def recalculateFromElements(self,elements):
        ''' 
        Based on Vallado, calculates an orbit from orbital elements
        Not ready to be used yet!
        '''
        if not isinstance(vec_r,array) or isinstance(vec_v,array):
            raise AttributeError("Needs array")
        
        # Define initial variables
        mu = self.mu
        
        nrm_r = norm(vec_r)
        nrm_v = norm(vec_v)        
        
        # (1) Calculate angular momentum
        vec_h = cross(vec_r, vec_v)
        nrm_h = norm(vec_h)
        
        # (2) Calculate node vector
        vec_n = cross(array([0,0,1]), vec_h)
        
        # (3) Calculate eccentricity vector
        
        vec_e = ( (nrm_v**2 - mu/nrm_r)*vec_r - (vec_r.dot(vec_r))*vec_v ) / mu
        nrm_e = norm(vec_e)
        
        if round(nrm_e,6) == 1.0:
            periapsis = nrm_h**2 / mu
            a = inf
        else:
            xi = nrm_v**2 / 2 - mu/nrm_r
            a = -mu/(2*xi)
            periapsis = a (1-nrm_e)
            
        
        i = arccos(vec_h[2] / nrm_h)
        if vec_n[1] < 0:
            i = PI2 - i
    
    def recalculateFromTRV(self,trv):
        ''' 
        Based on Vallado. This function calculates orbit parameters from given
        trv = [t0,r0,v0] where
        t0 - Time of observation (float)
        r0 - Position vector (numpy.array) of observation
        v0 - Velocity vector (numpy.array) of observation
        
        Call this function every time the initial parameters are changed.
        '''
        
        self.t0 = trv[0]
        self.r0 = trv[1]
        self.v0 = trv[2]
        
        logging.debug("Initializing..")
        logging.debug("mu %f"%self.mu)
        logging.debug("r0 %s"%str(self.r0))
        logging.debug("v0 %s"%str(self.v0))
        logging.debug("t0 %s"%str(self.t0))
        
        # Normalized position and velocity vectors
        self.r0l = norm(self.r0)
        self.v0l = norm(self.v0)
        
        # Auxilary variable xi
        self.xi = self.v0l**2.0 / 2.0 - self.mu / self.r0l 
        logging.debug("xi %f"%self.xi)
        
        if self.xi == 0:
            self.a = inf
            self.alpha = 1.0
        
        else:
            # Semi major axis
            self.a  = -self.mu / (2*self.xi) 
            
            if self.a == nan:
                print "There's a problem with semi-major axis. Problem details:"
                print "Position:",self.r0
                print "Velocity:",self.v0
            # Auxilary variable alpha
            self.alpha = 1.0 / self.a
        
        # Angular momentum vector and normalized
        self.h = cross(self.r0,self.v0)
        self.hl = norm(self.h)
        
        # Umm.. p is not period
        self.p = self.hl**2 / self.mu
        
        # Dot product of position and velocity        
        self.rvdot = self.r0.dot(self.v0)


        
        
        
    def get(self,t):
        ''' 
        Get 3D position and velocity at time t 
        Returns [r (numpy.array), v (numpy.array)]
        '''
        
        # (1) Delta-t
        dt = t - self.t0
        
        
        logging.debug("Semi-major: %f"%self.a)
        logging.debug("alpha: %f"%self.alpha)
        
        # (2) Create the initial X variable guess for
        #  2a) Elliptic or circular orbit
        if self.alpha > 1e-20:
            X0 = sqrt(self.mu) * dt * self.alpha
        
        #  2b) Parabolic orbit
        elif abs(self.alpha) < 1e-20:
            self.s = arctan((1)/(3*sqrt(self.mu / self.p**3)*dt)) / 2.0
            self.w = arctan(tan(self.s)**(1.0/3.0))
            X0 = sqrt(self.p) * 2 * (cos(2*self.w)/sin(2*self.w))
            logging.debug("s: %f"%self.s)
        
        #  2c) Hyperbolic orbit
        elif self.alpha < -1e-20:
            X0 = sign(dt) * sqrt(-self.a) * log((-2*self.mu*self.alpha*dt) / (self.rvdot * sign(dt) * sqrt(-self.mu * self.a) * (1- self.r0 * self.alpha)))
    
        else:
            logging.error("Error, ALPHA")
            raise AttributeError
        
        logging.debug("X0: %f"%X0)
        Xnew = X0
        
        # (3) Loop until we get an accurate (tolerance 1e-6) value for X
        while True:
            psi = Xnew**2 * self.alpha
            c2,c3 = self.FindC2C3(psi)
            
            logging.debug("psi: %f"%psi)
            logging.debug("c2: %f"%c2)
            logging.debug("c3: %f"%c3)
            
            r = Xnew**2 * c2 + self.rvdot / sqrt(self.mu) * Xnew * (1 - psi * c3) + self.r0l * (1 - psi * c2)

            Xold = Xnew
            Xnew = Xold + (sqrt(self.mu)*dt - Xold**3 * c3 - self.rvdot / sqrt(self.mu) * Xold**2 * c2 - self.r0l * Xold * (1 - psi * c3)) / r
            
            if abs(Xnew - Xold) < 1e-6:
                break
        
        logging.debug("X optimized at %f"%Xnew)
        
        # (4) Calculate universal functions f, g and f-dot and g-dot
        f = 1 - Xnew**2/self.r0l * c2
        g = dt - Xnew**3 / sqrt(self.mu) * c3
        gd = 1 - Xnew**2/r * c2
        fd = sqrt(self.mu) / (r*self.r0l) * Xnew * (psi * c3 - 1)

        logging.debug("f: %f"%f)
        logging.debug("g: %f"%g)
        logging.debug("fd: %f"%fd)
        logging.debug("gd: %f"%gd)
        
        # 
        R = f * self.r0 + g * self.v0 
        V = fd * self.r0 + gd * self.v0 
        
        logging.debug( "r: %f"%r)
        logging.debug( "r0l: %f"%self.r0l)
        logging.debug( "Position: %s"%str(R))
        logging.debug( "Velocity: %s"%str(V))
        logging.debug( "Check: %f"%(f*gd-fd*g))
        
        return [R,V]
            
    def FindC2C3(self, psi):
        '''
        Finds the helper variables c2 and c3 when given psi
        '''
        if psi > 1e-20:
            sqrtpsi = sqrt(psi)
            c2 = (1 - cos(sqrtpsi)) / psi
            c3 = (sqrtpsi - sin(sqrtpsi)) / sqrt(psi**3)
        else:
            if psi < -1e-20:
                sqrtpsi = sqrt(-psi)
                c2 = (1 - cosh(sqrtpsi)) / psi
                c3 = (sinh(sqrtpsi) - sqrtpsi) / sqrt(-psi**3)
                
            else:
                c2 = 0.5
                c3 = 1.0/6.0
                
        return (c2,c3)
                
    
    
    def getGround(self,t):
        ''' 
        Get ground position given t
        Currently supports only Kerbin
        
                 float              float
        returns [right ascension, declination]
        '''
        
        # (1) Get current 3D position
        r = self.get(t)[0]
        
        # (2) Calculate theta (planet rotation)
        # -0.00029.. Kerbins angular velocity rad(/s)
        #  1.57079.. 90 degrees, initial t=0 rotation (depends on map?)
        
        theta =  -0.0002908882086657216 * t - 1.5707963267948966
        
        # (3) Create a rotation matrix and rotate the current position
        rot_matrix = array([[cos(theta), sin(theta), 0], [-sin(theta), cos(theta), 0], [0, 0, 1]])
        rr = dot(r,rot_matrix)
        ur = rr / norm(rr)
        
        # (4) Solve declination (latitude)
        declination = arcsin(ur[2])
        
        # (5) Solve right ascension (longitude)
        if ur[1] > 0:
            rasc = degrees(arccos(ur[0] / cos(declination)))
        elif ur[1] <= 0:
            rasc = -degrees(arccos(ur[0]/ cos(declination)))
        
        # (6) Data to degrees, NOTE the order of return
        declination = degrees(declination)
        
        logging.debug("Theta: %f degrees, rad %f"%(degrees(theta),theta))
        logging.debug("Declination: %f degrees, rad %f"%(declination,radians(declination)))
        logging.debug("R. ascension: %f degrees, rad %f"%(rasc,radians(rasc)))
        logging.debug("ur: %s"%str(ur))
    
        return [rasc,declination]
        
    def getPeriod(self):
        ''' 
        Gets the period of orbit.
        Note! Currently works only on e<1 orbits!
        '''
        return PI2*sqrt(self.a**3/self.mu)