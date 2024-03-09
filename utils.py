import re

import pandas as pd


def replace_phev(series_name):
    return series_name.replace("PHEV", "新能源")


def process_car_model_names(model_name):
    model_name = model_name.replace("改款", "")  # Ignore "改款"
    model_name = re.sub(r'\d\.\dT', '', model_name)  # Ignore "*T" patterns like "1.5T"
    model_name = model_name.replace("版", "型")  # Treat "版" and "型" as the same
    model_name = ''.join(model_name.split())  # Remove all spaces
    return model_name


if __name__ == '__main__':
    data1 = pd.read_excel("result/cars_detail_qczj_北京.xlsx")
    data2 = pd.read_excel("result/cars_detail_qczj_北京_2.xlsx")

    data = pd.concat([data1, data2], ignore_index=True)
    data = data.drop_duplicates(subset=["车型之家名称", "汽车之家-门店名称"], keep="first")
    data.to_excel("result/cars_detail_qczj_北京_3.xlsx", index=False)
