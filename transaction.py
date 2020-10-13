'''
transaction.py
create transaction for blockchain 
'''
import time
from fastecdsa import ecdsa, point
from util import *

class Transaction:
  def __init__(self, sender, receiver, amount, timestamp=time.asctime().encode(), signature=(0,0)):  
    self.Timestamp = timestamp #bytestring size 24
    self.Sender = sender #tuple of 2 numbers
    self.Receiver = receiver #tuple of 2 numbers
    self.Amount = amount #float with maximum 12 digits after floating point
    self.Signature = signature #tuple of 2 numbers
  
  def __str__(self):
    return "Created Time: " + self.Timestamp.decode() + \
           "\nAmount: " + str(self.Amount) + \
           "\nSender Address: " + str(self.Sender) + \
           "\nReceiver Address: " + str(self.Receiver) + \
           "\nTransaction Authetication Code: " + str(self.Signature)

  def from_bytes(s):
    timestamp = s[:24]
    sender = b2pu(s[24:88])
    receiver = b2pu(s[88:152])
    amount = b2f(s[152:168])
    signature = b2pu(s[168:])
    return Transaction(sender, receiver, amount, timestamp, signature)

  def to_bytes(self):
    s = self.Timestamp #size 24
    s += pu2b(self.Sender) #sz 64
    s += pu2b(self.Receiver) #sz 64
    s += f2b(self.Amount) #sz 16
    s += pu2b(self.Signature) #sz 64
    return s

  def sign(self, PR): 
    m = self.to_bytes()[:-64]
    self.Signature = ecdsa.sign(m, PR)
    
  def verify(self):
    m = self.to_bytes()[:-64]
    PU = point.Point(self.Sender[0], self.Sender[1])
    return ecdsa.verify(self.Signature, m, PU)

  def digest(self):
    m = self.to_bytes()
    return double_sha256(m)