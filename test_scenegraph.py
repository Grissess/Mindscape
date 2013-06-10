import pygame
from pygame.locals import *
from OpenGL.GL import *

from vmath import Vector, Matrix
from scenegraph import *

pygame.init()

WIDTH, HEIGHT=640, 480
ASPECT=float(WIDTH)/HEIGHT
FOV=75

disp=pygame.display.set_mode((WIDTH, HEIGHT), HWSURFACE|OPENGL|DOUBLEBUF)
clock=pygame.time.Clock()
char=pygame.image.load('data/char.png')

glClearColor(0.2, 0.4, 0.4, 0)

cam=PerspectiveCamera(Vector(3, 3, 3), Vector(0, 0, 0), Vector(0, 1, 0), FOV, ASPECT, 0.1, 100)
sc=Scene(cam)
sc.modifications.add(ModBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA))
sc.modifications.add(ModTexFilter(GL_LINEAR, GL_LINEAR))
sc.modifications.add(ModTexWrap(GL_REPEAT, GL_REPEAT))
sc.enable.add(GL_DEPTH_TEST)
sc.enable.add(GL_BLEND)
sc.disable.add(GL_LIGHTING)

tex=Texture(char)

mesh=Mesh(Face(GL_QUADS, Vertex(Vector(-1, -1, 0), Vector(1, 0, 0), tex=Vector(0, 0)),
						 Vertex(Vector(1, -1, 0), Vector(0, 1, 0), tex=Vector(1, 0)),
						 Vertex(Vector(1, 1, 0), Vector(0, 0, 1), tex=Vector(1, 1)),
						 Vertex(Vector(-1, 1, 0), Vector(1, 1, 1), tex=Vector(0, 1))), texture=tex)
mesh.transform.rot=[0, Vector(0, 0, 1)]
mesh.enable.add(GL_TEXTURE_2D)
sc.children.append(mesh)

while True:
	for ev in pygame.event.get():
		if ev.type==QUIT or (ev.type==KEYDOWN and ev.key==K_ESCAPE):
			exit()
	glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
	mesh.transform.rot[0]+=1
	if mesh.transform.rot[0]>=360:
		mesh.transform.rot[0]-=360
	sc.Render()
	pygame.display.flip()
	clock.tick(30)