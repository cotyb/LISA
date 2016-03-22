#!/usr/bin/env python

'''
    a very simple topology for testing LISA
	                  1   3
	         |---------sw2--------|
	         |          |2        |
	        1|2         |         |1
	h1------sw1         |        sw4-------h2
	         |3         |        3|  2
	         |          |3        |
	         |---------sw3--------|
                      1  2 
    Description: Load topology in Mininet
    Author: XieLei (xieleicotyb@126.com)  2016/3/13
'''

from argparse import ArgumentParser
from socket import gethostbyname
from os import getuid

from mininet.log import lg, info
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import Link, Intf
from mininet.node import Host, OVSKernelSwitch, Controller, RemoteController

class LisaTopo( Topo ):

    def __init__( self ):
	    #super(LisaTopo, self).__init__()
        Topo.__init__(self)

        # Set topology info
        hosts = [1, 2]
        switches = [1, 2, 3, 4]
        links = [{(1, 2):(2, 1)}, {(1, 3):(3, 1)}, {(2, 3):(2, 3)}, {(2, 4):(3, 1)}, {(3, 4):(2, 3)}]
        links_sw_host = [{(1, 1):(1, 1)}, {(2, 4):(1, 2)}]

        # add switches and hosts
        self.sw_obj = []
	for s in switches:
            sw = self.addSwitch("s%s" %s)
	    self.sw_obj.append(sw)

        host_obj = []
	for h in hosts:
            host = self.addHost("h%s" %h)
	    host_obj.append(host)
        # Wire up switches       
        for link in links:
            self.addLink(self.sw_obj[link.keys()[0][0]-1], self.sw_obj[link.keys()[0][1]-1] , link.values()[0][0], link.values()[0][1])
        
        # Wire up hosts
        for link in links_sw_host:
            self.addLink(host_obj[link.keys()[0][0]-1], self.sw_obj[link.keys()[0][1]-1] , link.values()[0][0], link.values()[0][1])

        
class LisaMininet ( Mininet ):

    def build( self ):
        super( LisaMininet, self ).build()


def LisaTopoTest( controller_ip, controller_port,  controller_num ):
    topo = LisaTopo()

    #  main_controller = lambda a: RemoteController( a, ip=controller_ip, port=controller_port)
    
    net = LisaMininet( topo=topo, switch=OVSKernelSwitch, controller=None)
    controller_list = []
    for i in range(controller_num):
        name = "c%s" %i
        c = net.addController(name, controller=RemoteController,port=controller_port+i)
        controller_list.append(c)

    for s in topo.sw_obj:
        s = net.getNodeByName(s)
        s.start(controller_list)
    
    net.start()

        
    CLI( net )
    net.stop()

if __name__ == '__main__':
    if getuid()!=0:
        print "Please run this script as root / use sudo."
        exit(-1)

    lg.setLogLevel( 'info')
    description = "Put Lisa backbone in Mininet"
    parser = ArgumentParser(description=description)
    parser.add_argument("-c", dest="controller_name",
                      default="localhost",
                      help="Controller's hostname or IP")
    parser.add_argument("-p", dest="controller_port",type=int,
                      default=6633,
                      help="Controller's port")
    parser.add_argument("-num", dest="controller_number",type=int,
                      default=2,
                      help="the number of the controller")
    args = parser.parse_args()
    print description
    print "Starting with primary controller %s:%d" % (args.controller_name, args.controller_port)
    # print "Starting with dummy controller %s:%d" % (args.dummy_controller_name, args.dummy_controller_port)
    print "starting %s controllers in this network" %args.controller_number
    Mininet.init()
    LisaTopoTest(gethostbyname(args.controller_name), args.controller_port, args.controller_number)

topos = { 'mininetbuilder': ( lambda: LisaTopo() ) }
