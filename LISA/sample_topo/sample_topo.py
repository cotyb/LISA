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
from os import getuid

from mininet.log import lg, info, setLogLevel
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import Link, Intf
from mininet.node import Host, OVSKernelSwitch, Controller, RemoteController

class LisaTopo( Topo ):
    "Topology for LISA"

    def __init__( self ):
        #super(LisaTopo, self).__init__()
        Topo.__init__(self)

        # Set topology info
        hosts = [1, 2]
        switches = [1, 2, 3, 4]
        links = [{(1, 2):(2, 1)}, {(1, 3):(3, 1)}, {(2, 3):(2, 3)}, {(2, 4):(3, 1)}, {(3, 4):(2, 3)}]
        links_sw_host = [{(1, 1):(1, 1)}, {(2, 4):(1, 2)}]
		

        # Wire up switches       
        for link in links:
            s1 = self.addSwitch("s%s" % link.keys()[0][0])
	    s2 = self.addSwitch("s%s" % link.keys()[0][1])
            self.addLink(s1, s2 , link.values()[0][0], link.values()[0][1])
        
        # Wire up hosts
        for link in links_sw_host:
            h1 = self.addHost("h%s" % link.keys()[0][0])
	    s2 = self.addSwitch("s%s" % link.keys()[0][1])
            self.addLink(h1, s2 , link.values()[0][0], link.values()[0][1])

                
       
def LisaTopoTest():
    topo = LisaTopo()
    main_controller = lambda a:RemoteController(a, ip="localhost", port=6633)
    net = Mininet( topo=topo, switch=OVSKernelSwitch, controller=main_controller)
    
    
    net.start()
    
        
    CLI( net )
    net.stop()

if __name__ == '__main__':
    if getuid()!=0:
        print "Please run this script as root / use sudo."
        exit(-1)
    setLogLevel("info")

    LisaTopoTest()
    
