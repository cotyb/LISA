fp = open("s1_flow","r")
fw = open("agg_result/s1_flow","w")
rules = fp.readlines()
result = {}
for rule in rules:
    rule = eval(rule)
    if not result.has_key((rule["dst_ip"], rule["actions"])):
        result[(rule["dst_ip"], rule["actions"])] = [rule["src_ip"]]
    else:
        result[(rule["dst_ip"], rule["actions"])].append(rule["src_ip"])
for ele in result:
    result[ele]  = list(set(result[ele]))
    print >> fw, "\"src_ip\":%s, \"dst_ip\":%s, \"actions\":%s" %(sorted(result[ele]), ele[0], ele[1])