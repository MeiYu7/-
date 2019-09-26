import re


def parse_goods_id(value):
    return value.split("/")[-1].split(".")[0]


def deal_goods_name(value):
    return re.sub("【|图片|价格|品牌|报价|】|-|京东","",value).strip()


def deal_goods_details(value):
    # print("<---value--->",value)
    value_new = []
    value_new.append(value)
    return value_new

def deal_goods_price(value):
    try:
        value = float(value)
    except:
        value = value
    return value

add_list_value = lambda x:[x]