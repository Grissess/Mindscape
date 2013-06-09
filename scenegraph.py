'''
mindscape -- Mindscape Engine
scenegraph -- Scene Graph

This module contains the definitions of everything useful to the scene graph.

Objects, held by and manipulated by a renderer, are stored in a Scene, which
contains an arbitrary number of objects, and an active camera. When a scene is
rendered,
-The active camera is rendered first. This sets up the camera transformation
 for the rest of the scene.
-The objects are rendered in the order they appear in the list. Note that,
 since objects may have children, an object's children finish rendering before
 the call returns, so rendering one object may render an arbitrary number of
 other, child objects.

Any "object" may be one of the following:
Mesh: A collection of vertices in an order appropriate for rendering as a
	  sequence of primitives. Meshes form, in general, the most basic 3D
	  renderable. They support changing vertex data dynamically, but the
	  changed information is not compiled into the display list until the next
	  compilation pass, which, at the latest, will be during the next render
	  frame.
AnimatedMesh: Todo!
Sprite: A texture that is to face the camera, no matter the orientation.

Additionally, the following objects exist in various parts outside the
hierarchy of the scene graph:
Vertex: An object containing all the data needed to define a vertex.
Face: An object containing a set of vertices, and a primitive rendering mode.
Texture: A bound texture.
Transform: A transformation.
'''

import pygame
import numpy
from OpenGL.GL import *
from OpenGL.GLU import *

from vmath import Vector, Matrix

class Modification(object):
	def Apply(self):
		raise NotImplementedError('Modification object must define .Apply()')
	def Revert(self):
		raise NotImplementedError('Modification object must define .Revert()')

class Transform(Modification):
	pass #Just an ABC

class PRSTransform(Transform):
	def __init__(self, pos=None, rot=None, scale=None):
		self.pos=pos
		self.rot=rot #Tuple of (angle, axis) where axis is (or is castable to) Vec3
		self.scale=scale
	def Apply(self):
		if self.pos is not None:
			glTranslated(*self.pos.FastTo3())
		if self.rot is not None:
			glRotated(self.rot[0], *self.rot[1].FastTo3())
		if self.scale is not None:
			glScaled(*self.scale.FastTo3())
	def Revert(self): #Since the matrix stack handles these...
		raise NotImplementedError('Reversion is not allowed for transformations.')

class MultiTransform(Transform):
	def __init__(self, *transforms):
		self.transforms=list(transforms)
	def Apply(swelf):
		for tran in self.transforms:
			tran.Apply()

class MatrixTransform(Transform):
	def __init__(self, matrix):
		self.matrix=matrix
	def Apply(self):
		glMultMatrixd(*numpy.array(self.matrix.flatten())[0])

class Texture(Modification):
	def __init__(self, surf):
		self.id=glGenTextures(1)
		self.surf=surf
		self.Reload()
	def Reload(self):
		self.Apply()
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.surf.get_width(),
					 self.surf.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE,
					 pygame.image.tostring(self.surf, 'RGBA', True))
	def Apply(self):
		glBindTexture(GL_TEXTURE_2D, self.id)
	def Revert(self):
		pass #XXX Should we actually rebind the old texture? What if there isn't one?

class ModBlendFunc(Modification):
	def __init__(self, srcfunc, dstfunc):
		self.srcfunc=srcfunc
		self.dstfunc=dstfunc
	def Apply(self):
		glBlendFunc(self.srcfunc, self.dstfunc)
	def Revert(self):
		pass #XXX See above.

class ModTexFilter(Modification):
	def __init__(self, minfilter, magfilter):
		self.minfilter=minfilter
		self.magfilter=magfilter
	def Apply(self):
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, self.minfilter)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, self.magfilter)
	def Revert(self):
		pass #XXX Ditto...again.

class ModTexWrap(Modification):
	def __init__(self, wraps, wrapt):
		self.wraps=wraps
		self.wrapt=wrapt
	def Apply(self):
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, self.wraps)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, self.wrapt)
	def Revert(self):
		pass #XXX ...must I repeat myself?

class ModCall(Modification):
	def __init__(self, func, *args):
		self.func=func
		self.args=args
	def Apply(self):
		self.func(*self.args)
	def Revert(self):
		pass #XXX This one might actually be a problem...

class Renderable(object):
	#An object which can be rendered and may have other renderables as children.
	def __init__(self, *children, **kwargs):
		self.children=list(children)
		self.transform=kwargs.get('transform', PRSTransform())
		self.enable=kwargs.get('enable', set())
		self.disable=kwargs.get('disable', set())
		self.mmode=kwargs.get('mmode', None)
		self.texture=kwargs.get('texture', None)
		self.modifications=kwargs.get('modifications', set())
	def PushState(self):
		if self.enable or self.disable:
			glPushAttrib(GL_ENABLE_BIT)
			for en in self.enable:
				glEnable(en)
			for dis in self.disable:
				glDisable(dis)
		if self.mmode is not None:
			glMatrixMode(self.mmode)
		glPushMatrix()
		self.transform.Apply()
		if self.texture is not None:
			self.texture.Apply()
		for mod in self.modifications:
			mod.Apply()
	def PopState(self):
		for mod in self.modifications:
			mod.Revert()
		if self.mmode is not None:
			glMatrixMode(self.mmode)
		glPopMatrix()
		if self.enable or self.disable:
			glPopAttrib()
	#Context-manager hacks
	def __enter__(self):
		self.PushState()
	def __exit__(self, *exc_info):
		self.PopState()
	def Render(self):
		raise NotImplementedError('Renderable derivative must implement .Render()')
	def RenderChildren(self):
		for child in self.children:
			with child:
				child.Render()

