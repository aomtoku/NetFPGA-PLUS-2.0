#!/usr/bin/env python3

#
# Copyright (C) 2010, 2011 The Board of Trustees of The Leland Stanford
#                          Junior University
# Copyright (C) 2011 Eric Lo
# All rights reserved.
#
# This software was developed by Stanford University and the University of Cambridge Computer Laboratory 
# under National Science Foundation under Grant No. CNS-0855268,
# the University of Cambridge Computer Laboratory under EPSRC INTERNET Project EP/H040536/1 and
# by the University of Cambridge Computer Laboratory under DARPA/AFRL contract FA8750-11-C-0249 ("MRC2"), 
# as part of the DARPA MRC research programme.
#
# @NETFPGA_LICENSE_HEADER_START@
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @NETFPGA_LICENSE_HEADER_END@

import sys
from threading import Thread, Lock, Event
import time
import socket
import os
from collections import deque
from select import select
from scapy.all import *
from .scapy_sniff_patch import sniff

class pktExpect(Thread):
    ############################
    # Function: __init__
    # Arguments: calling object
    #            device name to sniff
    # Description: overrides Thread.__init__, initializes vars
    ############################
    def __init__ (self, device):
        Thread.__init__(self)
        self.daemon = True
        self.device = device
        self.done = False
        self.ready = False
        self.count = 0
        self.pkts = []
        self.exp_pkts = []
        self.matched =[]
        self.lock = Lock()
        self.status = -1
        self.compareEvent = Event()
        self.compare = pktCompare(self)
        self.barrierEvent = Event()
        self.started = False

    ############################
    # Function: run
    # Arguments: calling object
    # Description: starts background comparison thread, runs sniff
    ############################
    def run(self):
        self.compare.start()
        self.started = True
        while not self.done:
            try:
                sniff(prn=self.addPkt,iface=self.device, store=0,
                      stopperTimeout=1, stopper=self.isDone)
            except(KeyboardInterrupt):
                self.finish()

    ############################
    # Function: hasStarted
    # Arguments: calling object
    # Description: checks if the run method has been called
    ############################
    def hasStarted(self):
        return self.started

    ############################
    # Function: addPkt
    # Arguments: calling object
    #            packet to add to pkts
    # Description: adds packet to either matched or received packets list
    #              notifies background thread to compare packet lists
    ############################
    def addPkt(self,pkt):
        self.lock.acquire()
        self.pkts.append(pkt)
        self.count += 1
        self.barrierEvent.clear()
        self.lock.release()
        #if self.compareEvent.is_set():
        #    pass
        #else:
        #    self.compareEvent.set()

    ############################
    # Function: isDone
    # Arguments: calling object
    # Description: tells sniff if it should stop
    #              sets ready so client knows it can start sending packets
    ############################
    def isDone(self):
        self.ready = True
        return self.done

    ############################
    # Function: isReady
    # Arguments: calling object
    # Description: tells client if sniff is ready to receive packets
    ############################
    def isReady(self):
        return self.ready

    ############################
    # Function: expectPkt
    # Arguments: calling object
    #            packet to expect
    #            optional mask to apply to packet
    # Description: adds packet to list of packets to expect
    ############################
    def expectPkt(self, pkt, mask = None):
        self.lock.acquire()
        self.exp_pkts.append((pkt, mask))
        self.barrierEvent.clear()
        self.lock.release()

    ############################
    # Function: comparePkts
    # Arguments: calling object
    #            pkt A
    #            pkt B
    #            mask to use while comparing packets
    # Description: compares to packets, using the optional mask to ignore
    #              certain bytes
    ############################
    def comparePkts(self, pkta, pktb, mask = None):
        if mask:
            pkta = [ord(x) for x in pkta]
            pktb = [ord(x) for x in pktb]
            mask = [ord(x) for x in mask]
            for i in range(min(len(pkta), len(mask))):
                pkta[i] = pkta[i] & ~mask[i]
            for i in range(min(len(pktb), len(mask))):
                pktb[i] = pktb[i] & ~mask[i]

            pkta = ''.join([chr(x) for x in pkta])
            pktb = ''.join([chr(x) for x in pktb])

        return pkta == pktb

    ############################
    # Function: resolvePkts
    # Arguments: calling object
    # Description: checks unmatched received packets against unmatched expected packets
    #              notifies barrierEvent if expected and received packet lists are empty
    ############################
    def resolvePkts(self):
        self.lock.acquire()
        if (len(self.pkts) > 0) and  (len(self.exp_pkts) > 0):
            self.barrierEvent.clear()
            i = 0
            numPkts = len(self.pkts)
            while i < numPkts:
                strpkt = str(self.pkts[i])
                for (exp, mask) in self.exp_pkts:
                    strexp = str(exp)
                    strmask = None
                    if mask:
                        strmask = str(mask)
                    matches = self.comparePkts(strexp, strpkt, strmask)
                    if not matches and len(exp) < 60 and self.pkts[i].haslayer(scapy.Padding):
                        matches = self.comparePkts(
                                ''.join([strexp,str(self.pkts[i][scapy.Padding])]),
                                strpkt, strmask)
                    if matches:
                        self.matched.append(self.pkts[i])
                        self.pkts.remove(self.pkts[i])
                        self.exp_pkts.remove((exp, mask))
                        numPkts -= 1
                        i -= 1
                        break
                i += 1
        self.lock.release()
        if (len(self.exp_pkts) == 0):
            self.barrierEvent.set()
            return True
        return False

    ############################
    # Function: restart
    # Arguments: calling object
    # Description: resets all packet lists
    ############################
    def restart(self):
        self.lock.acquire()
        self.exp_pkts = []
        self.pkts = []
        self.matched = []
        self.lock.release()


    ############################
    # Function: finish
    # Arguments: calling object
    # Description: tells sniff to stop sniffing
    #              returns packets
    ############################
    def finish(self):
        print(self.device, 'finishing up')
        self.done = True
        self.lock.acquire()
        exp_pkts = [ exp for (exp, mask) in self.exp_pkts ]
        #print "\n\n\n -------------- received=%d and exptected=%d --------------- \n\n" % (len(self.pkts), len(exp_pkts))
        return (self.matched, self.pkts, exp_pkts)

