from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re,time,random,json
from pyquery import PyQuery as pq
from selenium.common.exceptions import StaleElementReferenceException


url = 'https://www.jd.com'
broswer = webdriver.Chrome()
wait = WebDriverWait(broswer,10)
js = "document.documentElement.scrollTop=500000"    #scrollTop的值就是距离网页顶端的像素值，0就表示在顶端

# 搜索关键字
def search():
    try:
        broswer.get(url)
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'#key'))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,'#search > div > div.form > button'))
        )
        input.send_keys("图书")
        submit.click()
        # 加一次刷新操作，世界都变得不太一样了
        broswer.refresh()
        broswer.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        time.sleep(random.randint(1,2))
        for product_info in parse_html():
            write_to_file(product_info)
        page_numb = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'#J_bottomPage .p-skip b'))
        )
        return page_numb.text    #得到详情页页码数
    except TimeoutException:
        search()

# 解析当前页面商品信息
def parse_html():
    try:
        wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#J_goodsList .gl-warp.clearfix .gl-item'))
        )
        html = broswer.page_source
        # print(html)    # done!
        # 网页存在乱码的情况，但是问题不大
        doc = pq(html)
        items = doc('#J_goodsList .gl-warp.clearfix .gl-item').items()
        for item in items:
            yield {
                'img_url':item.find('.p-img a img').attr('src'),
                'price': item.find('.p-price i').text() + item.find('.p-price em').text(),
                'commit': item.find('.p-commit strong').text(),
                'book_name':item.find('.p-name em').text(),
                'abstract': re.sub(r'\n', ' ', item.find('.p-name a').attr('title')),
                'shop':item.find('.p-shopnum a').attr('title'),
                'preferential':item.find('.p-icons i').text(),
            }
    except TimeoutException:
        parse_html()

# 存入本地
def write_to_file(product_info):
    with open('jd_info.text','a',encoding='utf-8') as f:
        f.write(json.dumps(product_info, ensure_ascii=False) + '\n')
        f.close()

# 模仿Chrome进行翻页
def next_page(pagenumb):
    #两手异常捕获，给你带来加倍的安全感～
    # 捕获超时异常 ==> 重新解析当前页面
    try:
        # 翻页速度较快，捕获html元素未加载完全的异常，重复当前操作
        try:
            input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR,'#J_bottomPage > span.p-skip > input'))
            )
            submit = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_bottomPage > span.p-skip > a'))
            )
            input.clear()
            input.send_keys(pagenumb)
            submit.click()
        except StaleElementReferenceException:
            input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#J_bottomPage > span.p-skip > input'))
            )
            submit = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_bottomPage > span.p-skip > a'))
            )
            input.clear()
            input.send_keys(pagenumb)
            submit.click()
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#J_bottomPage > span.p-num > a.curr'), str(pagenumb))
        )
        # 网页刷新
        broswer.refresh()
        broswer.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        time.sleep(random.randint(1, 2))
        for product_info in parse_html():
            write_to_file(product_info)
    except TimeoutException:
        next_page(pagenumb)

# 主程序文件
def main():
    pagenumb = search()
    total_numb = int(pagenumb)
    for page in range(2,total_numb):
        next_page(page)

if __name__ == '__main__':
    main()