class Camera(Renderable):
	def __init__(self, pos, center, up, **kwargs):
		super(Camera, self).__init__(**kwargs)
		self.pos=pos
		self.center=center
		self.up=up
		self.mmode=GL_MODELVIEW
	def PushState(self):
		pass #Do not affect the matrix stack; this one must remain current.
	def PopState(self):
		pass #Ditto.
	def Render(self):
		glMatrixMode(GL_MODELVIEW)
		gluLookAt(*(tuple(self.pos.FastTo3())+tuple(self.center.FastTo3())+tuple(self.up.FastTo3())))
		self.RenderChildren()

class PerspectiveCamera(Camera):
	def __init__(self, pos, center, up, fov, aspect, near, far, **kwargs):
		super(PerspectiveCamera, self).__init__(pos, center, up, **kwargs)
		self.fov=fov
		self.aspect=aspect
		self.near=near
		self.far=far
		self.mmode=GL_PROJECTION
	def Render(self):
		super(PerspectiveCamera, self).Render()
		glMatrixMode(GL_PROJECTION)
		gluPerspective(self.fov, self.aspect, self.near, self.far)

class OrthographicCamera(Camera):
	def __init__(self, pos, center, up, left, right, bottom, top, **kwargs):
		super(PerspectiveCamera, self).__init__(pos, center, up, **kwargs)
		self.left=left
		self.right=right
		self.bottom=bottom
		self.top=top
		self.mmode=GL_PROJECTION
	def Render(self):
		super(PerspectiveCamera, self).Render()
		glMatrixMode(GL_PROJECTION)
		gluOrtho2D(self.left, self.right, self.bottom, self.top)

class Scene(Renderable):
	def __init__(self, camera, **kwargs):
		super(Scene, self).__init__(**kwargs)
		self.camera=camera
	def Render(self):
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		with self.camera:
			self.camera.Render()
		glMatrixMode(GL_MODELVIEW)
		self.RenderChildren()

class Mesh(Renderable):
	def __init__(self, *faces, **kwargs):
		super(Mesh, self).__init__(**kwargs)
		self.faces=list(faces)
		self.compile=kwargs.get('compile', True)
	def Compile(self, execute=False):
		if not hasattr(self, 'list'):
			self.list=glGenLists(1)
		glNewList(self.list, (GL_COMPILE_AND_EXECUTE if execute else GL_COMPILE))
		self.Render(True)
		glEndList()
	def Render(self, justgeometry=False):
		if self.compile and not justgeometry:
			if hasattr(self, 'list'):
				glCallList(self.list)
			else:
				self.Compile(True)
			self.RenderChildren()
			return
		for face in self.faces:
			with face:
				face.Render()
		if not justgeometry:
			self.RenderChildren()

class Face(Renderable):
	def __init__(self, mode, *vertices, **kwargs):
		super(Face, self).__init__(**kwargs)
		self.mode=mode
		self.vertices=list(vertices)
	def Render(self):
		glBegin(self.mode)
		for vertex in self.vertices:
			#Can't transform--it performs things like pushing matrices that
			#will error on our glBegin/End pair.
			vertex.Render()
		glEnd()
		self.RenderChildren()

class Vertex(Renderable):
	def __init__(self, pos, col=None, norm=None, tex=None, **kwargs):
		super(Vertex, self).__init__(**kwargs)
		self.pos=pos
		self.col=col
		self.norm=norm
		self.tex=tex
	def Render(self):
		if self.col is not None:
			glColor4d(*self.col.FastTo4())
		if self.tex is not None:
			glTexCoord3d(*self.tex.FastTo3())
		if self.norm is not None:
			glNormal3d(*self.norm.FastTo3())
		glVertex4f(*self.pos.FastTo4())

class SSSprite(Renderable):
	def __init__(self, pos=None, size=None, center=False, **kwargs):
		super(SSSprite, self).__init__(**kwargs)
		self.pos=(Vector(0, 0, 0) if pos is None else pos)
		self.size=(Vector(1, 1) if size is None else size)
		self.center=center
	def Render(self, pos=None, size=None):
		if pos is None:
			pos=self.pos
		if size is None:
			size=self.size
		#Reset the matrices
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		#Ensure we're actually using the texture
		glEnable(GL_TEXTURE_2D)
		#Set the color such that modulation is essentially nullified
		glColor4d(1, 1, 1, 1)
		#Render to the screen
		low=(-1 if self.center else 0)
		glBegin(GL_QUADS)
		glTexCoord2d(0, 0)
		glVertex3d(pos.x+low*size.x, pos.y+low*size.x, pos.z)
		glTexCoord2d(1, 0)
		glVertex3d(pos.x+size.x, pos.y+low*size.y, pos.z)
		glTexCoord2d(1, 1)
		glVertex3d(pos.x+size.x, pos.y+size.y, pos.z)
		glTexCoord2d(0, 1)
		glVertex3d(pos.x+low*size.x, pos.y+size.y, pos.z)
		glEnd()
		#Disable the texture (others may re-enable it later)
		glDisable(GL_TEXTURE_2D)
		#Restore matrices
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		glPopMatrix()
		self.RenderChildren()

class WSSprite(SSSprite):
	def __init__(self, mapsize=False, **kwargs):
		super(WSSprite, self).__init__(**kwargs)
		self.mapsize=mapsize #TODO: Implement this. How?
	def Render(self):
		x, y, z=gluProject(*self.pos.FastTo3(), view=numpy.array([-1, -1, 2, 2]))
		#The weird viewport above should (theoretically) give us an identity viewport.
##		print 'Render at', x, y, z
		super(WSSprite, self).Render(Vector(x, y, z))
		self.RenderChildren()