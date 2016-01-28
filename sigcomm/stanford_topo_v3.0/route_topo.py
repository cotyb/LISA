#!/usr/bin/python
# program
#     creeate a topo for qiao
# histoty
# 2015-4-15    ZhengPeng    first release
from argparse import ArgumentParser
from socket import gethostbyname
from os import getuid

from mininet.log import lg, info
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import Link, Intf
from mininet.node import Host, UserSwitch, Controller, RemoteController



class VdpSimpleTopo( Topo ):
    "Topology for VdpSimpleTopo, 7 switches and 2 hosts"
    SWITCH_ID_MULTIPLIER = 100000
    PORT_TYPE_MULTIPLIER = 10000

    DUMMY_SWITCH_BASE = 1000
    
    def __init__( self ): 
        # Read topology info
        ports = {1:set([1,2,3]), 2:set([1,2,3,4]), 3:set([1,2,3]), \
                 4:set([1,2,3,4]), 5:set([1,2,3,4,5]), 6:set([1,2,3]), 7:set([1,2,3])}
        links = set([(100002,300002),(100003,200003), (300001,400003),(200001,400002),\
                     (200002,500004),(400001,500001), (500003,600002),(500002,700003), (600001,700002)])
        switches = ports.keys()

        # Add default members to class.
        super( VdpSimpleTopo, self ).__init__()

        # Create switch nodes
        for s in switches:
            self.addSwitch( "s%s" % s )

        # Wire up switches       
        self.create_links(links, ports)
        
        print "\twire up hosts:"
        # Wire up hosts
        host_id = len(switches) + 1
        for s in switches:
            # Edge ports
            for port in ports[s]:
                self.addHost( "h%s" % host_id )
                self.addLink( "h%s" % host_id, "s%s" % s, 0, port )
                host_id += 1
                print port

        # Consider all switches and hosts 'on'
        # self.enable_all()
    def create_links(self, links, ports):  
        '''Generate dummy switches
           For example, interface A1 connects to B1 and C1 at the same time. Since
           Mininet uses veth, which supports point to point communication only,
           we need to manually create dummy switches

        @param links link info from the file
        @param ports port info from the file
        ''' 
        # First pass, find special ports with more than 1 peer port
        first_pass = {}
        for (src_port_flat, dst_port_flat) in links:
            src_dpid = src_port_flat / self.SWITCH_ID_MULTIPLIER
            dst_dpid = dst_port_flat / self.SWITCH_ID_MULTIPLIER
            src_port = src_port_flat % self.PORT_TYPE_MULTIPLIER
            dst_port = dst_port_flat % self.PORT_TYPE_MULTIPLIER
            
            if (src_dpid, src_port) not in first_pass.keys():
                first_pass[(src_dpid, src_port)] = set()
            first_pass[(src_dpid, src_port)].add((dst_dpid, dst_port))
            if (dst_dpid, dst_port) not in first_pass.keys():
                first_pass[(dst_dpid, dst_port)] = set()
            first_pass[(dst_dpid, dst_port)].add((src_dpid, src_port))
        print "\tfirst_pass=", len(first_pass.items())
        for it in first_pass.items():
            print it

        # Second pass, create new links for those special ports | WIRE up dummy switches links
        dummy_switch_id = self.DUMMY_SWITCH_BASE
        for (dpid, port) in first_pass.keys():
            # Special ports!
            if(len(first_pass[(dpid,port)])>1):
                self.addSwitch( "s%s" % dummy_switch_id )
                self.dummy_switches.add(dummy_switch_id)
                print "dummy_switches.add(%s)" %dummy_switch_id
            
                self.addLink( node1="s%s" % dpid, node2="s%s" % dummy_switch_id, port1=port, port2=1 )
                print "add_dummy_link(%s, %s)->(%s, 1)" %(dpid, port, dummy_switch_id)
                dummy_switch_port = 2
                for (dst_dpid, dst_port) in first_pass[(dpid,port)]:
                    first_pass[(dst_dpid, dst_port)].discard((dpid,port))
                    self.addLink( node1="s%s" % dummy_switch_id, node2="s%s" % dst_dpid, port1=dummy_switch_port, port2=dst_port)
                    ports[dst_dpid].discard(dst_port)   # ZP: WHY?
                    dummy_switch_port += 1
                dummy_switch_id += 1  
                first_pass[(dpid,port)] = set()    
            ports[dpid].discard(port)
        
        # Third pass, create the remaining links | wire up the remaining links
        for (dpid, port) in first_pass.keys():
            for (dst_dpid, dst_port) in first_pass[(dpid,port)]:
                self.addLink( node1="s%s" % dpid, node2="s%s" % dst_dpid, port1=port, port2=dst_port )
                ports[dst_dpid].discard(dst_port)     
            ports[dpid].discard(port)       

topos = { 'routetopo': ( lambda: VdpSimpleTopo() ) }
