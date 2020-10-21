'''
util.py 
tools to modified the key and data format
'''

from fastecdsa import curve, keys
from hashlib import sha256

#from float to bytearray, max of 12 digits after floating point
def f2b (n):
  return int(n * 10**12).to_bytes(16, 'big')

#from bytearray to float
def b2f (n):
  return int.from_bytes(n, 'big')/(10**12)

# from string to bytearray
def i2b(n):
  return n.to_bytes(32, 'big')

# from bytearray to string
def b2i(n):
  return int.from_bytes(n, 'big')

#from private key (int) to bytearray
def pr2b (n):
  return i2b(n)

#from bytearray to private key (int)
def b2pr (n):
  return b2i(n)

#from public key (int, int) to bytearray
def pu2b (n):
  return n[0].to_bytes(32, 'big') + n[1].to_bytes(32, 'big')

#from bytearray to public key (int, int)
def b2pu (n):
  return int.from_bytes (n[:32], 'big'), int.from_bytes (n[32:], 'big')

# from string to bytearray
def str2b(string):
  return string.decode('utf-8')

# from bytearray to string
def b2str(string):
  return string.decode('utf-8')

#generate a key pair private key (int) and public key (int, int)
def generate_keypair():
  PR, PU = keys.gen_keypair(curve.P256)
  PU = (PU.x, PU.y)
  return PR, PU

#double sha256 hash of data m
def double_sha256(m):
  d = sha256(m)
  d = sha256(d.digest())
  return d.digest()

#T is the list of digest of all transaction in the block
#n is the len of T
#return the merkle root (size 32) of transaction list T
def merkle_root_generation(T, n):
  if n == 0:
    return None
  elif n == 1:
    return T[0]
  else:
    if n%2 != 0:
      T.append(b'')
    T = [double_sha256(i+j) for i, j in zip(T[::2], T[1::2])]
    n = int(n/2)+n%2
    return merkle_root_generation (T, n)