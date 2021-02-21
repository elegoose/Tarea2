import sys

import glfw
from OpenGL.GL import *

import basic_shapes as bs
import bodyclass as bc
import easy_shaders as es
import lighting_shaders as ls
import transformations as tr
import scene_graph as sg
import numpy as np
import controller as ctrl

controller = ctrl.Controller()


def on_key(window, key, scancode, action, mods):  # noqa
    if action != glfw.PRESS:
        return

    global controller

    if key == glfw.KEY_V:
        controller.followbody = not controller.followbody
    elif key == glfw.KEY_LEFT:
        if controller.bodyID - 1 < 0:
            controller.bodyID = controller.maxbodyID
            return
        controller.bodyID -= 1
    elif key == glfw.KEY_RIGHT:
        if controller.bodyID + 1 > controller.maxbodyID:
            controller.bodyID = 0
            return
        controller.bodyID += 1


if __name__ == '__main__':
    if not glfw.init():
        sys.exit()
    width = 1280
    height = 720
    proportion = width / height
    window = glfw.create_window(width, height, 'Sistema planetario 3D', None, None)
    if not window:
        glfw.terminate()
        sys.exit()
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.0, 0.0, 0.0, 0.0)

    # setting pipelines
    lightPipeline = ls.SimplePhongShaderProgram()
    textureLightPipeline = ls.SimpleTexturePhongShaderProgram()
    trailPipeline = es.SimpleModelViewProjectionShaderProgram()
    texturePipeline = es.SimpleTextureModelViewProjectionShaderProgram()
    texture2dPipeline = es.SimpleTextureTransformShaderProgram()
    circle2dPipeline = es.SimpleTransformShaderProgram()

    allbodies = bc.getbodiesinfo('bodies.json', proportion, controller)
    star = allbodies[0]
    bodies = allbodies[1]

    star.gpuShape = star.getgpushape()
    gpuSkyBox = es.toGPUShape(bs.createTextureCube("textures/skybox.jpg"), GL_REPEAT, GL_LINEAR)
    gpuBodyInfo = es.toGPUShape(bs.createTextureQuad("textures/bodyinfo.png"), GL_REPEAT, GL_NEAREST)
    gpuBars = es.toGPUShape(bs.createTextureQuad("textures/bars.png"), GL_REPEAT, GL_NEAREST)

    sceneBars = sg.SceneGraphNode('bars')
    sceneBars.childs += [gpuBars]
    sceneSystemBars = sg.SceneGraphNode('systemBars')
    sceneSystemBars.childs += [sceneBars]

    skybox_transform = tr.uniformScale(20)
    bodyInfoTransform = tr.matmul([tr.translate(0.6, 0, 0), tr.scale(0.8, 1.2, 0)])

    t0 = glfw.get_time()
    viewPos = np.array([controller.camx, controller.camy, controller.camz])
    view = tr.lookAt(
        viewPos,
        np.array([0, 0, 0]),
        np.array([0, 0, 1])
    )
    projection = tr.perspective(45, float(width) / float(height), 0.1, 100)
    i = 0.07
    controller.icon = star.icon
    while not glfw.window_should_close(window):
        controller.printinfo = False
        glfw.poll_events()

        t1 = glfw.get_time()
        dt = t1 - t0
        controller.update()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Skybox
        glUseProgram(texturePipeline.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(texturePipeline.shaderProgram, "model"), 1, GL_TRUE, skybox_transform)
        glUniformMatrix4fv(glGetUniformLocation(texturePipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(texturePipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        texturePipeline.drawShape(gpuSkyBox)

        if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
            controller.camaratheta -= 0.007
        if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
            controller.camaratheta += 0.007
        if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
            controller.camz += 0.01
        if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
            controller.camz -= 0.01
        if glfw.get_key(window, glfw.KEY_Z) == glfw.PRESS:
            controller.r -= 0.01
        if glfw.get_key(window, glfw.KEY_X) == glfw.PRESS:
            controller.r += 0.01

        # SECOND VIEW
        if controller.followbody:
            #
            camera = ctrl.camerapos(bodies, controller)
            viewPos = camera[0]
            eye = camera[1]

            view = tr.lookAt(
                eye,
                viewPos,
                np.array([0, 0, 1])
            )

        # FIRST VIEW
        else:
            viewPos = np.array([controller.camx, controller.camy, controller.camz])

            view = tr.lookAt(
                viewPos,
                np.array([0, 0, controller.camz]),
                np.array([0, 0, 1])
            )

        bc.drawbodies(star, bodies, lightPipeline, textureLightPipeline, trailPipeline,
                      dt, projection, view, viewPos, controller)

        if controller.followbody:
            if i >= 0.2 * proportion:
                i = -i
            i += 0.005
            glUseProgram(texture2dPipeline.shaderProgram)
            # widescreen
            sceneBars.transform = tr.translate(proportion * 0.5, 0.5, 0)
            sceneSystemBars.transform = tr.matmul(
                [tr.translate(0.5 + proportion / 10, 0.01 + proportion / 10, 0),
                 tr.scale(proportion / 10, abs(i), 0)])

            sg.drawSceneGraphNode(sceneSystemBars, texture2dPipeline, 'transform')

            icon = controller.icon
            icon_transform = tr.matmul(
                [tr.translate(0.29 + proportion / 10, 0.2 + proportion / 10, 0),
                 tr.uniformScale(0.38)])
            hasTexture = icon[1]
            iconGPUShape = icon[0]
            if hasTexture:
                pipeline = texture2dPipeline
            else:
                pipeline = circle2dPipeline
                icon_transform = tr.matmul(
                    [tr.translate(0.29 + proportion / 10, 0.2 + proportion / 10, 0),
                     tr.scale(1, proportion, 0)])
            glUseProgram(pipeline.shaderProgram)
            glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, 'transform'), 1, GL_TRUE,
                               icon_transform)
            pipeline.drawShape(iconGPUShape)

            glUseProgram(texture2dPipeline.shaderProgram)

            glUniformMatrix4fv(glGetUniformLocation(texture2dPipeline.shaderProgram, "transform"), 1, GL_TRUE,
                               bodyInfoTransform)
            texture2dPipeline.drawShape(gpuBodyInfo)

        glfw.swap_buffers(window)
    glfw.terminate()
