# Copyright (C) 2015 
# Author: aquatoney @ Xi'an Jiaotong University

"""
Definitions of basic network properties. 
"""

switch_factor = 10000

edge_ports = []
switches = {}
topology = {}

class Port:
  pid = -1
  sid = -1

  def __init__(self, p, s):
    self.pid = p
    self.sid = s

  def __hash__(self):
    return hash(self.sid*switch_factor+self.pid)

  def __eq__(self, rhs):
    return self.sid == rhs.sid and self.pid == rhs.pid

class Switch:
  sid = -1
  ports = {}

  def __init__(self, s, ports_list):
    self.sid = s
    self.ports = {}
    for i in ports_list:
      self.ports[i] = Port(i, self.sid)
    # for i in range(1, max_port+1): self.ports[i] = Port(i, self.sid)

  def __eq__(self, rhs):
    return self.sid == rhs.sid

  def dump(self):
    print self.sid
    for p in self.ports.values():
      if p in edge_ports:
        print 'port %s is an edge port' % p.pid
      elif p not in topology.keys():
        print 'port %s is an empty port' % p.pid
      else:
        linked_port = topology[p]
        print 'port %s links to port %s in switch %s' % (p.pid, linked_port.pid, linked_port.sid)

  def get_connected_sw(self):
    connected = []
    for p in self.ports.values():
      if p not in topology.keys():
        continue
      linked_port = topology[p]
      if not linked_port in edge_ports:
        connected.append((p.pid, linked_port.sid))
    return connected

def set_networks():
  pass
  
def add_double_link(p1, p2):
  topology[p1] = p2
  topology[p2] = p1

def add_single_link(p1, p2):
  topology[p1] = p2

def add_edge_ports(p1):
  edge_ports.append(p1)
