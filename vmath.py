'''
.. mindscape -- Mindscape Engine
vmath -- Vector Math
====================

This module defines some useful vector and matrix math, implemented generally
in numpy for speed.
'''

import numpy

class Vector(numpy.ndarray):
	'''A vector is an array of double-precision floating points of arbitrary
size (though usually between two and four members). The :class:`Vector` class is
actually the ``numpy.ndarray`` class, with a few special members, a fixed type,
and a special constructor (you may pass elements as arbitrary positional
arguments; keyword arguments are not supported).

Vectors can be converted to other vectors of different cardinality by using the
:func:`To2`, :func:`To3`, and :func:`To4` methods (or their fast equivalents,
described below).'''
	def __new__(mcs, *args):
		inst=numpy.ndarray.__new__(mcs, (len(args),), numpy.float64)
		inst[:]=args
		return inst
	def _get_x(self):
		return self[0]
	def _set_x(self, val):
		self[0]=val
	def _get_y(self):
		return self[1]
	def _set_y(self, val):
		self[1]=val
	def _get_z(self):
		return self[2]
	def _set_z(self, val):
		self[2]=val
	def _get_w(self):
		return self[3]
	def _set_w(self, val):
		self[3]=val
	#: The ``x`` component (item 0).
	x=property(_get_x, _set_x)
	#: The ``y`` component (item 1).
	y=property(_get_y, _set_y)
	#: The ``z`` component (item 2).
	z=property(_get_z, _set_z)
	#: The ``w`` component (item 3).
	w=property(_get_w, _set_w)
	def length(self):
		'''Returns the euclidean length of the vector.'''
		return numpy.sqrt(self.dot(self))
	def unit(self):
		'''Returns a :class:`Vector` of unit length.

.. warning::

	This will raise ``ZeroDivisonError`` if you pass a zero length vector!'''
		return self/self.length()
	def cross(self, other):
		'''Returns the cross product of the provided vectors.

.. note::

	Both vectors must have exactly three elements; you can use :func:`To3` or
	:func:`FastTo3` to ensure this.'''
		if len(self)!=len(other)!=3:
			raise ValueError('Cross product only defined in 3 (and 7) dimensions.')
		return type(self)(self.y*other.z-self.z*other.y,
						  self.z*other.x-self.x*other.z,
						  self.x*other.y-self.y*other.x)
	def _ToX(self, x, fast=False):
		if fast and len(self)==x:
			return self
		inst=numpy.zeros((x,))
		if x>=4:
			inst[3]=1 #W is, by default, 1
		inst[:len(self)]=self
		return type(self)(*inst)
	def To2(self):
		'''Returns a duplicate :class:`Vector` with only two elements.'''
		return self._ToX(2)
	def To3(self):
		'''Returns a duplicate :class:`Vector` with only three elements.'''
		return self._ToX(3)
	def To4(self):
		'''Returns a duplicate :class:`Vector` with only four elements.

.. note::

	The returned :class:`Vector` will have a ``w`` (index 3) of 1, if it was
	not previously present.'''
		return self._ToX(4)
	def FastTo2(self):
		'''Returns a :class:`Vector` with two elements.

.. warning::

	There is no guarantee that this is not the same :class:`Vector` object! In
	fact, this *will* be the case if the :class:`Vector` already has the
	requested length. While this will avoid an uneccessary object construction/
	data copy, it means that safety in contexts where the vector is to be
	mutated cannot be guaranteed. This should *only* be used when you need to
	pass the vector as an (immutable) argument to another function that only
	accepts, e.g., tuples or lists (of the specified size).'''
		return self._ToX(2, True)
	def FastTo3(self):
		'''Returns a :class:`Vector` with three elements.

.. warning::

	See :func:`FastTo2`'''
		return self._ToX(3, True)
	def FastTo4(self):
		'''Returns a :class:`Vector` with four elements.

.. warning::

	See :func:`FastTo2`'''
		return self._ToX(4, True)

class Matrix(numpy.matrix):
	'''A matrix is a two-dimensional collection of double-precision floating
point numbers wherein each dimension has the same cardinality (technically,
that means all of the matrices hereby defined are *square* matrices; for all
other cases, you'll want to use a ``numpy.ndarray`` of two dimensions instead.)
The class is implemented thinly on top of the ``numpy.matrix`` class, and
provides only additional operations (no new constructor syntaxes) and new
constructors.'''
	@classmethod
	def Rotation(cls, angle, axis): #XXX Only 3D rotations now.
		'''Constructs a 3D rotation matrix about the given :class:`Vector` (which is
converted to a unit-length 3D vector) by the specified angle. The domain of the
angle is determined by the domain of the underlying ``numpy.sin`` and
``numpy.cos`` functions (which is radians).

.. note::

	To specify the angle in degrees, use Python's ``math.radians`` function.'''
		d=axis.FastTo3().unit()
		dd=numpy.outer(d, d)
		i=numpy.eye(3, dtype=numpy.float64)
		skew=numpy.array([[0, d[2], -d[1]], [-d[2], 0, d[0]], [d[1], -d[0], 0]], numpy.float64)
		return cls(ddt+numpy.cos(angle)*(i-ddt)+numpy.sin(angle)*skew)
	@classmethod
	def Translation(cls, vec):
		'''Returns a 4D translation matrix by the give :class:`Vector` (which
is converted to a 3D vector).'''
		v=vec.FastTo3()
		return cls([[1, 0, 0, v.x], [0, 1, 0, v.y], [0, 0, 1, v.z], [0, 0, 0, 1]])
	@classmethod
	def Scale(cls, vec):
		'''Returns a 4D scaling matrix by the give :class:`Vector` (which
is converted to a 4D vector).'''
		v=vec.FastTo4()
		return cls([[v.x, 0, 0, 0], [0, v.y, 0, 0], [0, 0, v.z, 0], [0, 0, 0, v.w]])
	def _ToX(self, x, fast=False):
		if fast and len(self)==x:
			return self
		inst=type(self)(numpy.eye(x))
		inst[:len(self), :len(self)]=self
		return inst
	def To2(self):
		'''Returns a duplicate 2D :class:`Matrix`.'''
		return self._ToX(2)
	def To3(self):
		'''Returns a duplicate 3D :class:`Matrix`.'''
		return self._ToX(3)
	def To4(self):
		'''Returns a duplicate 4D :class:`Matrix`.'''
		return self._ToX(4)
	def FastTo2(self):
		'''Returns a 2D :class:`Matrix`.

.. warning::

	See :func:`Vector.FastTo2`.'''
		return self._ToX(2, True)
	def FastTo3(self):
		'''Returns a 3D :class:`Matrix`.

.. warning::

	See :func:`Vector.FastTo2`.'''
		return self._ToX(3, True)
	def FastTo4(self):
		'''Returns a 4D :class:`Matrix`.

.. warning::

	See :func:`Vector.FastTo2`.'''
		return self._ToX(4, True)