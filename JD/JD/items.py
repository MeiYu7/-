# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item,Field
from scrapy.loader.processors import Compose,MapCompose,TakeFirst,Identity

from JD.loaders.processors import *

class GoodsItem(Item):
    collection_exception = 'exception_field'
    goods_url = Field()
    goods_id = Field(input_processor = MapCompose(parse_goods_id))
    goods_name = Field(input_processor = MapCompose(deal_goods_name))
    goods_brand = Field()
    goods_details = Field(input_processor=Compose(deal_goods_details))
    goods_specs = Field()
    goods_price = Field(input_processor=MapCompose(deal_goods_price))
    update_time = Field()
    history_prices = Field(input_processor=Compose(add_list_value))
    goods_cate_id = Field()
    goods_code = Field()
    error = Field()  # 异常

class GoodsPriceItem(Item):
    last_price = Field(input_processor=MapCompose(deal_goods_price))
    last_time = Field()



class ErrorItem(Item):
    """出现异常的spider数据"""
    collection = 'exception_spider'
    title = Field()
    url = Field()
    type = Field()
    content = Field()
    time = Field()


class StatsItem(Item):
    """数据收集"""
    collection = 'scrapy_stats'

    start_time = Field()
    finish_time = Field()
    finish_reason = Field()
    item_scraped_count = Field()
    response_received_count = Field()
    item_dropped_count = Field()
    item_dropped_reasons_count = Field()
    finaly_insert_item = Field()
    finaly_find_ids = Field()
    time_secodes_consum = Field()