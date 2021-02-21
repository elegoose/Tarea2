import numpy as np
import easy_shaders as es
import basic_shapes as bs
import json
import scene_graph as sg
from OpenGL.GL import *
import transformations as tr
import obj_reader as obj


class Body:
    def __init__(self, color, radius, distance, velocity, model, inclination, bodyID, trail, satellites=None,
                 bodySceneGraph=None, trailSceneGraph=None,
                 systemSceneGraph=None, posx=0, posy=0, posz=0):
        self.color = color

        self.radius = radius

        self.distance = distance

        self.velocity = velocity

        self.model = model

        self.inclination = inclination

        self.bodyID = bodyID

        self.trail = trail

        self.thetai = np.random.uniform(-1, 1) * np.pi * 2

        self.theta = 0

        self.satellites = satellites

        self.bodySceneGraph = bodySceneGraph

        self.systemSceneGraph = systemSceneGraph

        self.posx = posx

        self.posy = posy

        self.posz = posz

        self.gpuShape = None

        self.trailGpuShape = None

        self.trailSceneGraph = trailSceneGraph

        self.hasTexture = False

    def getgpushape(self):
        if self.model == 'models/sun.obj':
            return es.toGPUShape(obj.readOBJ2(self.model, 'textures/sun.jpg'), GL_REPEAT, GL_LINEAR)
        try:
            texture = self.model.replace("models", "textures")
            texture = texture.replace("obj", "jpg")
            hasTexture = True
            return es.toGPUShape(obj.readOBJ2(self.model, texture), GL_REPEAT,
                                 GL_LINEAR), es.toGPUShape(self.trail), hasTexture
        except:  # noqa
            hasTexture = False
            return es.toGPUShape(obj.readOBJ(self.model, self.color)), es.toGPUShape(self.trail), hasTexture

    def draw(self, lightPipeline, textureLightPipeline, trailPipeline, dt, projection, view, viewPos, controller):
        # Getting body pos
        self.theta = self.thetai + self.velocity * dt
        self.posx = self.distance * np.cos(self.theta)
        self.posy = self.distance * np.sin(self.theta)/np.sqrt(1+self.inclination ** 2)
        self.posz = self.posy * self.inclination
        inclination_to_rad = np.arccos(1/(np.sqrt(self.inclination ** 2 + 1)))
        if self.inclination<0:
            inclination_to_rad = -inclination_to_rad
        # Drawing body trail
        glUseProgram(trailPipeline.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "model"), 1, GL_TRUE,
                           tr.rotationX(inclination_to_rad))
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        trailPipeline.drawShape(self.trailGpuShape)

        if controller.fillPolygon:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        if self.satellites == 'Null':
            # Si no tiene satelites, solo dibuja el cuerpo
            # if self.bodyID == controller.bodyID and controller.followbody:
            # glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "La"), 1, 1, 1)
            # glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ka"), 1, 1, 1)
            # mtheta = self.theta - 0.6 + self.velocity * dt
            # posx = self.distance * np.cos(mtheta)
            # posy = self.distance * np.sin(mtheta)
            # posz = self.inclination * posy + 0.45
            # glUniformMatrix4fv(glGetUniformLocation(lightPipeline.shaderProgram, 'model'), 1, GL_TRUE,
            #                    tr.matmul([tr.translate(posx, posy, posz), tr.uniformScale(self.radius * 0.5)]))

            # lightPipeline.drawShape(self.gpuShape)
            if self.hasTexture:
                pipeline = textureLightPipeline
            else:
                pipeline = lightPipeline
            glUseProgram(pipeline.shaderProgram)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            if controller.printinfo and controller.bodyID == self.bodyID:
                pladistance = np.sqrt(self.posx ** 2 + self.posy ** 2 + self.posz ** 2)

                print("distance planet:", np.round(pladistance, 2))
                print("real planet distance:", self.distance)
                print("error planet:", np.round(abs(pladistance - self.distance), 3))
                print("pos z:", self.posz)
                print("----------------------------")
            setlighting(pipeline, controller, viewPos, projection, view)
            glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE,
                               tr.matmul([tr.translate(self.posx, self.posy, self.posz), tr.uniformScale(self.radius)]))
            pipeline.drawShape(self.gpuShape)
        else:
            satelliteView = False
            for satellite in self.satellites:
                # Getting satellite pos
                satellite.theta = satellite.thetai + satellite.velocity * dt
                satellite.posx = satellite.distance * np.cos(satellite.theta)
                satellite.posy = satellite.distance * np.sin(satellite.theta)/np.sqrt(1+satellite.inclination ** 2)
                satellite.posz = satellite.posy * satellite.inclination



                if satellite.bodyID == controller.bodyID and controller.followbody:
                    satelliteView = True
                    if controller.printinfo:
                        satdistance = np.sqrt((self.posx + satellite.posx) ** 2 + (self.posy + satellite.posy) ** 2 + (
                                    self.posz + satellite.posz) ** 2)
                        pladistance = np.sqrt(self.posx ** 2 + self.posy ** 2 + self.posz ** 2)
                        # plasatdistance = abs(pladistance - satdistance) if pladistance>satdistance else abs(satdistance - pladistance)
                        plasatvector = [self.posx - (satellite.posx + self.posx),
                                        self.posy - (satellite.posy + self.posy),
                                        self.posz - (satellite.posz + self.posz)]
                        plasatdistance = np.sqrt(plasatvector[0] ** 2 + plasatvector[1] ** 2 + plasatvector[2] ** 2)

                        # print("distance sat to center:",np.round(satdistance,2))
                        # print("distance planet:",np.round(pladistance,2))
                        # print("distance planet sat:",np.round(plasatdistance,2))
                        # print("real planet distance:",self.distance)
                        print("real planet sat distance:", satellite.distance)
                        # print("error planet:",np.round(abs(pladistance-self.distance),3))
                        print("error planet sat:", np.round(abs(plasatdistance - satellite.distance), 3))
                        print("sat pos z:", satellite.posz + self.posz)
                        print("----------------------------")

                # Drawing satellite trail
                inclination_to_rad = np.arccos(1 / (np.sqrt(satellite.inclination ** 2 + 1)))
                if satellite.inclination < 0:
                    inclination_to_rad = -inclination_to_rad
                glUseProgram(trailPipeline.shaderProgram)
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
                satellite.trailSceneGraph.transform = tr.matmul(
                    [tr.translate(self.posx, self.posy, self.posz), tr.rotationX(inclination_to_rad)])
                sg.drawSceneGraphNode(satellite.trailSceneGraph, trailPipeline, 'model')

                # Drawing body+satellite
                if satellite.hasTexture:
                    pipeline = textureLightPipeline
                else:
                    pipeline = lightPipeline
                glUseProgram(pipeline.shaderProgram)
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                setlighting(pipeline, controller, viewPos, projection, view)
                glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE,
                                   tr.matmul(
                                       [tr.translate(self.posx + satellite.posx, self.posy + satellite.posy,
                                                     self.posz + satellite.posz), tr.uniformScale(satellite.radius)]))
                pipeline.drawShape(satellite.gpuShape)
                # satellite.bodySceneGraph.transform = tr.matmul(
                #     [tr.translate(satellite.posx, satellite.posy, satellite.posz),
                #      tr.uniformScale(satellite.radius)])

            if controller.fillPolygon:
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            else:
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            if self.hasTexture:
                pipeline = textureLightPipeline
            else:
                pipeline = lightPipeline
            glUseProgram(pipeline.shaderProgram)
            setlighting(pipeline, controller, viewPos, projection, view)
            glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE,
                               tr.matmul([tr.translate(self.posx, self.posy, self.posz), tr.uniformScale(self.radius)]))
            # self.bodySceneGraph.transform = tr.uniformScale(self.radius)
            # if satelliteView:
            #     glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE,
            #                        tr.uniformScale(0))
                # self.bodySceneGraph.transform = tr.uniformScale(0)
            # self.systemSceneGraph.transform = tr.translate(self.posx, self.posy, self.posz)
            pipeline.drawShape(self.gpuShape)
            # sg.drawSceneGraphNode(self.systemSceneGraph, lightPipeline, 'model')


