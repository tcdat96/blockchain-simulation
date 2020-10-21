'''
block.py
create a block for blockchain 
'''
import time
from util import *

class BlockHead:
  def __init__(self, previous_hash, merkle_root, nonce = 0, block_hash = None):  
    self.previous_hash = previous_hash
    self.merkle_root = merkle_root
    self.nonce = nonce
    self.block_hash = block_hash if (block_hash != None) else digest()

  def __str__(self):
    return "Created Time: " + self.timestamp.decode() + \
           "\nPrevious hash: " + str(self.previous_hash) + \
           "\nMerkle root: " + str(self.merkle_root) + \
           "\nNonce: " + str(self.nonce) + \
           "\nDigest: " + str(self.block_hash)

  def incrementNonce():
  	self.nonce += 1
  	return digest()

  def digest(self):
    m = self.to_bytes()
    return double_sha256(m)

  @staticmethod
  def from_bytes(s):
    previous_hash = b2str(s[:32])
    merkle_root = b2str(s[32:64])
    block_hash = b2str(s[64:96])
    nonce = b2i(s[96:128])
    return BlockHead(previous_hash, merkle_root, nonce, block_hash, timestamp)

  def to_bytes(self):
    s += str2b(self.previous_hash) #sz 32
    s += str2b(self.merkle_root) #sz 32
    s += str2b(self.block_hash) #sz 32
    s += i2b(self.nonce) #sz 32
    return s

class Block:
  self.diff = '0000'

  def __init__(self, previous_hash=None, transactions=[], timestamp=time.asctime().encode(), block_head=None):
  	if block_head:
      self.block_head = block_head
    else:
  	  self.transactions = map(lambda transaction: transaction.digest(), transactions)
      merkle_root = merkel_root_generation(self.transactions, len(transactions))
      self.block_head = BlockHead(previous_hash, merkle_root)

  @staticmethod
  def from_bytes(s):
    self.timestamp = s[:24]
    self.block_head = BlockHead.from_bytes(s[24:152])
    self.transactions = b2str(s[152:]).split('|')
    return Block(timestamp=timestamp)

  def to_bytes(self):
    s = self.timestamp #size 24
    s += self.block_head.to_bytes()
    s += str2b('|'.join(self.transactions))
    return s

  def hash_block(self):
    return self.block_head.digest()

  def mine(self):
  	while True:
  		block_hash = self.block_head.incrementNonce()
  		if (block_hash[:len(self.diff)] == self.diff):
  			self.block_hash = block_hash
  			break

  def validate(self):
  	block_hash = self.block_head.digest()
  	return block_hash == self.block_hash && block_hash[:len(self.diff)] == self.diff