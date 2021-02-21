import numpy as np
import basic_shapes as bs


def createCircle(N, r, g, b,radius):
    vertices = [0, 0, 0, r, g, b]  # Primer vertice
    indices = []

    dtheta = 2 * np.pi / N

    for i in range(N):
        theta = i * dtheta

        vertices += [
            # vertex coordinates
            radius * np.cos(theta), radius * np.sin(theta), 0,
            r, g, b]

        # Se crean triángulos respecto al centro para rellenar la circunferencia
        indices += [0, i, i + 1]
    # Conectado al segundo vertice
    indices += [0, N, 1]

    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)

    return bs.Shape(vertices, indices)


def createTrail(radio, N):
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
