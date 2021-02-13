import numpy as np
import easy_shaders as es
import basic_shapes as bs
import json
import scene_graph as sg
from OpenGL.GL import *
import transformations as tr


class Body:
    def __init__(self, color, radius, distance, velocity, model, inclination, bodyID, trail, satellites=None,
                 bodySceneGraph=None, trailSceneGraph=None, systemSceneGraph=None, posx=0, posy=0, posz=0):
        self.color = color

        self.radius = radius

        self.distance = distance

        self.velocity = velocity

        self.model = model

        self.inclination = inclination

        self.bodyID = bodyID

        self.trail = trail

        self.theta = np.random.uniform(-1, 1) * np.pi * 2

        self.satellites = satellites

        self.bodySceneGraph = bodySceneGraph

        self.systemSceneGraph = systemSceneGraph

        self.posx = posx

        self.posy = posy

        self.posz = posz

        self.gpuShape = None

        self.trailGpuShape = None

        self.trailSceneGraph = trailSceneGraph

    def getgpushape(self):
        return es.toGPUShape(shape=readOBJ(self.model, self.color)), es.toGPUShape(self.trail)

    def draw(self, lightPipeline, trailPipeline, dt, projection, view, controller):
        glUseProgram(trailPipeline.shaderProgram)
        if controller.fillPolygon:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "model"), 1, GL_TRUE,
                           tr.rotationX(self.inclination))
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        trailPipeline.drawShape(self.trailGpuShape)
        glUseProgram(lightPipeline.shaderProgram)
        theta = self.theta + self.velocity * dt
        self.posx = self.distance * np.cos(theta)
        self.posy = self.distance * np.sin(theta)
        self.posz = self.inclination * self.posy
        if self.satellites == 'Null':
            if controller.fillPolygon:
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            else:
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glUniformMatrix4fv(glGetUniformLocation(lightPipeline.shaderProgram, 'model'), 1, GL_TRUE,
                               tr.matmul([tr.translate(self.posx, self.posy, self.posz), tr.uniformScale(self.radius)]))
            lightPipeline.drawShape(self.gpuShape)
        else:
            for satellite in self.satellites:
                theta = satellite.theta + satellite.velocity * dt
                satellite.posx = -satellite.distance * np.cos(theta)
                satellite.posy = -satellite.distance * np.sin(theta)
                satellite.posz = satellite.inclination * satellite.posy
                # Transforming satellite trail to its coordinates
                satellite.trailSceneGraph.transform = tr.matmul(
                    [tr.translate(self.posx, self.posy, self.posz), tr.rotationX(satellite.inclination)])
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
                glUseProgram(trailPipeline.shaderProgram)
                sg.drawSceneGraphNode(satellite.trailSceneGraph, trailPipeline, 'model')

                satellite.bodySceneGraph.transform = tr.matmul(
                    [tr.translate(satellite.posx, satellite.posy - satellite.radius, satellite.posz),
                     tr.uniformScale(satellite.radius)])
            self.bodySceneGraph.transform = tr.uniformScale(self.radius)
            self.systemSceneGraph.transform = tr.translate(self.posx, self.posy, self.posz)
            glUseProgram(lightPipeline.shaderProgram)
            if controller.fillPolygon:
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            else:
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            sg.drawSceneGraphNode(self.systemSceneGraph, lightPipeline, 'model')


def drawbodies(bodies, lightPipeline, trailPipeline, dt, projection, view, controller):
    glUseProgram(lightPipeline.shaderProgram)
    for body in bodies:
        body.draw(lightPipeline, trailPipeline, dt, projection, view, controller)


def camerapos(bodies, controller, dt):
    eye = np.array([1, 0, 0])
    viewPos = np.array([0, 0, 0])
    for body in bodies:
        if controller.bodyID == body.bodyID:
            theta = body.theta + body.velocity * dt + np.pi * 1.5
            eyeposx = body.distance * np.cos(theta)
            eyeposy = body.distance * np.sin(theta)
            eyeposz = eyeposy * body.inclination
            posx = body.posx
            posy = body.posy
            posz = body.posz
            viewPos = np.array([posx, posy, posz])
            eye = np.array([eyeposx, eyeposy, eyeposz]) * 1.02
            return viewPos, eye
        if body.satellites != 'Null':
            for satellite in body.satellites:
                if controller.bodyID == satellite.bodyID:
                    theta = satellite.theta + satellite.velocity * dt - np.pi / 1.7
                    eyeposx = satellite.distance * np.cos(theta) + body.posx
                    eyeposy = satellite.distance * np.sin(theta) + body.posy
                    eyeposz = satellite.distance * np.sin(theta) * satellite.inclination + body.posz
                    posx = satellite.posx + body.posx
                    posy = satellite.posy + body.posy
                    posz = satellite.posz + body.posz
                    viewPos = np.array([posx, posy, posz])
                    eye = np.array([eyeposx, eyeposy, eyeposz]) * 1.02
                    return viewPos, eye
    return viewPos, eye
