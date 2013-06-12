'''
.. mindscape -- Mindscape Engine
event -- Events
===============

This module defines events that may be used anywhere that an event-driven
system is required.
'''

class EVENT:
	'''An enumeration containing valid values for :attr:`Event.type`.'''
	#: An event relating to the keyboard (key down, key up, character, ...)
	KBD=1
	#: An event relating to the mouse (button press, release, mouse move, ...)
	MOUSE=2

class KBD:
	'''An enumeration containing event subtypes for the :attr:`EVENT.KBD` event.'''
	#: A key was pressed.
	KEYDOWN=1
	#: A key was released.
	KEYUP=2
	#: A printable character was generated
	#:
	#: .. note::
	#:
	#:    Printable character generation may occur multiple times between a
	#:    key press and key release (such as when the key is held for long
	#:    enough to start auto-repeating), or not at all (such as if the key
	#:    is a non-printable, like a modifier key or an F-key). In general, if
	#:    you're interested in what the user is typing, hook :attr:`CHAR`;
	#:    otherwise, if you're interested in the state of the keyboard, hook
	#:    :attr:`KEYDOWN` and :attr:`KEYUP`.
	CHAR=3

class MOUSE:
	'''An enumeration containing event subtypes for the :attr:`EVENT.MOUSE` event.'''
	#: A mouse button was pressed.
	BUTTONDOWN=1
	#: A mouse button was released.
	BUTTONUP=2
	#: The mouse wheel was scrolled (or pivoted on some axis).
	#:
	#: .. note::
	#:
	#:    Due to the way SDL handles the scroll wheel, you may never see this
	#:    event. To my knowledge, however, some persons patched the SDL code to
	#:    interpret scroll wheel up and scroll wheel down movements as buttons
	#:    4 and 5--this is unfortunate for persons (like myself) that have
	#:    5-button mice and a scroll wheel that can also support horizontal
	#:    movement.
	#:
	#:    Barring this poor design decision, the engine will try to provide the
	#:    most accurate representation of what really happened, even if SDL is
	#:    coaxed into lying about it.
	WHEEL=3
	#: The cursor was moved.
	MOVE=4

class Event(object):
	'''An :class:`Event` contains all of the information needed to pass an
event to a system which uses events.

Events may be given arbitrary attributes from the keyword arguments passed to
the constructor. A later ``type=...`` in the keyword arguments will override
the specified event type given as a positional parameter, if one is provided.'''
	def __init__(self, type, **kwargs):
		#: The event type (one of the :class:`EVENT` values). Other attributes depend on the event.
		self.type=type
		for k, v in kwargs.iteritems():
			setattr(self, k , v)

class EventHandler(object):
	def Trigger(self, ev):
		'''Trigger an :class:`Event`.

.. note::

	Triggering an :class:`Event` is not the same as handling an event; triggering
	will inevitably cause handling by this object, and may cause handling
	by children (based on the propagation policy--how the subclass defines
	:func:`TriggerChildren`. Handling the :class:`Event` is done by :func:`Handle`,
	which actually causes the :class:`EventHandler` to process the event.'''
		self.Handle(ev)
		self.TriggerChildren(ev)
	def Handle(self, ev):
		'''Handle an :class:`Event`. By default, this does nothing.

.. note::

	See :func:`Trigger`.'''
		pass
	def TriggerChildren(self, ev):
		'''Propagate the event. Subclasses are expected to implement this if
they have some kind of propagation policy; otherwise, it may be left derived
(and thereby nonfunctional).

.. note::

	Since :class:`scenegraph.Renderable` is a direct subclass of this, and has
	children, it's a fair expectation that it has implemented the propagation
	policy.'''
		pass