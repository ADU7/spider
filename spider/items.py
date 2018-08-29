# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags
from spider.utils.common import extract_num

from spider.models.es_types import ArticleType


from elasticsearch_dsl.connections import connections
es = connections.create_connection(ArticleType._doc_type.using)


class SpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


def gen_suggests(index, info_tuple):
    # 根据字符串生成搜索建议数组
    used_words = set()
    suggests = []
    for text, weight in info_tuple:
        if text:
            # 调用es的analyze接口分析字符串
            words = es.indices.analyze(index=index, params={'filter': ["lowercase"]}, body={'text': text, 'analyzer': "ik_max_word"})
            anylyzed_words = set([r["token"] for r in words["tokens"] if len(r["token"]) > 1])
            new_words = anylyzed_words - used_words
        else:
            new_words = set()

        if new_words:
            suggests.append({"input": list(new_words), "weight": weight})

    return suggests


class JobboleSpiderItem(scrapy.Item):
    # 伯乐在线文章信息
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    create_date = scrapy.Field()
    tags = scrapy.Field()
    praise_nums = scrapy.Field()
    collection = scrapy.Field()
    comment_nums = scrapy.Field()
    content = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    INSERT INTO jobbole(title, create_date, url, url_object_id, comment_nums, collection, 
                    praise_nums, tags) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
        params = (
            self["title"], self["create_date"], self["url"], self["url_object_id"],
            self["comment_nums"], self["collection"], self["praise_nums"], self["tags"]
        )
        return insert_sql, params

    def save_to_es(self):
        # 数据保存到elasticsearch
        article = ArticleType()
        article.title = self['title']
        article.create_date = self["create_date"]
        # article.content = remove_tags(self["content"])
        # article.front_image_url = self["front_image_url"]
        # if "front_image_path" in self:
        #    article.front_image_path = self["front_image_path"]
        article.praise_nums = self["praise_nums"]
        article.collection = self["collection"]
        article.comment_nums = self["comment_nums"]
        article.url = self["url"]
        article.tags = self["tags"]
        article.meta.id = self["url_object_id"]
        article.content = self["content"]

        article.suggest = gen_suggests(ArticleType._doc_type.index, ((article.title, 10), (article.tags, 7)))

        article.save()
        return


def replace_splash(value):
    return value.replace("/", "")


def handle_strip(value):
    return value.strip()


def handle_jobaddr(value):
    addr_list = value.split("\n")
    addr_list = [item.strip() for item in addr_list if item.strip() != "查看地图"]
    return "".join(addr_list)


class LagouItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class LagouSpiderItem(scrapy.Item):
    # 拉勾网职位信息
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    title = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(input_processor=MapCompose(replace_splash))
    work_years = scrapy.Field(input_processor=MapCompose(replace_splash))
    degree_need = scrapy.Field(input_processor=MapCompose(replace_splash))
    job_type = scrapy.Field()
    publish_time = scrapy.Field()
    tags = scrapy.Field(output_processor=Join(","))
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field(input_processor=MapCompose(handle_strip))
    job_addr = scrapy.Field(input_processor=MapCompose(remove_tags, handle_jobaddr))
    company_name = scrapy.Field()
    company_url = scrapy.Field()
    job_id = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            INSERT INTO lagou(title, url, url_object_id, salary, job_city, work_years, degree_need,
            job_type, publish_time, tags, job_advantage, job_desc, job_addr, company_url, company_name, job_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE job_desc=VALUES(job_desc)
        """

        job_id = extract_num(self["url"])
        params = (self["title"], self["url"], self["url_object_id"], self["salary"], self["job_city"],
                  self["work_years"], self["degree_need"], self["job_type"], self["publish_time"],
                  self["tags"], self["job_advantage"], self["job_desc"], self["job_addr"],
                  self["company_url"], self["company_name"], job_id)

        return insert_sql, params
