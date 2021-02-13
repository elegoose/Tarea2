import sys

import glfw
from OpenGL.GL import *

import basic_shapes as bs
import bodyclass as bc
import easy_shaders as es
import lighting_shaders as ls
import transformations as tr
from controller import *

controller = Controller()
def on_key(window, key, scancode, action, mods):  # noqa
    if action != glfw.PRESS:
        return

    global controller

    if key == glfw.KEY_V:
        controller.followbody = not controller.followbody
    elif key == glfw.KEY_LEFT:
        if controller.bodyID-1 < 0:
            controller.bodyID = controller.maxbodyID
            return
        controller.bodyID -= 1
    elif key == glfw.KEY_RIGHT:
        if controller.bodyID+1 > controller.maxbodyID:
            controller.bodyID = 0
            return
        controller.bodyID += 1
    elif key == glfw.KEY_F:
        controller.fillPolygon = not controller.fillPolygon


if __name__ == '__main__':
    if not glfw.init():
        sys.exit()
    width = 900
    height = 900
    proportion = width / height
    window = glfw.create_window(width, height, 'Sistema planetario 3D', None, None)
    if not window:
        glfw.terminate()
        sys.exit()
    glfw.make_context_current(window)
    glfw.set_key_callback(window, on_key)
    lightPipeline = ls.SimpleGouraudShaderProgram()
    trailPipeline = es.SimpleModelViewProjectionShaderProgram()
    texturePipeline = es.SimpleTextureModelViewProjectionShaderProgram()

    gpuSkyBox = es.toGPUShape(bs.createTextureCube("skybox.jpg"), GL_REPEAT, GL_LINEAR)
    skybox_transform = tr.uniformScale(20)
    glClearColor(0.15, 0.15, 0.15, 1.0)
    glEnable(GL_DEPTH_TEST)
    allbodies = bc.getbodiesinfo('bodies.json', proportion)
    controller.maxbodyID = bc.maxbodyID
    star = allbodies[0]
    bodies = allbodies[1]
    star.gpuShape = es.toGPUShape(shape=bc.readOBJ(star.model, star.color))

    t0 = glfw.get_time()

    viewPos = np.array([controller.camx, controller.camy, controller.camz])

    view = tr.lookAt(
        viewPos,
        np.array([0, 0, 0]),
        np.array([0, 0, 1])
    )

    projection = tr.perspective(45, float(width) / float(height), 0.1, 100)
    # camAngle = 0
    la=1
    # ld=1
    # ls=1
    ka=0.1
    # kd=0.15
    # ks=0.3
    while not glfw.window_should_close(window):
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
            controller.camaratheta -= 0.01

        if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
            controller.camaratheta += 0.01

        if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
            controller.camz += 0.1

        if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
            controller.camz -= 0.1

        if glfw.get_key(window, glfw.KEY_Z) == glfw.PRESS:
            controller.r -= 0.1

        if glfw.get_key(window, glfw.KEY_X) == glfw.PRESS:
            controller.r += 0.1

        # if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        #     camAngle += 0.01
        #     print(camAngle)
        # elif glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        #     camAngle -= 0.01
        #     print(camAngle)

        # if glfw.get_key(window, glfw.KEY_1):
        #     la -= 0.01
        #     print('la', la)
        # elif glfw.get_key(window,glfw.KEY_2):
        #     la += 0.01
        #     print('la', la)
        # elif glfw.get_key(window,glfw.KEY_3):
        #     ld -= 0.01
        #     print('ld', ld)
        # elif glfw.get_key(window,glfw.KEY_4):
        #     ld += 0.01
        #     print('ld', ld)
        # elif glfw.get_key(window,glfw.KEY_5):
        #     ls -= 0.01
        #     print('ls',ls)
        # elif glfw.get_key(window,glfw.KEY_6):
        #     ls += 0.01
        #     print('ls',ls)
        # elif glfw.get_key(window,glfw.KEY_F1):
        #     ka -= 0.01
        #     print('ka',ka)
        # elif glfw.get_key(window,glfw.KEY_F2):
        #     ka += 0.01
        #     print('ka',ka)
        # elif glfw.get_key(window,glfw.KEY_F3):
        #     kd -= 0.01
        #     print('kd',kd)
        # elif glfw.get_key(window,glfw.KEY_F4):
        #     kd += 0.01
        #     print('kd',kd)
        # elif glfw.get_key(window,glfw.KEY_F5):
        #     ks -= 0.01
        #     print('ks',ks)
        # elif glfw.get_key(window,glfw.KEY_F6):
        #     ks += 0.01
        #     print('ks',ks)

        if controller.fillPolygon:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        glUseProgram(lightPipeline.shaderProgram)
        # SECOND VIEW
        if controller.followbody:
            camera = bc.camerapos(bodies, controller, dt)
            viewPos = camera[0]
            eye = camera[1]

            view = tr.lookAt(
                eye,
                viewPos,  # The camera will be the sun
                np.array([0, 0, 1])
            )

            # White light in all components: ambient, diffuse and specular.
            # glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "La"), 1, 1, 1)
            # glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ld"), 1, 1, 1)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ls"), 0, 0, 0)

            # Object is barely visible at only ambient. Bright white for diffuse and specular components.
            # glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ka"), 1, 1, 1)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Kd"), 0.15, 0.15, 0.15)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ks"), 0, 0, 0)

        # FIRST VIEW
        else:
            viewPos = np.array([controller.camx, controller.camy, controller.camz])

            view = tr.lookAt(
                viewPos,
                np.array([0, 0, 0]),
                np.array([0, 0, 1])
            )

            # glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "La"), 1, 1, 1)
            # glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ld"), 1, 1, 1)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ls"), 0.5, 0.5, 0.5)

            # glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ka"), 1, 1, 1)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Kd"), 0.15, 0.15, 0.15)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ks"), 0.5, 0.5, 0.5)

        # glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "La"), 1, 1, 1)
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ld"), 1, 1, 1)
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "lightPosition"), 0, 0, 0)
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "viewPosition"), viewPos[0], viewPos[1],
                    viewPos[2])
        glUniform1ui(glGetUniformLocation(lightPipeline.shaderProgram, "shininess"), 10)

        glUniform1f(glGetUniformLocation(lightPipeline.shaderProgram, "constantAttenuation"), 0.0001)
        glUniform1f(glGetUniformLocation(lightPipeline.shaderProgram, "linearAttenuation"), 0.03)
        glUniform1f(glGetUniformLocation(lightPipeline.shaderProgram, "quadraticAttenuation"), 0.01)

        # Draw star
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "La"), 1, 1, 1)
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ka"), 1, 1, 1)
        glUniformMatrix4fv(glGetUniformLocation(lightPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(lightPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(lightPipeline.shaderProgram, "model"), 1, GL_TRUE,
                           tr.matmul([tr.translate(0, 0, 0), tr.uniformScale(star.radius)]))
        lightPipeline.drawShape(star.gpuShape)

        # Draw bodies
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "La"), 0.5, 0.5, 0.5)
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ka"), 0.1, 0.1, 0.1)
        bc.drawbodies(bodies, lightPipeline, trailPipeline, dt, projection, view, controller)

        glfw.swap_buffers(window)
    glfw.terminate()
