#! -*-coding: utf-8 -*-
import base64
import random
from io import BytesIO

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from PIL import Image
import time


class Bilibili(object):
    def __init__(self, driver, username, password):
        self.driver = driver
        self.url = "https://passport.bilibili.com/login"
        self.username = username
        self.password = password

    def run(self):
        # 使用selenium模拟登录
        self.driver.get(self.url)
        self.login()
        time.sleep(1)
        # print(self.driver.page_source)

    def login(self):
        # 输入账号密码点击登录按钮
        userInput = self.driver.find_element_by_xpath("//input[@id='login-username']")
        pwdInput = self.driver.find_element_by_xpath("//input[@id='login-passwd']")
        submit = self.driver.find_element_by_xpath('//*[@id="geetest-wrap"]/div/div[5]/a[1]')
        time.sleep(1)
        userInput.send_keys(self.username)
        time.sleep(1)
        pwdInput.send_keys(self.password)
        time.sleep(0.5)
        submit.click()
        self.driver.implicitly_wait(2)
        # 破解滑块验证码
        #    1. 获取完整图片和有滑块缺口的图片
        #    2. 识别滑块缺口的位置
        #    3. 模拟人拖动滑块
        # 获取2张图片
        bgImg, fullImg = self.get_image()
        # 计算距离
        distance = self.get_distance(bgImg, fullImg)
        # 获取滑块
        slider = self.driver.find_element_by_xpath('/html/body/div[2]/div[2]/div[6]/div/div[1]/div[2]/div[2]')
        # 创建人的拖动轨迹的距离的列表
        track = self.set_track(distance)
        # 拖动滑块
        self.move_slider(slider, track, distance)
        time.sleep(2.12)

    def get_image(self):
        # 构建获取图片js代码 getElementsByClassName("geetest_canvas_bg geetest_absolute")[0]
        time.sleep(2)
        bg_js = 'return document.getElementsByClassName("geetest_canvas_bg geetest_absolute")[0].toDataURL("image/png");'  # 带缺口验证码图片js
        fullbg_js = 'return document.getElementsByClassName("geetest_canvas_fullbg geetest_fade geetest_absolute")[0].toDataURL("image/png");'  # 完整验证码图片js
        # 执行js代码 -> base64编码的byte类型
        bgInfo = self.driver.execute_script(bg_js)
        fullInfo = self.driver.execute_script(fullbg_js)
        bgBase64 = bgInfo.split(",")[1]
        fullBase64 = fullInfo.split(',')[1]
        # 图片解码转为图片二进制数据
        bgByte = base64.b64decode(bgBase64)
        fullByte = base64.b64decode(fullBase64)
        # 将图片二进制数打开
        bgImage = Image.open(BytesIO(bgByte))
        fullImage = Image.open(BytesIO(fullByte))
        return bgImage, fullImage

    def get_distance(self, img1, img2):
        """
        :param img1: 完整图片
        :param img2: 带缺口的图片
        :return: 缺口的距离
        """
        i = 0
        # 验证码滑块的起始位置
        left = 50
        # 两张图片rgb像素相差的阈值threshold
        threshold = 60
        # 偏差
        deviation = 4
        for i in range(left, img1.size[0]):
            for j in range(img1.size[1]):
                # load()方法返回一个用于读取和修改像素的操作对象
                rgb1 = img1.load()[i, j]
                rgb2 = img2.load()[i, j]
                res1 = abs(rgb1[0] - rgb2[0])
                res2 = abs(rgb1[1] - rgb2[1])
                res3 = abs(rgb1[2] - rgb2[2])
                if not (res1 < threshold and res2 < threshold and res3 < threshold):
                    distance = i - deviation
                    return distance
        return i

    def move_slider(self, slider, track, distance):
        ActionChains(self.driver).click_and_hold(slider).perform()
        for x in track:
            ActionChains(self.driver).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.32)
        ActionChains(self.driver).release().perform()

    def set_track(self, distance):
        track = []
        current = 0
        mid = distance * 4 / 5
        t = 0.2
        v = 0
        a = 0
        while current < distance:
            if current < mid:
                a = 2
            else:
                a -= 3
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
        return track


if __name__ == '__main__':
    # options = webdriver.ChromeOptions()
    username = input('请输入账号: ')
    password = input('请输入密码: ')
    driver = webdriver.Chrome()
    spider = Bilibili(driver, username, password)
    spider.run()
