'''
block.py
create a block for blockchain 
'''
import time
import pickle
import random
import logging
from crypto import merkle_root_generation, check_prefix_b64, double_sha256

from transaction import Transaction

class Block:
  difficulty = 2
  stop_mining = False

  def __init__(self, prev_hash, transactions=None, nonce=0, merkle_root=None, timestamp=time.asctime().encode()):
    self.prev_hash = prev_hash
    self.timestamp = timestamp
    self.nonce = nonce
    self.transactions = transactions

    self.hashcode = None
    self._compute()
    

  def _compute(self):
    tnsn = self.transactions if type(self.transactions[0])==bytes else [t.Digest for t in self.transactions]
    self.merkle_root = merkle_root_generation(tnsn)
    self.hashcode = self.digest()


  def __str__(self, block_head_only=True):
    return "Created Time: " + self.timestamp.decode() + \
           "\nPrevious hash: " + str(self.prev_hash) + \
           "\nNonce: " + str(self.nonce) + \
           "\nHash: " + str(self.hashcode) + \
           ('\n' if block_head_only else '\n' + '\n\n'.join([str(tsn) for tsn in self.transactions]))


  def digest(self):
    m = self.to_bytes(block_head_only=True)
    self.hashcode = double_sha256(m)
    return self.hashcode


  @staticmethod
  def from_bytes(data, tsns=None):
    data = pickle.loads(data)

    # reconstruct transactions
    if 'tsn_hash_list' in data:
      tsn_hash_list = data['tsn_hash_list'].split(b'|')
      try: 
        tsns = tsn_hash_list if (tsns is None) else [tsns[tsn_hash] for tsn_hash in tsn_hash_list]
      except: raise ValueError(data['hashcode'])
    else:
      tsns = data['full_tsns'].split(b'|')
      tsns = [Transaction(tsn) for tsn in tsns]
    return Block(data['prev_hash'], tsns, data['nonce'], timestamp=data['timestamp'])


  def to_bytes(self, block_head_only=False, tsn_hash_only=True):
    data = {'prev_hash': self.prev_hash, 'nonce': self.nonce, 'timestamp': self.timestamp}

    if block_head_only:
      data['merkle'] = self.merkle_root
    else:
      data['hashcode'] = self.hashcode
      if tsn_hash_only:
        tsn_hash_list = [t.Digest for t in self.transactions]
        data['tsn_hash_list'] = b'|'.join(tsn_hash_list)
      else:
        data['full_tsns'] = b'|'.join([tsn.to_bytes(nosign=True) for tsn in self.transactions])

    return pickle.dumps(data)


  def mine(self):
    logging.debug('Block - start mining now...')
    start = time.time()
    self.nonce = random.randint(-1e9, 1e9)
    initial_nonce = self.nonce
    while not self.stop_mining:
      if self.validate():
        logging.debug('Block - mining is done: {} tries in {:.0f}s'.format(self.nonce - initial_nonce, time.time() - start)) 
        return True
      self.nonce += 1
    # self.stop_mining = False
    logging.debug('Block - mining is aborted...')
    return False


  def validate(self, prev_hash=None, strict=True):
    if strict:
      self._compute()
    return check_prefix_b64(self.hashcode, self.difficulty)

  def __eq__(self, other):
    if not isinstance(other, Block):
      return False
    self._compute()
    return self.prev_hash == other.prev_hash\
           and self.nonce == other.nonce\
           and self.merkle_root == other.merkle_root \
           and self.timestamp == other.timestamp \
           and self.hashcode == other.hashcode