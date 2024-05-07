from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common import TimeoutException
from pyquery import PyQuery as pq
from urllib.parse import quote
import time
from lxml import etree
import requests
import openpyxl
import ast
import xlsxwriter
import sys

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "localhost:9222") #此处端口保持和命令行启动的端口一致
driver = Chrome(options=chrome_options)
actions = ActionChains(driver)
wait = WebDriverWait(driver, 10)


# chrome.exe --remote-debugging-port=9222 --user-data-dir='D:\chrome_data'
def get_item(url):
    result = {}  # 手机参数
    comment_list = []
    try:
        driver.get(url)
        time.sleep(2)
        html = driver.page_source
        doc = pq(html)
        parameter_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="detail"]/div[1]/ul/li[2]')))  # 参数按钮
        parameter_btn.click()
        time.sleep(1.5)
        items = doc('.clearfix').items()  # .Ptable-item
        for item in items:
            key = item('dt').text()
            content = item('dd').text()
            # key = item.find('.clearfix')('dt').text()
            # content = item.find('.clearfix')('dd').text()
            if key == '' or item == '':
                continue
            if key != '入网型号':
                result[key] = content
            else:
                if len(content) > 10:
                    result[key] = content[11:]
        print(result)
        comment_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="detail"]/div[1]/ul/li[5]')))  # 参数按钮
        comment_btn.click()
        max_page = 2
        for i in range(max_page):  # 评论翻页
            if i != 0:
                html = driver.page_source
                doc = pq(html)
                if doc.find('.ui-pager-next').text():  # 下一页
                    next_page_btn = driver.find_element(By.XPATH, '//*[@id="comment-0"]/div[12]/div/div/a[7]')
                    driver.execute_script('arguments[0].click();', next_page_btn)
                else:
                    break
            time.sleep(4)
            html = driver.page_source
            doc = pq(html)
            comments = doc('.comment-con').items()  # ('.J-comments-list comments-list ETab')('.tab-con')
            for item in comments:
                comment_list.append('。'.join(item.text().split('\n')))
        print(comment_list)
    except TimeoutException:
        return str(result), comment_list
    return str(result), comment_list


def get_jd_item():
    wb = openpyxl.load_workbook(filename="jd.xlsx")
    ws = wb['Sheet1']
    count = 1
    workbook = xlsxwriter.Workbook('jd_item.xlsx')
    worksheet = workbook.add_worksheet()
    worksheet.write(0, 0, 'index')
    worksheet.write(0, 1, 'id')
    worksheet.write(0, 2, 'name')
    worksheet.write(0, 3, 'price')
    worksheet.write(0, 4, 'specifications')
    for row in ws.iter_rows(min_row=2, min_col=1, max_row=ws.max_row, values_only=True):  # ws.max_row
        id = row[1]
        url = "https://item.jd.com/" + str(id) + ".html"
        worksheet.write(count, 0, row[0])
        worksheet.write(count, 1, url)
        worksheet.write(count, 2, row[2])
        worksheet.write(count, 3, row[3])
        spec, comments = get_item(url)
        if len(spec) == 0:
            time.sleep(10)
            continue
        else:
            worksheet.write(count, 4, spec)
        if len(comments):  # comments不为空
            for index, comment in enumerate(comments):
                print(comment)
                worksheet.write(count, index + 5, comment)
        else:
            print('empty')
        count += 1
    workbook.close()


def read_only():
    wb = openpyxl.load_workbook(filename="jd_item.xlsx")
    ws = wb['Sheet1']
    lis = []
    dic = {"id": None, "name": None, "price": None, "specification": None, 'comment': None}
    for row in ws.iter_rows(min_row=2, min_col=2, max_row=ws.max_row, values_only=True):  # , max_col=5
        dic["id"] = row[0]
        dic["name"] = row[1]
        dic["price"] = row[2]
        # print(row[3])  # 手机参数
        print(row)
        c = ast.literal_eval(row[3])
        # print(c, type(c))
        dic["specification"] = c
        lis.append(dic)
    # print(lis)
    return lis


if __name__ == '__main__':
    get_jd_item()  # 爬取手机参数和评价
    read_only()
