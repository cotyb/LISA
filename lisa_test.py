#!/usr/bin/env python
#coding = utf-8

import random
import logging
import copy
import time

__author__ = "cotyb"

'''
test lisa with multiple count
'''


class Lisa_Tester():

    def __init__(self):
        num_edge_sw = 16
        self.edge_sw = [x for x in range(1,17)]
        num_agg_sw = 10
        self.agg_sw = [1000, 1001, 1003, 1006, 1007]
        self.all_sw = self.edge_sw + self.agg_sw
        self.sw_hosts = {}
        self.sw_flows = {}
        self.sw_count = {}
        self.sw_statistic = {}
        self.move = 1
        #self.logger = logging.getLogger()

    def distribute_host(self):
        '''
        generate the hosts for every sw, 16 hosts per sw
        :return:noting
        '''
        for switch in self.edge_sw:
            #self.sw_hosts[switch] = ["10.0.0.%s-%s" %((switch-1)*16, switch*16-1)]
            self.sw_hosts[switch] = [((switch-1)*16, switch*16-1)]


    def generate_flows(self):
        '''
        generate the flows for every sw,
        according all path, make all path reasonable
        :return: noting
        '''
        path_file = open("result","r")
        paths = path_file.readlines()
        for path in paths:
            path = eval(path)
            path = path["path"]
            src_ip = self.sw_hosts[path[0]]
            dst_ip = "10.0.0.%s" %((path[-1]-1)*16)
            for sw in path:
                tmp = {}
                tmp["src_ip"] = src_ip
                tmp["dst_ip"] = dst_ip
                tmp["path"] = path
                if not self.sw_flows.has_key(sw):
                    #self.sw_flows[sw] = ["{\"src_ip\":%s, \"dst_ip\":%s, \"path\": %s}" %(src_ip, dst_ip, path)]
                    self.sw_flows[sw] = [tmp]
                else:
                    #self.sw_flows[sw].append("{\"src_ip\":%s, \"dst_ip\":%s, \"path\": %s}" %(src_ip, dst_ip, path))
                    self.sw_flows[sw].append(tmp)


    def write_flows2file(self):
        '''
        write flows to file in flows folder
        s1_flow to s16_flow and s1000_flow to s1009_flow store their flows
        all_flows store all flows
        :return: noting
        '''
        all_flow_file_name = "flows/all_flows"
        all_flow = open("flows/all_flows","w")
        for sw in range(1,17):
            file_name = "flows/s%s_flow" %sw
            with open(file_name,"w") as fp:
                print >> fp, self.sw_flows[sw]
                print >> all_flow, str(sw) + "\n"
                print >> all_flow, self.sw_flows[sw]

        for sw in range(1000,1010):
            if self.sw_flows.has_key(sw):
                file_name = "flows/s%s_flow" %sw
                with open(file_name,"w") as fp:
                    print >> all_flow, str(sw) + "\n"
                    print >> all_flow, self.sw_flows[sw]
                    print >> fp, self.sw_flows[sw]


    def generate_count(self, count_num):
        '''
        all are random
        the result stores in self.sw_count
        self.sw_count: a dict, {sw: [src_ip, path]}the key is sw, and the value is the rules about\
        the count install in sw
        :param count_num: the total number to distribute to 26 switches
        :return: noting
        '''
        for num in range(count_num):
            sw_index = random.randrange(0, 21)
            sw = self.all_sw[sw_index]
            count_nth_rule = random.randrange(0,len(self.sw_flows[sw]))
            src_ip_range = self.sw_flows[sw][count_nth_rule]["src_ip"][0]
            lower = random.randrange(0,src_ip_range[0] + 1)
            upper = random.randrange(src_ip_range[1], 256)
            lower_ip = "10.0.0.%s" %lower
            upper_ip = "10.0.0.%s" %upper

            if not self.sw_count.has_key(sw):
                self.sw_count[sw] = [[True, lower, upper, self.sw_flows[sw][count_nth_rule]["path"]]]
            else:
                self.sw_count[sw].append([True, lower, upper, self.sw_flows[sw][count_nth_rule]["path"]])

    def statistics(self, sw_count):
        '''
        statistics the changes of rules, including:
        total_rules: total num of rules from every sw
        self.sw_statistic: the total num of rules and addition rules of every sw
        self.sw_statistic: {sw:[before num of rules, after num of rules]}
        :return:noting
        '''
        for sw in self.all_sw:
            tmp_forward_flows = []
            for rule in self.sw_flows[sw]:
                tmp_forward_flows.append(rule["src_ip"][0])
            num_original_forward_rule = len(tmp_forward_flows)
            if not sw_count.has_key(sw):
                continue
            count_flow = [(rule[1], rule[2]) for rule in sw_count[sw]]
                #print count_flow
            for count_rule in count_flow:
                tmp_add_flow = []
                for forward_rule in tmp_forward_flows:
                    if count_rule[0] > forward_rule[1]:
                        continue
                    elif count_rule[1] < forward_rule[0]:
                        continue
                    elif count_rule[1] <= forward_rule[1]:
                        tmp_add_flow.append((count_rule[1], forward_rule[0]))
                    else:
                        tmp_add_flow.append((forward_rule[0], count_rule[1]))
                tmp_forward_flows += tmp_add_flow
            self.sw_statistic[sw] = (num_original_forward_rule, len(tmp_forward_flows))


    def compute_total_rules(self):
        '''
        compute the total rules of every situation
        :return: a list [before change total, after change total]
        '''
        result = [0, 0]
        for i in self.sw_statistic:
            result[0] += self.sw_statistic[i][0]
            result[1] += self.sw_statistic[i][1]
        return result

    def core_algorithm(self, count_number):
        '''
        the core algorithm
        change the count function along the path
        find the least num of rules
        :param count_number:the count number
        :return: before_num, min_num_total_rules
        '''
        before_num = self.compute_total_rules()[1]
        print "before move, the total rules in all switches are %s" %before_num
        #add a flag for self.sw_count, true stand for it can be moved, false for cannot
        handle_sw_count = copy.deepcopy(self.sw_count)
        # for sw in handle_sw_count:
        #     for rule in handle_sw_count[sw]:
        #         rule.insert(0, True)
        #tmp_sw_count = handle_sw_count
        for sw in self.all_sw:
            #print handle_sw_count
            tmp_sw_count = copy.deepcopy(handle_sw_count)
            min_num_total_rules = before_num
            if not tmp_sw_count.has_key(sw):
                continue
            count_rules = tmp_sw_count[sw]
            for count_rule in count_rules:
                if count_rule[0]:
                    reside_sw = sw
                    for along_sw in count_rule[3]:
                        if not tmp_sw_count.has_key(along_sw):
                            continue
                        tmp_sw_count[along_sw].append(count_rule)
                        tmp_sw_count[sw].remove(count_rule)
                        self.statistics(tmp_sw_count)
                        tmp_sw_count[along_sw].remove(count_rule)
                        tmp_sw_count[sw].append(count_rule)
                        tmp_num_rules = self.compute_total_rules()[1]
                        #print tmp_num_rules, min_num_total_rules
                        if tmp_num_rules < min_num_total_rules:
                            min_num_total_rules = tmp_num_rules
                            reside_sw = along_sw
                    tmp_sw_count[sw].remove(count_rule)
                    tmp_sw_count[reside_sw].append(count_rule)
                    tmp_sw_count[reside_sw][-1][0] = False
                    print "after %s moves, the total rules in all switches are %s" %(self.move, min_num_total_rules)
                    handle_sw_count = tmp_sw_count
                    self.move += 1
        return before_num, min_num_total_rules


if __name__ == '__main__':
    wfile = open("statistics","a")
    #print >> wfile, "path   count   init_num    min_num steps   time"
    count = [50, 100, 150, 200]
    for count_number in count:
        lisa_tester = Lisa_Tester()
        lisa_tester.distribute_host()
        lisa_tester.generate_flows()
        lisa_tester.write_flows2file()
        lisa_tester.generate_count(count_number)
        lisa_tester.statistics(lisa_tester.sw_count)
        st = time.time()
        init_num, min_num = lisa_tester.core_algorithm(count_number)
        st1 = time.time()
        steps = lisa_tester.move
        print >> wfile, 240, count_number, init_num, min_num, steps, st1-st

