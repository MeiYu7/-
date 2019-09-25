from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose,MapCompose,TakeFirst,Identity

from .processors import *


class GoodsItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class GoodsPriceItemLoader(ItemLoader):
    default_output_processor = TakeFirst()
