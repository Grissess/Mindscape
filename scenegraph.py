'''
.. mindscape -- Mindscape Engine
scenegraph -- Scene Graph
=========================

This module contains the definitions of everything useful to the scene graph.

:class:`Renderable`\ s, held by and manipulated by a renderer, are stored in a :class:`Scene`, which
contains an arbitrary number of objects, and an active camera. When a scene is
rendered,

* The active :class:`Camera` is rendered first. This sets up the camera transformation
  for the rest of the scene.
* The objects are rendered in the order they appear in the list. Note that,
  since objects may have children, an object's children finish rendering before
  the call returns, so rendering one object may render an arbitrary number of
  other, child objects.

Any :class:`Renderable` may be one of the following:

* :class:`Mesh`: A collection of vertices in an order appropriate for rendering as a
  sequence of primitives. Meshes form, in general, the most basic 3D
  renderable. They support changing vertex data dynamically, but the
  changed information is not compiled into the display list until the next
  compilation pass, which, at the latest, will be during the next render
  frame.
* AnimatedMesh: Todo!
* Sprite: A texture that is to face the camera, no matter the orientation.

Additionally, the following objects exist in various parts outside the
hierarchy of the scene graph:

* :class:`Vertex`: An object containing all the data needed to define a vertex.
* :class:`Face`: An object containing a set of vertices, and a primitive rendering mode.
* :class:`Texture`: A bound texture.
* :class:`Transform`: A transformation.
'''

import pygame
import numpy
from OpenGL.GL import *
from OpenGL.GLU import *

from vmath import Vector, Matrix

class Modification(object):
	'''The :class:`Modification` is a generic class that applies some state
change to the current context, and reverts that state change (ideally, to the
previous state) later--usually, when that state is no longer needed. It is
actually the parent of quite a few other classes, :class:`Texture` and
:class:`Transform` included.'''
	def Apply(self):
		'''Apply the state change.

.. note::

	This must be defined by a subclass.'''
		raise NotImplementedError('Modification object must define .Apply()')
	def Revert(self):
		'''Revert the state change.

.. note::

	This must be defined by a subclass.'''
		raise NotImplementedError('Modification object must define .Revert()')

class Transform(Modification):
	'''The :class:`Transform` class is actually nothing more than an ABC that
removes the :func:`Modification.Revert` call from the hierarchy (since
:class:`Transform` objects aren't required to revert their transforms; they
depend on the matrix stacks to do that.'''
	def Revert(self):
		'''Raises an error.'''
		raise NotImplementedError('Reversion is not allowed for transformations.')

class PRSTransform(Transform):
	'''The :class:`PRSTransform` is the general-case transform for any object.
It houses three attributes, which may be set to ``None`` to inhibit the GL
call that would normally be invoked. All arguments (which are thereby assigned
directly to the equivalently named attributes) default to ``None``, which makes
this object a no-op in that case. (In fact, the :class:`Renderable` class constructs
such a null-transform by default if none is given.)'''
	def __init__(self, pos=None, rot=None, scale=None):
		#: A 3D :class:`vmath.Vector` to translate by.
		self.pos=pos
		#: An iterable (angle, axis) where angle is a scalar in degrees and axis is a 3D :class:`vmath.Vector`.
		self.rot=rot #Tuple of (angle, axis) where axis is (or is castable to) Vec3
		#: A 3D :class:`vmath.Vector` to scale by.
		self.scale=scale
	def Apply(self):
		'''Apply the transformation to the current matrix.'''
		if self.pos is not None:
			glTranslated(*self.pos.FastTo3())
		if self.rot is not None:
			glRotated(self.rot[0], *self.rot[1].FastTo3())
		if self.scale is not None:
			glScaled(*self.scale.FastTo3())

class MultiTransform(Transform):
	'''The :class:'MultiTransform` simply applies a list of transformations (as
specified in its constructor, or through manipulating the ``transforms``
attribute) in the order given.'''
	def __init__(self, *transforms):
		#: A ``list`` of :class:`Transform`\ s to apply in order.
		self.transforms=list(transforms)
	def Apply(swelf):
		'''Apply the transformation to the current matrix.'''
		for tran in self.transforms:
			tran.Apply()

class MatrixTransform(Transform):
	'''The :class:`MatrixTransform` multiplies the current matrix directly by
the :class:`vmath.Matrix` given.'''
	def __init__(self, matrix):
		#: A :class:`vmath.Matrix` to multiply into the current matrix.
		self.matrix=matrix
	def Apply(self):
		'''Apply the transformation to the current matrix.'''
		glMultMatrixd(*numpy.array(self.matrix.flatten())[0])

