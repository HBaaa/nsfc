# -*- coding: utf-8 -*-
import re
import os
import sys
import json
import datetime
import urllib

import scrapy
from nsfc.spiders.utils import GetCode

reload(sys)
sys.setdefaultencoding('utf-8')


class NsfcSpiderSpider(scrapy.Spider):
    name = 'nsfc_spider'
    allowed_domains = ['letpub.com.cn']
    base_url = 'http://www.letpub.com.cn/'

    now_year = datetime.datetime.now().year

    def __init__(self, **kwargs):
        self.code = kwargs.get('code')
        self.startTime = kwargs.get('startTime', str(self.now_year))
        self.endTime = kwargs.get('endTime', str(self.now_year))

    def start_requests(self):

        if not self.code:
            msg = 'argument code is required!'
            self.crawler.engine.close_spider(self, msg)
        elif os.path.isfile(self.code):
            with open(self.code) as f:
                codes = f.read().strip().split()
        else:
            codes = self.code.split(',')

        payload = {
            'page': 'grant',
            # 'name': '',
            # 'person': '',
            # 'no': '',
            # 'company': '',
            'addcomment_s1': '',  # 学科分类
            'addcomment_s2': '',  # 一级学科
            'addcomment_s3': '',  # 二级学科
            'addcomment_s4': '',  # 三级学科
            # 'money1': '',  # 项目金额
            # 'money2': '',
            'startTime': self.startTime,  # 批准时间
            'endTime': self.endTime,
            # 'subcategory': '',  # 项目类别
            'currentpage': '1',
            # 'searchsubmit': 'true',
        }

        for code in codes:
            code_data = GetCode.get_field_code()
            child_codes = GetCode.get_child_code(code,
                                                 code_data=code_data,
                                                 recursive=True)
            # child_codes = [{'code': code, 'name': code_data[code]['name']}]
            for child in child_codes:
                child_code = child['code']

                self.logger.info(
                    '\033[32mquering {code} {name}\033[0m'.format(**child))

                payload['addcomment_s1'] = child_code[0]
                class1 = class2 = class3 = ''
                if len(child_code) >= 3:
                    class1 = child_code[:3]
                if len(child_code) >= 5:
                    class2 = child_code[:5]
                if len(child_code) >= 7:
                    class3 = child_code[:7]

                payload['addcomment_s2'] = class1
                payload['addcomment_s3'] = class2
                payload['addcomment_s4'] = class3

                query_strings = [urllib.urlencode(payload)]  # C C03 C0301 C030101

                if class3:
                    payload['addcomment_s4'] = class2
                    query_strings += [urllib.urlencode(payload)]  # C C03 C0301 C0301

                if class2:
                    payload['addcomment_s4'] = class1
                    payload['addcomment_s3'] = class1
                    query_strings += [urllib.urlencode(payload)]  # C C03 C03 C03

                for query_string in query_strings:
                    self.logger.info('query_string: {}'.format(query_string))
                    url = self.base_url + '?' + query_string
                    yield scrapy.Request(url)

    def parse(self, response):

        info = response.xpath('//*[@id="main"]/center[1]/div/text()').get()
        result = re.findall(r'搜索条件匹配：(\d+)条记录.*?共(\d+)页', info.encode('utf-8'))
        total_record, total_page = map(int, result[0])

        # re.findall(r'', response.url)

        self.logger.info(
            '\033[32mfind {total_record} records with {total_page} pages\033[0m<{url}>'
            .format(url=response.url, **locals()))

        # =================================================
        # 结果最多显示50页，如果匹配结果太多，请您进一步精炼筛选条件
        # =================================================
        if total_page > 50:
            msg = '\033[1;31m匹配结果太多，请您进一步精炼筛选条件\033[0m'
            self.crawler.engine.close_spider(self, msg)

        ths = response.xpath('//*[@id="main"]/table/tr[2]/th/text()').getall()
        # print '\t'.join(ths)

        trs = response.xpath('//*[@id="main"]/table/tr')
        for tr in trs[2:-1]:
            tds = tr.xpath('td/text()').getall()
            if tr.attrib.get('style'):
                context = dict(zip(ths, tds))
            else:
                key, value = tds
                context[key] = value
            # print json.dumps(context, indent=2, ensure_ascii=False)
            if len(context) == 11:
                yield context

        next_page_url = response.xpath(
            '//table[@class="table_yjfx"]/tr[1]/td/a')[-2].attrib['href']
        next_page = re.findall(r'currentpage=(\d+)', next_page_url)[0]
        now_page = re.findall(r'currentpage=(\d+)', response.url)[0]
        self.logger.info(
            'now_page: {now_page}, next_page: {next_page}'.format(**locals()))
        if next_page != now_page:
            yield response.follow(next_page_url, callback=self.parse)
