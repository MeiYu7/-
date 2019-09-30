

def parse_goods_brands(arr):
    cate_list = []
    for cate1 in arr:
        for cate2 in cate1["cate1_lists"]:
            cate2_name = cate2["cate2"]
            for cate3 in cate2["cate2_lists"]:
                cate3_name = cate3["cate3"]
                for brand in cate3["brand_lists"]:
                    item = {}
                    item["goods_brand"] = brand["brand_name"]
                    item["goods_code"] = brand["code4"]
                    item["goods_cate"] = cate3_name
                    cate_list.append(item)

    return cate_list
