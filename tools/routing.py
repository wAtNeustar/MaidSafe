#!/usr/bin/env python
# Copyright (c) 2012 maidsafe.net limited
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#     * Neither the name of the maidsafe.net limited nor the names of its
#     contributors may be used to endorse or promote products derived from this
#     software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import datetime
import subprocess
import utils
import random
from subprocess import Popen, PIPE, STDOUT
from time import sleep

from routing_python_api import *

num_of_nodes = 20
num_of_bootstraps = 2
num_of_vaults = num_of_nodes / 2 - num_of_bootstraps
num_of_clients = num_of_nodes - num_of_vaults - num_of_bootstraps

send_to_direct = 0
send_to_group = 1
send_to_closest = 2


def SetupKeys(num):
  print("\tSetting up keys ... ")
  return subprocess.call(['./routing_key_helper', '-c', '-p', '-n', str(num)], stdout=PIPE)


def SetupBootstraps():
  print("\tSetup boostrap nodes ...")
  p_b0 = RoutingNode("", False, 0)
  p_b1 = RoutingNode("", False, 1)
  peer_0 = p_b0.GetNodeInfo()
  if peer_0 == -1:
    return -1
  peer_1 = p_b1.GetNodeInfo()
  if peer_1 == -1:
    return -1
  p_b0.SetPeer(peer_1)
  p_b1.SetPeer(peer_0)
  p_b0.ZeroStateJoin()
  p_b1.ZeroStateJoin()
  sleep(2)
  return [peer_0, p_b0, p_b1]


def AddRoutingObject(peer, idx):
  if idx < (num_of_nodes / 2):
    p_v = RoutingNode("", False, idx)
  if idx >= (num_of_nodes / 2):
    p_v = RoutingNode("", True, idx)
  p_v.SetPeer(peer)
  p_v.Join()
  if p_v == -1:
    print 'Failed to add routing object ' + str(i) + ' !'
    return -1
  sleep(1)
  return p_v


def SetupRoutingNodes(peer, num_vaults, num_clients):
  print("\tSetup " + str(num_vaults) + " vaults and " + str(num_clients) + " clients, please wait ....")
  p_nodes = range(num_vaults + num_clients)
  i = 0;
  while i < (num_vaults + num_clients):
    if i < num_vaults:
      p_nodes[i] = RoutingNode("", False, i + num_of_bootstraps)
    if i >= num_vaults:
      p_nodes[i] = RoutingNode("", True, (num_of_bootstraps + num_of_vaults) + (i - num_vaults))
    p_nodes[i].SetPeer(peer)
    p_nodes[i].Join()
    if p_nodes[i] == -1:
      print 'Failed to add routing object ' + str(i + num_of_bootstraps) + ' !'
      #TODO cleanup the previous opened nodes
      return -1
    i = i + 1
    sleep(1)
  return p_nodes


def CheckNodeIsNotInRoutingTable(p_nodes, idx):
  for index in range(num_of_nodes / 2):
    if(p_nodes[index].ExistInRoutingTable(idx)):
      return -1
  return 0


def CheckRoutingTableSize(p_nodes):
  find_unexpected = False
  for index in range(num_of_bootstraps + num_of_vaults):
    routing_table_size = p_nodes[index].RoutingTableSize()
    if (routing_table_size < (num_of_bootstraps + num_of_vaults - 1)):
      find_unexpected = True
      print("\trouting table in node " + str(index) + " is incorrect ; expected : " + str(num_of_bootstraps + num_of_vaults - 1) + " , having : " + str(routing_table_size))
  if find_unexpected:
    return -1
  return 0


def SendGroup(p_nodes, p, source, target):
  if source == -1:
    source = random.randint(0, num_of_nodes / 2 - 1)
  if p_nodes != -1:
    p = p_nodes[source]
  print("\tSending a 1024 bytes msg from " + str(source) + " to group index " + str(target) + ", please wait ...")
  result = p.SendAMessage(target, send_to_group, 1024)
  if result:
    print("\t Message sent sucessfully")
  else:
    print("\t Message sending failed")
  return result


def SendDirectMsg(p_nodes, p_n, source, dst, datasize):
  if source == -1:
    source = random.randint(0, num_of_nodes / 2 - 1)
  if dst == -1:
    dst = source;
    while(dst == source):  # send to self will be super quick, shall be excluded
      dst = random.randint(0, num_of_nodes / 2 - 1) # dest can be a bootstrap node
  if p_nodes != -1:
    p_n = p_nodes[source]
  print("\tSending a " + str(datasize) + " bytes msg from " + str(source) + " to " + str(dst) + ", please wait ...")
  result = p_n.SendAMessage(dst, send_to_direct, datasize)
  if result:
    print("\t Message sent sucessfully")
  else:
    print("\t Message sending failed")
  return result


