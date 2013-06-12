'''
.. mindscape -- Mindscape Engine
log -- Logging

This module basically does nothing but set up the ``logging`` module proper.

The entire rest of the ``logging`` namespace is otherwise available on this module.
'''

from logging import *

import base64
import binascii

DV1=5
DV2=2
DV3=1

addLevelName(DV1, 'DV1') #Debug Verbosity 1
addLevelName(DV2, 'DV2') #Debug Verbosity 2
addLevelName(DV3, 'DV3') #Debug Verbosity 3

fm=Formatter('%(levelname)-8s %(relativeCreated)-6d [%(name)s] %(msg)s')

main=getLogger('ms')
main.setLevel(DV3)

hand=StreamHandler(open('log.txt', 'w'))
hand.setLevel(DV3)
hand.setFormatter(fm)

main.addHandler(hand)

main.info('Logging system ready.')

def obCode(obj):
	#Fast to bitstring
	s=''
	i=id(obj)
	while i>0:
		s=chr(i%256)
		i/=256
	return base64.b64encode(s)