# Copyright (C) 2015 
# Author: aquatoney @ Xi'an Jiaotong University

"""
Definition of types in LISA

This model defines the common types in LISA as well as their operations.
"""

from interval import Interval, IntervalSet

from util.utils import *

class RangeItem:
  items = IntervalSet.empty()

  def __init__(self, low, high):
    """
    Initialize a range item with lower bound and higher bound.
    """
    self.items = IntervalSet([Interval(low, high)])

  def __eq__(self, rhs):
    """
    Redefine == operator
    """
    assert isinstance(rhs, RangeItem)
    return self.items == rhs.items

  def empty(self):
    if len(self.items) == 0:
      return True
    return False

  def dump(self, type='ip'):
    if self.empty():
      print 'Empty RangeItem'
    else:
      if type == 'int':
        print 'RangeItem %s - %s' % (self.items.lower_bound(), self.items.upper_bound())
      elif type == 'ip':
        print 'RangeItem %s - %s' % (long2ip(self.items.lower_bound()), long2ip(self.items.upper_bound()))


  def produce(self):
    return RangeItem(self.items.lower_bound(), self.items.upper_bound())

  def overlaps(self, rhs):
    """
    If this item is overlapped with the other
    """
    if len(self.items & rhs.items) != 0:
      return True
    return False

  def includes(self, rhs):
    """
    If this item includes the other
    """
    if self.items & rhs.items == rhs.items:
      return True
    return False

  def decouples(self, rhs):
    """
    Decouple this item with the other
    """
    assert isinstance(rhs, RangeItem)
    # print self.items, rhs.items
    new_values = [self.items - rhs.items, rhs.items - self.items, self.items & rhs.items] 
    new_items = []
    for value in new_values:
      # print value
      # print '%s - %s' % str(value.lower_bound()), str(value.upper_bound)
      if len(value) != 0:
        new_items.append(RangeItem(value.lower_bound(), value.upper_bound()))
      else:
        empty_range = RangeItem(0, 0)
        empty_range.items = IntervalSet.empty()
        new_items.append(empty_range)
    return new_items

class SetItem:
  items = []

  def __init__(self, li):
    """
    Initialize a set item with a set of items
    """
    self.items = set(li)

  def __eq__(self, rhs):
    """
    Redefine == operator
    """
    assert isinstance(rhs, SetItem)
    return self.items == rhs.items

  def empty(self):
    if len(self.items) == 0:
      return True
    return False

  def dump(self):
    for i in self.items:
      print i,
    print ''

  def produce(self):
    return SetItem(self.items)

  def overlaps(self, rhs):
    """
    If this item is overlapped with the other
    """
    if len(self.items & rhs.items) != 0:
      return True
    return False

  def includes(self):
    """
    If this item includes the other
    """
    if self.items & rhs.items == rhs.items:
      return True
    return False

  def decouples(self, rhs):
    """
    Decouple this item with the other
    """
    assert isinstance(rhs, SetItem)
    new_values = [(self.items - rhs.items), (rhs.items - self.items), self.items & rhs.items] 
    new_items = []
    for value in new_values:
      new_items.append(SetItem(value))
    return new_items
    # return (self.items - rhs.items), (rhs.items - self.items), self.items & rhs.items

class DotItem:
  items = -1

  def __init__(self, dot):
    """
    Initialize a dot item with a specific value
    """
    self.items = dot

  def __eq__(self, rhs):
    """
    Redefine == operator
    """
    assert isinstance(rhs, DotItem)
    return self.items == rhs.items

  def empty(self):
    if self.items == -1:
      return True
    return False

  def dump(self):
    print self.items

  def produce(self):
    return DotItem(self.items)

  def overlaps(self, rhs):
    """
    If this item is overlapped with the other
    """
    if self.items == rhs.items:
      return True
    return False

  def includes(self, rhs):
    if self.items == rhs.items: return True
    return False

  def decouples(self, rhs):
    """
    Decouple this item with the other
    """
    assert isinstance(rhs, DotItem)
    empty_dot = DotItem(-1)
    return [empty_dot, empty_dot, self]
