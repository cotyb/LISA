#coding = ""utf-8
import os
files = os.listdir("flows-h100-copy")
#result = os.mkdir("result")
print files
for file in files:
    #print type(file)
    fp = open("flows-h100-copy/" + file,"r")
    fw = open("result/" + file,"w")
    for flow in fp.readlines()[1:]:
        if flow.__contains__("4294967293"):
            continue
        try:
            flow = eval(flow)
        except:
            print file
            print flow
        if flow[0]["match"].has_key("nw_src"):
            print >> fw,"{\"src_ip\":\"%s\", \"dst_ip\":\"%s\", \"in_port\":\"%s\", \"actions\":\"%s\"}" %(flow[0]["match"]["nw_src"],\
                                            flow[0]["match"]["nw_dst"], flow[0]["match"]["in_port"], flow[0]["actions"])
    fp.close()
    fw.close()