class Texture(Modification):
	'''The :class:`Texture` class provides a method to load ``pygame.Surface``\ s
into video memory and onto geometry. The actual mapping of the texture onto the
geometry is determined by texture coordinates (see the :class:`Vertex` class) as
well as the current mapping mode (see :class:`ModTexWrap`). This class is currently
implemented so as to exclusively support 2D textures; however, 3D textures may
become available shortly (and :class:`Vertex` already has support for 4D texture
coordinates), which will make it easier (and faster, but more memory-consuming)
to load animated textures.

If the surface parameter is ``None``, the texture will be allocated, but no
data will be uploaded to it.'''
	def __init__(self, surf=None):
		#: An unsigned integer which represents GL's handle to the texture.
		self.id=glGenTextures(1)
		#: A ``pygame.Surface`` from which the texture data is loaded.
		self.surf=surf
		if surf is not None:
			self.Reload()
	def Reload(self):
		'''Reloads the texture memory from the surface.

.. note::

	You must call this after modifying the texture surface for those changes to
	be visible in GL. This is not guaranteed to be a fast operation; video cards
	(and their drivers) tend to prioritize speed of access over speed of uploading
	(for obvious reasons), so this will likely not be an efficient way to animate
	textures, and should only be done as necessary.'''
		self.Apply()
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.surf.get_width(),
					 self.surf.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE,
					 pygame.image.tostring(self.surf, 'RGBA', True))
	def Apply(self):
		'''Bind the texture such that it is available for the next rendering operation.'''
		glBindTexture(GL_TEXTURE_2D, self.id)
	def Revert(self):
		'''Does nothing.

.. note::

	If you don't want to have your geometry be affected by the texture any more,
	disable GL_TEXTURE_2D. This is easiest done by having it so that
	GL_TEXTURE_2D is enabled only so long as that geometry is rendering--by
	putting it in the :attr:`Renderable.enable` set.'''
		pass #XXX Should we actually rebind the old texture? What if there isn't one?

class ModBlendFunc(Modification):
	'''This is a simple :class:`Modification` which changes the current GL
blend function. The arguments are expected to be equivalent to the glBlendFunc
call'''
	def __init__(self, srcfunc, dstfunc):
		#: An unsigned integer specifying the source function (see the GL documentation)
		self.srcfunc=srcfunc
		#: An unsigned integer specifying the destination function (see the GL documentation)
		self.dstfunc=dstfunc
	def Apply(self):
		'''Apply the blending function.'''
		glBlendFunc(self.srcfunc, self.dstfunc)
	def Revert(self):
		'''Does nothing.

.. note::

	This behavior shouldn't be a problem so long as you remember to modify the
	blending function (or disable) GL_BLEND as needed. See :func:`Texture.Revert`.'''
		pass #XXX See above.

class ModTexFilter(Modification):
	'''This :class:`Modification` changes the texture filter parameters. The
parameters given are expected to be the same ones given in a glTexParameterf
call with GL_TEXTURE_2D as the target and ...MAG_FILTER or ...MIN_FILTER as
the parameter.'''
	def __init__(self, minfilter, magfilter):
		#: An unsigned integer specifying the minification filter (see the GL documentation)
		self.minfilter=minfilter
		#: An unsigned integer specifying the magnification filter (see the GL documentation)
		self.magfilter=magfilter
	def Apply(self):
		'''Applies the texture filters.'''
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, self.minfilter)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, self.magfilter)
	def Revert(self):
		'''Does nothing.

.. note::

	This shouldn't be a problem if you set this as needed and disable GL_TEXTURE_2D
	when you're not using it (see :func:`Texture.Revert`.) In general, this only
	needs to be set once for the whole application, barring special circumstances.'''
		pass #XXX Ditto...again.

class ModTexWrap(Modification):
	'''This :class:`Modification` changes the texture wrapping parameters. The
parameters given are expected to be the same ones given in a glTexParameterf
call with GL_TEXTURE_2D as the target and ...WRAP_S or ...WRAP_T as
the parameter.'''
	def __init__(self, wraps, wrapt):
		#: An unsigned integer specifying the s coordinate wrapping mode (see the GL documentation)
		self.wraps=wraps
		#: An unsigned integer specifying the t coordinate wrapping mode (see the GL documentation)
		self.wrapt=wrapt
	def Apply(self):
		'''Apply the wrapping mode.'''
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, self.wraps)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, self.wrapt)
	def Revert(self):
		'''Does nothing.

.. note::

	See :func:`ModTexFilter.Revert`.'''
		pass #XXX ...must I repeat myself?