def JAV1(peer):
#  print("Running Routing Sanity Check JAV1 Test, please wait ....")
  p_v = AddRoutingObject(peer, 2)
  if p_v == -1:
    print 'Failed to add routing object!'
    return -1
  return 0


def JAV2(peer):
#  print("Running Routing Sanity Check JAV2 Test, please wait ....")
  p_v = AddRoutingObject(peer, 8)
  if p_v == -1:
    print 'Failed to add routing object!'
    return -1
  result = 0
  if not SendDirectMsg(-1, p_v, 8, 1, 1024):
    result = -1
  return result


def P1(p_nodes):
  if p_nodes == -1:
    return -1;
 # print("Running Routing Sanity Check P1 Test, please wait ....")
  num_iteration = 5
  for i in range(num_iteration): # vault to vault
    if not SendDirectMsg(p_nodes, -1, -1, -1, 1048576):
      return -1
#  print('\tAverage transmission time of 1 MB data from vault to vault is : ' + str(duration / num_iteration))
  for i in range(num_iteration): # client to vault
    source = random.randint(num_of_nodes / 2, num_of_nodes - 1)
    if not SendDirectMsg(p_nodes, -1, source, -1, 1048576):
      return -1
#  print('\tAverage transmission time of 1 MB data from client to vault is : ' + str(duration / num_iteration))
  return 0


def JAC1(peer, p_nodes):
#  print("Running Routing Sanity Check JAC1 Test, please wait ....")
  client_index = num_of_nodes / 2 + 2
  p_c = AddRoutingObject(peer, client_index)
  result = 0
  if p_c == -1:
    print 'Failed to add routing object!'
    return -1
  if SendDirectMsg(-1, p_c, client_index, client_index, 1024):
    print 'Client shall not be able to send to itself'
    result = -1

  if not SendDirectMsg(-1, p_c, client_index, 5, 1024):
    print 'Client failed to send to vault 5'
    result = -1
  if not CheckNodeIsNotInRoutingTable(p_nodes, client_index):
    result = -1
  return result


def JAC2(peer, p_nodes):
#  print("Running Routing Sanity Check JAC2 Test, please wait ....")
  v_drop = 3
  # drop the vault first
  p_nodes[v_drop] = -1
  sleep(1)
  # join the node back
  p_nodes[v_drop] = AddRoutingObject(peer, v_drop)
  if p_nodes[v_drop] == -1:
    print "Failed to join the dropped node back!"
    return -1
  # check routing table
  result = 0
  for i in range(num_of_nodes / 2, num_of_nodes):
#   print '----------------- :' + str(i)
    if CheckNodeIsNotInRoutingTable(p_nodes, i) == -1:
      result = -1
  return result

def  SGM1(p_nodes):
#  print("Running Routing Sanity Check SGM1 Test, please wait ....")
  num_iteration = 5
  for i in range(num_iteration):
    rnd = random.randint(0, num_of_nodes / 2 - 1)
    if not SendGroup(p_nodes, -1, rnd, -1):
      return -1
    target = random.randint(0, num_of_nodes - 1)
    if not SendGroup(p_nodes, -1, rnd, target):
      return -1
  return 0


def SanityCheck():
  global num_of_nodes
  num_of_nodes = 20
  global num_of_vaults
  num_of_vaults = num_of_nodes / 2 - num_of_bootstraps
  global num_of_clients
  num_of_clients = num_of_nodes - num_of_vaults - num_of_bootstraps
  print("Running Routing Sanity Check, please wait ....")

  if not SetupKeys(num_of_nodes) == 0:
    return -1
  items = SetupBootstraps()
  if items == -1:
    return -1
  peer = items[0]
  p_bs = [items[1], items[2]]

  if JAV1(peer) == 0:
    print 'Join a vault  : PASSED\n'
  else:
    print 'Join a vault  : FAILED\n'

  if JAV2(peer) == 0:
    print 'Join a vault and send message  : PASSED\n'
  else:
    print 'Join a vault and send message  : FAILED\n'

  p_vaults = SetupRoutingNodes(peer, num_of_vaults, 0)
  if JAC1(peer, p_bs + p_vaults) == 0:
    print 'Join a client and send a message : PASSED\n'
  else:
    print 'Join a client and send a message  : FAILED\n'

  p_clients = SetupRoutingNodes(peer, 0, num_of_clients)
  p_nodes = p_bs + p_vaults + p_clients

  if SGM1(p_nodes) == 0:
    print 'Test group messages  : PASSED\n'
  else:
    print 'Test group messages  : FAILED\n'

  if P1(p_nodes) == 0:
    print 'Performance Test (send large msg multiple times)  : PASSED\n'
  else:
    print 'Performance Test (send large msg multiple times)  : FAILED\n'

  if JAC2(peer, p_nodes) == 0:
    print 'Check no client in routing table  : PASSED\n'
  else:
    print 'Check no client in routing tables : FAILED\n'

  utils.ClearScreen()