def drawbodies(star, bodies, lightPipeline, textureLightPipeline, trailPipeline, dt, projection, view, viewPos,
               controller):
    # Drawing Star
    glUseProgram(textureLightPipeline.shaderProgram)
    setlighting(textureLightPipeline, controller, viewPos, projection, view, isStar=True)
    glUniformMatrix4fv(glGetUniformLocation(textureLightPipeline.shaderProgram, "model"), 1, GL_TRUE,
                       tr.matmul([tr.translate(0, 0, 0), tr.uniformScale(star.radius)]))
    textureLightPipeline.drawShape(star.gpuShape)

    # Drawing bodies
    for body in bodies:
        body.draw(lightPipeline, textureLightPipeline, trailPipeline, dt, projection, view, viewPos, controller)


def drawUFO(distance, sceneUFO, texturePipeline, trailPipeline, controller, viewPos, projection, view, dt): # noqa
    velocity = 0.1
    inclination = 0.8
    theta = velocity * dt

    glUseProgram(trailPipeline.shaderProgram)
    glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
    glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
    glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "model"), 1, GL_TRUE,
                       tr.matmul([tr.rotationX(inclination)]))
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    trailPipeline.drawShape(es.toGPUShape(createTrail(distance, 40)))

    glUseProgram(texturePipeline.shaderProgram)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    setlighting(texturePipeline, controller, viewPos, projection, view)
    sceneUFO.transform = tr.matmul([tr.rotationX(inclination), tr.rotationZ(theta)])
    sg.drawSceneGraphNode(sceneUFO, texturePipeline, 'model')


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

    planets = data[0]['Satellites']
    for planet in planets:
        color = planet['Color']
        radius = planet['Radius']
        distance = planet['Distance']
        velocity = planet['Velocity']
        model = planet['Model']
        inclination = planet['Inclination']
        satellites = planet['Satellites']

        planetbody = Body(color, radius, distance, velocity, model, inclination, bodyID, createTrail(distance, 40),
                          satellites=satellites)

        planetbody.gpuShape = planetbody.getgpushape()[0]
        planetbody.trailGpuShape = planetbody.getgpushape()[1]
        planetbody.hasTexture = planetbody.getgpushape()[2]

        # planetIconSceneGraph = sg.SceneGraphNode('icon')
        # planetIconSceneGraph.childs += [planetbody.gpuShape]
        # planetbody.bodyIconSceneGraph = planetIconSceneGraph
        #
        # planetInfoSceneGraph = sg.SceneGraphNode('info')
        # planetInfoSceneGraph.childs += [planetIconSceneGraph]
        # planetbody.bodyInfoSceneGraph = planetInfoSceneGraph

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
                radius = satellite['Radius']
                distance = satellite['Distance']
                velocity = satellite['Velocity']
                model = satellite['Model']
                inclination = satellite['Inclination']

                satellitebody = Body(color, radius, distance, velocity, model, inclination, bodyID,
                                     createTrail(distance, 40))

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

                satellitebody.hasTexture = satellitebody.getgpushape()[2]

                planetbody.satellites.append(satellitebody)

            planetbody.systemSceneGraph = systemSceneGraph
        bodies.append(planetbody)
    maxbodyID = bodyID - 1
    return star, bodies


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


