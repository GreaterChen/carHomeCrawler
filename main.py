import requests
import parsel

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/116.0.0.0 Safari/537.36",
           "Accept": "application/json;charset=utf-8"
           }
url = "https://www.dongchedi.com/auto/series/5820"

response = requests.get(url=url, headers=headers)
selector = parsel.Selector(response.text)

car = selector.css('div#carModels')

ul = selector.xpath('//div[@id="carModels"]/div[1]/ul')
divs_with_data_log_click = ul.xpath('./li[1]//div[@data-log-click]')
for car in divs_with_data_log_click:
    child_divs = car.xpath('./div')
    zdj = child_divs[1].xpath('.//text()').getall()[0]
    print("指导价:", zdj)
    jxs = child_divs[2].xpath('.//text()').getall()[0]
    print("经销商报价:", jxs)

