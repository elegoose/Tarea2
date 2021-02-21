import numpy as np
import easy_shaders as es
import my_shapes as my
import json
import scene_graph as sg
from OpenGL.GL import *
import transformations as tr
import obj_reader as obj
import basic_shapes as bs


class Body:
    def __init__(self, color, radius, distance, velocity, model, inclination, bodyID, trail, satellites=None):
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

        self.posx = 0

        self.posy = 0

        self.posz = 0

        self.gpuShape = None

        self.trailGpuShape = None

        self.trailSceneGraph = None

        self.hasTexture = False

        self.icon = None

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
        inclination_to_rad = np.arccos(1 / (np.sqrt(self.inclination ** 2 + 1)))
        if self.inclination < 0:
            inclination_to_rad = -inclination_to_rad
        # Drawing body trail
        glUseProgram(trailPipeline.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "model"), 1, GL_TRUE,
                           tr.rotationX(inclination_to_rad))
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        trailPipeline.drawShape(self.trailGpuShape)

        self.theta = self.thetai + self.velocity * dt
        self.posx = self.distance * np.cos(self.theta)
        self.posy = self.distance * np.sin(self.theta) / np.sqrt(1 + self.inclination ** 2)
        self.posz = self.posy * self.inclination
        if self.satellites == 'Null':
            if self.bodyID == controller.bodyID:
                controller.icon = self.icon

            if self.hasTexture:
                pipeline = textureLightPipeline
            else:
                pipeline = lightPipeline
            glUseProgram(pipeline.shaderProgram)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            setlighting(pipeline, controller, viewPos, projection, view)
            body_transform = tr.matmul([tr.translate(self.posx, self.posy, self.posz),
                                        tr.uniformScale(self.radius)])
            if self.model == 'models/ufo.obj':
                body_transform = tr.matmul([tr.translate(self.posx, self.posy, self.posz),
                                            tr.uniformScale(self.radius),
                                            tr.rotationX(np.pi / 2),
                                            tr.rotationY(2 * dt)])
            glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE,
                               body_transform)
            pipeline.drawShape(self.gpuShape)
        else:
            if self.bodyID == controller.bodyID:
                controller.icon = self.icon
            for satellite in self.satellites:
                if satellite.bodyID == controller.bodyID:
                    controller.icon = satellite.icon

                # Getting satellite pos
                satellite.theta = satellite.thetai + satellite.velocity * dt
                satellite.posx = satellite.distance * np.cos(satellite.theta)
                satellite.posy = satellite.distance * np.sin(satellite.theta) / np.sqrt(1 + satellite.inclination ** 2)
                satellite.posz = satellite.posy * satellite.inclination

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

            if self.hasTexture:
                pipeline = textureLightPipeline
            else:
                pipeline = lightPipeline
            glUseProgram(pipeline.shaderProgram)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            setlighting(pipeline, controller, viewPos, projection, view)
            body_transform = tr.matmul([tr.translate(self.posx, self.posy, self.posz),
                                        tr.uniformScale(self.radius)])
            if self.model == 'models/saturn.obj':
                body_transform = tr.matmul([tr.translate(self.posx, self.posy, self.posz),
                                            tr.uniformScale(self.radius),
                                            tr.rotationX(np.pi / 2),
                                            tr.rotationY(dt)])
                ring_transform = tr.matmul([tr.translate(self.posx, self.posy, self.posz),
                                            tr.uniformScale(self.radius),
                                            tr.rotationX(np.pi / 3),
                                            tr.rotationY(dt)])
                glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE,
                                   body_transform)
                pipeline.drawShape(self.gpuShape[0])
                glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE,
                                   ring_transform)
                pipeline.drawShape(self.gpuShape[1])
                return

            glUseProgram(pipeline.shaderProgram)
            setlighting(pipeline, controller, viewPos, projection, view)
            glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'model'), 1, GL_TRUE,
                               body_transform)
            pipeline.drawShape(self.gpuShape)


def drawbodies(star, bodies, lightPipeline, textureLightPipeline, trailPipeline, dt, projection, view, viewPos,
               controller):
    # Drawing Star
    if controller.bodyID == 0:
        controller.icon = star.icon
    glUseProgram(textureLightPipeline.shaderProgram)
    setlighting(textureLightPipeline, controller, viewPos, projection, view, isStar=True)
    glUniformMatrix4fv(glGetUniformLocation(textureLightPipeline.shaderProgram, "model"), 1, GL_TRUE,
                       tr.matmul([tr.translate(0, 0, 0),
                                  tr.uniformScale(star.radius),
                                  tr.rotationX(np.pi / 2)]))
    textureLightPipeline.drawShape(star.gpuShape)

    # Drawing bodies
    for body in bodies:
        body.draw(lightPipeline, textureLightPipeline, trailPipeline, dt, projection, view, viewPos, controller)


