'''
miner.py
'''
import time
from util import *

class Miner:
  block_capacity = 500

  self.chain = []
  self.transaction_pool = []

  def __init__(self):  
    pass

  def receive(self, transaction):
    pass

  def update_chain(self, block):
    if block.validate():
      chain.append(block)    

  def publish_block(self, block):
    pass

  def mine(self):
    if len(transaction_pool) >= block_capacity:
      new_block = Block(chain[-1].block_hash, transaction_pool[:block_capacity])
      # TODO: should have sth to interrupt this when another block is added
      new_block.mine()
      transaction_pool = transaction_pool[500:]
      update_chain(new_block)
      publish_block(new_block)
