#-*- encoding: utf8 -*-
"""
学科代码API: http://output.nsfc.gov.cn/common/data/fieldCode
"""
import os
import sys
import time
from collections import defaultdict

import requests

reload(sys)
sys.setdefaultencoding('utf-8')


class GetCode(object):
    base_url = 'http://output.nsfc.gov.cn/common/data/'

    @classmethod
    def get_field_code(cls):
        url = cls.base_url + 'fieldCode'

        while True:
            try:
                data = requests.get(url).json()['data']
                break
            except requests.exceptions.ConnectionError:
                time.sleep(5)

        result = defaultdict(dict)
        for field in data:
            name = field['name']
            code = field['code']

            result[code]['name'] = name
            result[code]['child'] = {}

            if len(code) == 1:
                continue

            parent_code = code[:-2]
            result[parent_code]['child'][code] = name

        return dict(result)

    @classmethod
    def get_child_code(cls, code, code_data=None, recursive=True):
        code_data = code_data or cls.get_field_code()
        child = code_data[code].get('child')

        if recursive and child:
            for child_code in child:
                for each in cls.get_child_code(child_code, code_data):
                    yield each
        else:
            yield {'code': code, 'name': code_data[code]['name']}

    @classmethod
    def get_support_types(cls):
        url = cls.base_url + 'supportTypeData'

        while True:
            try:
                data = requests.get(url).json()['data']
                break
            except requests.exceptions.ConnectionError:
                time.sleep(5)

        result = {}
        for project in data:
            name = project['name']
            code = project['value']
            result[code] = name

        return result

if __name__ == '__main__':

    # print GetCode.get_field_code().get('C06')
    for each in list(GetCode.get_child_code('C', recursive=False)):
        print '{code}\t{name}'.format(**each)

    for each in list(GetCode.get_child_code('H', recursive=False)):
        print '{code}\t{name}'.format(**each)
