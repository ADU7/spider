# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from spider.items import LagouSpiderItem, LagouItemLoader
from spider.utils.common import get_md5


class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com/']

    # if not settings, it will be redirect to login
    custom_settings = {
        "COOKIES_ENABLED": False,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': 'JSESSIONID=ABAAABAAADEAAFI4F553B12F3291AE8B8A6B735D1E7B589; user_trace_token=20180401191831-4bd4baff-89a6-47e2-8c53-81627ddc8563; _ga=GA1.2.1507796738.1522581513; LGUID=20180401191832-69ac215e-359e-11e8-ac0b-525400f775ce; X_HTTP_TOKEN=a67f5ce486d5afa1d164ad327fa57958; gate_login_token=""; _putrc=14B0A4C7945AB3E1; login=true; unick=%E6%9D%9C%E5%9F%B9%E8%BE%89; WEBTJ-ID=20180426234614-16302a2324f7e1-09250f19f0c355-336e7b05-1296000-16302a2325145a; TG-TRACK-CODE=search_code; _gid=GA1.2.1474511299.1534674083; Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1534674083; LGSID=20180819182123-9f54471c-a399-11e8-92e0-525400f775ce; PRE_UTM=; PRE_HOST=; PRE_SITE=; PRE_LAND=https%3A%2F%2Fwww.lagou.com%2Fjobs%2F2131194.html; LG_LOGIN_USER_ID=a04f62212c62c499a1afc4197fc33b0739aa4ecb52c218f5; showExpriedIndex=1; showExpriedCompanyHome=1; showExpriedMyPublish=1; hasDeliver=4; gate_login_token=df70981a8d7a5bca767e46c4184815864c80967097cb63f3; index_location_city=%E6%B7%B1%E5%9C%B3; _gat=1; Hm_lpvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1534674456; LGRID=20180819182735-7d2d560c-a39a-11e8-92e0-525400f775ce',
            'Host': 'www.lagou.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
        }
    }

    rules = (
        Rule(LinkExtractor(allow=("zhaopin/.*",)), follow=True),
        Rule(LinkExtractor(allow=("gongsi/j\d+.html",)), follow=True),
        Rule(LinkExtractor(allow=r'jobs/\d+.html'), callback='parse_job', follow=True),
    )

    def parse_job(self, response):
        item_loader = LagouItemLoader(item=LagouSpiderItem(), response=response)
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("title", ".job-name::attr(title)")
        item_loader.add_css("salary", ".position-content span[class='salary']::text")
        item_loader.add_xpath("job_city", "//*[@class='job_request']/p/span[2]/text()")
        item_loader.add_xpath("work_years", "//*[@class='job_request']/p/span[3]/text()")
        item_loader.add_xpath("degree_need", "//*[@class='job_request']/p/span[4]/text()")
        item_loader.add_xpath("job_type", "//*[@class='job_request']/p/span[5]/text()")
        item_loader.add_css("publish_time", ".publish_time::text")
        item_loader.add_css("tags", ".position-label.clearfix li::text")
        item_loader.add_css("job_advantage", "#job_detail p::text")
        item_loader.add_css("job_desc", ".job_bt div")
        item_loader.add_css("job_addr", ".work_addr")
        item_loader.add_css("company_name", "#job_company dt img::attr(alt)")
        item_loader.add_css("company_url", "#job_company dt a::attr(href)")
        job_item = item_loader.load_item()
        yield job_item