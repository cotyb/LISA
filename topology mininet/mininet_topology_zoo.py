#!/usr/bin/env python
# conding = "utf-8"

__author__ = "cotyb"

from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import Link, Intf, TCLink
from mininet.topo import Topo
from mininet.util import dumpNodeConnections
import logging
import os

class Mininet_topology_zoo(Topo):
    '''
    construct the topology in mininet from topology zoo
    http://www.topology-zoo.org/
    every switch has only one host.
    '''
    all_switches = []
    all_links = []

    def __init__(self):
        # Read topology info
        file = open("Xeex.gml","r")
        self.all_switches, self.all_links = self.handler(file)
        # Add default members to class
        super(Mininet_topology_zoo, self).__init__()
        # Create switches and hosts
        self._addSwitches(self.all_switches)
        self._addLinks(self.all_switches, self.all_links)

    def handler(self,file):
        switches = []
        links = []
        for line in file:
            if line.startswith("    id "):
                token = line.split("\n")
                token = token[0].split(" ")
                line = line[7:]
                if not line.startswith("\""):
                    token = line.split("\n")
                    switches.append(int(token[0]))
            if line.startswith("    source"):
                token = line.split("\n")
                token = token[0].split(" ")
                sw1 = int(token[-1])
            if line.startswith("    target"):
                token = line.split("\n")
                token = token[0].split(" ")
                sw2 = int(token[-1])
                links.append((sw1,sw2))
        return switches, links

    def _addSwitches(self,switches):
        for s in switches:
            self.addSwitch('s%d' %s)
            self.addHost('h%d'  %s)


    def _addLinks(self,switches,links):
        for s in switches:
            self.addLink("h%s" %s, "s%s" %s, 0)
        for dpid1, dpid2 in links:
            self.addLink(node1="s%s" %dpid1, node2="s%s" %dpid2)
topos = {'topo_zoo':(lambda :Mininet_topology_zoo())}
