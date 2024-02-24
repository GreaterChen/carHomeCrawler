import sys
from time import sleep
import pandas as pd
from selenium.webdriver import ActionChains
from tqdm import tqdm

from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from pypinyin import pinyin, Style


def get_initials(text):
    initials = ''.join([word[0][0] for word in pinyin(text, style=Style.NORMAL)])
    return initials


class Crawler:
    def __init__(self):
        option = webdriver.EdgeOptions()
        # option.add_argument("headless")  # 注释可以显示浏览器
        option.add_argument('no-sandbox')
        option.add_argument(
            "user-agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 "
            "Safari/537.36'")

        # driver_path = ChromeDriverManager().install()
        # service = Service(driver_path)
        self.browser = webdriver.Edge(options=option)
        self.browser.maximize_window()

        self.wait = WebDriverWait(self.browser, 3)

    def run(self):
        dcd_links = [8942, 4668, 1729, 5314, 4640, 3932, 4838, 4538, 3719, 4543, 2913, 2816, 1422, 798, 1647, 215, 148,
                     131]
        self.work_dcd(dcd_links, city="北京")

        qczz_links = ["https://www.autohome.com.cn/7223/#pvareaid=100124",
                      "https://www.autohome.com.cn/5382/#pvareaid=100124",
                      "https://www.autohome.com.cn/6149/#pvareaid=100124",
                      "https://www.autohome.com.cn/6362/#pvareaid=100124",
                      "https://www.autohome.com.cn/5828/#pvareaid=100124",
                      "https://www.autohome.com.cn/6150/#pvareaid=100124",
                      "https://www.autohome.com.cn/6544/#pvareaid=100124",
                      "https://www.autohome.com.cn/5758/#pvareaid=100124",
                      "https://www.autohome.com.cn/5232/#pvareaid=100124",
                      "https://www.autohome.com.cn/5765/#pvareaid=100124",
                      "https://www.autohome.com.cn/4764/#pvareaid=100124",
                      "https://www.autohome.com.cn/4663/#pvareaid=100124",
                      "https://www.autohome.com.cn/3553/#pvareaid=100124",
                      "https://www.autohome.com.cn/4083/#pvareaid=100124",
                      "https://www.autohome.com.cn/3972/#pvareaid=100124",
                      "https://www.autohome.com.cn/3248/#pvareaid=100124",
                      "https://www.autohome.com.cn/2561/#pvareaid=100124",
                      "https://www.autohome.com.cn/3230/#pvareaid=100124"
                      ]
        self.work_qczz(qczz_links)

    def work_qczz(self, links, city="北京"):
        cars_data = []
        first_run = True
        for link in tqdm(links):
            self.browser.get(link)
            if first_run:
                try:
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//span[@class="inquiry_layer_close"]'))).click()
                except:
                    pass
                first_run = False
            self.browser.find_element(By.XPATH, '//p[@class="promotion-citychange"]/a').click()
            send_area = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, '//input[@id="auto-citypicker-txt"]')))

            send_area.send_keys(f"{city}")
            self.browser.find_element(By.XPATH, '//ul[@id="auto-citypicker-tip-list"]/li/a').click()
            self.browser.refresh()

            all_info = self.browser.find_element(By.XPATH, '//div[@class="series-list"]')
            name = all_info.find_element(By.XPATH, './div[@class="athm-title"]/div[1]').text
            different_mode = all_info.find_elements(By.XPATH, './div[@class="series-content"]/div[@id="specWrap-2"]/dl')
            for mode in different_mode:
                all_car = mode.find_elements(By.XPATH, './dd')
                for car in all_car:
                    car_name = car.find_element(By.XPATH, './div[@class="spec-name"]/div/p[1]/a[1]').text
                    zdj = car.find_element(By.XPATH, './div[@class="spec-guidance"]').text
                    jxs = car.find_element(By.XPATH, './div[@class="spec-lowest"]').text
                    if car_name != '':
                        cars_data.append({"车型": name, "型号": car_name, "指导价": zdj, "经销商报价": jxs})

        # 使用pandas保存或处理数据
        df = pd.DataFrame(cars_data)
        df.to_excel("cars_data_qczz.xlsx", index=False)

        # 爬取完毕后，关闭浏览器
        self.browser.quit()

    def work_dcd(self, links, city="北京"):
        cars_data = []
        first_run = True
        for link in tqdm(links):
            url = "https://www.dongchedi.com/auto/series/" + str(link) + "?city=" + city
            # url = "https://www.dongchedi.com/auto/series/8942?city=%E5%8C%97%E4%BA%AC"

            self.browser.get(url)
            if first_run:
                first_letter = get_initials(city)[0]

                select_city_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@class="tw-relative new-header_city__2HpkN"]/button')))
                select_city_button.click()

                letter_area = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//section[@class="jsx-3656537516"]/div/span['
                                                          f'@data-letter="{first_letter}"]')))
                letter_area.click()

                target_city = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//section[@class='jsx-4165276750 city-section-wrap']/div["
                                                          f"@data-letter='{first_letter}']/span["
                                                          f"contains(text(), '{city}')]")))
                target_city.click()
                first_run = False

            try:
                # 等待“点击显示更多”的按钮出现，并点击它
                load_more_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '点击展示更多')]")))
                ActionChains(self.browser).move_to_element(load_more_button).click(load_more_button).perform()
            except:
                pass

            # 爬取数据
            all_info = self.browser.find_element(By.XPATH, '//div[@id="carModels"]')
            name = all_info.find_element(By.XPATH, './div[1]/div[1]/h2/span').text.split('·')[0]
            different_mode_list = all_info.find_elements(By.XPATH, './div[1]/ul/li')
            for mode in different_mode_list:
                divs_with_data_log_click = mode.find_elements(By.XPATH, './div[@data-log-click]')
                for car in divs_with_data_log_click:
                    child_divs = car.find_elements(By.XPATH, './div')
                    car_name = child_divs[0].find_element(By.XPATH, './div/div[1]').text
                    zdj = child_divs[1].text  # 指导价
                    jxs = child_divs[2].text  # 经销商报价
                    if car_name != '':
                        cars_data.append({"车型": name, "型号": car_name, "指导价": zdj, "经销商报价": jxs})

        df = pd.DataFrame(cars_data)
        df.to_excel("cars_data_dcd.xlsx", index=False)

        # 爬取完毕后，关闭浏览器
        self.browser.quit()


if __name__ == '__main__':
    r = Crawler()
    r.run()
