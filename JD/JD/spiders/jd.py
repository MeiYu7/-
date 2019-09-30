# -*- coding: utf-8 -*-
import re
import scrapy
import json
from selenium import webdriver
# from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from datetime import date, datetime
from JD.items import GoodsItem, GoodsPriceItem
from JD.loaders.loader import GoodsPriceItemLoader, GoodsItemLoader
from JD.utils.parse_keys import parse_goods_brands


class JdSpider(scrapy.Spider):
    name = 'jd'
    allowed_domains = ['jd.com', 'p.3.cn']
    # start_urls = ['http://list.jd.com/']
    sku_url_temp = "https://item.jd.com/{}.html"
    sku_price_temp = "https://p.3.cn/prices/mgets?skuIds=J_{}"
    search_url_temp = "https://search.jd.com/Search?keyword={}&enc=utf-81&page={}"
    item = {}
    item_num = 0
    data_num = 0
    ids_set = set()

    def __init__(self):
        # # spider启动信号和spider_opened函数绑定
        # dispatcher.connect(self.spider_opened, signals.spider_opened)
        # # spider关闭信号和spider_spider_closed函数绑定
        # dispatcher.connect(self.spider_closed, signals.spider_closed)
        # selenium模拟浏览器
        # Chrome浏览器
        options = webdriver.ChromeOptions()
        # 设置中文
        options.add_argument('lang=zh_CN.UTF-8')
        # 设置无图加载 1 允许所有图片; 2 阻止所有图片; 3 阻止第三方服务器图片
        prefs = {
            'profile.default_content_setting_values': {'images': 2}
        }
        options.add_experimental_option('prefs', prefs)
        # 设置无头浏览器
        options.add_argument('--headless')
        self.browser = webdriver.Chrome(chrome_options=options,
                                        executable_path="D:/chromedriver.exe")

    def spider_opened(self):
        print("爬虫开始咯....")
        self.start_time = datetime.now()

    def spider_closed(self):
        # print(self.item)
        # with open("./order_list_new.json","w",encoding="utf-8" ) as f:
        #     json.dump(self.item, f,ensure_ascii=False,indent = 4)
        print("最终采集ids", len(self.ids_set), "个")
        print("最终采集item", self.item_num, "个")
        print("最终解析data", self.data_num, "个")
        self.logger.info("最终采集ids{}个".format(len(self.ids_set)))
        self.logger.info("最终采集item{}个".format(self.item_num))
        self.logger.info("最终解析data{}个".format(self.data_num))
        self.browser.close()
        self.end_time = datetime.now()
        print("爬虫结束咯.....耗时:", (self.end_time - self.start_time))
        self.crawler.stats.set_value("finaly_find_ids", len(self.ids_set))
        self.crawler.stats.set_value("time_secodes_consum",(self.end_time - self.start_time).seconds)


    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        cls.from_settings(crawler.settings)
        spider = super(JdSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    @classmethod
    def from_settings(cls, settings):
        cls.mongo_db = settings.get("DB_MONGO")
        cls.cate_brand = settings.get("CATE_COLLECTION")

    def start_requests(self):
        cates = self.mongo_db[self.cate_brand].find()
        for i in parse_goods_brands(cates)[7:10]:
            brand_item = {}
            brand_item["goods_brand"] = i["goods_brand"]
            brand_item["goods_cate"] = i["goods_cate"]
            brand_item["goods_code"] = int(i["goods_code"])
            # self.word = "笔记本计算机 华为（HUAWEI）"
            self.word = brand_item["goods_cate"] + " " + " ".join(brand_item["goods_brand"])
            print(self.word)
            yield scrapy.Request(self.search_url_temp.format(self.word, 1), callback=self.parse,
                                 meta={"brand_item": brand_item}, dont_filter=True)

    def parse_selector(self, response):
        # 细分分类
        selector_list = response.xpath("//div[contains(@class,'J_selectorLine')]")
        for selector in selector_list:
            selector_name = selector.xpath("./@class").extract_first()
            if selector_name not in ("J_selectorLine s-brand", "J_selectorLine s-line s-senior"):
                a_list = selector.xpath(".//li/a")
                for a in a_list:
                    a_href = "https://search.jd.com/" + a.xpath("./@href").extract_first()
                    yield scrapy.Request(a_href, callback=self.parse_selector_url, meta={"brand_item": response.meta["brand_item"]},
                                         dont_filter=True)

        # 剩余页码数据
        for i in range(3, 201, 2):
            yield scrapy.Request(self.search_url_temp.format(self.word, 1), callback=self.parse,
                                 meta={"middleware": "SeleniumMiddleware", "brand_item": response.meta["brand_item"]})

    def parse_selector_url(self, response):
        selector_url_start = response.request.url
        selector_url_start = re.sub(r'#J_searchWrap', '', selector_url_start)

        try:
            total_page = int(response.xpath("//span[@class='fp-text']/i/text()").extract_first())
        except Exception as e:
            print("解析页码错误", e)
            total_page = 100
        for i in range(1, (2 * total_page + 1), 2):
            url = selector_url_start + '&page=' + str(i)
            yield scrapy.Request(url, callback=self.parse,
                                 meta={"middleware": "SeleniumMiddleware", "brand_item": response.meta["brand_item"]}, dont_filter=True)

    def parse(self, response):
        print("parse_url", response.request.url)
        li_list = response.xpath('//ul[@class="gl-warp clearfix"]/li')
        if len(li_list) > 0:
            for li in li_list:
                goods_id = li.xpath("./@data-sku").extract_first()
                # print(goods_id)
                yield scrapy.Request(self.sku_url_temp.format(goods_id), callback=self.parse_sku,meta={"brand_item": response.meta["brand_item"]}, dont_filter=True)

    def parse_sku(self, response):
        colorSize_str = re.findall(r"colorSize:(.*?}]),[ ]+?[warestatus:]+", response.body.decode(response.encoding))
        if len(colorSize_str) > 0:
            colorSize_list = json.loads(colorSize_str[0], strict=False)
            for sku in colorSize_list:
                item = {}
                goods_id = sku.pop("skuId")
                self.ids_set.add(goods_id)

                item["goods_specs"] = " ".join(sku.values())
                yield scrapy.Request(self.sku_url_temp.format(goods_id), callback=self.parse_data, meta={"item": item,"brand_item": response.meta["brand_item"]})

        else:
            self.ids_set.add(response.request.url.split("/")[-1].split(".")[0])
            item_1 = {}
            item_1["goods_specs"] = response.xpath(
                "//div[@class='sku-name']/text()").extract_first().strip() if response.xpath(
                "//div[@class='sku-name']/text()").extract_first() else response.xpath(
                "//div[@id='itemName']/text()").extract_first()
            yield scrapy.Request(response.request.url, callback=self.parse_data, meta={"item": item_1,"brand_item": response.meta["brand_item"]})

    def parse_data(self, response):
        self.data_num += 1
        item_loader = GoodsItemLoader(item=GoodsItem(), response=response)
        item_loader.add_value("goods_specs", response.meta["item"]["goods_specs"])
        item_loader.add_value("goods_code", response.meta["brand_item"]["goods_code"])
        item_loader.add_value("goods_url", response.request.url)
        item_loader.add_value("goods_id", response.request.url)
        item_loader.add_xpath("goods_name", "//ul[contains(@class,'parameter2')]/li[1]/@title")
        if not response.xpath("//ul[contains(@class,'parameter2')]/li[1]/@title").extract_first():
            item_loader.replace_xpath("goods_name", "//title/text()")
        item_loader.add_xpath("goods_brand", "//ul[@id='parameter-brand']/li/@title")
        item_loader.add_xpath("goods_details", "//ul[contains(@class,'parameter2')]/li//text()")
        item_loader.add_value("update_time", "")
        item = item_loader.load_item()
        yield scrapy.Request(self.sku_price_temp.format(item["goods_id"]), callback=self.parse_price,
                             meta={"item_loader": item})

    def parse_price(self, response):
        item_loader = response.meta["item_loader"]
        price_dict = json.loads(response.body)
        time_now =datetime.strftime(date.today(), '%Y-%m-%d')
        price_item = {}

        if len(price_dict) > 0:
            price_item_loader = GoodsPriceItemLoader(item=GoodsPriceItem())
            price_item_loader.add_value("last_price", price_dict[0]["p"])
            price_item_loader.add_value("last_time", time_now)
            price_item = price_item_loader.load_item()

        item_loader = GoodsItemLoader(item=item_loader)
        item_loader.replace_value("update_time", time_now)
        item_loader.add_value("history_prices", price_item)
        item_loader.add_value("goods_price", price_item["last_price"])
        item = item_loader.load_item()
        # print("===>", item)
        self.item_num += 1
        self.crawler.stats.inc_value("item_num")
        print("此时item{}个".format(self.item_num))
        print("此时解析data{}个".format(self.data_num))

        yield item
