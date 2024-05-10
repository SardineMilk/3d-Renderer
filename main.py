
from math import sin, cos, radians

import pygame
import pygame.gfxdraw
from pygame.locals import *
from pygame.math import *
from pygame import gfxdraw

"""
import profiler
profiler.profiler().start(True)
"""

class Face:
    def __init__(self, triangle, colour) -> None:
        self.triangle = triangle
        self.colour = colour

        v1 = triangle[1] - triangle[0]
        v2 = triangle[2] - triangle[0]
        self.normal = v1.cross(v2)
        self.normal = Vector3(self.normal).normalize()

        self.centroid = get_face_centroid(self.triangle)
        
        

class Camera:
    def __init__(self, camera_position, camera_yaw, camera_pitch, camera_roll) -> None:
        self.position = camera_position
        self.yaw = camera_yaw
        self.pitch = camera_pitch
        self.roll = camera_roll


def move_camera():
    speed = MOVE_SPEED * delta/1000
    camera_x, camera_y, camera_z = camera.position
    yaw = radians(camera.yaw)

    if keys[K_w]:  # Move forward
        camera_x += sin(yaw) * speed
        camera_z += cos(yaw) * speed
    if keys[K_s]:  # Move backward
        camera_x -= sin(yaw) * speed
        camera_z -= cos(yaw) * speed
    if keys[K_d]:  # Strafe left
        camera_x += cos(yaw) * speed
        camera_z -= sin(yaw) * speed
    if keys[K_a]:  # Strafe right
        camera_x -= cos(yaw) * speed
        camera_z += sin(yaw) * speed
    if keys[K_SPACE]:  # Move up
        camera_y -= speed
    if keys[K_LSHIFT]:  # Move down
        camera_y += speed

    camera.position = (camera_x, camera_y, camera_z)

    return camera



def process_face(face):
    projected_face = ()  # Pygame polygons need a tuple instead of a list

    relative_pos = face.centroid - camera.position
    dot = face.normal.dot(relative_pos)

    if dot <= 0:
        return None

    for temp_vertex in face.triangle:
        vertex = Vector3(temp_vertex)  # So the vertex isn't edited
        vertex -= camera.position  # subtract because we are moving the world relative to the camera
        # Rotate Yaw - Y
        vertex = vertex.rotate(-camera.yaw, Vector3(0, 1, 0))
        # Rotate Pitch - X
        vertex = vertex.rotate(camera.pitch, Vector3(1, 0, 0))
        # Rotate Roll - Z
        #vertex = vertex.rotate(camera.roll, Vector3(0, 0, 1))
        # Frustum Culling - Don't render if behind camera
        if vertex[2] <= FRUSTUM_TOLERANCE:  # vertex[2] is the z_pos
            # If it's not visible, don't render the face
            return None

        x, y = project_vertex(vertex)
        # Concatenate the projected vertex to the face tuple
        projected_face += ((x, y),)

    # If all vertices are visible
    colour = abs(face.normal[0])*127, abs(face.normal[1])*127, abs(face.normal[2])*127
    processed_face = (projected_face, colour)
    return processed_face



def project_vertex(vertex):
    x, y, z = vertex
    x_2d = ((x / z) + 1) * centre_x
    y_2d = ((y / z) + 1) * centre_y

    return int(x_2d), int(y_2d)


def clamp(n, minn, maxn):
    return max(minn, min(n, maxn))


def read_obj_file(file_name):
    vertices = []
    faces = []
    mesh = []

    # Read and close file
    with open(file_name, "r") as file:
        data = file.readlines()

    for line in data:
        line = line.split(" ")  # Split at every space
        
        line = [x for x in line if x != " " and x != ""]  # Remove excess spaces

        if line[0] == "v":
            vertex = Vector3(float(line[1]), float(line[2]), float(line[3]))
            vertices.append(vertex)
            
        elif line[0] == "f":
            # Discard the identifier
            face_data = line[1:]
            face = []
            # Iterate through the face data and append indices to face
            for indices in face_data:
                if indices != "\n":
                    index_list = indices.split("/")
                    face.append(int(index_list[0])-1)
            faces.append(face)

    for face in faces:
        triangle = [-vertices[i] for i in face]
        face_data = Face(triangle, (0, 127, 127))
        mesh.append(face_data)

    return mesh
                

def get_face_centroid(triangle):

    centroid = Vector3(0, 0, 0)
    centroid += triangle[0]
    centroid += triangle[1]
    centroid += triangle[2]
    centroid /= 3

    return centroid


def get_face_dist(face):
    return (face.centroid-camera.position).length()


# Constants
WIDTH, HEIGHT = 800, 800  # Base resolution for display
FRUSTUM_TOLERANCE = 0.25
MAX_FPS = 250
MOUSE_SENSITIVITY = 0.25
MOVE_SPEED = 5

# Setup pygame and display
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
centre_x, centre_y = screen.get_width()/2, screen.get_height()/2
clock = pygame.time.Clock()

# Misc variables
time = 0
frames = 0
outline = True

# Mouse lock
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

camera = Camera(Vector3(0.0, 0.0, 0.0), 0, 0, 0)

mesh = read_obj_file("human.obj")

running = True
while running:
    # Player logic
    for event in pygame.event.get():  # Movement breaks without this for some reason
        if event.type == MOUSEMOTION:
            mouse_dx, mouse_dy = event.rel
            camera.yaw += mouse_dx * MOUSE_SENSITIVITY
            camera.pitch += mouse_dy * MOUSE_SENSITIVITY
            camera.pitch = clamp(camera.pitch, -90, 90)  # Clamp camera pitch to directly up and down

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            if event.key == K_e:
                outline = not outline

    keys = pygame.key.get_pressed()

    # Time and frame rate
    current_time = pygame.time.get_ticks()
    delta = current_time - time
    time = current_time

    fps = round(clock.get_fps(), 2)

    camera = move_camera()

    mesh = sorted(mesh, key=get_face_dist, reverse=True)  # Sort based on distance from camera to face centroid
    processed_mesh = [process_face(face) for face in mesh] 
    processed_mesh = list(filter(None, processed_mesh))

    # Render
    screen.fill((32, 32, 32))
    for face, colour in processed_mesh:
        pygame.gfxdraw.filled_polygon(screen, face, colour)
        if outline:
            pygame.gfxdraw.aapolygon(screen, face, (127, 127, 127))

    pygame.display.flip()
    clock.tick(MAX_FPS)

    # Print data
    print(f"{fps}, {len(processed_mesh)}/{len(mesh)}")

pygame.quit()