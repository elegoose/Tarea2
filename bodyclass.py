import numpy as np
import easy_shaders as es
import basic_shapes as bs
import json
import scene_graph as sg
from OpenGL.GL import *
import transformations as tr

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


class Body:
    def __init__(self, color, radius, distance, velocity, model, inclination, bodyID, satellites=None,
                 bodySceneGraph=None, systemSceneGraph=None, posx=0, posy=0):
        self.color = color

        self.radius = radius

        self.distance = distance * 2

        self.velocity = velocity

        self.model = model

        self.inclination = inclination

        self.bodyID = bodyID

        self.theta = np.random.uniform(-1, 1) * np.pi * 2

        self.satellites = satellites

        self.bodySceneGraph = bodySceneGraph

        self.systemSceneGraph = systemSceneGraph

        self.posx = posx

        self.posy = posy

        self.gpuShape = None

    def getgpushape(self):
        return es.toGPUShape(shape=readOBJ(self.model, self.color))

    def draw(self,lightPipeline,dt):
        glUseProgram(lightPipeline.shaderProgram)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        theta =  self.theta + self.velocity * dt
        self.posx = self.distance * np.cos(theta)
        self.posy = self.distance * np.sin(theta)
        if self.satellites=='Null':
            glUniformMatrix4fv(glGetUniformLocation(lightPipeline.shaderProgram, 'model'), 1, GL_TRUE,
                               tr.matmul([tr.translate(self.posx,self.posy,0),tr.uniformScale(self.radius)]))
            lightPipeline.drawShape(self.gpuShape)
        else:
            for satellite in self.satellites:
                theta = satellite.theta + satellite.velocity * dt
                satellite.posx = satellite.distance * np.cos(theta)
                satellite.posy = satellite.distance * np.sin(theta)
                satellite.bodySceneGraph.transform = tr.matmul([tr.translate(satellite.posx,satellite.posy,0),tr.uniformScale(satellite.radius)])
            self.bodySceneGraph.transform = tr.uniformScale(self.radius)
            self.systemSceneGraph.transform = tr.translate(self.posx,self.posy,0)
            sg.drawSceneGraphNode(self.systemSceneGraph, lightPipeline, 'model')

def drawbodies(bodies,lightPipeline,dt):
    glUseProgram(lightPipeline.shaderProgram)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    for body in bodies:
        body.draw(lightPipeline,dt)




def getbodiesinfo(file,proportion):
    with open(file) as f:
        data = json.load(f)
    bodies = []
    # Star
    color = data[0]['Color']
    radius = data[0]['Radius']
    model = data[0]['Model']
    star = Body(color, radius, 0, 0, model, 0, 0)
    star.gpuShape = star.getgpushape()
    bodyID = 1
    bodies.append(star)
    planets = data[0]['Satellites']
    for planet in planets:
        color = planet['Color']
        radius = planet['Radius'] * proportion
        distance = planet['Distance'] * proportion
        velocity = planet['Velocity']
        model = planet['Model']
        inclination = planet['Inclination']
        satellites = planet['Satellites']
        planetbody = Body(color, radius, distance, velocity, model, inclination, bodyID, satellites)
        planetbody.gpuShape = planetbody.getgpushape()
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
                satellitebody = Body(color, radius, distance, velocity, model, inclination, bodyID)
                bodyID += 1
                satellitebody.gpuShape = satellitebody.getgpushape()
                satelliteSceneGraph = sg.SceneGraphNode('satellite')
                satelliteSceneGraph.childs += [satellitebody.gpuShape]
                satellitebody.bodySceneGraph = satelliteSceneGraph
                systemSceneGraph.childs += [satelliteSceneGraph]

                planetbody.satellites.append(satellitebody)
            planetbody.systemSceneGraph = systemSceneGraph
        bodies.append(planetbody)
    return bodies