def getbodiesinfo(file, proportion, controller):
    with open(file) as f:
        data = json.load(f)
    bodies = []
    # Star
    color = data[0]['Color']
    radius = data[0]['Radius']
    model = data[0]['Model']

    star = Body(color, radius, 0, 0, model, 0, 0, None)
    star.icon = es.toGPUShape(bs.createTextureQuad('icons/sun.png'), GL_REPEAT, GL_NEAREST), True
    bodyID = 1
    planets = data[0]['Satellites']
    for planet in planets:
        color = planet['Color']
        radius = planet['Radius'] * proportion
        distance = planet['Distance'] * proportion
        velocity = planet['Velocity']
        model = planet['Model']
        inclination = planet['Inclination']
        satellites = planet['Satellites']

        planetbody = Body(color, radius, distance, velocity, model, inclination, bodyID, my.createTrail(distance, 60),
                          satellites=satellites)

        planetbody.gpuShape = planetbody.getgpushape()[0]
        planetbody.trailGpuShape = planetbody.getgpushape()[1]
        planetbody.hasTexture = planetbody.getgpushape()[2]
        if planetbody.hasTexture:
            texture = planetbody.model.replace("models", "icons")
            texture = texture.replace("obj", "png")
            planetbody.icon = es.toGPUShape(bs.createTextureQuad(texture),
                                            GL_REPEAT, GL_NEAREST), planetbody.hasTexture
        else:
            planetbody.icon = es.toGPUShape(my.createCircle(30, *color, 0.1)), planetbody.hasTexture
        # Planet Trail
        bodyID += 1
        if satellites != 'Null':

            if planetbody.model == "models/saturn.obj":
                planetbody.gpuShape = [planetbody.getgpushape()[0],
                                       es.toGPUShape(obj.readOBJ2('models/saturn_ring.obj',
                                                                  'textures/saturn_rings.jpg'),
                                                     GL_REPEAT, GL_NEAREST
                                                     )]
            planetbody.satellites = []
            for satellite in satellites:
                color = satellite['Color']
                radius = satellite['Radius'] * proportion
                distance = satellite['Distance'] * proportion
                velocity = satellite['Velocity']
                model = satellite['Model']
                inclination = satellite['Inclination']

                satellitebody = Body(color, radius, distance, velocity, model, inclination, bodyID,
                                     my.createTrail(distance, 40))

                bodyID += 1

                satellitebody.gpuShape = satellitebody.getgpushape()[0]

                satellitebody.trailGpuShape = satellitebody.getgpushape()[1]

                trailSceneGraph = sg.SceneGraphNode('satelliteTrail')
                trailSceneGraph.childs += [satellitebody.trailGpuShape]

                systemTrailSceneGraph = sg.SceneGraphNode('systemSatelliteTrail')
                systemTrailSceneGraph.childs += [trailSceneGraph]

                satellitebody.trailSceneGraph = systemTrailSceneGraph

                satellitebody.hasTexture = satellitebody.getgpushape()[2]

                if satellitebody.hasTexture:
                    texture = satellitebody.model.replace("models", "icons")
                    texture = texture.replace("obj", "png")
                    satellitebody.icon = es.toGPUShape(bs.createTextureQuad(texture),
                                                       GL_REPEAT, GL_NEAREST), satellitebody.hasTexture
                else:
                    satellitebody.icon = es.toGPUShape(my.createCircle(30, *color, 0.1)), satellitebody.hasTexture

                planetbody.satellites.append(satellitebody)

        bodies.append(planetbody)
    ufodistance = 4
    ufovelocity = 0.3
    UFO = Body(None, 1, ufodistance, ufovelocity, 'models/ufo.obj', 0.8, bodyID,
               my.createTrail(ufodistance, 60), satellites='Null')
    UFO.gpuShape = UFO.getgpushape()[0]
    UFO.trailGpuShape = UFO.getgpushape()[1]
    UFO.hasTexture = UFO.getgpushape()[2]
    UFO.icon = es.toGPUShape(bs.createTextureQuad('icons/ufo.png'), GL_REPEAT, GL_NEAREST), True
    bodies.append(UFO)
    bodyID += 1
    controller.maxbodyID = bodyID - 1
    return star, bodies


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
