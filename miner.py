'''
miner.py
'''
from enum import Enum

import time
import random
import logging
import pickle

from threading import Lock, RLock

from transaction import Transaction
from block import Block
from EventHook import EventHook

class Status(Enum):
  INVALID = 0
  VALID = 1
  DUPLICATE = 2

class Miner:
  block_capacity = 5
  min_sync_interval = 30      # seconds

  # The general rule is as follows
  # 1. if the miner needs to be synced
  #   + no mining is allowed, current task will also be cancelled
  #   + newly received block must wait, unless we are already handling it
  # 2. if the newly received block is valid, the mining task will be aborted, even if it's done
  chain_lock = Lock()
  sync_lock = Lock()

  def __init__(self):
    self.chain = []
    self.tsn_pool = {}
    self.new_block = None

    self.pending_blocks = []
    self.invalid = []

    self.need_to_sync = False
    self.last_sync = time.time()

    self.on_block_added_listeners = EventHook()


  def to_bytes(self):
    data = {'chain': self.chain, 'pool': self.tsn_pool}
    return pickle.dumps(data)


  def restore(self, data):
    data = pickle.loads(data)
    self.chain = data['chain']
    self.tsn_pool = data['pool']


  def get_ledger_size(self):
    return len(self.to_bytes())


  def trigger_sync(self):
    self.need_to_sync = True


  def sync_data(self, data):
    data = pickle.loads(data)
    chain = data['chain']
    pool = data['pool']
    
    # wait for all chain-related operations to complete
    self.chain_lock.acquire()

    # suspend adding new blocks
    if self.need_to_sync and not self.sync_lock.locked():
      self.sync_lock.acquire()

    # abort mining
    self._intercept_mining()

    # we need to assume the first block is correct now
    # we will verify this in the next sync
    if len(self.chain) == 0:
      self.chain.append(chain[0])

    diff = len(chain) - len(self.chain)
    # if it's even behind us or doesn't match our latest block
    if diff < 0 or self.chain[0] != chain[0] or self.chain[-1] != chain[len(self.chain)-1]:
      return False
    elif diff > 0:
      initial_size = len(self.chain)
      # append each block to chain
      for block in chain[len(self.chain):]:
        # if something is not right
        if not self._handle_received_block(block):
          # restore initial chain
          self.chain = self.chain[:initial_size]
          return False
      
      # all blocks are added to chain
      # now to the pool
      self.tsn_pool.update(pool)

      return False

    # it is the same as us, then sync is complete
    self.need_to_sync = False
    self.sync_lock.release()
    return True


  def add_transaction(self, tsn):
    if tsn.Digest in self.tsn_pool:
      logging.debug('Miner - duplicated transaction: ' + tsn.Digest.decode())
      return Status.DUPLICATE
    if tsn.verify() and self.verify_fund(tsn):
      self.tsn_pool[tsn.Digest] = tsn
      logging.debug('Miner - one transaction added. Pool now has {} transactions'.format(len(self.tsn_pool)))
      return Status.VALID
    else:
      logging.debug('Miner - invalid transaction: ' + tsn.Digest.decode() + str(tsn.verify()) + str(self.verify_fund(tsn)))
      return Status.INVALID


  def add_first_block(self, data):
    self.chain_lock.acquire()
    # make sure chain is empty
    if len(self.chain) == 0:
      self._intercept_mining()
      # reconstruct
      block = Block.from_bytes(data, self.tsn_pool)
      if block is not None:
        self._append_chain(block)
        logging.debug('Miner - First block added')
    self.chain_lock.release()



  def add_received_block(self, data):
    logging.debug('Miner - receiving block from others')

    self.chain_lock.acquire()

    # if syncing
    if self.need_to_sync:
      # allow sync to continue
      self.chain_lock.release()
      # then wait for it to complete
      self.sync_lock.acquire()
      self.sync_lock.release()
      self.chain_lock.acquire()

    # reconstruct block
    try: block = Block.from_bytes(data, self.tsn_pool)
    except Exception as e:
      # check if it's a duplicate
      hashcode = str(e)
      if any(str(b.hashcode) == hashcode for b in self.chain):
        logging.debug('Miner - duplicated block: ' + hashcode)
        self.chain_lock.release()
        return Status.DUPLICATE, None
      # otherwise, request sync, then recheck it after sync
      logging.debug('Miner - missing transactions. Requesting sync...')
      self.trigger_sync()
      self.chain_lock.release()
      return self.add_received_block(data)

    # attempt to add this block
    done = self._handle_received_block(block)

    # it's okay to continue mining now
    self.chain_lock.release()

    # if sync is required, recheck it after sync
    if not done and self.need_to_sync:
      logging.debug('Miner - mismatch block. Requesting sync...')
      return self.add_received_block(data)

    return Status.VALID if done else Status.INVALID, block


  def _handle_received_block(self, block):    
    done = False
    # validation
    if block.validate():
      # if it's a new block
      if block.prev_hash == self.chain[-1].hashcode:
        # append it to chain
        if self._verify_block(block):
          self._intercept_mining()
          self._append_chain(block)
          done = True
      # or maybe potential of divergence
      elif block.prev_hash == self.chain[-2].hashcode:
        self._handle_divergence(block)
        done = True
      # okay, the block obviously doesn't fit our current chain
      elif not self.need_to_sync:
        if time.time() - self.last_sync > self.min_sync_interval:
          logging.debug('Miner - not matching previous blocks. Initiating syncing...')
          self.trigger_sync()
        else:
          logging.debug('Miner - invalid block')

    return done, block


  def _verify_block(self, block):
    for tsn in block.transactions:
      if not tsn.verify() or not self.verify_fund(tsn):
        logging.debug('Miner - aborting... invalid transaction: {}'.format(tsn.Digest))
        return False


  def _intercept_mining(self):
    logging.debug('Miner - intercepting mining thread...')
    if self.new_block != None:
      self.new_block.stop_mining = True
      self.new_block = None


  def _handle_divergence(self, new_block):
    last_block = self.chain[-1]

    is_new_block_smaller = new_block.nonce < last_block.nonce
    choose_smaller_block = (new_block.nonce + last_block.nonce) % 2 == 0

    if is_new_block_smaller == choose_smaller_block:
      # add back those transactions of the going-to-be-pruned block
      for tsn in last_block.transactions:
        self.tsn_pool[tsn.hashcode] = tsn
      # attempt to replace it with new block
      self.chain = self.chain[:-1]
      if self._verify_block(new_block):
          logging.debug('Miner - divergence: replaced with newly received block')
          self._intercept_mining()
          self._append_chain(new_block)
          del last_block
      else:
        logging.debug('Miner - divergence: newly received block is invalid')
        self._append_chain(last_block)
    else:
        logging.debug('Miner - divergence: keep unchanged')



  def verify_fund(self, new_tsn):
    # ensure maximum of 2 receivers and they are unique
    receivers = new_tsn.Receivers
    if len(receivers) != 1 and (len(receivers) != 2 or receivers[0][1] == receivers[1][1]):
      return False

    receiving = sum([recv[0] for recv in receivers])

    senders = set([sender[1] for sender in new_tsn.Senders])
    for sender in senders:
      receiving -= self._get_latest_balance(sender)

    return receiving == -100 or receiving <= 0


  def _get_latest_balance(self, address):
    balance = 0
    # iterate backwards
    for block in self.chain[::-1]:
      for tsn in block.transactions:
        # if they received money
        for recv in tsn.Receivers:
          if address == recv[1]:
            balance += recv[0]
        # and stop if they made this transaction
        if address in tsn.Senders:
          break
    return balance


  def _append_chain(self, block=None):
    if block is None:
      block = self.new_block

    self.chain.append(block)

    # update pool
    for tsn in block.transactions:
      self.tsn_pool.pop(tsn.Digest, None)

    logging.debug('Miner - new block added to chain. Chain now has {} blocks, and pool '
                   'has {} remaining transactions'.format(len(self.chain), len(self.tsn_pool)))


  def _publish_block(self):
    new_block = self.new_block
    if self.new_block is None or not new_block.validate():
      return False

    self.chain_lock.acquire()
    # make sure that we still haven't received any new block
    if self.new_block is not None:
      logging.debug('Miner - broadcasting new block...')
      self.on_block_added_listeners.fire(self.new_block)
      self._append_chain(self.new_block)

    self.chain_lock.release()


  def mine(self):
    while True:
      # print(str(self.chain_lock.locked()) + ' ' + str(self.need_to_sync))

      # if we still don't have enough transactions
      if self.chain_lock.locked() or self.need_to_sync or len(self.tsn_pool) < self.block_capacity:
        time.sleep(1)
        continue

      self.chain_lock.acquire()
      # otherwise, take k random transactions from pool
      transactions = random.sample(list(self.tsn_pool.values()), k=self.block_capacity)
      # create a new block
      prev_hash = self.chain[-1].hashcode if len(self.chain) > 0 else 0
      self.new_block = Block(prev_hash, transactions)
      self.chain_lock.release()
      
      # then start mining
      if self.new_block and self.new_block.mine():
        self._publish_block()
      
