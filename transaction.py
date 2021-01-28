
'''
transaction.py
create transaction for blockchain 
'''
import time
from util import *
from crypto import *

# senders list of tuple(hash of transaction, address)
# receivers list of tuple(amount, address)
class Transaction:
  def __init__(self, T=None, senders = list(), receivers = list()):
    if T == None:
      self.Timestamp = time.asctime().encode()
      self.Senders = senders
      self.Receivers = receivers
      self.Digest = double_sha256(self.to_bytes(nohash=True, nosign=True))
    else:
      self.from_bytes(T)
  
  def __str__(self):
    return "Created Time: " + self.Timestamp.decode() + \
           "\nHash: " + str(self.Digest) + \
           "\nSenders: " + str(self.Senders) + \
           "\nReceivers: " + str(self.Receivers) +\
           "\nSignatures: " + str(self.Signatures)
  
  def to_bytes(self, nosign = False, nohash=False):
    senders = [b64encode(digest + b'\n' + address) 
                  for digest, address in self.Senders]

    receivers = [b64encode(str(amount).encode() + b'\n' + address)
                    for amount, address in self.Receivers]

    s = [self.Timestamp, 
            b64encode(b'\n'.join(senders)),
            b64encode(b'\n'.join(receivers))]

    if not nohash:
      s.insert(0, self.Digest)

    if not nosign:
      s.append(b64encode(b'\n'.join(self.Signatures)))

    return b'\n'.join(s)

  def from_bytes(self, T):
    T = T.splitlines()
    self.Digest = T[0]
    self.Timestamp = T[1]
    self.Signatures = b64decode(T[-1]).splitlines()

    senders = b64decode(T[2]).splitlines()
    self.Senders = [b64decode(s).splitlines() for s in senders]

    receivers = b64decode(T[3]).splitlines()
    receivers = [b64decode(r).splitlines() for r in receivers]
    self.Receivers = [[float(r[0].decode()), r[1]] for r in receivers]

  def sign(self, PRs):
    m = self.to_bytes(nosign = True)
    self.Signatures = [sign(m, PR) for PR in PRs]

  def verify(self):
    m = self.to_bytes(nosign=True)
    for sig, address in zip(self.Signatures, self.Senders):
      if not verify(sig, m, address[1]):
        return False

    return True