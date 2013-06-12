'''
.. mindscape -- Mindscape Engine
layout -- Layout Manager
========================

This module provides an interface to a simple layout manager which is entirely
compatible with the scenegraph (provided that it is rendered after 3D geometry
and with the depth test turned off). The layout manager is a *tiling* manager,
which means that it deals with :class:`Grid`\ s.
'''

import pygame
from OpenGL.GL import *

from vmath import Vector
from scenegraph import Renderable, Texture
from event import EVENT, KBD, MOUSE

class LayoutCell(object):
	'''A :class:`LayoutCell` represents a single cell in a layout facility. In
particular, once computations have been undergone by the manager holding (a set)
of these cells, the :attr:`offset` and :attr:`size` attributes should represent
the (window coordinate) space that this cell takes up, on one dimension. (Two
cells are needed for two dimensions.)'''
	def __init__(self, weight=1.0, fixed=0):
		#: A floating point number indicating how much space this cell should be given relative to other cells in the same layout.
		self.weight=weight
		#: A numeric amount of fixed space this cell must contain (measured in the window coordinate system).
		self.fixed=fixed
		#: The offset from the origin on the dimension specifying this cell (-1 if not computed or not in a layout).
		self.offset=-1
		#: The size of this cell on this dimension (-1 if not computed or not in a layout).
		self.size=-1

class LayoutVector(object):
	'''A :class:`LayoutVector` contains a vector (well, a list) of cells arranged
along one dimension. The layout may be computed against a dimensional measure
(in any coordinate system, though typically the window coordinate system is used
for compatibility with the rest of this module), and the :attr:`LayoutCell.offset`
and :attr:`LayoutCell.size` attributes will be set appropriately.

The constructor may be given either one parameter (the number of :class:`LayoutCell`\ s
to construct), or an arbitrary number of positional parameters containing
:class:`LayoutCell`\ s or derivatives thereof (or, really, any object implementing
that interface).

Furthermore, ``__getitem__``, ``__len__``, and ``__iter__`` are implemented,
and defer calls to the underlying cell collection.'''
	def __init__(self, *cells):
		if len(cells)==1 and isinstance(cells[0], (int, long)):
			self.cells=[LayoutCell() for i in xrange(cells[0])]
		else:
			self.cells=list(cells)
	def Compute(self, dim):
		'''Compute the layout of the cells along this dimension, assuming a size
along this dimensions of the argument given.'''
		dim-=sum([i.fixed for i in self.cells]) #Remove fixed allocations from weighting
		wtotal=sum([i.weight for i in self.cells])
		offset=0
		for cell in self.cells:
			cell.offset=offset
			cell.size=cell.fixed+(dim*cell.weight/wtotal)
			offset+=cell.size
	def __getitem__(self, idx):
		return self.cells[idx]
	def __len__(self):
		return len(self.cells)
	def __iter__(self):
		return iter(self.cells)

class Grid(object):
	'''A :class:`Grid` is basically just two :class:`LayoutVector`\ s on
perpendicular axes, with a convenience function (:func:`CellPair`) to return
the two cells (as a tuple) at the specified indices.

The constructor expects two parameters, which may either be integers (specifying
the number of cells to construct on that axis) or a :class:`LayoutVector`, subclass,
or implementor of that interface.'''
	def __init__(self, rows, cols):
		#: A :class:`LayoutVector` specifying layout along the Y axis.
		self.rows=(LayoutVector(rows) if isinstance(rows, (int, long)) else rows)
		#: A :class:`LayoutVector` specifyinh layout along the X axis.
		self.cols=(LayoutVector(cols) if isinstance(cols, (int, long)) else cols)
	def Compute(self, dims):
		'''Compute all :class:`LayoutVector`\ s from the dimension :class:`vmath.Vector`
given.'''
		self.rows.Compute(dims.y)
		self.cols.Compute(dims.x)
	def CellPair(self, x, y):
		'''Returns a tuple ``(:class:`LayoutCell`, :class:`LayoutCell`)`` as
specified by the ``x`` and ``y`` parameters.'''
		return self.cols[x], self.rows[y]
	def CellsAt(self, pos):
		'''Returns a tuple ``(:class:`LayoutCell`, :class:`LayoutCell`)`` that
represents the cell pair at the given position in the layout held by this
:class:`Grid`. This may be used for various sorts of hit-testing.'''
		xcell=None
		ycell=None
		for cell in self.cols:
			if pos.x>=cell.offset and pos.x<cell.offset+cell.size:
				xcell=cell
		for cell in self.rows:
			if pos.y>=cell.offset and pos.y<cell.offset+cell.size:
				ycell=cell
		return xcell, ycell