def setlighting(pipeline, controller, viewPos, projection, view, isStar=False):
    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "La"), 0.5, 0.5, 0.5)
    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ls"), 0.5, 0.5, 0.5)
    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ld"), 0.5, 0.5, 0.5)

    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Kd"), 0.15, 0.15, 0.15)
    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ks"), 0.5, 0.5, 0.5)
    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ka"), 0.1, 0.1, 0.1)

    if controller.followbody:
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ls"), 0, 0, 0)

        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Kd"), 0.15, 0.15, 0.15)
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ks"), 0, 0, 0)

    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "lightPosition"), 0, 0, 0)
    glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "viewPosition"), viewPos[0], viewPos[1],
                viewPos[2])

    glUniform1ui(glGetUniformLocation(pipeline.shaderProgram, "shininess"), 10)
    glUniform1f(glGetUniformLocation(pipeline.shaderProgram, "constantAttenuation"), 0.0001)
    glUniform1f(glGetUniformLocation(pipeline.shaderProgram, "linearAttenuation"), 0.03)
    glUniform1f(glGetUniformLocation(pipeline.shaderProgram, "quadraticAttenuation"), 0.01)

    glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, "projection"), 1, GL_TRUE,
                       projection)
    glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, "view"), 1, GL_TRUE, view)
    if isStar:
        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "La"), 1, 1, 1)

        glUniform3f(glGetUniformLocation(pipeline.shaderProgram, "Ka"), 1, 1, 1)
