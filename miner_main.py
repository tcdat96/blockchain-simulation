from threading import Thread
from queue import Queue
import time

from miner import Miner, Status
from block import Block
from transaction import Transaction
from network import *

from debug_util import configure_logging

# configure_logging('miner_error.log', level=logging.ERROR)
configure_logging('miner.log', level=logging.DEBUG)

miner = Miner()
buffer = Queue()
network_handler = Networking('10.0.195.216', buffer)
syncing = False

def generate_dummy_transactions():
    from WalletGenerator import Wallet_Generator, Transaction_Generator
    W, B = Wallet_Generator(10, 100.)
    T={}
    for _ in range(5):
        t, s, r = Transaction_Generator(list(W.values()))
        T[t.Digest] = (t, s, r)
        t,s,r = T[t.Digest]
        # s.confirm(t)
        # r.receive(t)
    return B, T


def broadcast_block(block):
    network_handler.broadcast(block.to_bytes(), NEW_BLOCK)


def task_mine():
    miner.mine()


def task_listen():
    network_handler.listening()


def task_sync(tries=3, omit=[]):
    # initial state
    initial_tries = tries
    initial_miner = miner.to_bytes()

    while tries > 0:
        data, addr = network_handler.sync(30, omit)
        # if our data is up-to-date
        if miner.sync_data(data):
           break 
        # otherwise, continue to sync with others
        omit.append(addr)
        tries -= 1

    if tries == 0:
        # out of tries now, restore and run from scratch
        miner.restore(initial_miner)
        task_sync(initial_tries, omit)
    else:
        # sync completed
        global syncing 
        syncing = False


def task_handle_message(addr, tag, data):
    print('({}, {})'.format(addr, tag))
    if tag == NEW_TRANSACTION:
        tsn = Transaction(data)
        status = miner.add_transaction(tsn)
        if status == Status.INVALID:
            network_handler.sending(addr[0], tsn.Digest, INVALID_TRANSACTION)
        elif status == Status.VALID:
            network_handler.broadcast(data, NEW_TRANSACTION, exclude=addr[0])
    elif tag == NEW_BLOCK:
        status, block = miner.add_received_block(data)
        if status == Status.INVALID:
            network_handler.sending(addr[0], block.hashcode, INVALID_BLOCK)
        elif status == Status.VALID:
            network_handler.broadcast(data, NEW_BLOCK, exclude=addr[0])
    elif tag == INVALID_BLOCK:
        miner.trigger_sync()
    elif tag == REQUEST_LEDGER_SIZE:
        ledger_size = miner.get_ledger_size()
        network_handler.sending(addr[0], ledger_size, RETURN_LEDGER_SIZE)
    elif tag == REQUEST_TO_SYNC:
        data = miner.to_bytes()
        network_handler.sending(addr[0], data, RETURN_TO_SYNC, IS_SYN=True)
    elif tag == FIRST_BLOCK:
        miner.add_first_block(data)



if __name__ == "__main__":
    # dummy data
    # first_block, _ = generate_dummy_transactions()
    # miner._update_chain(first_block)
    # for t in transactions.values():
    #     miner.add_transaction(t[0])


    Thread(target=task_mine, daemon=True).start()
    Thread(target=task_listen, daemon=True).start()

    miner.on_block_added_listeners += broadcast_block
    # miner.trigger_sync()
    time.sleep(5)

    network_handler.request(HOST='10.0.195.172')

    while True:
        # check if we need to sync
        # global syncing
        # if miner.need_to_sync and not syncing:
        #     syncing = True
        #     Thread(target=task_sync, daemon=True).start()

        # check for new message
        if not buffer.empty():
            msg = buffer.get_nowait()
            if msg is not None:
                Thread(target=task_handle_message, args=(msg), daemon=True).start()