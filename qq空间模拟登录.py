#! -*-coding: utf-8 -*-
import os
import time
import cv2
import numpy as np
import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class Spider(object):
    def __init__(self, driver, username, password):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.nums = [13, 26, 98, 79, 745, 19, 17, 35, 36, 6,
                     82, 43, 4, 111, 123, 40, 58, 13, 23, 19, 63,  61, 85, 64, 12, 10]
        self.username = username
        self.password = password

    def run(self):
        self.login()
        time.sleep(2)
        self.parse()

    def login(self):
        # 请求登录页面， 输入账号密码
        self.request_login(self.username, self.password)
        # 验证码弹出后下载到本地
        self.get_img()
        # 解析滑块到凹槽的距离
        distance = self.get_distance()
        # 设置拖动轨迹
        track = self.set_track(distance)
        # 拖动滑块到正确位置
        self.move_slider(track, distance)

    def request_login(self, username, password):

        self.driver.get("https://qzone.qq.com/")
        self.driver.switch_to.frame("login_frame")
        login_link = self.driver.find_element(By.ID, "switcher_plogin")
        login_link.click()
        user = self.driver.find_element(By.ID, "u")
        pwd = self.driver.find_element(By.ID, "p")
        user.send_keys(username)
        pwd.send_keys(password)
        time.sleep(1)
        submit = self.driver.find_element(By.ID, "login_button")
        submit.click()
        time.sleep(2)

    def get_img(self):
        iframe = self.driver.find_element_by_xpath('//iframe')
        self.driver.switch_to.frame(iframe)
        bg_img = self.driver.find_element_by_xpath('//*[@id="slideBg"]')
        slide_img = self.driver.find_element_by_xpath('//*[@id="slideBlock"]')
        with open("bg.png", "wb") as f:
            bg_img = requests.get(bg_img.get_attribute("src")).content
            f.write(bg_img)
        with open("slider.png", "wb") as f:
            slide_img = requests.get(slide_img.get_attribute(("src"))).content
            f.write(slide_img)

    def get_distance(self):
        slider = 'slider.png'
        bg = 'bg.png'
        slider_img = cv2.imread(slider, 0)
        bg_img = cv2.imread(bg, 0)
        slider_img = cv2.resize(slider_img, (56, 56))
        bg_img = cv2.resize(bg_img, (280, 163))
        # weight， height
        w, h = bg_img.shape[::-1]
        # print(f"背景图片宽高为{w}, {h}")
        bg = 'bg.jpg'
        slider = 'slider.jpg'
        slider_img = abs(255 - slider_img)
        # print(slider_img)
        result = cv2.matchTemplate(bg_img, slider_img, cv2.TM_CCOEFF_NORMED)
        x, y = np.unravel_index(result.argmax(), result.shape)
        # print(x, y)
        # 展示修改的图片
        # cv2.imshow("sldier", slider_img)
        # cv2.imshow("bg_img", bg_img)
        cv2.waitKey(0)
        return y

    def set_track(self, distance):
        track = []
        current = 0
        distance -= 26
        mid = distance * (4 / 5)
        t = 0.2
        v = 0
        a = 0
        while current < distance:
            if current < mid:
                a = 2
            else:
                a = 3
            v0 = v
            # v = vo + at
            v = v0 + a * t
            # s = vo*t + (1/2)a*t^2
            move = v0 * t + (1 / 2) * a * t * t
            current += move
            track.append(round(move))
        return track

    def move_slider(self, track, distance):
        slider = self.driver.find_element_by_id("tcaptcha_drag_thumb")
        ActionChains(self.driver).click_and_hold(slider).perform()
        for x in track:
            ActionChains(self.driver).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.12)
        ActionChains(self.driver).release().perform()

    def parse(self):
        pass



if __name__ == '__main__':
    username = input("请输入qq号:")
    password = input("请输入密码:")
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    driver = webdriver.Chrome()
    spider = Spider(driver, username, password)
    spider.run()