maxbodyID = 0
def getbodiesinfo(file, proportion):
    global maxbodyID
    with open(file) as f:
        data = json.load(f)
    bodies = []
    # Star
    color = data[0]['Color']
    radius = data[0]['Radius']
    model = data[0]['Model']
    star = Body(color, radius, 0, 0, model, 0, 0, None)
    bodyID = 1
    # bodies.append(star)
    planets = data[0]['Satellites']
    for planet in planets:
        color = planet['Color']
        radius = planet['Radius'] * proportion
        distance = planet['Distance'] * proportion
        velocity = planet['Velocity']
        model = planet['Model']
        inclination = planet['Inclination']
        satellites = planet['Satellites']
        planetbody = Body(color, radius, distance, velocity, model, inclination, bodyID, createTrail(distance, 25),
                          satellites=satellites)
        planetbody.gpuShape = planetbody.getgpushape()[0]
        planetbody.trailGpuShape = planetbody.getgpushape()[1]

        # Planet Trail
        bodyID += 1
        if satellites != 'Null':
            planetSceneGraph = sg.SceneGraphNode('planet')
            planetSceneGraph.childs += [planetbody.gpuShape]
            planetbody.bodySceneGraph = planetSceneGraph

            systemSceneGraph = sg.SceneGraphNode('system')
            systemSceneGraph.childs += [planetSceneGraph]

            planetbody.satellites = []
            for satellite in satellites:
                color = satellite['Color']
                radius = satellite['Radius'] * proportion
                distance = satellite['Distance'] * proportion
                velocity = satellite['Velocity']
                model = satellite['Model']
                inclination = satellite['Inclination']
                satellitebody = Body(color, radius, distance, velocity, model, inclination, bodyID,
                                     createTrail(distance, 25))
                bodyID += 1
                satellitebody.gpuShape = satellitebody.getgpushape()[0]
                satelliteSceneGraph = sg.SceneGraphNode('satellite')
                satelliteSceneGraph.childs += [satellitebody.gpuShape]
                satellitebody.bodySceneGraph = satelliteSceneGraph
                systemSceneGraph.childs += [satelliteSceneGraph]

                satellitebody.trailGpuShape = satellitebody.getgpushape()[1]
                trailSceneGraph = sg.SceneGraphNode('satelliteTrail')
                trailSceneGraph.childs += [satellitebody.trailGpuShape]
                systemTrailSceneGraph = sg.SceneGraphNode('systemSatelliteTrail')
                systemTrailSceneGraph.childs += [trailSceneGraph]
                satellitebody.trailSceneGraph = systemTrailSceneGraph

                planetbody.satellites.append(satellitebody)
            planetbody.systemSceneGraph = systemSceneGraph
        bodies.append(planetbody)
    maxbodyID = bodyID-1
    return star, bodies


def readFaceVertex(faceDescription):  # noqa
    aux = faceDescription.split('/')

    assert len(aux[0]), "Vertex index has not been defined."

    faceVertex = [int(aux[0]), None, None]

    assert len(aux) == 3, "Only faces where its vertices require 3 indices are defined."

    if len(aux[1]) != 0:
        faceVertex[1] = int(aux[1])

    if len(aux[2]) != 0:
        faceVertex[2] = int(aux[2])

    return faceVertex


def readOBJ(filename, color):  # noqa
    vertices = []
    normals = []
    # textCoords = []
    faces = []
    with open(filename, 'r') as file:
        for line in file.readlines():
            aux = line.strip().split(' ')

            if aux[0] == 'v':
                vertices += [[float(coord) for coord in aux[1:]]]

            elif aux[0] == 'vn':
                normals += [[float(coord) for coord in aux[1:]]]

            # elif aux[0] == 'vt':
            #     assert len(aux[1:]) == 2, "Texture coordinates with different than 2 dimensions are not supported"
            #     textCoords += [[float(coord) for coord in aux[1:]]]

            elif aux[0] == 'f':
                N = len(aux)
                faces += [[readFaceVertex(faceVertex) for faceVertex in aux[1:4]]]
                for i in range(3, N - 1):
                    faces += [[readFaceVertex(faceVertex) for faceVertex in [aux[i], aux[i + 1], aux[1]]]]

        vertexData = []
        indices = []
        index = 0

        # Per previous construction, each face is a triangle
        for face in faces:

            # Checking each of the triangle vertices
            for i in range(0, 3):
                vertex = vertices[face[i][0] - 1]
                normal = normals[face[i][2] - 1]

                vertexData += [
                    vertex[0], vertex[1], vertex[2],
                    color[0], color[1], color[2],
                    normal[0], normal[1], normal[2]
                ]

            # Connecting the 3 vertices to create a triangle
            indices += [index, index + 1, index + 2]
            index += 3

        return bs.Shape(vertexData, indices)


def createTrail(radio, N):  # noqa
    vertices = []
    indices = []

    dtheta = 2 * np.pi / N

    for i in range(N):
        theta = i * dtheta

        vertices += [
            radio * np.cos(theta), radio * np.sin(theta), 0,

            0.91, 0.93, 0.85]

        if i == 0:
            indices += [0, 0, 1]
        elif i == N - 1:
            pass
        else:
            indices += [i, i, i + 1]

    # Uniendo circunferencia
    indices += [N - 1, N - 1, 0]

    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)

    return bs.Shape(vertices, indices)
