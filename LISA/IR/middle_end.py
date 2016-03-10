#coding=utf-8

from itertools import *

from inst import *
from networks import *
from lisa_types import *


names = ['switch', 'dst_ip']
dst_ip = RangeItem(1000, 1000)

sw_1 = DotItem(1)
# src_ip1 = RangeItem(500, 2000)
# dst_ip1 = RangeItem(1000, 1000)
# vlan1 = SetItem([1, 2, 3])
# port1 = DotItem(80)

sw_2 = DotItem(2)
# src_ip2 = RangeItem(1000, 3000)
# dst_ip2 = RangeItem(1000, 1000)
# vlan2 = SetItem([1, 2, 4])
# port2 = DotItem(80)

sw_3 = DotItem(3)
sw_4 = DotItem(4)

c_1 = Constraint(['fwd_port'], [1])
c_2 = Constraint(['fwd_port'], [2])
c_3 = Constraint(['fwd_port'], [3])

a_1 = Annotation([('FORBID', 1),('TOWARDS', 2)])
a_2 = Annotation([('FORBID', 2),('TOWARDS', 4)])
a_3 = Annotation([('FORBID', 4),('FORWARD', 2)])

a_4 = Annotation([('FORBID', 1),('TOWARDS', 3)])
a_5 = Annotation([('FORBID', 3),('TOWARDS', 4)])
a_6 = Annotation([('FORBID', 4),('FORWARD', 2)])


print '################scope overlapping test################'
scope1 = Scope(names, [sw_1, dst_ip])
scope2 = Scope(names, [sw_2, dst_ip])
scope3 = Scope(names, [sw_3, dst_ip])
scope4 = Scope(names, [sw_4, dst_ip])
# scope1.dump()
# scope2.dump()
if scope1.overlaps(scope2):
  conflicting_scope = scope1.decouples_scope(scope2)
  conflicting_scope.dump()

print '################instruction conflicting test################'
# A DstIP 10.0.0.2 FORWARD 2
inst_1 = Instruction(scope1, c_2, a_1)
# B DstIP 10.0.0.2 FORWARD 3
inst_2 = Instruction(scope2, c_3, a_2)
# D DstIP 10.0.0.2 FORWARD 2
inst_3 = Instruction(scope4, c_2, a_3)
# A DstIP 10.0.0.2 FORWARD 3
inst_4 = Instruction(scope1, c_3, a_4)
# C DstIP 10.0.0.2 FORWARD 2
inst_5 = Instruction(scope3, c_2, a_5)
# D DstIP 10.0.0.2 FORWARD 2
inst_6 = Instruction(scope4, c_2, a_6)


if inst_1.conflicts(inst_2):
  n_1, n_2 = inst_1.decouples(inst_2)
  n_1.dump()
  n_2.dump()

print '################instruction decouple test################'
raw_inst = [inst_1, inst_2, inst_3, inst_4, inst_5, inst_6]
priority_dict = {0: raw_inst}
art_pri = 0
while True:
  if art_pri not in priority_dict.keys():
    print 'no such inst set with priority %s' % str(art_pri)
    break
  else:
    for t in combinations(priority_dict[art_pri], 2):
      if t[0].conflicts(t[1]) and t[0].scope != t[1].scope:
        n_1, n_2 = t[0].decouples(t[1])
        if art_pri+1 not in priority_dict.keys(): priority_dict[art_pri+1] = []
        priority_dict[art_pri+1].extend([n_1, n_2])
  art_pri += 1

# NOTE: need to sort the inst in the dict to use the groupby function
for k in priority_dict.keys():
  priority_dict[k].sort(key = lambda inst: inst.scope.get_attr('switch').items)

  print k,
  for inst in priority_dict[k]:
    inst.dump()

print '################instruction set test################'

inst_sets = []
for p in priority_dict.keys():
  art_insts = priority_dict[p]
  for i, k in groupby(art_insts, lambda inst: inst.scope):
    art_set = InstSet(list(k), p)
    inst_sets.append(art_set)
    
    print 'the %s insts with the following scope:' % len(art_set.insts)
    i.dump()
    print 'insts:'
    for n in art_set.insts:
      n.dump()
    print 'end'

for sid, inst_set in groupby(inst_sets, lambda set: set.get_scope().get_attr('switch').items):
  if sid not in switch_set_map.keys(): switch_set_map[sid] = []
  switch_set_map[sid].extend(inst_set)

for sets in switch_set_map.values():
  sets.sort(reverse = True, key = lambda s: s.priority)



print '################topology test################'
s_a = Switch(1, 3)
s_b = Switch(2, 3)
s_c = Switch(3, 3)
s_d = Switch(4, 3)

for s in [s_a, s_b, s_c, s_d]:
  switches[s.sid] = s

# assume double link graph
add_double_link(s_a.ports[2], s_b.ports[1])
add_double_link(s_a.ports[3], s_c.ports[1])
add_double_link(s_b.ports[2], s_c.ports[3])
add_double_link(s_b.ports[3], s_d.ports[1])
add_double_link(s_c.ports[2], s_d.ports[3])

# edge ports
add_edge_ports(s_a.ports[1])
add_edge_ports(s_d.ports[2])

for s in switches.values():
  s.dump()

print '################elimination test################'

for set in inst_sets:
  print set.size()
  if set.size() > 1:
    print 'ready to eliminate'
    if set.eliminates():
      print 'successful elimination'
    else:
      print 'cannot eliminated'

for set in inst_sets:
  inst = set.insts[0]
  inst.dump()



