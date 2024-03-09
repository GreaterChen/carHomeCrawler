import pickle
import sys
import traceback
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

from utils import replace_phev, process_car_model_names


def get_initials(text):
    initials = ''.join([word[0][0] for word in pinyin(text, style=Style.NORMAL)])
    return initials


class Crawler:
    def __init__(self):
        self.option = webdriver.ChromeOptions()
        # option.add_argument("headless")  # 注释可以显示浏览器
        self.option.add_argument("--disable-extensions")
        self.option.add_argument("--disable-gpu")
        self.option.add_argument("--disable-software-rasterizer")
        self.option.add_argument('--ignore-certificate-errors')
        self.option.add_argument('--allow-running-insecure-content')
        self.option.add_argument("blink-settings=imagesEnabled=false")
        self.option.add_argument('no-sandbox')
        self.option.add_argument(
            "user-agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 "
            "Safari/537.36'")

        # driver_path = ChromeDriverManager().install()
        # service = Service(driver_path)
        self.browser = webdriver.Chrome(options=self.option)
        self.browser.maximize_window()

        self.wait = WebDriverWait(self.browser, 5)
        self.wait_1 = WebDriverWait(self.browser, 1)

    def run(self):
        dcd_df = pd.read_excel("data/raw_data_dcd.xlsx")
        links = dcd_df['懂车帝车系页链接'].to_list()
        dcd_links = [link for link in links if 'https' in link]

        # dcd_links = [8942, 4668, 1729, 5314, 4640, 3932, 4838, 4538, 3719, 4543, 2913, 2816, 1422, 798, 1647, 215, 148,
        #              131]
        # self.work_dcd(dcd_links)

        qczj_df = pd.read_excel("data/raw_data.xlsx")
        qczj_links = qczj_df['汽车之家车系页链接'].dropna().tolist()
        cities = qczj_df['城市'].dropna().tolist()
        self.work_qczj(qczj_links, cities)
        self.browser.quit()

    def get_new_browser(self):
        self.browser.quit()
        self.browser = webdriver.Chrome(options=self.option)
        self.browser.maximize_window()
        self.wait = WebDriverWait(self.browser, 5)
        self.wait_1 = WebDriverWait(self.browser, 1)

    def work_qczj_detail(self, cars_data, city):
        error_data = []

        cars_detail_data = []
        for item in cars_data:
            try:
                self.browser.get(item["详情页面"])
                level = self.browser.find_element(By.XPATH,
                                                  '//div[@class="spec-param"]/div[@class="spec-content"]/div/div[1]/p').text
            except:
                print("Unexpected error:", traceback.format_exc())
                error_data.append(item)
                continue

            try:
                self.wait_1.until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@class="dealer-shop-more"]/a')))
                try:
                    more_info_url = self.browser.find_element(By.XPATH,
                                                              '//div[@class="dealer-shop-more"]/a').get_attribute(
                        'href')
                    self.browser.get(more_info_url)
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//div[@class="wiki-pagination-btn"]/a')))
                    pages = self.browser.find_elements(By.XPATH,
                                                       '//div[@class="wiki-pagination-btn"]/a')

                    self.browser.execute_script("arguments[0].scrollIntoView();", pages[0])
                    last_name = None
                    for page_cnt in range(len(pages)):
                        if page_cnt != 0:
                            self.browser.find_element(By.XPATH, "//div[@class='wiki-pagination-next']").click()
                            all_cars = self.browser.find_elements(By.XPATH,
                                                                  '//div[@id="dealerList"]/div[@class="item active"]/div/div[@class="dealer-shop"]')
                            cur_name = all_cars[0].find_element(By.XPATH, './div[@class="shop-title"]/a').text
                            while cur_name == last_name:
                                try:
                                    all_cars = self.browser.find_elements(By.XPATH,
                                                                      '//div[@id="dealerList"]/div[@class="item active"]/div/div[@class="dealer-shop"]')
                                    cur_name = all_cars[0].find_element(By.XPATH, './div[@class="shop-title"]/a').text
                                except:
                                    all_cars = self.browser.find_elements(By.XPATH,
                                                                          '//div[@id="dealerList"]/div[@class="item active"]/div/div[@class="dealer-shop"]')
                                    cur_name = all_cars[0].find_element(By.XPATH, './div[@class="shop-title"]/a').text
                        all_cars = self.browser.find_elements(By.XPATH,
                                                              '//div[@id="dealerList"]/div[@class="item active"]/div/div[@class="dealer-shop"]')
                        last_name = all_cars[0].find_element(By.XPATH, './div[@class="shop-title"]/a').text
                        for car in all_cars:
                            shop_name = car.find_element(By.XPATH, './div[@class="shop-title"]/a').text
                            shop_price = car.find_element(By.XPATH,
                                                          './div[@class="shop-price"]/span[@class="price"]/em').text
                            shop_address = car.find_element(By.XPATH,
                                                            './div[@class="shop-detail"]/div[@class="shop-info"]/p[@class="shop-address"]/span').text
                            cars_detail_data.append(
                                {"圈定车系名称": item["车系"], "圈定城市": city, "车型之家名称": item["车型"],
                                 "汽车之家-经销商报价": item["经销商报价"],
                                 "汽车之家-厂商指导价": item["指导价"],
                                 "汽车之家-门店名称": shop_name, "汽车之家-门店报价": shop_price,
                                 "汽车之家-门店标签": level,
                                 "汽车之家-地址信息": shop_address, "详情页面": item["详情页面"]})

                except:
                    print("Unexpected error:", traceback.format_exc())
                    error_data.append(item)
                    continue

            except:
                try:
                    all_cars = self.browser.find_elements(By.XPATH,
                                                          '//div[@class="dealer-list"]/div[@class="dealer-shop"]')
                    for car in all_cars:
                        shop_name = car.find_element(By.XPATH, './div[@class="shop-title"]/a').text
                        shop_price = car.find_element(By.XPATH,
                                                      './div[@class="shop-price"]/span[@class="price"]/em').text
                        shop_address = car.find_element(By.XPATH,
                                                        './div[@class="shop-detail"]/div[@class="shop-info"]/p[@class="shop-address"]/span').text
                        cars_detail_data.append(
                            {"圈定车系名称": item["车系"], "圈定城市": city, "车型之家名称": item["车型"],
                             "汽车之家-经销商报价": item["经销商报价"], "汽车之家-厂商指导价": item["指导价"],
                             "汽车之家-门店名称": shop_name, "汽车之家-门店报价": shop_price,
                             "汽车之家-门店标签": level,
                             "汽车之家-地址信息": shop_address, "详情页面": item["详情页面"]})
                except:
                    print("Unexpected error:", traceback.format_exc())
                    error_data.append(item)
                    continue
        return cars_detail_data, error_data

    def work_qczj(self, links, cities=None, prefix=""):
        if cities is None:
            cities = ["北京"]
        first_run = True
        for city in tqdm(cities[:1]):
            self.get_new_browser()
            change_city = True
            cars_detail_data = []
            error_data = []
            error_link = []
            for link in tqdm(links[48:]):
                cars_data = []
                try:
                    self.browser.get(link)
                    if first_run:
                        try:
                            self.wait.until(
                                EC.element_to_be_clickable((By.XPATH, '//span[@class="inquiry_layer_close"]'))).click()
                        except:
                            pass
                        first_run = False
                    if change_city:
                        self.browser.find_element(By.XPATH, '//p[@class="promotion-citychange"]/a').click()
                        send_area = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, '//input[@id="auto-citypicker-txt"]')))
                        send_area.send_keys(f"{city}")
                        self.browser.find_element(By.XPATH, '//ul[@id="auto-citypicker-tip-list"]/li/a').click()
                        self.browser.refresh()
                        change_city = False

                    all_info = self.browser.find_element(By.XPATH, '//div[@class="series-list"]')
                    name = all_info.find_element(By.XPATH, './div[@class="athm-title"]/div[1]').text
                    different_mode = all_info.find_elements(By.XPATH,
                                                            './div[@class="series-content"]/div[@id="specWrap-2"]/dl')
                    for mode in different_mode:
                        all_car = mode.find_elements(By.XPATH, './dd')
                        for car in all_car:
                            car_name = car.find_element(By.XPATH, './div[@class="spec-name"]/div/p[1]/a').text
                            url = car.find_element(By.XPATH, './div[@class="spec-name"]/div/p[1]/a').get_attribute(
                                "href")
                            zdj = car.find_element(By.XPATH, './div[@class="spec-guidance"]').text
                            jxs = car.find_element(By.XPATH, './div[@class="spec-lowest"]').text.replace("起", "")
                            if car_name != '':
                                cars_data.append(
                                    {"车系": name, "车型": car_name, "指导价": zdj, "经销商报价": jxs, "详情页面": url})
                except:
                    # 打印详细信息
                    print("Unexpected error:", traceback.format_exc())
                    error_link.append(link)
                    continue

                cars_detail_data_sub, error_data_sub = self.work_qczj_detail(cars_data, city)
                cars_detail_data.extend(cars_detail_data_sub)
                error_data.extend(error_data_sub)

            with open(f'log/error_{city}{prefix}.pkl', 'wb') as f:
                pickle.dump(error_data, f)
            with open(f'log/error_link_{city}{prefix}.pkl', 'wb') as f:
                pickle.dump(error_link, f)

            # 使用pandas保存或处理数据
            df = pd.DataFrame(cars_detail_data)
            df.to_excel(f"result/cars_detail_qczj_{city}{prefix}.xlsx", index=False)

    def work_dcd_detail(self, cars_data, city):
        error_data = []
        cars_detail_data = []
        for item in cars_data:
            try:
                self.browser.get(item["详情页面"])
                try:
                    geneal_info = self.browser.find_element(By.XPATH, '//div[@class="tw-col-span-2 tw-relative"]')
                    level = geneal_info.find_element(By.XPATH, './p/span[1]').text

                except:
                    level = ""

                footer_bar = self.browser.find_elements(By.XPATH, '//ul[@class="jsx-1325911405 tw-flex"]/li')
                if len(footer_bar):
                    next_btn = footer_bar[-1]
                    pages = int(footer_bar[-2].text)
                    for page in range(pages):
                        if page != 0:
                            next_btn.click()
                        all_info = self.browser.find_element(By.XPATH, '//div[@id="newCar"]')
                        cars = all_info.find_elements(By.XPATH, './section/ul/li')
                        for car in cars:
                            shop_name = car.find_element(By.XPATH, './div[1]/div[1]/div').text
                            shop_price = car.find_element(By.XPATH, './div[1]/div[2]').text
                            shop_address = car.find_element(By.XPATH, './div[3]/div[2]/div[1]/span/div').text
                            cars_detail_data.append(
                                {"圈定车系名称": item["车系"], "圈定城市": city, "车型懂车帝名称": item["车型"],
                                 "懂车帝-经销商报价": item["经销商报价"], "懂车帝-厂商指导价": item["指导价"],
                                 "懂车帝-门店名称": shop_name, "懂车帝-门店报价": shop_price,
                                 "懂车帝-地址信息": shop_address,
                                 "懂车帝-门店标签": level, "详情页面": item["详情页面"]})
                else:
                    try:
                        all_info = self.browser.find_element(By.XPATH, '//div[@id="newCar"]')
                    except:
                        continue
                    cars = all_info.find_elements(By.XPATH, './section/ul/li')
                    for car in cars:
                        shop_name = car.find_element(By.XPATH, './div[1]/div[1]/div').text
                        shop_price = car.find_element(By.XPATH, './div[1]/div[2]').text
                        shop_address = car.find_element(By.XPATH, './div[3]/div[2]/div[1]/span/div').text
                        cars_detail_data.append(
                            {"圈定车系名称": item["车系"], "圈定城市": city, "车型懂车帝名称": item["车型"],
                             "懂车帝-经销商报价": item["经销商报价"], "懂车帝-厂商指导价": item["指导价"],
                             "懂车帝-门店名称": shop_name, "懂车帝-门店报价": shop_price,
                             "懂车帝-地址信息": shop_address,
                             "懂车帝-门店标签": level, "详情页面": item["详情页面"]})

            except:
                print("Unexpected error:", traceback.format_exc())
                error_data.append(item)
                continue
        return cars_detail_data, error_data

    def work_dcd(self, links, cities=None, prefix=""):
        if cities is None:
            cities = ["北京"]
        first_run = True
        for city in tqdm(cities):
            cars_detail_data = []
            error_data = []
            error_link = []
            cnt = 0
            for link in tqdm(links):
                cars_data = []
                # url = "https://www.dongchedi.com/auto/series/" + str(link) + "?city=" + city

                self.browser.get(link)
                if first_run:
                    first_letter = get_initials(city)[0]

                    select_city_button = self.wait.until(
                        EC.element_to_be_clickable(
                            (By.XPATH, '//div[@class="tw-relative new-header_city__2HpkN"]/button')))
                    select_city_button.click()

                    letter_area = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//section[@class="jsx-3656537516"]/div/span['
                                                              f'@data-letter="{first_letter}"]')))
                    letter_area.click()

                    target_city = self.wait.until(
                        EC.element_to_be_clickable(
                            (By.XPATH, f"//section[@class='jsx-4165276750 city-section-wrap']/div["
                                       f"@data-letter='{first_letter}']/span["
                                       f"contains(text(), '{city}')]")))
                    target_city.click()
                    first_run = False

                try:
                    # 等待“点击显示更多”的按钮出现，并点击它
                    load_more_button = self.wait_1.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '点击展示更多')]")))
                    ActionChains(self.browser).move_to_element(load_more_button).click(load_more_button).perform()
                except:
                    pass

                # 爬取数据
                try:
                    all_info = self.browser.find_element(By.XPATH, '//div[@id="carModels"]')
                    name = all_info.find_element(By.XPATH, './div[1]/div[1]/h2/span').text.split('·')[0]
                    different_mode_list = all_info.find_elements(By.XPATH, './div[1]/ul/li')
                    for mode in different_mode_list:
                        divs_with_data_log_click = mode.find_elements(By.XPATH, './div[@data-log-click]')
                        for car in divs_with_data_log_click:
                            child_divs = car.find_elements(By.XPATH, './div')
                            car_name = child_divs[0].find_element(By.XPATH, './div/div[1]/a').text
                            detail_url = child_divs[0].find_element(By.XPATH, './div/div[1]/a').get_attribute("href")
                            zdj = child_divs[1].text  # 指导价
                            jxs = child_divs[2].text  # 经销商报价
                            if car_name != '':
                                cars_data.append(
                                    {"车系": name, "车型": car_name, "指导价": zdj, "经销商报价": jxs,
                                     "详情页面": detail_url})
                except:
                    # 打印详细信息
                    print("Unexpected error:", traceback.format_exc())
                    error_link.append(link)
                    continue

                cars_detail_data_sub, error_data_sub = self.work_dcd_detail(cars_data, city)
                cars_detail_data.extend(cars_detail_data_sub)
                error_data.extend(error_data_sub)

            df = pd.DataFrame(cars_detail_data)
            df.to_excel(f"result/dcd/cars_detail_dcd_{city}{prefix}.xlsx", index=False)

            with open(f'log/dcd/error_{city}{prefix}.pkl', 'wb') as f:
                pickle.dump(error_data, f)

            with open(f'log/dcd/error_link_{city}{prefix}.pkl', 'wb') as f:
                pickle.dump(error_link, f)

    def rerun_qczj(self):
        with open('log/error_link_北京.pkl', 'rb') as f:
            error_links = pickle.load(f)
        # self.work_qczj(error_links, ["北京"], prefix="_rerun")


        print("Rerun 1 done")
        with open('log/error_北京.pkl', 'rb') as f:
            cars_data = pickle.load(f)
        cars_detail_data, error_data = self.work_qczj_detail(cars_data, "北京")

        with open(f'log/error_北京_rerun_2.pkl', 'wb') as f:
            pickle.dump(error_data, f)

        df = pd.DataFrame(cars_detail_data)
        df.to_excel(f"result/cars_detail_qczj_北京_rerun_2.xlsx", index=False)

    def rerun_dcd(self):
        with open('log/dcd/error_link_北京.pkl', 'rb') as f:
            error_links = pickle.load(f)
        self.work_dcd(error_links, ["北京"], prefix="_rerun")

        with open('log/dcd/error_北京.pkl', 'rb') as f:
            cars_data = pickle.load(f)
        cars_detail_data, error_data = self.work_dcd_detail(cars_data, "北京")

        with open(f'log/dcd/error_北京_rerun_2.pkl', 'wb') as f:
            pickle.dump(error_data, f)

        df = pd.DataFrame(cars_detail_data)
        df.to_excel(f"result/dcd/cars_detail_dcd_北京_rerun_2.xlsx", index=False)

        self.concat_dcd_error()

    def concat_dcd_error(self):
        origin_data = pd.read_excel("result/dcd/cars_detail_dcd_北京.xlsx")
        error_data = pd.read_excel("result/dcd/cars_detail_dcd_北京_rerun.xlsx")
        error_data_2 = pd.read_excel("result/dcd/cars_detail_dcd_北京_rerun_2.xlsx")

        origin_data.set_index(['圈定车系名称', '车型懂车帝名称', '懂车帝-门店名称'], inplace=True)
        if len(error_data):
            error_data.set_index(['圈定车系名称', '车型懂车帝名称', '懂车帝-门店名称'], inplace=True)
            origin_data.update(error_data)

        if len(error_data_2):
            error_data_2.set_index(['圈定车系名称', '车型懂车帝名称', '懂车帝-门店名称'], inplace=True)
            origin_data.update(error_data_2)

        final_df = pd.concat([origin_data, error_data, error_data_2], axis=0).drop_duplicates(keep='last').reset_index()
        final_df.to_excel("result/dcd/final.xlsx", index=False)

    def process_min_msrp_data(self, data, model_name_column, msrp_column, store_name_column, jxs_column):
        # Group by car model and find the minimum MSRP for each
        min_msrp_per_model = data.groupby(['车系_车型名称', '圈定城市'])[msrp_column].min().reset_index()

        # Merge to get only the rows with the minimum MSRP
        min_msrp_data = pd.merge(data, min_msrp_per_model, on=['车系_车型名称', '圈定城市', msrp_column])

        # Group by car model and city again and aggregate store names into a list
        result = min_msrp_data.groupby(['车系_车型名称', '圈定城市']).agg({
            model_name_column: 'first',  # Keep the model name
            msrp_column: 'first',  # Keep the minimum MSRP
            store_name_column: lambda x: list(x),  # Aggregate store names into a list
            jxs_column: 'first'
        }).reset_index()

        return result

    def concat(self, dcd_path, qczj_path):
        dcd_df = pd.read_excel(dcd_path)
        qczj_df = pd.read_excel(qczj_path)

        dcd_df['圈定车系名称'] = dcd_df['圈定车系名称'].str.replace("PHEV", "新能源")
        qczj_df['圈定车系名称'] = qczj_df['圈定车系名称'].str.replace("PHEV", "新能源")

        dcd_df['处理后车型名称'] = dcd_df['车型懂车帝名称'].apply(process_car_model_names)
        qczj_df['处理后车型名称'] = qczj_df['车型之家名称'].apply(process_car_model_names)

        dcd_df['车系_车型名称'] = (dcd_df['圈定车系名称'] + '|' + dcd_df['处理后车型名称'])
        qczj_df['车系_车型名称'] = (qczj_df['圈定车系名称'] + '|' + qczj_df['处理后车型名称'])

        # Convert MSRP columns to float for both datasets
        # dcd_df['懂车帝-厂商指导价'] = dcd_df['懂车帝-厂商指导价'].str.replace('万', '').astype(float)
        # qczj_df['汽车之家-厂商指导价'] = qczj_df['汽车之家-厂商指导价'].str.replace('万', '').astype(float)

        dcd_msrp_result = self.process_min_msrp_data(dcd_df, '车型懂车帝名称', '懂车帝-门店报价', '懂车帝-门店名称',
                                                     '懂车帝-经销商报价')
        qczj_msrp_result = self.process_min_msrp_data(qczj_df, '车型之家名称', '汽车之家-门店报价', '汽车之家-门店名称',
                                                      '汽车之家-经销商报价')

        merged_msrp_result = pd.merge(
            dcd_msrp_result,
            qczj_msrp_result,
            on=['车系_车型名称', '圈定城市'],
            suffixes=('_懂车帝', '_汽车之家'),
            how='outer'
        )

        merged_msrp_result['车系名'] = merged_msrp_result['车系_车型名称'].str.split('|').str[0]
        merged_msrp_result['车型名'] = merged_msrp_result['车系_车型名称'].str.split('|').str[1]
        merged_msrp_result.drop(['车系_车型名称'], axis=1, inplace=True)
        cols_to_move = ['车系名', '车型名']
        merged_msrp_result = merged_msrp_result[
            cols_to_move + [col for col in merged_msrp_result.columns if col not in cols_to_move]]

        merged_msrp_result.to_excel("result/merged_result.xlsx", index=False)


if __name__ == '__main__':
    r = Crawler()
    # r.run()
    # r.rerun_qczj()
    r.concat("result/dcd/cars_detail_dcd_北京.xlsx", "result/cars_detail_qczj_北京_3.xlsx")