class ModCall(Modification):
	'''This :class:`Modification` calls a specified function with the
specified arguments when it is applied. This is intended to allow for the
inclusion of esoteric or unimplemented state-changing features.

Currently, reversion is not supported, but it probably will be.'''
	def __init__(self, func, *args):
		#: A ``callable`` to be called.
		self.func=func
		#: An iterable of arguments to be passed positionally.
		self.args=args
	def Apply(self):
		'''Call the function.'''
		self.func(*self.args)
	def Revert(self):
		'''Does nothing.

.. note::

	Todo!'''
		pass #XXX This one might actually be a problem...

class Renderable(object):
	'''The :class:`Renderable` class implements anything and everything that
can actually be drawn to the screen. Importantly, it is responsible for
implementing the shared functionality between all such objects, such as their
ability to have children under their coordinate space, to enable and disable
GL features, to be set to a specific matrix mode, to implement transformations,
and to modify the current state--and possibly more.

The renderable constructor is interesting in that it interprets all of its
positional arguments as being children. To specify non-children arguments, such
arguments *must* be given as keyword arguments. Furthermore, this giving (and
propagating) of keyword arguments is copied down the inheritance chain, meaning
that the :attr:`texture` argument has the same meaning on a :class:`WSSprite`
as it does a :class:`Mesh`, or even a :class:`Camera` (though it is not used
there). Keep this inheritance in mind when considering how to, e.g., move a
:class:`Mesh`, change the texture of a :class:`WSSprite`, etc.'''
	def __init__(self, *children, **kwargs):
		#: A list of :class:`Renderable`\ s, which may be empty.
		self.children=list(children)
		#: A :class:`Transform` to be applied before rendering; defaults to an empty :class:`PRSTransform`.
		self.transform=kwargs.get('transform', PRSTransform())
		#: A ``set`` of states to be enabled before rendering; defaults to an empty set.
		self.enable=kwargs.get('enable', set())
		#: A ``set`` of states to be disabled before rendering; defaults to an empty set.
		self.disable=kwargs.get('disable', set())
		#: An unsigned integer (or None, by default) which, if set, forces the matrix mode before rendering.
		self.mmode=kwargs.get('mmode', None)
		#: A :class:`Texture` to be bound before rendering, if set (default None).
		self.texture=kwargs.get('texture', None)
		#: A ``set`` of modifications to be :func:`Modification.Apply`'d before rendering; default empty.
		self.modifications=kwargs.get('modifications', set())
	def PushState(self):
		'''Push the state (set up everything before actually rendering).

.. note::

	You can do this by using the object as a context manager::

		with renderable:
			renderable.Render()

	This is guaranteed to call :func:`PopState` for you, even if an error occurs.'''
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
		'''Pop the state (undo all modifications done before rendering).'''
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
		'''Actually render the object.

.. note::

	This must be defined in a subclass.'''
		raise NotImplementedError('Renderable derivative must implement .Render()')
	def RenderChildren(self):
		'''Render all child objects.

This is intended to be called from within a defined :func:`Render` method.

.. warning::

	There is no guarantee as to how a child may change the state, or what function
	calls it will make while rendering--which is of particular concern if you're
	between glBegin() and glEnd(). You should not call this method from inside
	such a pairing, nor should you call it if you're concerned about losing some
	of your state information; it's best to call this at the end of :func:`Render`
	and depend on your own :func:`PopState` method to do whatever cleanup is
	needed.'''
		for child in self.children:
			with child:
				child.Render()

class Camera(Renderable):
	'''This class is the base class to two more specific cameras, but it also
implements the shared functionality of setting up the GL_MODELVIEW side of the
camera transformation--which makes the camera have a set position and orientation
in the scene.'''
	def __init__(self, pos, center, up, **kwargs):
		super(Camera, self).__init__(**kwargs)
		#: A 3D :class:`vmath.Vector` representing the camera position.
		self.pos=pos
		#: A 3D :class:`vmath.Vector` representing the point to look at.
		self.center=center
		#: A 3D :class:`vmath.Vector` representing up direction.
		self.up=up
		self.mmode=GL_MODELVIEW
	def PushState(self):
		'''Does nothing. (The default :func:`Renderable.PushState` would interfere with the matrix mode.)'''
		pass #Do not affect the matrix stack; this one must remain current.
	def PopState(self):
		'''Does nothing. (The default :func:`Renderable.PopState` would interfere with the matrix mode.)'''
		pass #Ditto.
	def Render(self):
		'''Sets up the camera transformation.'''
		glMatrixMode(GL_MODELVIEW)
		gluLookAt(*(tuple(self.pos.FastTo3())+tuple(self.center.FastTo3())+tuple(self.up.FastTo3())))
		self.RenderChildren()

