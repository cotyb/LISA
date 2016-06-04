# Copyright (C) 2015 
# Author: aquatoney @ Xi'an Jiaotong University

"""
Definition of general instructions in LISA
"""
from itertools import *

from networks import *

class Scope:
  scope_dict = {}

  def __init__(self, names, scopes):
    """
    Initialize a scope
    """
    assert len(names) == len(scopes)
    self.scope_dict = {}
    for i, n in enumerate(names):
      self.scope_dict[n] = scopes[i]

  def __eq__(self, rhs):
    return self.scope_dict == rhs.scope_dict

  def produce_scope(self):
    return Scope(self.scope_dict.keys(), self.scope_dict.values())

  def dump(self):
    for k in self.scope_dict.keys():
      print k, 
      self.scope_dict[k].dump()

  def get_attr(self, name):
    return self.scope_dict[name]

  def overlaps(self, rhs):
    assert len(self.scope_dict) == len(rhs.scope_dict)
    assert self.scope_dict.keys() == rhs.scope_dict.keys()
    for key in self.scope_dict.keys():
      self_value = self.scope_dict[key]
      rhs_value = rhs.scope_dict[key]
      if not self_value.overlaps(rhs_value):
        # print 'not conflicting'
        return False
    return True

  def includes(self, rhs, exception = []):
    assert len(self.scope_dict) == len(rhs.scope_dict)
    assert self.scope_dict.keys() == rhs.scope_dict.keys()
    for key in self.scope_dict.keys():
      if key in exception: continue
      self_value = self.scope_dict[key]
      rhs_value = rhs.scope_dict[key]
      if not self_value.includes(rhs_value):
        # print 'not including'
        return False
    return True

  def decouples_scope(self, rhs, depth=0):
    assert len(self.scope_dict) == len(rhs.scope_dict)
    assert self.scope_dict.keys() == rhs.scope_dict.keys()

    conflicting_scope = []
    for i in range(depth, len(self.scope_dict)):
      key = self.scope_dict.keys()[i]
      if self.scope_dict[key].overlaps(rhs.scope_dict[key]):
        # print 'overlapped in %s (%sth level)' % (key, str(depth))
        new_items = self.scope_dict[key].decouples(rhs.scope_dict[key])
        # the intersected part needs further check
        if not new_items[2].empty():
          new_scope_self = self.produce_scope()
          new_scope_self.scope_dict[key] = new_items[2]
          new_scope_rhs = rhs.produce_scope()
          new_scope_rhs.scope_dict[key] = new_items[2]
          # print 'ready to go next level (current %s, next %s)' % (str(depth), str(depth+1))
          # print 'self scope',
          # new_scope_self.dump()
          # print 'rhs scope',
          # new_scope_rhs.dump()
          # print ''
          if depth+1 == len(rhs.scope_dict):
            # print 'this is the final conflicting scope'
            conflicting_scope = new_scope_self
          else:
            conflicting_scope = new_scope_self.decouples_scope(new_scope_rhs, depth+1)

        break

    # conflicting_scope.dump()
    return conflicting_scope


class Annotation:
  """
  Define the specific values in DOF with annotations. 
  """
  anno = []

  def __init__(self, a):
    self.anno = a

  def __eq__(self, rhs):
    return self.anno == rhs.anno

  def sort(self):
    self.anno.sort(key = lambda a: a[0])

  def intersects(self, rhs):
    assert isinstance(rhs, Annotation)
    # self.anno.extend(rhs.anno)
    self.adds(rhs)

  def adds(self, rhs):
    for a in rhs.anno: 
      if a not in self.anno:
        self.anno.append(a)
    # if rhs not in self.anno: self.anno.extend(rhs)

  def remove(self, a):
    if a in self.anno: self.anno.remove(a)

  def dump(self):
    for a in self.anno:
      print a, 
    print ''


class Constraint:
  """
  Define the requirements (actions) on the scopes.
  """
  action_dict = {}

  def __init__(self, names, actions):
    assert len(names) == len(actions)
    self.action_dict = {}
    for i, n in enumerate(names):
      self.action_dict[n] = actions[i]

  def __eq__(self, rhs):
    assert isinstance(rhs, Constraint)
    return self.action_dict == rhs.action_dict

  def dump(self):
    for k in self.action_dict.keys():
      print k, self.action_dict[k]
      # print self.action_dict[k]
      # self.action_dict[k].dump()
    # print ''

  def get_attr(self, name):
    return self.action_dict[name]


