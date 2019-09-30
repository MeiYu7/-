import json
from pprint import pprint
import re
file = open("../order_list_new.json", "r", encoding="utf=8")
file_json = json.loads(file.read())
file.close()

# pprint(file_json)

new_file = []
i = 1
j = 1
o = 1
r = 1
for k,v in file_json.items():
    # i = 1
    item1 = {}
    item1["cate1"] = k
    item1["code1"] = i
    item1["cate1_lists"] = []
    new_file.append(item1)
    i += 1
    for m,n in v.items():
        # j = 1
        item2={}
        item2["cate2"] = m
        item2["code2"] = int(str(item1["code1"]) + ('%03d' % j))
        item2["cate2_lists"] = []
        item1["cate1_lists"].append(item2)
        j += 1

        for a,b in n.items():
            # o = 1
            item3 = {}
            item3["cate3"] = a
            item3["code3"] = int(str(item2["code2"]) + ('%03d' % o))
            item3["brand_lists"] = []
            item2["cate2_lists"].append(item3)
            o+=1

            for brand in b:
                # r = 1
                item4 = {}
                item4["brand_name"] = [re.sub(r'（|）',"", i) for i in  re.findall(r"(\w+|（.*）)",brand,re.S)]
                item4["code4"] = int(str(item3["code3"]) + ('%03d' % r))
                item3["brand_lists"].append(item4)
                r += 1
            else:
                r = 1
        else:
            o=1
    else:
        j = 1
else:
    i = 1



pprint(new_file)
