class PerspectiveCamera(Camera):
	'''A :class:`Perspective` camera is a :class:`Camera` whose projection
matrix is created by using the gluPerspective function, to which this class'
constructor (and attributes) are applied.'''
	def __init__(self, pos, center, up, fov, aspect, near, far, **kwargs):
		super(PerspectiveCamera, self).__init__(pos, center, up, **kwargs)
		#: A floating point field-of-view along the Y dimension.
		self.fov=fov
		#: A floating point aspect ratio representing the viewport's X/Y ratio.
		self.aspect=aspect
		#: The near clipping plane (>0)
		self.near=near
		#: The far clipping plane. (>0)
		self.far=far
		self.mmode=GL_PROJECTION
	def Render(self):
		'''Apply the camera projection.'''
		super(PerspectiveCamera, self).Render()
		glMatrixMode(GL_PROJECTION)
		gluPerspective(self.fov, self.aspect, self.near, self.far)

class OrthographicCamera(Camera):
	'''A :class:`Perspective` camera is a :class:`Camera` whose projection
matrix is created by using the gluOrtho2D function, to which this class'
constructor (and attributes) are applied.'''
	def __init__(self, pos, center, up, left, right, bottom, top, **kwargs):
		super(PerspectiveCamera, self).__init__(pos, center, up, **kwargs)
		#: The leftmost coordinate.
		self.left=left
		#: The lrightmost coordinate.
		self.right=right
		#: The bottommost coordinate.
		self.bottom=bottom
		#: The topmost coordinate.
		self.top=top
		self.mmode=GL_PROJECTION
	def Render(self):
		'''Apply the camera projection.'''
		super(PerspectiveCamera, self).Render()
		glMatrixMode(GL_PROJECTION)
		gluOrtho2D(self.left, self.right, self.bottom, self.top)

class Scene(Renderable):
	'''A :class:`Scene` is intended to be the scenegraph parent of all other
children in the graph. Thereby, the :class:`Scene` is solely responsible for
setting up the global state and initializing the GL to a known state before
rendering all of its objects.

Despite this design intention, it is entirely possible to have multiple
:class:`Scene`\ s, or :class:`Scene`\ s within :class:`Scene`\ s, etc.'''
	def __init__(self, camera, **kwargs):
		super(Scene, self).__init__(**kwargs)
		self.camera=camera
	def Render(self):
		'''Renders the scene.

.. note::

	To ensure that the :class:`Scene` has initialized the environment properly,
	you *must* call :func:`Renderable.PushState` and :func:`Renderable.PopState`
	as you would for a normal :class:`Renderable` before rendering it. This is
	most easily accomplished by using the :class:`Renderable`'s context-manager
	feature::

		with scene:
			scene.Render()'''
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		with self.camera:
			self.camera.Render()
		glMatrixMode(GL_MODELVIEW)
		self.RenderChildren()

class Mesh(Renderable):
	'''A :class:`Mesh` object consists of zero or more :class:`Faces`, and
represents the smallest object that can be compiled into a GL display list.
Aside from this feature, they are no different from any other :class:`Renderable`.'''
	def __init__(self, *faces, **kwargs):
		super(Mesh, self).__init__(**kwargs)
		#: A list of :class:`Face` objects
		self.faces=list(faces)
		#: Whether or not to compile this :class:`Mesh`.
		self.compile=kwargs.get('compile', True)
	def Compile(self, execute=False):
		'''Compile the mesh.

.. note::

	This performs the process unconditionally, and will disregard the :attr:`compile`
	attribute. However, without the :attr:`compile` attribute set, the compiled
	display list won't actually be called on rendering. (One surmises the resultant
	display list could, of course, be used elsewhere for hackish reasons...).'''
		if not hasattr(self, 'list'):
			self.list=glGenLists(1)
		glNewList(self.list, (GL_COMPILE_AND_EXECUTE if execute else GL_COMPILE))
		self.Render(True)
		glEndList()
	def Render(self, justgeometry=False):
		'''Renders the mesh. if :attr:`compile` is True, this will also compile
the mesh, if needed.'''
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
	'''The :class:`Face` class represents one GL primitive as a primitive mode
and a sequence of vertices (of the type :class:`Vertex`).'''
	def __init__(self, mode, *vertices, **kwargs):
		super(Face, self).__init__(**kwargs)
		#: The primitive mode, to be passed to glBegin.
		self.mode=mode
		#: An iterable of :class:`Vertex` objects.
		self.vertices=list(vertices)
	def Render(self):
		'''Render the face (by drawing one primitive).

.. note::

	Due to concerns highlighted in :func:`Renderable.RenderChildren`, the
	:class:`Face` does not render its children until after the drawing of the
	primitive is over, nor does it push the state of a :class:`Vertex`.'''
		glBegin(self.mode)
		for vertex in self.vertices:
			#Can't transform--it performs things like pushing matrices that
			#will error on our glBegin/End pair.
			vertex.Render()
		glEnd()
		self.RenderChildren()

