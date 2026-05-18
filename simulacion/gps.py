import numpy as np
import pandas as pd
class Gps:
    def __init__(self, gpsfile = None, times = [], xs = [], ys = [], zs = [], vxs = [], vys = [], vzs = []):
        if gpsfile == None:
            pass
        else:
            self.gpsfile = gpsfile
            df = pd.read_fwf(gpsfile,skiprows=1, names=["times", "x", "y", "z", "vx", "vy", "vz"])        
            self.times = str(df["times"].to_numpy()).replace(":", "-")
            self.xs = df["x"].to_numpy()
            self.ys = df["y"].to_numpy()
            self.zs = df["z"].to_numpy()
            self.vxs = df["vx"].to_numpy()
            self.vys = df["vy"].to_numpy()
            self.vzs = df["vz"].to_numpy()
    
    def speed(self,t):
        return np.sqrt(self.xs[t]**2 + self.ys[t]**2 + self.zs[t]**2)
    
    def posVector(self,t):
        return np.array([self.xs[t], self.ys[t], self.zs[t]])
    
    def posVelocity(self,t):
        return [self.vxs[t], self.vys[t], self.vzs[t]]
    