class Widget(Renderable):
	'''A :class:`Widget` is a special type of :class:`scenegraph.Renderable`
that expects to be in an environment where:

* The projection and modelview matrices are identity, giving a precise mapping
  between input (vertex) coordinates and normalized device coordinates, *but*
* the viewport is set so that the rendering bounds are only a small portion of
  the window--specified by the cell pair given.

As such, the :func:`scenegraph.Renderable.PushState` and :func:`scenegraph.Renderable.PopState`
functions are overriden (such that the :attr:`scenegraph.Renderable.enable`,
:attr:`scenegraph.Renderable.disable`, and :attr:`scenegraph.Renderable.modifications`
will *not* work). Their primary job is to set up the viewport, as specified
above. (The matrices are assumed to be identity beforehand, an assumption usually
guaranteed by an enclosing :class:`Container`).

The ``xcell`` and ``ycell`` parameters should be set to a cell on corresponding
layout axes.'''
	def __init__(self, xcell, ycell, fcol=None, bcol=None, **kwargs):
		super(Widget, self).__init__(**kwargs)
		#: A :class:`LayoutCell` along the x axis.
		self.xcell=xcell
		#: A :class:`LayoutCell` along the y axis.
		self.ycell=ycell
		#: A :class:`vmath.Vector` cotaining the foreground color, or ``None`` (whose application differs per widget).
		self.fcol=fcol
		#: A :class:`vmath.Vector` containing the background color, or ``None`` (whose application differs per widget).
		self.bcol=bcol
	@property
	def pos(self):
		'''A 2D :class:`vmath.Vector` containing the cell positions.'''
		return Vector(self.xcell.offset, self.ycell.offset)
	@property
	def size(self):
		'''A 2D :class:`vmath.Vector` containing the cell sizes.'''
		return Vector(self.xcell.size, self.ycell.size)
	def PushState(self):
		'''Initialize the state (basically, push and set the viewport).

.. note::

	This does not respect any of the other :class:`scenegraph.Renderable`
	attributes, including :attr:`scenegraph.Renderable.enable`,
	:attr:`scenegraph.Renderable.disable`, :attr:`scenegraph.Renderable.modifications`,
	and so on.'''
		glPushAttrib(GL_VIEWPORT_BIT)
		glViewport(*([int(i) for i in self.pos]+[int(i) for i in self.size]))
	def PopState(self):
		'''Reset the state (basically, pop the viewport).'''
		glPopAttrib()

class Container(Widget):
	'''A :class:`Container` is a :class:`Widget` that contains other :class:`Widget`\ s.
In particular, a :class:`Container` is special in that it can accept an
:attr:`Widget.xcell` and :attr:`Widget.ycell` value of ``None``, implying that
this container is the *top-level container*, which causes it to do useful duties
(like set up the identity matrices; see :class:`Widget`).

Containers always have a layout system--presently, :attr:`grid` (though the name
is subject to change). It is logical (but not required) to put :class:`Widget`\ s
that are in this layout system as children of the :class:`Container`. Other
:class:`scenegraph.Renderable`\ s should not be made children of :class:`Container`\ s
due to the odd circumstances under which :class:`Widget`\ s are rendered.'''
	def __init__(self, grid, xcell=None, ycell=None, **kwargs):
		super(Container, self).__init__(xcell, ycell, **kwargs)
		self.grid=grid
	def PushState(self):
		'''Initialize the state. Depending on whether this is a top-level
container, this may initialize the matrices (without affecting the viewport),
or it may just set a viewport as with the usual :func:`Widget.PushState`.'''
		if self.xcell is None or self.ycell is None:
			#Initialize this as if we are a master layout (we probably are)
			glMatrixMode(GL_PROJECTION)
			glPushMatrix()
			glLoadIdentity()
			glMatrixMode(GL_MODELVIEW)
			glPushMatrix()
			glLoadIdentity()
			self.grid.Compute(Vector(*(glGetIntegerv(GL_VIEWPORT)[2:])))
		else:
			self.grid.Compute(self.size)
			super(Container, self).PushState() #Just do what every other widget does
	def PopState(self):
		'''Reverts the state, undoing the actions done during :func:`PushState`.'''
		if self.xcell is None or self.ycell is None:
			glMatrixMode(GL_PROJECTION)
			glPopMatrix()
			glMatrixMode(GL_MODELVIEW)
			glPopMatrix()
		else:
			super(Container, self).PopState()
	def Render(self):
		'''Render the :class:`Container` (which actually does nothing but
renders its children via :func:`scenegraph.Renderable.RenderChildren`.'''
		self.RenderChildren()
	def ChildAt(self, pos):
		'''Returns a :class:`Widget` at the position specified, if one exists
there; otherwise, returns ``None``.'''
		xc, yc=self.grid.CellsAt(pos)
		if xc is None or yc is None:
			return None
		for child in self.children:
			if child.xcell is xc and child.ycell is yc:
				return child
		return None #Explicit is better than implicit.
	def TriggerChildren(self, ev):
		'''Overrides the default propagation behavior by ensuring that
:class:`Event` objects with a ``pos`` attribute are dispatched only to
:class:`Widget` objects in that position.

.. note::

	This special naming convention is all-inclusive; *any* :class:`Event` with
	a ``pos`` attribute will be propagated thusly, and any without a ``pos``
	attribute will simply propagate to all children, as usual. This means you
	can use the same behavior in your position-sensitive events, as well.'''
		if hasattr(ev, 'pos'):
			child=self.ChildAt(ev.pos)
			if child is not None:
