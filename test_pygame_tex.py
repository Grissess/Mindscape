import pygame
from OpenGL.GL import *
from pygame.locals import *

pygame.init()

disp=pygame.display.set_mode((640, 480), HWSURFACE|OPENGL|DOUBLEBUF)

#-----Initialize textures-----

char=pygame.image.load('data/char.png')

char_id=glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, char_id)
#glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, char.get_width(), char.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, pygame.image.tostring(char, 'RGBA', True))

#-----Initialize viewport and rendering-----

glDisable(GL_LIGHTING)
glEnable(GL_TEXTURE_2D)
#glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

glClearColor(0, 0, 1, 0)

glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

#-----Initialize rendering-----

mainlist=glGenLists(1)
glNewList(mainlist, GL_COMPILE)

glBegin(GL_QUADS)
for x, y in zip((-1, 1, 1, -1), (-1, -1, 1, 1)):
	glColor4f(1, 1, 1, 1)
	glTexCoord2f(x, y)
	glVertex3f(x, y, 0)
glEnd()

glEndList()

#-----Initialize timing utilities-----

clock=pygame.time.Clock()

while True:
	for ev in pygame.event.get():
		if ev.type==QUIT or (ev.type==KEYDOWN and ev.key==K_ESCAPE):
			exit()
	glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
	glRotatef(1, 0, 0, 1)
	glCallList(mainlist)
	pygame.display.flip()
	clock.tick(30)
	

