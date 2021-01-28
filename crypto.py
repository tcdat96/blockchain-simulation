'''
crypto.py
handling double sha256 hash and elipstic curve encryption

All input format: bytestring
HashFormat: bytestring
Encryption Key Format: base64 bytestring

'''

from fastecdsa import curve, keys, ecdsa, point
from hashlib import sha256
from base64 import b64encode, b64decode
from util import *

'''
  Part 1: Hash 
'''
#double sha256 hash
#m: message (in bytes)
#return hash in 32 bytes
def double_sha256(m):
  d = sha256(m)
  d = sha256(d.digest())
  return b64encode(d.digest())

#T is the list of digest of all transaction in the block
#n is the len of T
#return the merkel root (size 32) of transaction list T
def merkle_root_generation(T):
  n = len(T)
  if n == 0:
    return None
  elif n == 1:
    return T[0]
  else:
    if n%2 != 0:
      T.append(b'')
    T = [double_sha256(i+j) for i, j in zip(T[::2], T[1::2])]
    return merkle_root_generation (T)

#get n-bytes prefix of message m converted to number
def check_prefix_b64(m, n):
  m = b64decode(m)
  return int.from_bytes(m[:n], 'big') == 0

#concate nonce number n (size s bytes) to m
def add_nonce(m, n, s):
  return m+n.to_bytes(s, 'big')

#get nonce number for message m and n bytes = 0
#return nonce i and byte size s
def get_nonce(m, n):
  s = 0
  next = True
  while next:
    s+=1
    for i in range(2**(s*8)):
      temp = add_nonce(m, i, s)
      if check_prefix_b64(double_sha256(temp), n):
        next = False
        break
  return i, s

'''
  Part 2: Private Key encryption
'''

#generate a key pair private key (b64 bytes) and public key (b64 bytes)
def get_keypair():
  PR, PU = keys.gen_keypair(curve.P256)
  PU = (PU.x, PU.y)
  return i2a(PR), u2a(PU)

#sign message m (bytes) using private key PR (base64 bytes)
def sign(m, PR):
  return u2a(ecdsa.sign(m, a2i(PR)))

#verify a signature sig with m and public key PU (base64 bytes)
def verify(sig, m, PU):
  x, y = a2u(PU)
  PU = point.Point(x, y)
  return ecdsa.verify(a2u(sig), m, PU)