def GetAnInputNum(default, msg):
  num = default
  number = raw_input(msg)
  try:
    num = int(number)
    if num < 0:
      num = default;
      print("\terror input, using default value")
    if num > 1024:
      num = default;
      print("\terror input, using default value")
  except:
    print("\terror input, using default value")
    pass
  return num

def MsgSendingMenu():
  global num_of_vaults
  num_of_vaults = GetAnInputNum(8, "Please input number of vaults to setup (default is 8 vaults): ")
  global num_of_clients
  num_of_clients = GetAnInputNum(10, "Please input number of clients to setup (default is 10 clients): ")
  global num_of_nodes
  num_of_nodes = num_of_bootstraps + num_of_vaults + num_of_clients

  if not SetupKeys(num_of_nodes) == 0:
    return -1
  items = SetupBootstraps()
  if items == -1:
    return -1
  peer = items[0]
  p_bs = [items[1], items[2]]
  p_ = SetupRoutingNodes(peer, num_of_vaults, num_of_clients)
  p_nodes = p_bs + p_

  option = 'a'
  while(option != 'm'):
    utils.ClearScreen()
    print ("================================")
    print ("MaidSafe Quality Assurance Suite | routing Actions | Msg Sending")
    print ("================================")
    print ("1: Sending a Direct Msg to Random")
    print ("2: Sending a Direct Msg to Target")
    print ("3: Sending Direct Msg to Random Target infinitely (type x to stop)")
    print ("4: Sending a Group Msg to Random Group")
    print ("5: Sending a Group Msg to Target Group")
    print ("6: Sending Group Msg to Random Group infinitely (type x to stop)")
    print ("7: Checking Routing Table Size")

    option = raw_input("Please select an option (m for main QA menu): ").lower()
    if (option == "1"):
      source = random.randint(0, num_of_nodes - 1)
      SendDirectMsg(p_nodes, -1, source, -1, 1048576)
    if (option == "2"):
      number = raw_input("Please input index of node to send from: ")
      source = int(number)
      number = raw_input("Please input index of node to send to: ")
      dest = int(number)
      SendDirectMsg(p_nodes, -1, source, dest, 1048576)
    if (option == "3"):
      while(option != 'x'):
        source = random.randint(0, num_of_nodes - 1)
        SendDirectMsg(p_nodes, -1, source, -1, 1048576)
    if (option == "4"):
      source = random.randint(0, num_of_nodes - 1)
      SendGroup(p_nodes, -1, source, -1)
    if (option == "5"):
      number = raw_input("Please input index of node to send from: ")
      source = int(number)
      number = raw_input("Please input index of group to send to: ")
      dest = int(number)
      SendGroup(p_nodes, -1, source, dest)
    if (option == "6"):
      while(option != 'x'):
        source = random.randint(0, num_of_nodes - 1)
        SendGroup(p_nodes, -1, source, -1)
    if (option == "7"):
      if CheckRoutingTableSize(p_nodes) == -1:
        print 'Routing table size check  : FAILED\n'
      else:
        print 'Routing table size check  : PASSED\n'
  utils.ClearScreen()


def RoutingMenu():
  option = 'a'
  utils.ClearScreen()
  while(option != 'm'):
    utils.ClearScreen()
    procs = utils.CountProcs('lifestuff_vault')
    print(str(procs) + " Vaults running on this machine")
    print ("================================")
    print ("MaidSafe Quality Assurance Suite | routing Actions")
    print ("================================")
    print ("1: Routing Sanity Checks (10 minutes average)")
#    if procs == 0:
#      print ("2: Connect nodes to remote network")
#    else:
    print ("3: Feature Checks")
    print ("4: Kill all routing nodes on this machine")
    print ("5: Random churn on this machine, rate (% churn per minute) (not yet implemented)")
    print ("6: Msg Send Menu")
    option = raw_input("Please select an option (m for main QA menu): ").lower()
    if (option == "1"):
      SanityCheck()
    if (option == "6"):
      MsgSendingMenu()

  utils.ClearScreen()


def main():
  print("This is the suite for lifestuff QA analysis")
  RoutingMenu()

if __name__ == "__main__":
  sys.exit(main())

