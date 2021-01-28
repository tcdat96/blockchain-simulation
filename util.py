
'''
util.py 
tools to modified the key and data format
'''

from struct import *
from base64 import b64encode, b64decode

#from double to bytes (len: 8 bytes)
def f2b (n):
  return pack('>d', n)

#from bytes to double (len of input bytes: 8)
def b2f (n):
  return unpack('>d', n)

#from int to bytes (len: 32)
def i2b (n):
  return n.to_bytes(32, 'big')

#from bytes to int
def b2i (n):
  return int.from_bytes(n, 'big')

#from int to base64
def i2a (n):
  return b64encode(i2b(n))

#from base64 to int
def a2i (n):
  return b2i(b64decode(n))

#from int tuple (int, int) to bytes (output len: 64 bytes)
def u2b (n):
  return i2b(n[0]) + i2b(n[1])

#from bytes to int tuple (input len: 64 bytes)
def b2u (n):
  return b2i(n[:32]), b2i(n[32:])

#from int tuple to base64
def u2a (n):
  return b64encode(u2b(n))

#from base64 to int tuple
def a2u (n):
  return b2u(b64decode(n))