##				print 'Pre event prop:', ev.pos
				ev.pos-=child.pos #Relative coordinate
##				print 'Child pos:', child.pos
##				print 'Post event prop:', ev.pos
				child.Trigger(ev)
		else:
			super(Container, self).TriggerChildren(ev)

class ALIGN:
	'''An enumeration class of legal values for :attr:`Label.align` and similar
attributes in derived classes.'''
	#: Align the left edge with the left edge of the cell.
	LEFT=0x01
	#: Center the object in the cell horizontally.
	#:
	#: .. note::
	#:
	#:    This is the default, so its value is 0, and it is not effective with the other attributes.
	CENTER=0x00
	#: Align the right edge with the right edge of the cell.
	RIGHT=0x02
	#: Align the top edge with the top edge of the cell.
	TOP=0x04
	#: Center the object in the cell vertically.
	#:
	#: .. note::
	#:
	#:    This is the default, so its value is 0, and it is not effective with the other attributes.
	MIDDLE=0x00
	#: Align the bottom edge with the bottom edge of the cell.
	BOTTOM=0x08
	#: Fill the entire horizontal expanse, stretching the object if necessary. (Equivalent to LEFT|RIGHT.)
	FILLX=LEFT|RIGHT
	#: Fill the entire vertical expanse, stretching the object if necessary. (Equivalent to TOP|BOTTOM.)
	FILLY=TOP|BOTTOM

class Label(Widget):
	'''The :class:`Label` is a :class:`Widget` designed to display text.

Since this function is useful to some other :class:`Widget`\ s, it's also the
base class for a few.'''
	def  __init__(self, xcell, ycell, text='', align=0, font=None, **kwargs):
		super(Label, self).__init__(xcell, ycell, **kwargs)
		#: A string containing the text to display.
		self.text=text
		self._oldtext=None
		#: The alignment mode (a :class:`ALIGN` bit mask).
		self.align=align
		#: The ``pygame.Font`` object to use for rendering.
		self.font=(pygame.font.SysFont(pygame.font.get_default_font(), 30) if font is None else font)
		#: The :class:`scenegraph.Texture` used to store the font texture.
		self.tex=None
		if self.text:
			self.Update()
	def Update(self, text=None):
		'''Updates the Label, drawing the new :attr:`text` to the :attr:`tex`
:class:`scenegraph.Texture`.

.. note::

	This is done automatically whenever :attr:`text` is no longer determined to
	be the same object as before. Since strings in Python are immutable, this
	must be the case if the value is no longer the same as well. However, this
	process is *not* performed if the :attr:`Widget.fcol` attribute is changed
	(which determines the font color), and so it must be either called manually
	from code that does this, or the :attr:`text` attribute must be changed to
	a different object. A trivial way of performing the latter is assigning
	``label.text=str(label.text)``.

	This behavior may change in later versions to update when the color is changed
	as well.'''
		if text is None:
			text=self.text
		fcol=self.fcol
		if fcol is None:
			fcol=Vector(1, 1, 1)
		tsurf=self.font.render(text, True, tuple(255*fcol.FastTo3()))
		if self.tex is None:
			self.tex=Texture()
		self.tex.surf=tsurf
		self.tex.Reload()
	def Render(self):
		'''Renders the label using the current viewport.'''
		glPushAttrib(GL_ENABLE_BIT)
		glDisable(GL_TEXTURE_2D)
		glDisable(GL_DEPTH_TEST)
		if self.bcol is not None:
			glColor4d(*self.bcol.FastTo4())
			glRectdv((-1, -1), (1, 1))
		if self.text:
			if self.text is not self._oldtext:
				self.Update()
				self._oldtext=self.text
			self.RenderText()
		glPopAttrib()
	def RenderText(self):
		'''Renders the text--a process which is usable by subclasses as needed.'''
		glPushAttrib(GL_ENABLE_BIT)
		tsz=Vector(*self.tex.surf.get_size())
		vsz=Vector(*(glGetIntegerv(GL_VIEWPORT)[2:]))
		csz=tsz/vsz
		minima=-csz
		maxima=csz.copy()
		if self.align&ALIGN.LEFT:
			minima.x=-1
			maxima.x-=1-csz.x
		if self.align&ALIGN.RIGHT:
			maxima.x=1
			if not self.align&ALIGN.LEFT:
				minima.x+=1-csz.x
		if self.align&ALIGN.BOTTOM:
			minima.y=-1
			maxima.y-=1-csz.y
		if self.align&ALIGN.TOP:
			maxima.y=1
			if not self.align&ALIGN.BOTTOM:
				minima.y+=1-csz.y
		glEnable(GL_TEXTURE_2D)
		self.tex.Apply()
