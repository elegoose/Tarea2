import numpy as np


class Controller:
    def __init__(self):
        self.camaratheta = 0
        self.r = 5
        self.camx = 1
        self.camy = 0
        self.camz = 0
        self.followbody = False
        self.bodyID = 0
        self.maxbodyID = 0
        self.fillPolygon = True

    def update(self):
        self.camx = self.r * np.cos(self.camaratheta)
        self.camy = self.r * np.sin(self.camaratheta)
