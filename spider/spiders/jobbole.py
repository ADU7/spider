# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
from urllib import parse
import re
from spider.items import JobboleSpiderItem
from spider.utils.common import get_md5
import datetime


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    # def __init__(self):
    #     self.browser = webdriver.Chrome(executable_path="/Users/peihuidu/PycharmProjects/chromedriver")
    #     super(JobboleSpider, self).__init__()
    #     dispatcher.connect(self.spider_closed, signals.spider_closed)
    #
    # def spider_closed(self, spider):
    #     #当爬虫退出的时候关闭chrome
    #     print ("spider closed")
    #     self.browser.quit()

    def parse(self, response):
        # 解析列表页中所有文章的url交给scrapy下载，并回调parse_detail进行具体解析
        nodes = response.css("#archive .post-thumb a")
        for node in nodes:
            node_url = node.css("::attr(href)").extract_first("")
            yield Request(url=parse.urljoin(response.url, node_url), callback=self.parse_detail)

        # 解析下一页url交给scrapy下载，回调parse
        next_page = response.css("#archive .next.page-numbers::attr(href)").extract_first("")
        if next_page:
            yield Request(url=parse.urljoin(response.url, next_page), callback=self.parse)

    def parse_detail(self, response):
        title = response.css("#wrapper .entry-header h1::text").extract()[0]
        create_date = response.css("#wrapper .entry-meta p::text").extract()[0].strip().replace("·", "").strip()
        try:
            create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()
        except Exception as e:
            create_date = datetime.datetime.now().date()
        tags_list = response.css("#wrapper .entry-meta a::text").extract()
        tags_list = [element for element in tags_list if not element.strip().endswith("评论")]
        tags = ",".join(tags_list)
        praise_nums = response.css(".vote-post-up h10::text").extract_first(0)
        collection = response.css(".bookmark-btn::text").extract()[0]
        match_re = re.match(".*?(\d+).*", collection)
        if match_re:
            collection = int(match_re.group(1))
        else:
            collection = 0
        comment_nums = response.css("a[href='#article-comment'] span::text").extract()[0]
        match_re = re.match(".*?(\d+).*", comment_nums)
        if match_re:
            comment_nums = int(match_re.group(1))
        else:
            comment_nums = 0

        content = response.css("div.entry").extract()[0]

        jobbole_item = JobboleSpiderItem()
        jobbole_item["url"] = response.url
        jobbole_item["url_object_id"] = get_md5(response.url)
        jobbole_item["title"] = title
        jobbole_item["create_date"] = create_date
        jobbole_item["tags"] = tags
        jobbole_item["praise_nums"] = praise_nums
        jobbole_item["collection"] = collection
        jobbole_item["comment_nums"] = comment_nums
        jobbole_item["content"] = content
        yield jobbole_item
