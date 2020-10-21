'''
block.py
create a block for blockchain 
'''
import time
from util import *

class Block:
  self.difficulty = 4

  def __init__(self, previous_hash, transactions=None, nonce=0, merkle_root=None, timestamp=time.asctime().encode()):
    self.previous_hash = previous_hash
    self.timestamp = timestamp
    self.nonce = nonce

    if merkle_root == None:
      self.transactions = map(lambda transaction: transaction.digest(), transactions)
      self.merkle_root = merkle_root_generation(self.transactions, len(transactions))
    else:
      self.transactions = transactions
      self.merkle_root = merkle_root

  def __str__(self):
    return "Created Time: " + self.timestamp.decode() + \
           "\nPrevious hash: " + self.previous_hash + \
           "\nMerkle root: " + self.merkle_root + \
           "\nNonce: " + str(self.nonce) + \
           "\nHash: " + digest()

  def digest(self):
    m = self.to_bytes(include_transactions=False)
    return double_sha256(m)

  @staticmethod
  def from_bytes(s):
    previous_hash = b2str(s[:32])
    merkle_root = b2str(s[32:64])
    nonce = b2i(s[64:96])
    timestamp = s[96:120]
    transactions = b2str(s[120:]).split('|')
    return Block(previous_hash, transactions, nonce, merkle_root, timestamp)

  def to_bytes(self, include_transactions=True):
    s = str2b(self.previous_hash) #sz 32
    s += str2b(self.merkle_root) #sz 32
    s += i2b(self.nonce) #sz 32
    s += self.timestamp #size 24
    if include_transactions:
      s += str2b('|'.join(self.transactions))
    return s

  def mine(self):
    target = '0' * self.difficulty
    while True:
      block_hash = self.digest()
      if (block_hash[:self.difficulty] == target):
        break
      self.nonce += 1

  def validate(self):
    block_hash = self.digest()
    return block_hash[:self.difficulty] == ('0' * self.difficulty)