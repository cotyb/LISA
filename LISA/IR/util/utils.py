#coding=utf-8

import socket, struct

def ip2long(ip):
  """
  Convert an IP string to long
  """
  packedIP = socket.inet_aton(ip)
  return struct.unpack("!L", packedIP)[0]

def long2ip(long):
  func = lambda x: '.'.join([str(x/(256**i)%256) for i in range(3,-1,-1)])
  return func(long)