import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from lxml import etree
import pandas as pd

options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

driver.get('https://www.bilibili.com')
wait = WebDriverWait(driver, 5)
search_input = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'nav-search-keyword')))
search_button = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="nav-search-btn"]/button')))
search_input.send_keys('假面骑士ʿ')
search_button.click()


all_handles = driver.window_handles
driver.switch_to.window(all_handles[1])
max_click = wait.until(EC.presence_of_element_located((By.XPATH, '//li[@class="filter-item"][1]/a')))
max_click.click()


def parse_data(page_source):
    parser = etree.HTML(page_source)
    titles = []
    watch_timeses = []
    dates = []
    authors = []
    lis = parser.xpath('//ul[contains(@class, "video-list")]/li')
    for li in lis:
        try:
            title = li.xpath('./a[1]/@title')[0].strip()
            watch_times = li.xpath('.//div[@class="tags"]/span[1]/text()')[0].strip()
            date = li.xpath('.//div[@class="tags"]/span[3]/text()')[0].strip()
            author = li.xpath('.//div[@class="tags"]/span[last()]/a/text()')[0].strip()
            titles.append(title)
            watch_timeses.append(watch_times)
            dates.append(date)
            authors.append(author)
        except Exception as e:
            print(f'error: {e}')
    items = dict(
        title=titles,
        watch_times=watch_timeses,
        date=dates,
        author=authors
    )
    return items


def save_data(items):
    data = pd.DataFrame(items)
    return data


res = []
for i in range(50):
    items = pd.DataFrame(parse_data(driver.page_source))
    if i != 49:
        next_page_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//ul[@class='pages']/li[last()]/button")))
        next_page_btn.click()
    time.sleep(2)
    res.append(items)


df = res[0]
for i in range(1, len(res)):
    df = pd.concat([df, res[i]], ignore_index=True)


df.to_csv("假面骑士视频播放量排行榜.csv")
