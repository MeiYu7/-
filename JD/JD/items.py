# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item,Field
from scrapy.loader.processors import Compose,MapCompose,TakeFirst,Identity

from JD.loaders.processors import *

class GoodsItem(Item):
    goods_url = Field()
    goods_id = Field(input_processor = MapCompose(parse_goods_id))
    goods_name = Field(input_processor = MapCompose(deal_goods_name))
    goods_brand = Field()
    goods_details = Field(input_process=MapCompose(deal_goods_details))
    goods_specs = Field()
    goods_price = Field()
    update_time = Field()
    history_price = Field()

class GoodsPriceItem(Item):
    last_price = Field()
    last_time = Field()



class ErrorItem(Item):
    """出现异常的spider数据"""
    collection = 'exception_spider'
    title = Field()
    url = Field()
    type = Field()
    content = Field()
    time = Field()