##			print 'Label', self.text, 'has TID', self.tex.id, 'and surf', self.tex.surf
		glColor4d(1, 1, 1, 1)
		glBegin(GL_QUADS)
		glTexCoord2d(0, 0)
		glVertex2d(minima.x, minima.y)
		glTexCoord2d(1, 0)
		glVertex2d(maxima.x, minima.y)
		glTexCoord2d(1, 1)
		glVertex2d(maxima.x, maxima.y)
		glTexCoord2d(0, 1)
		glVertex2d(minima.x, maxima.y)
		glEnd()
		glPopAttrib()

class ORIENT:
	'''An enumeration of legal values for the :attr:`Slider.orient` attribute.'''
	#: Orient horizontally, along the X axis.
	HORIZONTAL=0
	#: Orient vertically, along the Y axis.
	VERTICAL=1

class Slider(Label):
	'''A :class:`Slider` is a type of widget that allows a user to manipulate a
value by providing an axis between two extreme values; the user is expected to
use the mouse to select the value as a point within this range; the value is
readable as the :attr:`value` attribute.'''
	def __init__(self, xcell, ycell, value=0, min=0, max=1, mapfunc=None, showval=True, orient=ORIENT.HORIZONTAL, hwidth=0.05, hcol=None, **kwargs):
		super(Slider, self).__init__(xcell, ycell, **kwargs)
		#: The actual value of this :class:`Slider`, as modified by the user (and possibly mapped by :attr:`mapfunc`).
		self.value=value
		self._oldvalue=None
		#: The smallest value this should contain.
		self.min=min
		#: The largest value this should contain.
		self.max=max
		#: A function called with the raw, floating-point value from the user input, whose return is mapped to :attr:`value`.
		self.mapfunc=mapfunc
		#: True to display the value as a text object (which obeys :class:`Label` attributes like :attr:`Label.align`).
		self.showval=showval
		#: The orientation (a :class:`ORIENT` constant).
		self.orient=orient
		#: The floating-point width of the slide handle in normalized device coordinates (where 1 would be half the viewport).
		self.hwidth=hwidth
		#: A 4D :class:`vmath.Vector` color of the slide handle (or ``None`` for the default transparent gray).
		self.hcol=hcol
	@property
	def range(self):
		'''The computed difference between :attr:`max` and :attr:`min`.'''
		return self.max-self.min
	@property
	def ratio(self):
		'''The position of :attr:`value` normalized such that the minimal point
is 0 and the maximal point is 1.'''
		return (self.value-self.min)/self.range
	def Map(self, n):
		'''Maps a value ``n`` in the range [0, 1] to a value between [min, max].'''
		return (n*self.range)+self.min
	@staticmethod
	def Step(n):
		'''Produces a lambda function that may be used as a value for :attr:`mapfunc`.
The return function will produce values ``x`` such that ``x*n`` is an integer
(barring round-off error), or, alternatively, will clamp values to ``1/n`` increments.

Calling this with ``n==1`` will result in an analogue to the ``int`` function, which
should probably be used instead.'''
		return lambda x, n=n: int(x*n)/float(n)
	def Render(self):
		'''Renders the slider.'''
		glPushAttrib(GL_ENABLE_BIT)
		glDisable(GL_DEPTH_TEST)
		glDisable(GL_TEXTURE_2D)
		if self.bcol is not None:
			glColor4d(*self.bcol.FastTo4())
			glRectdv((-1, -1), (1, 1))
		if self.showval and self.value!=self._oldvalue:
			self.text=str(self.value)
			self.Update()
			self.RenderText()
		hcol=self.hcol
		if hcol is None:
			hcol=Vector(0.5, 0.5, 0.5, 0.5)
		glColor4d(*hcol.FastTo4())
		pos=self.ratio*2-1
		if self.orient==ORIENT.HORIZONTAL:
			glRectdv((pos-self.hwidth, -1), (pos+self.hwidth, 1))
		else:
			glRectdv((-1, pos-self.hwidth), (1, pos+self.hwidth))
		glPopAttrib()
	def Handle(self, ev):
		if ev.type==EVENT.MOUSE and ev.subtype==MOUSE.MOVE and ev.buttons[0]:
			if self.orient==ORIENT.HORIZONTAL:
				ratio=ev.pos.x/self.size.x
			else:
				ratio=ev.pos.y/self.size.y
			self.value=self.Map(ratio)