class Vertex(Renderable):
	'''A :class:`Vertex` is, quite possibly, the most primitive :class:`Renderable`
derivative. When rendered, the :class:`Vertex` will call at most four functions,
the final one of which being glVertex4d, which places a vertex into a primitive.
The :class:`Vertex` class also, of course, provides support for color, normals,
and texture coordinates of these vertices.'''
	def __init__(self, pos, col=None, norm=None, tex=None, **kwargs):
		super(Vertex, self).__init__(**kwargs)
		#: A 4D :class:`vmath.Vector` representing the vertex's local position.
		self.pos=pos
		#: A 4D :class:`vmath.Vector` representing the vertex's color and alpha.
		self.col=col
		#: A 3D :class:`vmath.Vector` representing the vertex's normal vector.
		self.norm=norm
		#: A 4D :class:`vmath.Vector` representing the vertex's texture coordinate.
		self.tex=tex
	def Render(self):
		'''Renders the vertex.

.. note::

	As outlined in :func:`Face.Render`, ``PushState()`` and ``PopState()`` will
	not be called for a :class:`Vertex`, because these are likely to introduce
	calls which are illegal between glBegin and glEnd.'''
		if self.col is not None:
			glColor4d(*self.col.FastTo4())
		if self.tex is not None:
			glTexCoord3d(*self.tex.FastTo3())
		if self.norm is not None:
			glNormal3d(*self.norm.FastTo3())
		glVertex4f(*self.pos.FastTo4())

class SSSprite(Renderable):
	'''An :class:`SSSprite`, or a "Screen Space Sprite," is a sprite (fixed,
textured graphic which always renders orthogonal to the view) which is positioned
relative to the screen space--wherein the lower left corner is (-1, -1), the
upper right corner is (1, 1), and the Z-coordinate is only used during depth
testing (with GL_DEPTH_TEST enabled) to allow for Z-ordering occlusion. For
this class to be useful at all, the :attr:`Renderable.texture` attribute must
be set.'''
	def __init__(self, pos=None, size=None, center=False, **kwargs):
		super(SSSprite, self).__init__(**kwargs)
		#: A 3D :class:`vmath.Vector` representing the lower left corner position in screen space (or the center if :attr:`center` is True).
		self.pos=(Vector(0, 0, 0) if pos is None else pos)
		#: A 2D :class:`vmath.Vector` representing the size of the sprite in screen space (where 2 is full width/height).
		self.size=(Vector(1, 1) if size is None else size)
		#: True if the :attr:`pos` attribute is to be interpreted as a center point instead of the lower left corner.
		self.center=center
	def Render(self, pos=None, size=None):
		'''Renders the sprite; optionally, an override position and size may be given.'''
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
	'''A :class:`WSSprite`, or "World Space Sprite," is a sprite that appears
at a specified position in the scene, rather than at a fixed screen space
coordinate. Aside from that, it is functionally identical to its parent class,
the :class:`SSSprite`.'''
	def __init__(self, mapsize=False, **kwargs):
		super(WSSprite, self).__init__(**kwargs)
		#: (Not implemented; will eventually map the size using the depth coordinate.)
		self.mapsize=mapsize #TODO: Implement this. How?
	def Render(self):
		'''Renders the sprite (by passing in the position override parameter to
:func:`SSSprite.Render`).'''
		x, y, z=gluProject(*self.pos.FastTo3(), view=numpy.array([-1, -1, 2, 2]))
		#The weird viewport above should (theoretically) give us an identity viewport.
##		print 'Render at', x, y, z
		super(WSSprite, self).Render(Vector(x, y, z))
		self.RenderChildren()