class pktSend(Thread):
    ############################
    # Function: __init__
    # Arguments: calling object
    #            device name
    #            socket configuration options
    # Description: overrides Thread.__init__, initializes vars, opens socket
    ############################
    def __init__(self, device, family = socket.AF_PACKET,
                 type = socket.SOCK_RAW, proto = socket.htons(3)):
        Thread.__init__(self)
        self.daemon = True
        self.lock = Lock()
        self.closed = False
        self.toSend = deque()
        self.sock = socket.socket(family, type, proto)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 0)
        while True:
            r,w,x = select.select([self.sock.fileno()], [], [], 0)
            if r:
                os.read(self.sock.fileno(),1600)
            else:
                break
        self.sock.bind((device,3))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2**30)
        self.sentcount = 0
        self.sendcount = 0
        self.device = device

    ############################
    # Function: run
    # Arguments: calling object
    # Description: overrides Thread.run, sends packets in queue
    ############################
    def run(self):
        while not self.closed:
            try:
                if len(self.toSend) > 0:
                    self.lock.acquire()
                    self.sock.send(bytes(self.toSend.popleft()))
                    self.sentcount += 1
                    self.lock.release()
            except(KeyboardInterrupt):
                self.close()

    ############################
    # Function: sendPkt
    # Arguments: calling object
    #            packet to send
    # Description: adds packets to queue to be sent
    #              delays so scapy doesn't drop packets
    ############################
    def sendPkt(self, pkt):
        self.lock.acquire()
        self.toSend.append(pkt)
        self.sendcount += 1
        self.lock.release()

    ############################
    # Function: close
    # Arguments: calling object
    # Description: waits for packets to drain, then closes socket
    ############################
    def close(self):
        while len(self.toSend) > 0:
            pass
        if self.closed:
            return
        self.closed = True
        self.sock.close()

class pktCompare(Thread):
    ############################
    # Function: __init__
    # Arguments: calling object
    #            pktExpect object
    # Description: overrides Thread.__init__, initializes vars
    ############################
    def __init__ (self, expect):
        Thread.__init__(self)
        self.daemon = True
        self.done = False
        self.compareEvent = expect.compareEvent
        self.compare = expect.resolvePkts

    ############################
    # Function: run
    # Arguments: calling object
    # Description: waits until woken by addPkt, then calls resolvePkts
    ############################
    def run(self):
        while not self.done:
            self.compareEvent.wait()
            self.compare()
            self.compareEvent.clear()