class Instruction:
  """
  Define an instruction with scope, annotation and constraint.
  """
  scope = ''
  constraint = ''
  annotation = ''
  priority = 0
  default = False

  def __init__(self, s, c, a, p=0):
    self.scope = s
    self.constraint = c
    self.annotation = a
    self.priority = p
    self.default = False

  def __eq__(self, rhs):
    return self.scope == rhs.scope and self.constraint == rhs.constraint and self.priority == rhs.priority

  def dump(self):
    self.scope.dump()
    self.constraint.dump()
    self.annotation.dump()
    print 'priority:', self.priority

  def set_default(self, d):
    self.default = d

  def is_default(self):
    return True if self.default else False

  def conflicts(self, rhs):
    # a conflict happens
    if self.constraint != rhs.constraint and \
       self.scope.overlaps(rhs.scope) and \
       self.priority == rhs.priority:
      return True
    return False

  def decouples(self, rhs):
    assert self.conflicts(rhs)
    conflicting_scope = self.scope.decouples_scope(rhs.scope)
    inst_1 = Instruction(conflicting_scope, self.constraint, self.annotation, self.priority+1)
    inst_2 = Instruction(conflicting_scope, rhs.constraint, rhs.annotation, rhs.priority+1)
    return inst_1, inst_2

inst_sets = []
switch_set_map = {}

def sort_inst_sets():
  # inst_sets.sort(reverse = True, key = lambda inst: inst.priority)
  pass


class InstSet:
  """
  Define a set of instructions
  """
  insts = []
  priority = 0

  def __init__(self, i, p):
    self.insts = i
    self.priority = p

  def check_integrity(self):
    scope = self.insts[0].scope
    for i in self.insts:
      assert scope == i.scope

  def size(self):
    return len(self.insts)

  def dump(self):
    for i in self.insts:
      i.dump()

  def get_scope(self):
    return self.insts[0].scope

  def sort(self):
    self.insts.sort(key = lambda inst: inst.scope)

  def assign_action(self, name, action):
    for inst in self.insts:
      inst.constraint.action_dict[name] = action

  def assign_dofs(self, dofs):
    for inst in self.insts:
      inst.annotation.anno = dofs

  def eliminates(self, extra_dof = None):
    flag = True
    for inst in self.insts: 
      if inst != self.insts[0]:
        flag = False
    if flag: return True

    art_sw = switches[self.get_scope().get_attr('switch').items]
    connected_sw = art_sw.get_connected_sw()
    # print 'art_sw', art_sw.sid
    # art_sw.dump()

    # print 'art_insts'
    # for inst in self.insts:
    #   inst.dump()
    # print 'end'

    art_dof = Annotation([])
    for a in [inst.annotation for inst in self.insts]:
      art_dof.intersects(a)
    if extra_dof != None: art_dof.intersects(extra_dof)

    # print 'art_dof'
    # print art_dof.anno
    # print 'end'
    dof_map = {}
    for d, k in groupby(art_dof.anno, lambda a: a[0]):
      if d not in dof_map.keys(): dof_map[d] = []
      dof_map[d].extend(list(k))

    # print 'dof_dump'
    # for i in dof_map.items():
    #   print i[0], i[1]
    # print 'end'

    if 'FORBID' in dof_map.keys():
      for forbid in dof_map['FORBID']:
        # print forbid
        # forbid_port = (forbid[1], art_sw.sid)
        # print forbid_port
        # print connected_sw
        for c in connected_sw:
          if forbid[1] == c[1]: connected_sw.remove(c)
        # if forbid_port in connected_sw: connected_sw.remove(forbid_port)

    if 'FORWARD' in dof_map.keys():
      # print dof_map['FORWARD']
      for forward in dof_map['FORWARD']:
        fwd_port = (forward[1], art_sw.sid)
        if Port(fwd_port[0], fwd_port[1]) in edge_ports: 
          return True
        elif fwd_port in connected_sw: 
          connected_sw = [fwd_port]
        else: 
          return False

    final_result = False
    if 'TOWARDS' in dof_map.keys():
      for towards in dof_map['TOWARDS']:
        if final_result: break
        for sw in connected_sw:
          # print 'current connected'
          # print connected_sw
          if final_result: break
          pid = sw[0]
          sid = sw[1]
          candidate_inst_sets = switch_set_map[sid]
          # check the inst set from high priority ones to lower
          for inst_set in candidate_inst_sets:
            if inst_set.get_scope().includes(self.get_scope(), exception = 'switch'):
              next_dof = Annotation(dof_map['FORBID']+dof_map['TOWARDS'])
              next_dof.remove(('TOWARDS', pid))
              final_result = inst_set.eliminates(next_dof)
              if final_result:
                self.assign_action('fwd_port', pid)
                new_dofs = []
                for dof in dof_map.values(): new_dofs += dof
                self.assign_dofs(new_dofs)
                # self.insts[0].annotation.dump()

    if ('TOWARDS' not in dof_map.keys() or len(dof_map['TOWARDS']) == 0) and \
       not final_result and len(connected_sw) != 0:
      final_result = True
      self.assign_action('fwd_port', connected_sw[0][0])
      self.assign_dofs(dof_map['FORBID']+dof_map['TOWARDS'])

    return final_result