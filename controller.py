import numpy as np


class Controller:
    def __init__(self):
        self.camaratheta = 0
        self.r = 5
        self.camx = 1
        self.camy = 0
        self.camz = 1
        self.followbody = False
        self.bodyID = 0
        self.maxbodyID = 0
        self.icon = None

    def update(self):
        self.camx = self.r * np.cos(self.camaratheta)
        self.camy = self.r * np.sin(self.camaratheta)


def camerapos(bodies, controller):
    eye = np.array([1, 0, 0])
    viewPos = np.array([0, 0, 0])
    for body in bodies:
        if controller.bodyID == 0:
            camx = 0.73
            camy = 0.12
            camz = 0.16
            eye = np.array([camx, camy, camz])
            viewPos = np.array([0, 0, 0])
            return viewPos, eye
        elif body.model == 'models/ufo.obj' and controller.bodyID == body.bodyID:
            camtheta = -0.24
            cameradistance = body.distance + 0.1
            eyeposx = cameradistance * np.cos(body.theta + camtheta)
            eyeposy = cameradistance * np.sin(body.theta + camtheta) / np.sqrt(1 + body.inclination ** 2)
            eyeposz = eyeposy * body.inclination

            viewPos = np.array([body.posx, body.posy, body.posz])
            eye = np.array([eyeposx, eyeposy, eyeposz + 0.24])
            return viewPos, eye
        elif controller.bodyID == body.bodyID:
            camtheta = - 0.65
            cameradistance = body.distance + 0.019
            eyeposx = cameradistance * np.cos(body.theta + camtheta)
            eyeposy = cameradistance * np.sin(body.theta + camtheta) / np.sqrt(1 + body.inclination ** 2)
            eyeposz = eyeposy * body.inclination

            viewPos = np.array([body.posx, body.posy, body.posz])
            eye = np.array([eyeposx, eyeposy, eyeposz + 0.05])
            return viewPos, eye
        elif body.satellites != 'Null':
            for satellite in body.satellites:
                if controller.bodyID == satellite.bodyID:
                    camtheta = - 0.76
                    cameradistance = satellite.distance + 0.01
                    eyeposx = cameradistance * np.cos(satellite.theta + camtheta) + body.posx
                    eyeposy = cameradistance * np.sin(satellite.theta + camtheta) / np.sqrt(
                        1 + satellite.inclination ** 2) + body.posy
                    eyeposz = cameradistance * satellite.inclination * np.sin(satellite.theta + camtheta) / np.sqrt(
                        1 + satellite.inclination ** 2) + body.posz
                    eye = np.array([eyeposx, eyeposy, eyeposz + 0.05])
                    viewPos = np.array(
                        [satellite.posx + body.posx, satellite.posy + body.posy, satellite.posz + body.posz])
                    return viewPos, eye
    return viewPos, eye
