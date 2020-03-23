#! -*-coding: utf-8 -*-
from io import BytesIO
import requests
from base64 import b64decode
from parsel import Selector
from fontTools.ttLib import TTFont
import re
import os
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier


class MaoYanSpider(object):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
        }
        self.url = 'https://piaofang.maoyan.com/store'

    def get_base_font_map(self):
        base_font = TTFont('maoyan.woff')
        base_list = base_font.getGlyphOrder()[2:]
        base_glyf = base_font['glyf']
        baseFontMap = {
            7: base_glyf[base_list[0]].coordinates,
            0: base_glyf[base_list[1]].coordinates,
            9: base_glyf[base_list[2]].coordinates,
            5: base_glyf[base_list[3]].coordinates,
            1: base_glyf[base_list[4]].coordinates,
            2: base_glyf[base_list[5]].coordinates,
            8: base_glyf[base_list[6]].coordinates,
            4: base_glyf[base_list[7]].coordinates,
            6: base_glyf[base_list[8]].coordinates,
            3: base_glyf[base_list[9]].coordinates,
        }
        return baseFontMap

    def request_page(self):
        resp = requests.get(self.url, headers=self.headers)
        if resp.ok:
            return resp.text
        else:
            print(f"响应错误,状态码{resp.status_code}")

    def get_online_font_map(self, html, base_hash_map):
        # 提取字体文件url, 该url每次访问都会改变, 是base64数据
        woff_url = re.search('src:url\((.*?)\)\sformat', html).group(1).split(',')[1]
        font_data = b64decode(woff_url)
        # 在内存中打开, 不下载到本地
        font = TTFont(BytesIO(font_data))
        # 获取字体的names, code代表字符, name代表字形名称
        names = font.getGlyphOrder()[2:]
        # 定义存放names对应的字的列表
        fonts = []
        # 遍历所有字体加密的字符
        for i in range(len(names)):
            # 根据字形名称获取字形数据,是个包含点坐标的类似的二维数组
            coordinate = font['glyf'][names[i]].coordinates
            # 将坐标转化为数组, 求和
            coordinate = np.array(coordinate).sum(axis=1)
            # 定义存放本地下载的猫眼字体的坐标和请求网页字体的坐标的相似度列表
            alikes = []
            for j in range(len(names)):
                base_coordinate = np.array(base_hash_map[j]).sum(axis=1)
                alike = self.compare(base_coordinate, coordinate)
                alikes.append(alike)
            # fonts存放了对应的数字
            fonts.append(alikes.index(max(alikes)))
            # 字典推导式, 存储格式 加密字体: 解密字体
        new_hash_map = {names[i].replace('uni', '&#x', 1).lower() + ';': str(fonts[i]) for i in range(len(names))}
        return new_hash_map

    def replace_html(self, html, font_map):
        for encry_str, decry_str in font_map.items():
            html = re.sub(encry_str, decry_str, html)
        with open('猫眼.html', 'w', encoding='utf-8')as f:
            f.write(html)
        return html

    def parse_html(self, html):
        selector = Selector(html)
        titles = selector.xpath('//div[@class="title"]//text()').extract()
        release_date = selector.xpath('//*[@id="movie-list"]/section/article/text()').extract()
        release_date = [re.match('\n\s*(.*?)\n', data).group(1) for data in release_date if
                        re.match('\n\s*(.*?)\n', data)]
        director = selector.xpath('//p[@class="lineDot"]/text()').extract()
        director = [data.strip() for data in director if data.strip() != '']
        actor = selector.xpath('//span[@class="star-tag"]/text()').extract()
        # 有部电影没有演员信息
        actor.insert(4, None)
        like_people = selector.xpath("//i[@class='cs']/text()").extract()
        like_people = [i + '人想看' for i in like_people]
        movies_info = []
        for i in range(len(titles)):
            movie_info = dict(
                title=titles[i],
                release_date=release_date[i],
                director=director[i],
                actor=actor[i],
                like_people=like_people[i]
            )
            # print(movie_info)
            movies_info.append(movie_info)
        return movies_info

    def save_to_csv(self, data):
        data = pd.DataFrame(data)
        data.to_csv('猫眼电影上映榜单')

    def run(self):
        base_font_map = self.get_base_font_map()
        html = self.request_page()
        online_font_map = self.get_online_font_map(html, base_font_map)
        html = self.replace_html(html, online_font_map)
        with open('猫眼.html', 'r', encoding='utf-8')as f:
            html = f.read()
            data = self.parse_html(html)
            self.save_to_csv(data)

    @staticmethod
    def compare(arr1, arr2):
        # 比较2个数组的相似度
        length = min(len(arr1), len(arr2))
        alike = 0
        for i in range(length):
            if abs(arr1[i] - arr2[i]) < 50:
                alike += 1
        return alike


if __name__ == '__main__':
    spider = MaoYanSpider()
    spider.run()
