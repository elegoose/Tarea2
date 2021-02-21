import sys

import glfw
from OpenGL.GL import *

import basic_shapes as bs
import bodyclass as bc
import easy_shaders as es
import lighting_shaders as ls
import transformations as tr
import scene_graph as sg
import obj_reader as obj
from controller import *

controller = Controller()


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
    elif key == glfw.KEY_F:
        controller.fillPolygon = not controller.fillPolygon

    elif key == glfw.KEY_ENTER:
        print("------------------------")
        print("distance: ",controller.mover)
        print("angle: ", controller.movea)
    elif key == glfw.KEY_M:
        print("                    ")
        print(" ///////////////////////////")
        print("*******MARCA***********")
        print(" ///////////////////////////")
        print("                    ")


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
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.15, 0.15, 0.15, 1.0)

    # lightPipeline = ls.SimpleGouraudShaderProgram()
    lightPipeline = ls.SimplePhongShaderProgram()
    # textureLightPipeline = ls.SimpleTextureGouraudShaderProgram()
    textureLightPipeline = ls.SimpleTexturePhongShaderProgram()
    trailPipeline = es.SimpleModelViewProjectionShaderProgram()
    texturePipeline = es.SimpleTextureModelViewProjectionShaderProgram()
    texture2dPipeline = es.SimpleTextureTransformShaderProgram()

    allbodies = bc.getbodiesinfo('bodies.json',proportion)
    controller.maxbodyID = bc.maxbodyID
    star = allbodies[0]
    bodies = allbodies[1]

    star.gpuShape = star.getgpushape()
    gpuSkyBox = es.toGPUShape(bs.createTextureCube("textures/skybox.jpg"), GL_REPEAT, GL_LINEAR)
    gpuBodyInfo = es.toGPUShape(bs.createTextureQuad("textures/bodyinfo.png"), GL_REPEAT, GL_NEAREST)
    gpuBars = es.toGPUShape(bs.createTextureQuad("textures/bars.png"), GL_REPEAT, GL_NEAREST)
    gpuOvni = es.toGPUShape(obj.readOBJ2('models/ovniobj.obj', 'textures/ovnitexture.jpg'), GL_REPEAT, GL_LINEAR)

    sceneCenterOvni = sg.SceneGraphNode('centerOvni')
    sceneCenterOvni.childs += [gpuOvni]

    ufodistance = 3
    ufotheta = 0.3
    x = np.cos(ufotheta) * ufodistance
    y = np.sin(ufotheta) * ufodistance
    sceneCenterOvni.transform = tr.matmul([tr.translate(x, y, -0.03), tr.rotationX(1.2), tr.uniformScale(0.6)])
    sceneOvni = sg.SceneGraphNode('Ovni')
    sceneOvni.childs += [sceneCenterOvni]

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
    prueba = es.toGPUShape(obj.readOBJ('models/sphere.obj', [1, 1, 1]))
    trail = es.toGPUShape(bc.createTrail(2, 40))
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

        if glfw.get_key(window, glfw.KEY_KP_6) == glfw.PRESS:
            controller.movea += 0.01
            print('angle: ',controller.movea)
        if glfw.get_key(window, glfw.KEY_KP_4) == glfw.PRESS:
            controller.movea -= 0.01
            print('angle: ',controller.movea)
        if glfw.get_key(window, glfw.KEY_KP_ADD) == glfw.PRESS:
            controller.mover += 0.01
            print('distance: ',controller.mover)
        if glfw.get_key(window, glfw.KEY_KP_SUBTRACT) == glfw.PRESS:
            controller.mover -= 0.01
            print('distance: ',controller.mover)

        if controller.fillPolygon:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        # SECOND VIEW
        if controller.followbody:
            #
            camera = camerapos(bodies, controller)
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

        bc.drawUFO(ufodistance, sceneOvni, textureLightPipeline, trailPipeline,
                   controller, viewPos, projection, view, dt)

        if controller.followbody:
            if i >= 0.2 * proportion:
                i = -i
            i += 0.005
            glUseProgram(texture2dPipeline.shaderProgram)
            # widescreen
            sceneBars.transform = tr.translate(proportion * 0.5, 0.5, 0)
            sceneSystemBars.transform = tr.matmul(
                [tr.translate(0.5 + proportion / 10, 0.01 + proportion / 10, 0), tr.scale(proportion / 10, abs(i), 0)])
            sg.drawSceneGraphNode(sceneSystemBars, texture2dPipeline, 'transform')
            glUniformMatrix4fv(glGetUniformLocation(texture2dPipeline.shaderProgram, "transform"), 1, GL_TRUE,
                               bodyInfoTransform)
            texture2dPipeline.drawShape(gpuBodyInfo)
        body = 0
        # theta = -bodies[body].satellites[0].thetai - bodies[body].satellites[0].velocity*1.5*dt
        # cameradistance = bodies[body].satellites[0].distance + 0.5
        # eyeposx = cameradistance * np.cos(theta) + bodies[body].distance * np.cos(bodies[body].theta)
        # eyeposy = cameradistance * np.sin(theta) + bodies[body].distance * np.sin(bodies[body].theta)
        # eyeposz = cameradistance * np.sin(theta) * bodies[body].satellites[0].inclination + bodies[body].distance * np.sin(
        #     bodies[body].theta) * bodies[body].inclination
        # posx = bodies[body].satellites[0].distance * (np.cos(theta) + np.sin(theta)) + bodies[body].distance * np.cos(bodies[body].theta)
        # posy = bodies[body].satellites[0].distance * (-np.sin(theta)+np.cos(theta)) + bodies[body].distance * np.sin(bodies[body].theta)
        # posz = bodies[body].satellites[0].distance * np.sin(theta) * bodies[body].satellites[0].inclination + bodies[body].distance * np.sin(
        #     bodies[body].theta) * bodies[body].inclination
        # planet = bodies[body]
        # r = planet.distance
        # theta = planet.velocity * dt
        # x = np.sqrt(r) * np.sin(theta)
        # y = -np.sqrt(r/2) * np.sin(theta)
        # z =  -np.sqrt(r/2) * np.sin(theta)
        inclination = 0.4
        r = 2
        inc_angle = np.arccos(1/(np.sqrt(inclination ** 2 + 1)))
        glUseProgram(trailPipeline.shaderProgram)

        glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)

        glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "view"), 1, GL_TRUE, view)

        glUniformMatrix4fv(glGetUniformLocation(trailPipeline.shaderProgram, "model"), 1, GL_TRUE,
                           tr.rotationX(inc_angle))

        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        trailPipeline.drawShape(trail)

        theta = 0.4*dt
        x = r*np.cos(theta)
        y = r * np.sin(theta)/np.sqrt(1+inclination ** 2)
        z = y * inclination
        if controller.printinfo:
            pladistance = np.sqrt(x ** 2 + y ** 2 + z ** 2)

            print("distance planet:", np.round(pladistance, 2))
            print("real planet distance:", r)
            print("error planet:", np.round(abs(pladistance - r), 3))
            print("----------------------------")

        glUseProgram(lightPipeline.shaderProgram)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        bc.setlighting(lightPipeline, controller, viewPos, projection , view)
        glUniformMatrix4fv(glGetUniformLocation(lightPipeline.shaderProgram, 'model'), 1, GL_TRUE,
                                              tr.matmul([tr.translate(x, y, z), tr.uniformScale(0.1)]))
        lightPipeline.drawShape(prueba)



        glfw.swap_buffers(window)
    glfw.terminate()
