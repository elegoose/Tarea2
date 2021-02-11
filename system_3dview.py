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
        controller.bodyID -= 1
    elif key == glfw.KEY_RIGHT:
        controller.bodyID += 1


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

        glUseProgram(lightPipeline.shaderProgram)
        # SECOND VIEW
        if controller.followbody:
            selectedbody = star
            for body in bodies:
                if controller.bodyID == body.bodyID:
                    selectedbody = body
                if body.satellites != 'Null':
                    for satellite in body.satellites:
                        if controller.bodyID == satellite.bodyID:
                            selectedbody = satellite

            viewPos = np.array([selectedbody.posx, selectedbody.posy, controller.camz])
            eye = np.array(
                [selectedbody.posx + controller.camx, selectedbody.posy + controller.camy,
                 controller.camz])
            view = tr.lookAt(
                eye,
                viewPos,  # The camera will be the sun
                np.array([0, 0, 1])
            )

            # White light in all components: ambient, diffuse and specular.
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "La"), 1.0, 1.0, 1.0)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ld"), 0.3, 0.3, 0.3)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ls"), 0.3, 0.3, 0.3)

            # Object is barely visible at only ambient. Bright white for diffuse and specular components.
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ka"), 0.1, 0.1, 0.1)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Kd"), 0.3, 0.3, 0.3)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ks"), 0.3, 0.3, 0.3)

            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "lightPosition"),
                        selectedbody.posx,
                        selectedbody.posy, 0)
        # FIRST VIEW
        else:
            viewPos = np.array([controller.camx, controller.camy, controller.camz])

            view = tr.lookAt(
                viewPos,
                np.array([0, 0, 0]),
                np.array([0, 0, 1])
            )

            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "La"), 1.0, 1.0, 1.0)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ld"), 1.0, 1.0, 1.0)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ls"), 1.0, 1.0, 1.0)

            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ka"), 0.4, 0.4, 0.4)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Kd"), 0.9, 0.9, 0.9)
            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ks"), 1.0, 1.0, 1.0)

            glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "lightPosition"), 0, 0, 0)

        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "viewPosition"), viewPos[0], viewPos[1],
                    viewPos[2])
        glUniform1ui(glGetUniformLocation(lightPipeline.shaderProgram, "shininess"), 10)

        glUniform1f(glGetUniformLocation(lightPipeline.shaderProgram, "constantAttenuation"), 0.0001)
        glUniform1f(glGetUniformLocation(lightPipeline.shaderProgram, "linearAttenuation"), 0.03)
        glUniform1f(glGetUniformLocation(lightPipeline.shaderProgram, "quadraticAttenuation"), 0.01)

        # Draw star
        glUniformMatrix4fv(glGetUniformLocation(lightPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(lightPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniformMatrix4fv(glGetUniformLocation(lightPipeline.shaderProgram, "model"), 1, GL_TRUE,
                           tr.matmul([tr.translate(0, 0, 0), tr.uniformScale(star.radius)]))
        lightPipeline.drawShape(star.gpuShape)

        # Draw bodies
        bc.drawbodies(bodies, lightPipeline, trailPipeline, dt, projection, view)

        glfw.swap_buffers(window)
    glfw.terminate()
