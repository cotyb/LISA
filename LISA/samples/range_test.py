from interval import Interval, IntervalSet

r1 = IntervalSet([Interval(1, 1000), Interval(1100, 1200)])
r2 = IntervalSet([Interval(30, 50), Interval(60, 200), Interval(1150, 1300)])

r3 = IntervalSet([Interval(1000, 3000)])
r4 = IntervalSet([Interval(1000, 3000)])
r5 = IntervalSet([Interval(30000, 12000)])

# print (r3 - r4), (r4 - r3), r3 & r4
# print len(IntervalSet.empty())

if r3 & r4 == r4:
	print 'yes'

# print r3 & r4
# if (r3 - r4).is_empty():
#   print "true"
# print (r3 - r4).empty()