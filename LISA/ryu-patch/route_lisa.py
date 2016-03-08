#!/usr/bin/python
# coding:utf-8

__author__ = 'cotyb'

import logging
import struct
from operator import attrgetter
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp

import random

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link

import network_aware
import network_monitor


class Shortest_Route(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        "Network_Aware": network_aware.Network_Aware,
        "Network_Monitor": network_monitor.Network_Monitor,
    }

    def __init__(self, *args, **kwargs):
        super(Shortest_Route, self).__init__(*args, **kwargs)
        self.network_aware = kwargs["Network_Aware"]
        self.network_monitor = kwargs["Network_Monitor"]
        self.mac_to_port = {}
        self.datapaths = {}
	
	self.test_count = 0
	#self.f = open("result1.txt","w")
	#self.f.truncate()
	#self.f.close()

        #switches: [dpid,dpid...]
        self.total_switches = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,1000,1001,1002,1003,1004,1005,1006,1007,1008,1009]
        # links   :(src_dpid,dst_dpid)->(src_port,dst_port)
        self.link_to_port = self.network_aware.link_to_port
	print self.link_to_port
        # {sw :[host1_ip,host2_ip,host3_ip,host4_ip]}
        self.access_table = self.network_aware.access_table

        # dpid->port_num (ports without link)
        self.access_ports = self.network_aware.access_ports
        self.graph = self.network_aware.graph
        #to avoid the loop after adding critical nodes and links
        self.lisa_graph = self.graph




    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def add_flow(self, dp, p, match, actions, idle_timeout=0, hard_timeout=0):
        ofproto = dp.ofproto
        parser = dp.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=dp, priority=p,
                                idle_timeout=idle_timeout,
                                hard_timeout=hard_timeout,
                                match=match, instructions=inst)
        dp.send_msg(mod)

    def install_flow(self, path, flow_info, buffer_id, data):
        '''
            path=[dpid1, dpid2, dpid3...]
            flow_info=(eth_type, src_ip, dst_ip, in_port)
        '''
        # first flow entry
        in_port = flow_info[3]
        assert path
        datapath_first = self.datapaths[path[0]]
        ofproto = datapath_first.ofproto
        parser = datapath_first.ofproto_parser
        out_port = ofproto.OFPP_LOCAL

        # inter_link
        if len(path) > 2:
            for i in xrange(1, len(path) - 1):
                port = self.get_link2port(path[i - 1], path[i])
                port_next = self.get_link2port(path[i], path[i + 1])
                if port:
                    src_port, dst_port = port[1], port_next[0]
                    datapath = self.datapaths[path[i]]
                    ofproto = datapath.ofproto
                    parser = datapath.ofproto_parser
                    actions = []

                    actions.append(parser.OFPActionOutput(dst_port))
                    match = parser.OFPMatch(
                        in_port=src_port,
                        eth_type=flow_info[0],
                        ipv4_src=flow_info[1],
                        ipv4_dst=flow_info[2])
                    self.add_flow(
                        datapath, 1, match, actions,
                        idle_timeout=10, hard_timeout=30)

                    # inter links pkt_out
                    msg_data = None
                    if buffer_id == ofproto.OFP_NO_BUFFER:
                        msg_data = data

                    out = parser.OFPPacketOut(
                        datapath=datapath, buffer_id=buffer_id,
                        data=msg_data, in_port=src_port, actions=actions)

                    datapath.send_msg(out)

        if len(path) > 1:
            # the  first flow entry
            port_pair = self.get_link2port(path[0], path[1])
            out_port = port_pair[0]

            actions = []
            actions.append(parser.OFPActionOutput(out_port))
            match = parser.OFPMatch(
                in_port=in_port,
                eth_type=flow_info[0],
                ipv4_src=flow_info[1],
                ipv4_dst=flow_info[2])
            self.add_flow(datapath_first,
                          1, match, actions, idle_timeout=10, hard_timeout=30)

            # the last hop: tor -> host
            datapath = self.datapaths[path[-1]]
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            actions = []
            src_port = self.get_link2port(path[-2], path[-1])[1]
            dst_port = None

            for key in self.access_table.keys():
                if flow_info[2] == self.access_table[key]:
                    dst_port = key[1]
                    break
            actions.append(parser.OFPActionOutput(dst_port))
            match = parser.OFPMatch(
                in_port=src_port,
                eth_type=flow_info[0],
                ipv4_src=flow_info[1],
                ipv4_dst=flow_info[2])

            self.add_flow(
                datapath, 1, match, actions, idle_timeout=10, hard_timeout=30)

            # first pkt_out
            actions = []

            actions.append(parser.OFPActionOutput(out_port))
            msg_data = None
            if buffer_id == ofproto.OFP_NO_BUFFER:
                msg_data = data

            out = parser.OFPPacketOut(
                datapath=datapath_first, buffer_id=buffer_id,
                data=msg_data, in_port=in_port, actions=actions)

            datapath_first.send_msg(out)

            # last pkt_out
            actions = []
            actions.append(parser.OFPActionOutput(dst_port))
            msg_data = None
            if buffer_id == ofproto.OFP_NO_BUFFER:
                msg_data = data

            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=buffer_id,
                data=msg_data, in_port=src_port, actions=actions)

            datapath.send_msg(out)

        else:  # src and dst on the same
            out_port = None
            actions = []
            for key in self.access_table.keys():
                if flow_info[2] == self.access_table[key]:
                    out_port = key[1]
                    break

            actions.append(parser.OFPActionOutput(out_port))
            match = parser.OFPMatch(
                in_port=in_port,
                eth_type=flow_info[0],
                ipv4_src=flow_info[1],
                ipv4_dst=flow_info[2])
            self.add_flow(
                datapath_first, 1, match, actions,
                idle_timeout=10, hard_timeout=30)

            # pkt_out
            msg_data = None
            if buffer_id == ofproto.OFP_NO_BUFFER:
                msg_data = data

            out = parser.OFPPacketOut(
                datapath=datapath_first, buffer_id=buffer_id,
                data=msg_data, in_port=in_port, actions=actions)

            datapath_first.send_msg(out)


    '''
    the functions for lisa
    '''
    # get the full permutation of the lists 
    # get the full permutation of the critical nodes and get the best path
    def perm(self,Perm_list):
    	if (len(Perm_list)<=1):
    		return [Perm_list]
    	result = []
    	for i in range(len(Perm_list)):
    		s= Perm_list[:i]+Perm_list[i+1:]
    		p = self.perm(s)
    		for x in p:
    			result.append(Perm_list[i:i+1]+x)
    	return result

    # get the shortest route of the critical nodes respectively
    def possible_path_route(self,possible_path,cri_nodes,src_sw,dst_sw):
        '''
        first, get the distance from every critical node to the others
        distance_table store the distance of every two critical nodes
        '''
        distance_table = {}    #{cri_node1:{cri_node2:dis1,cir_node3:dis2,...cri_noden:disn}}
        path_table = {}
        inter_nodes_path = []
        for critical_node in cri_nodes:
        	result = self.dijkstra(self.graph,critical_node)
        	path_table[critical_node] = result[1][critical_node]
        	distance_table[critical_node] = result[0]
        # store the information of src_sw and dst_sw	
        src_sw_result = self.dijkstra(self.graph,src_sw)
        path_table[src_sw] = src_sw_result[1][src_sw]
        distance_table[src_sw] = src_sw_result[0]
        dst_sw_result = self.dijkstra(self.graph,dst_sw)
        path_table[dst_sw] = dst_sw_result[1][dst_sw]
        distance_table[dst_sw] = dst_sw_result[0]

    	for critical_nodes_path in possible_path:
    		path_distance = 0
    		path_route = []
    		for dummy_id in range(len(critical_nodes_path)-1):
    			path_distance = path_distance + distance_table[critical_nodes_path[dummy_id]][critical_nodes_path[dummy_id+1]]
    			path_route = path_route + path_table[critical_nodes_path[dummy_id]][critical_nodes_path[dummy_id+1]]
    			path_route.insert(0,critical_nodes_path[0])
    		path_route_backup = path_route
    		path_route = path_table[src_sw][path_route[0]] + path_route[1:] + path_table[path_route[-1]][dst_sw]
    		path_distance = path_distance + distance_table[src_sw][path_route_backup[0]] + distance_table[path_route_backup[-1]][dst_sw]
    		path_route.append(path_distance)
    		path_route.insert(0,src_sw)
    		inter_nodes_path.append(path_route)
        return inter_nodes_path

    def End_to_end_connectivity(self,srcip,dstip):
    	switch_dof = {}
        distance_table = {}
    	src_location = self.get_host_location(srcip)
    	dst_location = self.get_host_location(dstip)

    	if src_location:
    		src_sw = src_location[0]
    	if dst_location:
    		dst_sw = dst_location[0]

    	result = self.dijkstra(self.graph,src_sw)
        distance_table[src_sw] = result[0]
    	if result:
    		path = result[1][src_sw][dst_sw]
    		path.insert(0,src_sw)
    		lisa_path = path
        full_path = path
        total_distance = distance_table[src_sw][dst_sw]
    	for dummy_id in range(len(lisa_path)):
    		if dummy_id == 0 or dummy_id == len(lisa_path)-1:
    			switch_dof[lisa_path[dummy_id]] = "FIXED_FORWARD"
    		else:
    			switch_dof[lisa_path[dummy_id]] = "TOWARDS " + str(lisa_path[-1])

    	print switch_dof
    	return switch_dof


    def Passing_critical_node(self,srcip,dstip,critical_nodes,critical_links):
    	switch_dof = {}
    	cri_nodes = critical_nodes
    	src_location = self.get_host_location(srcip)
    	dst_location = self.get_host_location(dstip)

    	if src_location:
    		src_sw = src_location[0]
    	if dst_location:
    		dst_sw = dst_location[0]

    	if src_sw in cri_nodes:
    		cri_nodes.remove(src_sw)
    	if dst_sw in cri_nodes:
    		cri_nodes.remove(dst_sw)
    	if len(cri_nodes) < 1:
    		self.End_to_end_connectivity((self,srcip,dstip,cri_nodes,critical_links))

        distance_table = {}    #{cri_node1:{cri_node2:dis1,cir_node3:dis2,...cri_noden:disn}}
        path_table = {}        #{sw1:{sw2:[node,node]},sw2:{}}
        for critical_node in cri_nodes:
            result = self.dijkstra(self.graph,critical_node)
            path_table[critical_node] = result[1][critical_node]
            distance_table[critical_node] = result[0]
        # store the information of src_sw and dst_sw    
        src_sw_result = self.dijkstra(self.graph,src_sw)
        path_table[src_sw] = src_sw_result[1][src_sw]
        distance_table[src_sw] = src_sw_result[0]
        dst_sw_result = self.dijkstra(self.graph,dst_sw)
        path_table[dst_sw] = dst_sw_result[1][dst_sw]
        distance_table[dst_sw] = dst_sw_result[0]

        cri_nodes.append(dst_sw)
        cri_nodes.insert(0,src_sw)
        total_distance = 0
        full_path = []
        for dummy_i in range(len(cri_nodes)-1):
            split_list = path_table[cri_nodes[dummy_i]][cri_nodes[dummy_i+1]]
            full_path = full_path + split_list
            split_list.insert(0,cri_nodes[dummy_i])
            for node in split_list:
                switch_dof[node] = "TOWARDS " + str(split_list[-1])
                switch_dof[split_list[-1]] = "FIXED_FORWARD"
            total_distance = total_distance + distance_table[cri_nodes[dummy_i]][cri_nodes[dummy_i+1]]
        full_path.insert(0,src_sw)
        print switch_dof
        print "total distance is " ,total_distance 
        return switch_dof



        '''
        the critical nodes is unordered, and find the shortest route
        '''
        '''
    	possible_inter_path = self.perm(cri_nodes)
    	all_possible_route = self.possible_path_route(possible_inter_path, cri_nodes, src_sw, dst_sw)
    	#print all_possible_route
    	shortest_route = [100000]
    	for full_route in all_possible_route:
    		if shortest_route[-1] > full_route[-1]:
    			shortest_route = full_route
    	#shortest route store the path and the shortest distance, like [path, distance]
    	full_path = shortest_route[:-1]
    	# switch_dof[src_sw] = "FIXED_FORWARD"
    	# switch_dof[dst_sw] = "FIXED_FORWARD"
    	# cri_node_path = full_path[1:-1]
    	index_of_cri_node = []
    	for node in full_path:
    		if node in cri_nodes:
    			index_of_cri_node.append(full_path.index(node))
    	index_of_cri_node.insert(0,0)
    	#index_of_cri_node.insert(-1,len(full_path)-1)

    	for dummy in range(len(index_of_cri_node)-1):
    		split_list = full_path[index_of_cri_node[dummy]+1:index_of_cri_node[dummy+1]+1]
    		print split_list
    		switch_dof[split_list[-1]] = "FIXED_FORWARD"
    		for dummy_id in range(len(split_list)-1):
    			switch_dof[split_list[dummy_id]] = "TOWARDS " + str(split_list[-1])
    	for node in full_path[index_of_cri_node[-1]+1:]:
    		switch_dof[node] = "TOWARDS " + str(full_path[-1])
    	switch_dof[src_sw] = "FIXED_FORWARD"
    	switch_dof[dst_sw] = "FIXED_FORWARD"

        print switch_dof
        '''

        

    def Traveling_critical_link(self,srcip,dstip,critical_nodes,critical_links):
        #critical_links:[(sw,port),(sw,port)]
        #store 
        switch_dof = {}
        src_location = self.get_host_location(srcip)
        dst_location = self.get_host_location(dstip)

        if src_location:
            src_sw = src_location[0]
        if dst_location:
            dst_sw = dst_location[0]

        switches = []
        ports = []
        cri_links = critical_links
        for node in cri_links:
            switches.append(node[0])
            ports.append(node[1])
        sw_link_ports = (ports[0],ports[1])
        if self.link_to_port[(switches[0],switches[1])] != sw_link_ports:
            self.logger.info("These two switches are not connected by these two ports")
        else:    
            distance_table = {}    #{cri_node1:{cri_node2:dis1,cir_node3:dis2,...cri_noden:disn}}
            path_table = {}        #{sw1:{sw2:[node,node]},sw2:{}}
            for critical_node in switches:
                result = self.dijkstra(self.graph,critical_node)
                path_table[critical_node] = result[1][critical_node]
                distance_table[critical_node] = result[0]
            # store the information of src_sw and dst_sw    
            src_sw_result = self.dijkstra(self.graph,src_sw)
            path_table[src_sw] = src_sw_result[1][src_sw]
            distance_table[src_sw] = src_sw_result[0]
            dst_sw_result = self.dijkstra(self.graph,dst_sw)
            path_table[dst_sw] = dst_sw_result[1][dst_sw]
            distance_table[dst_sw] = dst_sw_result[0]
            distance_a = distance_table[src_sw][switches[0]]
            path_a = path_table[src_sw][switches[0]]
            path_a.insert(0,src_sw)
            for node in path_a:
                switch_dof[node] = "TOWARDS " + str(path_a[-1])
            switch_dof[path_a[-1]] = "FIXED_FORWARD " + str(switches[1])
            distance_b = distance_table[switches[1]][dst_sw]
            path_b = path_table[switches[1]][dst_sw]
            path_b.insert(0,switches[1])
            for node in path_b:
                switch_dof[node] = "TOWARDS " + str(dst_sw)
            switch_dof[dst_sw] = "FIXED_FORWARD"
            full_path = path_a + path_b
            total_distance = distance_a + distance_b + distance_table[switches[0]][switches[1]]
            print "total_distance is ", total_distance
            print switch_dof
            return switch_dof



    def Dropping_and_rewriting(self,srcip,dstip,critical_nodes,critical_links):
        '''
        critical nodes is the dropping node
        '''
        switch_dof = {}
        drop_node = critical_nodes[0]
        distance_table = {}    #{cri_node1:{cri_node2:dis1,cir_node3:dis2,...cri_noden:disn}}
        path_table = {} 

    	src_location = self.get_host_location(srcip)
        dst_location = self.get_host_location(dstip)

        if src_location:
            src_sw = src_location[0]
        if dst_location:
            dst_sw = dst_location[0]

        src_sw_result = self.dijkstra(self.graph,src_sw)
        path_table[src_sw] = src_sw_result[1][src_sw]
        distance_table[src_sw] = src_sw_result[0]
        full_path = path_table[src_sw][drop_node]
        full_path.insert(0,src_sw)
        total_distance = distance_table[src_sw][drop_node]
        for node in full_path:
            switch_dof[node] = "TOWARDS" + str(drop_node)
        switch_dof[drop_node] = "FIXED_FORWARD " + "nowhere"
        print "total distance is " , total_distance
        print switch_dof
        return switch_dof



    # def route_lisa(self,srcip,dstip,critical_nodes,critical_links,drop_nodes):
    #     #self.route_lisa(ip_src,ip_dst,[1,3],[[(3,1),(4,3)],[(2,3),(3,2)]],[2,3])
    #     '''
    #     MODE={'S1': self.End_to_end_connectivity,
	   #    	'S2': self.Passing_critical_node,
	   #    	'S3': self.Traveling_critical_link,
	   #   	'S4': self.Dropping_and_rewriting}
    #     MODE.get(mode)(srcip,dstip,critical_nodes,critical_links)
    #     '''
    #     switch_dof = {}        #final result:{sw1:tag, sw2:tag... swn:tag}
    #     distance_table = {}    #{cri_node1:{cri_node2:dis1,cir_node3:dis2,...cri_noden:disn}}
    #     path_table = {}        #{cri_node1:{cri_node2:path1,cir_node3:path2,...cri_noden:pathn}}
    #     full_path = []         #the path to install flow
    #     total_distance = 0     #the total distance of full_path
    #     src_location = self.get_host_location(srcip)
    #     dst_location = self.get_host_location(dstip)

    #     if src_location:
    #         src_sw = src_location[0]
    #     if dst_location:
    #         dst_sw = dst_location[0]

    #     src_sw_result = self.dijkstra(self.graph,src_sw)
    #     path_table[src_sw] = src_sw_result[1][src_sw]
    #     distance_table[src_sw] = src_sw_result[0]
    #     dst_sw_result = self.dijkstra(self.graph,dst_sw)
    #     path_table[dst_sw] = dst_sw_result[1][dst_sw]
    #     distance_table[dst_sw] = dst_sw_result[0]

    #     #if the critical nodes, critical links and drop nodes are all None, handle with end to end
    #     if critical_nodes is None and critical_links is None and drop_nodes is None:
    #         self.logger.info("end to end")
    #         full_path = path_table[src_sw][dst_sw]
    #         full_path.insert(0, src_sw)
    #         total_distance = distance_table[src_sw][dst_sw]
    #         for node in full_path:
    #             switch_dof[node] = "TOWARDS " + str(dst_sw)
    #         switch_dof[dst_sw] = "FIXED_FORWARD" + str(dstip)
    #         print switch_dof
    #         print "total distance is %s \n" %total_distance

    #     elif critical_nodes and critical_links is None and drop_nodes is None:
    #         self.logger.info("only critical_nodes")
    #         switch_dof = self.Passing_critical_node(srcip,dstip,critical_nodes,None,None)

    #     elif critical_nodes is None and critical_links and drop_nodes is None:
    #         self.logger.info("only critical links")
    #         switches = []
    #         for link in critical_links:
    #             dummy_switches = []
    #             dummy_ports = []
    #             for sw_port in link:
    #                 dummy_switches.append(sw_port[0])
    #                 switches.append(sw_port[0])
    #                 dummy_ports.append(sw_port[1])
    #             if self.link_to_port[(dummy_switches[0],dummy_switches[1])] != (dummy_ports[0],dummy_ports[1]):
    #                 self.logger.info("%s are not connected by %s") % (dummy_switches, dummy_ports)
    #             else:
    #                 switch_dof = self.Passing_critical_node(srcip,dstip,switches,None,None)
    #                 for node in switches:




    # return switch_dof
    def route_lisa(self,srcip,dstip,information):
        '''
        the content of information:
        it's a list
        it has following element:
        {1:dpid}   critical_nodes
        {2:[(sw,port),(sw,port)]}   critical_links
        {3:dpid}   drop_nodes
        '''
        switch_dof = {}        #final result:{sw1:tag, sw2:tag... swn:tag}
        distance_table = {}    #{cri_node1:{cri_node2:dis1,cir_node3:dis2,...cri_noden:disn}}
        path_table = {}        #{cri_node1:{cri_node2:path1,cir_node3:path2,...cri_noden:pathn}}
        full_path = []         #the path to install flow
        total_distance = 0     #the total distance of full_path
        src_location = self.get_host_location(srcip)
        dst_location = self.get_host_location(dstip)
		

        if src_location:
            src_sw = src_location[0]
        if dst_location:
            dst_sw = dst_location[0]

        all_switches = []
        switches_in_links = []
        drop_switches = []
	if information != None:
            for element in information:
                if element.has_key(1):
                    all_switches.append(element[1])
                elif element.has_key(2):
                    links = element[2]
                    dummy_ports = []
                    dummy_switches = []
                    for sw_port in links:
                        dummy_switches.append(sw_port[0])
                        #all_switches.append(sw_port[0])
                        #switches_in_links.append(sw_port[0])
                        dummy_ports.append(sw_port[1])
                    if self.link_to_port[(dummy_switches[0],dummy_switches[1])] != (dummy_ports[0],dummy_ports[1]):
                        self.logger.info("%s are not connected by %s") % (dummy_switches, dummy_ports)
                    else:
                        for switch in dummy_switches:
                            all_switches.append(switch)
                            switches_in_links.append(switch)
                elif element.has_key(3):
                    all_switches.append(element[3])
                    drop_switches.append(element[3])

        all_switches.append(dst_sw)
        all_switches.insert(0,src_sw)

        if src_sw == dst_sw:
            for switch in all_switches:
                if src_sw != switch:
                    self.logger.info("it'a a loop")
                    break
                else:
                    continue
        # for switch in all_switches:
         #    result = self.dijkstra(self.graph,switch)
	    # if result:
         #        path_table[switch] = result[1][switch]
         #        distance_table[switch] = result[0]

        for dummy_i in range(len(all_switches)-1):
            result = self.dijkstra(self.lisa_graph,all_switches[dummy_i])          
            if result:
		#distance = result[0][all_switches[dummy_i]][all_switches[dummy_i+1]]
                split_list = result[1][all_switches[dummy_i]][all_switches[dummy_i+1]]
            full_path = full_path + split_list
            split_list.insert(0,all_switches[dummy_i])
            for switch in split_list:
                switch_dof[switch] = "TOWARDS " + str(split_list[-1])
            split_list_temp = split_list[:-1]
            for switch in split_list_temp:
                for each_switch in all_switches:
                    if each_switch != switch:
                        self.lisa_graph[switch][each_switch] = float('inf')
                        self.lisa_graph[each_switch][switch] = float('inf')




            #total_distance = total_distance + distance
        full_path.insert(0,src_sw)
        for switch in switches_in_links:
            if switches_in_links.index(switch) %2 == 0:
                switch_dof[switch] = "FIXED_FORWARD " + str(switches_in_links[switches_in_links.index(switch)+1])
        for switch in drop_switches:
            switch_dof[switch] = "FIXED_FORWARD " + "nowhere"
        switch_dof[dst_sw] = "FIXED_FORWARD " + str(dstip)

        print switch_dof
        #print total_distance
        return switch_dof, full_path











    def get_host_location(self, host_ip):
        for key in self.access_table:
            if self.access_table[key] == host_ip:
                return key
        self.logger.debug("%s location is not found." % host_ip)
        return None

    def get_path(self, graph, src):
        result = self.dijkstra(graph, src)
        if result:
            path = result[1]
            return path
        self.logger.debug("Path is not found.")
        return None

    def get_link2port(self, src_dpid, dst_dpid):
        if (src_dpid, dst_dpid) in self.link_to_port:
            return self.link_to_port[(src_dpid, dst_dpid)]
        else:
            self.logger.debug("Link to port is not found.")
            return None

    def dijkstra(self, graph, src):
        if graph is None:
            self.logger.debug("Graph is empty.")
            return None
        length = len(graph)
        type_ = type(graph)

        # Initiation
        if type_ == list:
            nodes = [i for i in xrange(length)]
        elif type_ == dict:
            nodes = graph.keys()
        visited = [src]
        path = {src: {src: []}}
        if src not in nodes:
            self.logger.info("Src is not in nodes.")
            return None
        else:
            nodes.remove(src)
        distance_graph = {src: 0}
        pre = next = src
        no_link_value = 100000

        while nodes:
            distance = no_link_value
            for v in visited:
                for d in nodes:
                    new_dist = graph[src][v] + graph[v][d]
                    if new_dist <= distance:
                        distance = new_dist
                        next = d
                        pre = v
                        graph[src][d] = new_dist

            if distance < no_link_value:
                path[src][next] = [i for i in path[src][pre]]
                path[src][next].append(next)
                distance_graph[next] = distance
                visited.append(next)
                nodes.remove(next)
            else:
                self.logger.info("Next node is not found.")
                return None

        return distance_graph, path

    '''
    In packet_in handler, we need to learn access_table by ARP.
    Therefore, the first packet from UNKOWN host MUST be ARP.
    '''

    def generate_cri_node(self,num):
	if num == 0:
	    return []
	else:
	    information = []
	    switches = []
	    i = 0
	    while i < num:
		index = random.randrange(0,26)
		if self.total_switches[index] not in switches:
		    switches.append(self.total_switches[index])
		    information.append({1:self.total_switches[index]})
		    i += 1
		else:
		    index = random.randrange(0,26)
	return information

    def generate_cri_link(self,num):
	information = []
	if num == 0:
	    return []
	else:
	    num_link = len(self.link_to_port)
	    index = random.randrange(0,num_link)	
	    key_need = self.link_to_port.keys()[index]
	    #print key_need
	    #print self.link_to_port
	    for key in self.link_to_port:
		#print key, value
		if key == key_need:
		    tmp = [(key[0],self.link_to_port[key][0]),(key[1],self.link_to_port[key][1])] 
		    information.append({2:tmp})
    		    break
	    print information
	    return information

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
	#print "packet in"
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)

        eth_type = pkt.get_protocols(ethernet.ethernet)[0].ethertype
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        if isinstance(arp_pkt, arp.arp):
            arp_src_ip = arp_pkt.src_ip
            arp_dst_ip = arp_pkt.dst_ip

            result = self.get_host_location(arp_dst_ip)
            if result:  # host record in access table.
                datapath_dst, out_port = result[0], result[1]
                actions = [parser.OFPActionOutput(out_port)]
                datapath = self.datapaths[datapath_dst]

                out = parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=ofproto.OFP_NO_BUFFER,
                    in_port=ofproto.OFPP_CONTROLLER,
                    actions=actions, data=msg.data)
                datapath.send_msg(out)
            else:       # access info is not existed. send to all host.
                for dpid in self.access_ports:
                    for port in self.access_ports[dpid]:
                        if (dpid, port) not in self.access_table.keys():
                            actions = [parser.OFPActionOutput(port)]
                            datapath = self.datapaths[dpid]
                            out = parser.OFPPacketOut(
                                datapath=datapath,
                                buffer_id=ofproto.OFP_NO_BUFFER,
                                in_port=ofproto.OFPP_CONTROLLER,
                                actions=actions, data=msg.data)
                            datapath.send_msg(out)

        if isinstance(ip_pkt, ipv4.ipv4):
            ip_src = ip_pkt.src
            ip_dst = ip_pkt.dst
			
	    #self.route_lisa(ip_src,ip_dst,[{1:6}])

            result = None
            src_sw = None
            dst_sw = None

            src_location = self.get_host_location(ip_src)
            dst_location = self.get_host_location(ip_dst)

            if src_location:
                src_sw = src_location[0]

            if dst_location:
                dst_sw = dst_location[0]
            result = self.dijkstra(self.graph, src_sw)
	    #print "-----------------result---------------"
	    #print result	
	    #print "------------------graph-----------------"
	    #print self.graph
	    information = []
	    #generate cri nodes and cri links 
	    cri_node_num = random.randrange(0,4)
	    cri_link_num = random.randrange(0,2)
	    information1 = self.generate_cri_node(cri_node_num)
	    information2 = self.generate_cri_link(cri_link_num)
	    if information2 != []:
	        realnum_of_cri_node = len(information1)
		if realnum_of_cri_node != 0:
	            index_of_link = random.randrange(0,realnum_of_cri_node)
	    	    information1.insert(index_of_link, information2[0])
		else:
		    information1 = information2
	    information = information1
	    print "----------------------information---------------------------"
	    print information
	    
            if result:
                path = result[1][src_sw][dst_sw]
                path.insert(0, src_sw)
                switch_dof, full_path = self.route_lisa(ip_src,ip_dst,information)
		#to identify if there are loop, if yes, drop
		full_path_set = set(full_path)
		dof = []
		flag = 1
		if len(full_path_set) == len(full_path):
		#get the port of path[0->-2]
		    for i in xrange(len(full_path)-1):
			switch_array = []			
			if self.get_link2port(full_path[i],full_path[i+1]) != None:
			    switch_array.append(full_path[i])
			    switch_array.append(self.get_link2port(full_path[i],full_path[i+1])[0])
			    switch_array.append(switch_dof[full_path[i]])
			    dof.append(switch_array)
			else:
			    flag = 0
			    break
		    if flag == 1:
			#get the port of path[-1]
		        switch_array = []
		        dst_port = None
		        for key in self.access_table.keys():
	                    if ip_dst == self.access_table[key]:
			        dst_port = key[1]
			        break
		        switch_array.append(full_path[-1])
		        switch_array.append(dst_port)
		        switch_array.append(switch_dof[full_path[-1]])		    
		        dof.append(switch_array)
		        self.f = open("result1.txt","a")
		        print >> self.f,ip_src,",",ip_dst,",",src_sw,",",dst_sw,",",dof
		        self.f.close()
		        self.test_count += 1
		    print "--------------------------------------test count-----------------------------"
		    print self.test_count	
		self.logger.info("the distance is %d" %result[0][dst_sw])
                self.logger.info(
                    " PATH[%s --> %s]:%s\n" % (ip_src, ip_dst, path))
                self.logger.info("LISA_PATH[%s --> %s]:%s\n" % (ip_src, ip_dst, full_path))


                flow_info = (eth_type, ip_src, ip_dst, in_port)
                #self.install_flow(full_path, flow_info, msg.buffer_id, msg.data)
            else:
                # Reflesh the topology database.
                self.network_aware.get_topology(None)
