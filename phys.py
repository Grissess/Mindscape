'''
.. mindscape -- Mindscape Engine
phys -- Physics
===============

Implements an interface for physics engines in the Mindscape engine.

Currently, this uses PyODE, but any other library with a similar interface can
be used as a stand-in.
'''

import ode

from vmath import Vector

class STYPE:
	SIMPLE=1
	QTREE=2
	HASH=3

class SIM:
	NORMAL=0
	QUICK=1

class Environment(object):
	SPACE_MAP={STYPE.SIMPLE: ode.SimpleSpace,
			   STYPE.QTREE: ode.QuadTreeSpace,
			   STYPE.HASH: ode.HashSpace}
	SIM_MAP={SIM.NORMAL: ode.World.step,
			 SIM.QUICK: ode.World.quickStep}
	def __init__(self, stype=STYPE.QTREE, gravity=None, sim=SIM.NORMAL):
		self.world=ode.World()
		if gravity is not None:
			self.world.setGravity(tuple(gravity))
		self.space=self.SPACE_MAP[stype]()
		self.contactgroup=ode.JointGroup()
		self.sim=sim
	def _get_gravity(self):
		return Vector(*self.world.getGravity())
	def _set_gravity(self, grav):
		self.world.setGravity(tuple(grav))
	gravity=property(_get_gravity, _set_gravity)
	def Step(self, size):
		self.SIM_MAP[self.sim](self.world, size)

class Mass(object):
	def __init__(self, mass):
		self.mass=mass
	def __iadd__(self, other):
		self.mass.add(other.mass)
	@classmethod
	def Box(cls, density, dims, absolute=False):
		m=ode.Mass()
		if absolute:
			m.setBoxTotal(density, *dims)
		else:
			m.setBox(density, *dims)
		return cls(m)
	@classmethod
	def Sphere(cls, density, radius, absolute=False):
		m=ode.Mass()
		if absolute:
			m.setSphereTotal(density, radius)
		else:
			m.setSphere(density, radius)
		return cls(m)

class Body(object):
	def __init__(self, env, mass):
		self.env=env
		self.body=ode.Body(env.world)
	def _get_mass(self):
		return self.body.getMass()
	def _set_mass(self, mass):
		self.body.setMass(mass.mass)

class Geometry(object):
	def Attach(self, body):
		self.geom.setBody(body.body)
	def BuildMass(self, density, absolute=False):
		raise NotImplementedError('Geometry derivative must define .BuildMass()')

class Mesh(Geometry):
	def __init__(self, env, mesh):
		self.env=env
		self.mesh=mesh
		self.data=ode.TriMeshData()
		self.Rebuild()
		self.geom=ode.GeomTriMesh(self.data, env.space)
	def Rebuild(self):
		#Note that this build assumes either a GL_TRIANGLE_STRIP or compatible
		#mode, such as GL_QUADS. Winding doesn't matter (AFAIK), so if you've
		#used CCW winding for the polygons for the renderer, it won't hurt.
		#Note that vertices are split often.
		vertices=[]
		indices=[]
		for face in self.mesh.faces:
			if len(face.vertices)>2:
				vertices.extend(face.vertices[:2])
				for vertex in face.vertices[2:]:
					vertices.append(vertex)
					l=len(vertices)
					indices.append((l-3, l-2, l-1))
		vertices=[i.pos for i in vertices]
		self.data.build(vertices, indices)

class Sphere(Geometry):
	def __init__(self, env, radius):
		self.env=env
		self.geom=ode.GeomSphere(env.space, radius)
	def _get_radius(self):
		return self.geom.getRadius()
	def _set_radius(self, rad):
		return self.geom.setRadius(rad)
	radius=property(_get_radius, _set_radius)
	def BuildMass(self, density, absolute=False):
		return Mass.Sphere(density, self.radius, absolute)

class Box(Geometry):
	def __init__(self, env, dims):
		self.env=env
		self.geom=ode.GeomBox(env.space, tuple(dims.FastTo3()))
	def _get_dims(self):
		return Vector(*self.geom.getLengths())
	def _set_dims(self, dims):
		self.geom.setLengths(tuple(dims.FastTo3()))
	dims=property(_get_dims, _set_dims)
	def BuildMass(self, density, absolute=False):
		return Mass.Box(density, self.dims, absolute)