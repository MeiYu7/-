# -*- coding: utf-8 -*-
import re
import scrapy
import json
from selenium import webdriver
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from pprint import pprint
import time
from datetime import date, datetime
from scrapy.loader.processors import Compose, MapCompose
from JD.items import GoodsItem,GoodsPriceItem
from JD.loaders.loader import GoodsPriceItemLoader, GoodsItemLoader
from JD.loaders.processors import parse_goods_id,deal_goods_name,deal_goods_details



class JdSpider(scrapy.Spider):
    name = 'jd'
    allowed_domains = ['jd.com', 'list.jd.com', 'item.jd.com', 'p.3.cn','search.jd.com']
    # start_urls = ['http://list.jd.com/']
    sku_url_temp = "https://item.jd.com/{}.html"
    sku_price_temp = "https://p.3.cn/prices/mgets?skuIds=J_{}"
    search_url_temp = "https://search.jd.com/Search?keyword={}&enc=utf-81&page={}"
    item = {}
    item_num = 0
    data_num = 0
    ids_set = set()

    def __init__(self):
        # spider启动信号和spider_opened函数绑定
        dispatcher.connect(self.spider_opened, signals.spider_opened)
        # spider关闭信号和spider_spider_closed函数绑定
        dispatcher.connect(self.spider_closed, signals.spider_closed)
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
                                        executable_path="C:/Users/myq91/Downloads/chromedriver.exe")

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
        self.browser.close()
        self.end_time = datetime.now()

        print("爬虫结束咯.....耗时:" ,(self.end_time-self.start_time))

    def start_requests(self):
        self.word = "笔记本计算机 联想（Lenovo）"
        yield scrapy.Request(self.search_url_temp.format(self.word, 1), callback=self.parse)

    def read_order_list(self, response):
        """
        read order_list
        :param response:
        :return:
        """
        search_url_temp = "https://search.jd.com/Search?keyword={}&enc=utf-81&page=1"
        with open("./order_list.json", "r", encoding="utf-8") as f:
            order_list_json = json.loads(f.read())
        print(order_list_json)
        for k, v in order_list_json.items():
            self.item[k] = v
            for i, j in v.items():
                self.item[k][i] = j
                for m, n in j.items():
                    self.item[k][i][m] = n
                    url = search_url_temp.format(m)
                    yield scrapy.Request(url, callback=self.search_brand, meta={"n_list": n})

    def search_brand(self, response):
        n_list = response.meta["n_list"]
        brand_list = response.xpath("//ul[@class='J_valueList v-fixed']/li/a")
        for brand in brand_list[:15]:
            n_list.append(brand.xpath("./@title").extract_first())

    def parse_selector(self, response):
        # 细分分类
        print("请求细分初始url",response.request.url)
        selector_list = response.xpath("//div[contains(@class,'J_selectorLine')]")
        for selector in selector_list:
            selector_name = selector.xpath("./@class").extract_first()
            if selector_name not in ("J_selectorLine s-brand", "J_selectorLine s-line s-senior"):
                a_list = selector.xpath(".//li/a")
                for a in a_list:
                    a_href = "https://search.jd.com/" + a.xpath("./@href").extract_first()
                    yield scrapy.Request(a_href, callback=self.parse_selector_url,dont_filter=True)

        # 剩余页码数据
        for i in range(3, 201, 2):
            print("剩余页码正在请求{}页".format(i))
            yield scrapy.Request(self.search_url_temp.format(self.word, 1), callback=self.parse,meta={"middleware": "SeleniumMiddleware"})

    def parse_selector_url(self, response):
        selector_url_start = response.request.url
        selector_url_start = re.sub(r'#J_searchWrap', '', selector_url_start)

        try:
            total_page = int(response.xpath("//span[@class='fp-text']/i/text()").extract_first())
        except Exception as e:
            print("解析页码错误", e)
            total_page = 100
        print("细分分类里一共页码",total_page)
        for i in range(1, (2*total_page + 1), 2):
            url = selector_url_start + '&page=' + str(i)
            print("请求细分分类：", url)
            yield scrapy.Request(url, callback=self.parse,meta={"middleware": "SeleniumMiddleware"}, dont_filter=True)


    def parse(self, response):
        print("parse_url",response.request.url)
        li_list = response.xpath('//ul[@class="gl-warp clearfix"]/li')
        print("--->", len(li_list))

        if len(li_list) > 0:
            for li in li_list:
                goods_id = li.xpath("./@data-sku").extract_first()
                # print(goods_id)
                yield scrapy.Request(self.sku_url_temp.format(goods_id), callback=self.parse_sku,dont_filter=True)

    def parse_sku(self, response):
        """
        attr_list = response.xpath("//div[@id='choose-attrs']/div")[:-1]
        for attr in attr_list:
            sku_list = attr.xpath("./div[@class='dd']/div[contains(@class,'item')]")
            for sku in sku_list:
                item = {}
                data_sku = sku.xpath("./@data-sku").extract_first()
                item["goods_specs"] = sku.xpath("./@data-value").extract_first()
                yield scrapy.Request(self.sku_url_temp.format(data_sku), callback=self.parse_data, meta={"item":item})
        """
        print("parse_sku_url", response.request.url)
        colorSize_str = re.findall(r"colorSize:(.*?}]),[ ]+?", response.body.decode(response.encoding))
        if len(colorSize_str) > 0:
            try:
                colorSize_list = json.loads(colorSize_str[0],strict=False)
                for sku in colorSize_list:
                    item = {}
                    goods_id = sku.pop("skuId")
                    print(goods_id)
                    self.ids_set.add(goods_id)
                    item["goods_specs"] = " ".join(sku.values())
                    yield scrapy.Request(self.sku_url_temp.format(goods_id), callback=self.parse_data, meta={"item": item})
            except json.decoder.JSONDecodeError:
                print("*********")
                print(colorSize_str)
                print("*********")
        else:
            self.ids_set.add(response.request.url.split("/")[-1].split(".")[0])
            item_1 = {}
            item_1["goods_specs"] = response.xpath(
                "//div[@class='sku-name']/text()").extract_first().strip() if response.xpath(
                "//div[@class='sku-name']/text()").extract_first() else response.xpath(
                "//div[@id='itemName']/text()").extract_first()
            yield scrapy.Request(response.request.url, callback=self.parse_data, meta={"item": item_1})

    def parse_data(self, response):
        print("parse_date_url", response.request.url)
        self.data_num+=1
        item_loader = GoodsItemLoader(item=GoodsItem(),response=response, spider=self)
        # item = response.meta["item"]
        item_loader.add_value("goods_specs",response.meta["item"]["goods_specs"])
        item_loader.add_value("goods_url", response.request.url)
        item_loader.add_value("goods_id", response.request.url)
        item_loader.add_xpath("goods_name", "//ul[contains(@class,'parameter2')]/li[1]/@title")
        if not response.xpath("//ul[contains(@class,'parameter2')]/li[1]/@title").extract_first():
            item_loader.replace_xpath("goods_name", "//title/text()")
        item_loader.add_xpath("goods_brand", "//ul[@id='parameter-brand']/li/@title")
        item_loader.add_xpath("goods_details","//ul[contains(@class,'parameter2')]/li/text()")
        item_loader.add_value("history_price", [])
        item_loader.add_value("update_time", "")


        # item["goods_url"] = response.request.url
        # item["goods_id"] = response.request.url.split("/")[-1].split(".")[0]
        # item["goods_name"] = response.xpath(
        #     "//ul[contains(@class,'parameter2')]/li[1]/@title").extract_first() if response.xpath(
        #     "//ul[contains(@class,'parameter2')]/li[1]/@title").extract_first() else response.xpath(
        #     "//title/text()").extract_first()
        # item["goods_brand"] = response.xpath("//ul[@id='parameter-brand']/li/@title").extract_first() if response.xpath(
        #     "//ul[@id='parameter-brand']/li/@title").extract_first() else item["goods_name"]
        # item["goods_details"] = []
        # item["history_prices"] = []
        # item["goods_details"] = [li.xpath("./text()").extract_first() for li in
        #                          response.xpath("//ul[contains(@class,'parameter2')]/li")]

        # goods_details = response.xpath("//ul[contains(@class,'parameter2')]/li/text()").extract()
        # print('--->',goods_details)

        item = item_loader.load_item()
        print("====>",item)

        # yield scrapy.Request(self.sku_price_temp.format(item["goods_id"]), callback=self.parse_price,
        #                      meta={"item": item})

    def parse_price(self, response):
        item = response.meta["item"]
        price_dict = json.loads(response.body)
        time_now = datetime.strftime(date.today(), '%Y-%m-%d')

        price_item = {}

        if len(price_dict) > 0:
            price_item_loader = GoodsPriceItemLoader(item=GoodsPriceItem())
            price_item_loader.add_value("goods_price", price_dict[0]["p"])
            price_item_loader.add_value("last_time",time_now)
            price_item = price_item_loader.load_item()

        item_loader = GoodsItemLoader(item=GoodsItem())
        item_loader.replace_value("update_time", time_now)
        item_loader.add_value("history_prices", price_item)
        item = item_loader.load_item()

            # price_item = {}
            # item["time_now"] = time_now
            # item["goods_price"] = price_dict[0]["p"]
            # price_item["last_price"] = price_dict[0]["p"]
            # price_item["last_time"] = time_now
            # item["history_prices"].append(price_item)


        print(item)
        self.item_num += 1
        print("此时item", self.item_num, "个")
        print("此时解析data", self.data_num, "个")

        # yield item
