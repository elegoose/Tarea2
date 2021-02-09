import glfw
from OpenGL.GL import *
import sys
import lighting_shaders as ls
import easy_shaders as es
import bodyclass as bc
import basic_shapes as bs
import transformations as tr
import numpy as np

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

    lightPipeline = ls.SimpleGouraudShaderProgram()
    bodyPipeline = es.SimpleModelViewProjectionShaderProgram()
    texturePipeline = es.SimpleTextureModelViewProjectionShaderProgram()

    gpuSkyBox = es.toGPUShape(bs.createTextureCube("skybox.jpg"), GL_REPEAT, GL_LINEAR)

    skybox_transform = tr.uniformScale(20)
    glClearColor(0.15, 0.15, 0.15, 1.0)
    glEnable(GL_DEPTH_TEST)

    bodies = bc.getbodiesinfo('bodies.json', proportion)

    star = bodies[0]
    star.gpuShape = star.getgpushape()
    bodies = bodies[1:]

    t0 = glfw.get_time()
    camera_theta = 0
    camZ = 0
    Rc = 5

    projection = tr.perspective(45, float(width) / float(height), 0.1, 100)

    while not glfw.window_should_close(window):
        glfw.poll_events()

        t1 = glfw.get_time()
        dt = t1 - t0
        if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
            camera_theta -= 0.01

        if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
            camera_theta += 0.01

        if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
            camZ += 0.1

        if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
            camZ -= 0.1
        if glfw.get_key(window, glfw.KEY_Z) == glfw.PRESS:
            Rc -= 0.1
        if glfw.get_key(window, glfw.KEY_X) == glfw.PRESS:
            Rc += 0.1
            # Setting up the view transform

        camX = Rc * np.cos(camera_theta)
        camY = Rc * np.sin(camera_theta)
        viewPos = np.array([camX, camY, camZ])

        view = tr.lookAt(
            viewPos,
            np.array([0, 0, 0]),
            np.array([0, 0, 1])
        )
        for planeta in bodies:

            theta = planeta.theta + planeta.velocity * dt
            planeta.posx = planeta.distance * np.cos(theta)
            planeta.posy = planeta.distance * np.sin(theta)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        #Skybox
        glUseProgram(texturePipeline.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(texturePipeline.shaderProgram, "model"), 1, GL_TRUE, skybox_transform)
        glUniformMatrix4fv(glGetUniformLocation(texturePipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(texturePipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        texturePipeline.drawShape(gpuSkyBox)

        #Bodies
        glUseProgram(lightPipeline.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(lightPipeline.shaderProgram, "projection"), 1, GL_TRUE, projection)
        glUniformMatrix4fv(glGetUniformLocation(lightPipeline.shaderProgram, "view"), 1, GL_TRUE, view)
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "La"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ld"), 1.0, 1.0, 1.0)
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ls"), 1.0, 1.0, 1.0)

        # Object is barely visible at only ambient. Bright white for diffuse and specular components.
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ka"), 0.4, 0.4, 0.4)
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Kd"), 0.9, 0.9, 0.9)
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "Ks"), 1.0, 1.0, 1.0)

        # Here we can see how we can change the light position and view position at the same time.
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "lightPosition"), 0, 0,0)
        glUniform3f(glGetUniformLocation(lightPipeline.shaderProgram, "viewPosition"), viewPos[0], viewPos[1],
                    viewPos[2])
        glUniform1ui(glGetUniformLocation(lightPipeline.shaderProgram, "shininess"), 10)

        glUniform1f(glGetUniformLocation(lightPipeline.shaderProgram, "constantAttenuation"), 0.0001)
        glUniform1f(glGetUniformLocation(lightPipeline.shaderProgram, "linearAttenuation"), 0.03)
        glUniform1f(glGetUniformLocation(lightPipeline.shaderProgram, "quadraticAttenuation"), 0.01)
        glUniformMatrix4fv(glGetUniformLocation(lightPipeline.shaderProgram, "model"), 1, GL_TRUE,
                           tr.matmul([tr.translate(0, 0, 0), tr.uniformScale(star.radius)]))
        lightPipeline.drawShape(star.gpuShape)
        bc.drawbodies(bodies,lightPipeline,dt)
        glfw.swap_buffers(window)
    glfw.terminate()
