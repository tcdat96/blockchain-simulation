#@title Client Generator
from miner import Miner
from wallet import Wallet
from transaction import Transaction
from block import Block
from queue import Queue, PriorityQueue
from threading import Thread, Lock
import logging
from network import *
from numpy import argmax
import time
import random

# n: number of wallet
# v: initial amount of each wallet
# return W: dict {wallet_address: wallet}
#.       B: first block
def Wallet_Generator(n:int=15, v:float=100.):
    random.seed()
    W={}
    T =[]
    for _ in range(n):
        w = Wallet()
        t = Transaction (senders=[(b'',w.address)], receivers=[(v, w.address)])
        T.append(t)
        w.receive(t)
        W[w.address]=w
    
    B = Block(b'', T)
    
    return W, B, T

def Transaction_Generator(W):
    s, r = random.sample(list(W.values()), k=2)
    if s.pending['hash']:
        return None
    else:
        if s.balance() > 0.25:
            amount = random.randint(1,s.balance()*4)*0.25
            t = s.send(amount=amount, address=r.address)
            return t, s, r

# Thread Handlers
def Transaction_Generator_Handler(W:dict, T:dict, lock:Lock, net:Networking):
    while not net.stop:
        with lock:
            m = Transaction_Generator(W)
            if m != None:
                T[m[0].Digest] = m
                net.broadcast(m[0].to_bytes(), NEW_TRANSACTION)

# Check if t has reciver address in W and t not in T already,
# Then add to T
def New_Transaction_Handler(W:dict, T:dict, DAT:bytes, lock:Lock):
    t = Transaction()
    t.from_bytes(DAT)
    for receiver in t.Receivers:
        with lock:
            if receiver[1] in W:
                if t.Digest not in T:
                    T[t.Digest] = (t, None, receiver[1])

# If invalid is pending in a wallet, remove pending
# If invalid is in T pool, remove invalid
def Invalid_Transaction_Handler(W:dict, T:dict, DAT:bytes, lock:Lock):
    if DAT in T:
        t,s,r = T[DAT]
        T.pop(DAT)
        with lock:
            if s.pending['hash'] == t.Digest:
                s.pending['hash'] = None


def get_len(C:dict, b:bytes, counter=0):
    if b not in C:
        return counter
    counter += 1
    temp = C[b]
    return max([get_len(C, temp[i].hashcode, counter) for i in temp])


# Add new block to unprocecces list
def New_Block_Handler(C:dict, DAT:bytes, lock:Lock):
    print('add block')
    b = Block.from_bytes(DAT,tsns=None)

    with lock:
        print('add block', b.prev_hash)
        if b.prev_hash not in C: 
            C[b.prev_hash] = {b.hashcode: b}
            return
        if b.hashcode not in C[b.prev_hash]:
            C[b.prev_hash][b.hashcode] = b
            return
        return
    
def Block_Handler(C:dict, T:dict, pre_b:bytes, lockC:Lock, lockT:Lock):
    while True:
        time.sleep(1)
        with lockC:
            print('get block', len(C))
            if len(C) < 1:
                continue
            print('get block', pre_b)
            B = list(C[pre_b].values())
            if len(B) == 1:
                b = B[0]
            else:
                idx = argmax([get_len(C, b.hashcode) for b in B])
                b = B[idx]

            C.pop(pre_b)
            pre_b = b.hashcode

        T_list = b.transactions
        for i in T_list:
            with lockT:
                print('process T')
                if i in T:
                    t,s,r = T[i]
                    s.confirm(t)
                    r.receive(t)


            




# '''
# Test
# '''
if __name__ == "__main__":
    # configure logging
    logging.basicConfig(filename='client.log', level=logging.DEBUG)
    handler = logging.FileHandler('client.log', 'w', 'utf-8')
    logging.getLogger().addHandler(handler)

    # initial wallets and first block
    W, B, T = Wallet_Generator()
    BUFFER = Queue()

    # initial network
    net = Networking('10.0.195.172', BUFFER)
    net.HOSTs=['10.0.195.216', '10.0.195.116', '10.0.195.231']
    Thread(target=net.listening, daemon=True).start()

    # sending first block to all nodes
    time.sleep(10)
    print("Broadcasting first block")
    print(len(B.to_bytes(tsn_hash_only=False)))
    print('Main', B.hashcode)
    net.broadcast(B.to_bytes(tsn_hash_only=False), FIRST_BLOCK)

    lockT = Lock(); lockC = Lock(); C={}; T={}
    Thread(target=Transaction_Generator_Handler, args=(W, T, lockT, net), daemon=True).start()
    print(B)
    Thread(target=Block_Handler, args=(C, T, B.hashcode, lockC, lockT), daemon=True).start()
    start_time = time.time()
    print("looping...")
    while True:
        if time.time()-start_time >= 20:
            for w in W:
                print('pending ', len(list(T.keys())))
                print(W[w])
            start_time=time.time()
        if not BUFFER.empty():
            addr, tag, DAT = BUFFER.get()
            if tag == NEW_TRANSACTION:
                Thread(target=New_Transaction_Handler, args=(W, T, DAT, lockT), daemon=True).start()
            if tag == INVALID_TRANSACTION:
                Thread(target=Invalid_Transaction_Handler, args=(W, T, DAT, lockT), daemon=True).start()
            if tag == NEW_BLOCK:
                Thread(target=New_Block_Handler, args=(C, DAT, lockC), daemon=True).start()

