'''
wallet.py
managing address and transaction associate with it
'''
import time
from transaction import Transaction
from crypto import get_keypair

class Wallet:
  def __init__(self):
    self.key, self.address = get_keypair()
    self.transactions = {b'': {'hash': b'', 
                               'amount': 0., 
                               'time': time.asctime(),
                               'balance': 0.}}
    self.pending = {'hash': None}

  def __str__(self):
    T = list(self.transactions.values())
    s = 'Address: %s\n'%self.address.decode()
    s += 'Total Balance: %f\n\n'%(T[-1]['balance'])
    for t in T[:-11:-1]:
      s += '%s%50s%20f\n'%(t['time'], t['hash'].decode(), t['amount'])

    return s

  def balance (self):
    T = list(self.transactions.values())
    return T[-1]['balance']

  def receive (self, T: Transaction):
    if self.transactions.get(T.Digest) != None:
      return None

    for output in T.Receivers:
      if output[1] == self.address:
        balance = list(self.transactions.values())[-1]['balance']
        self.transactions[T.Digest] = {'hash': T.Digest, 
                                       'amount': output[0], 
                                       'time': time.asctime(),
                                       'balance': balance + output[0]}
  
  def send (self, amount: float, address: bytes):
    T = list(self.transactions.values())
    chg = T[-1]['balance'] - amount
    if chg < 0 :
      return None
    receivers = [[amount, address]]
    if chg > 0:
      receivers.append([chg, self.address])

    senders = []
    for t in T[::-1]:
      if t['amount'] < 0:
        if t['balance'] > 0:
          senders.append([t['hash'], self.address])
        break
      senders.append([t['hash'], self.address])

    T = Transaction(senders=senders, receivers=receivers)
    T.sign([self.key for _ in senders])
    self.pending = {'hash': T.Digest, 
                     'amount': -amount, 
                     'time': time.asctime()}

    return T

  def confirm (self, T: Transaction):
    if self.pending['hash'] == T.Digest:
      balance = list(self.transactions.values())[-1]['balance']
      self.transactions[T.Digest] = {'hash': self.pending['hash'], 
                                     'amount': self.pending['amount'], 
                                     'time': time.asctime(),
                                     'balance': balance + self.pending['amount']}
      self.pending = {'hash': None}

  def join (self, W):
    return W.send(list(W.transactions.values())[-1]['balance'], self.address)