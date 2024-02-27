import re


def replace_phev(series_name):
    return series_name.replace("PHEV", "新能源")


def process_car_model_names(model_name):
    model_name = model_name.replace("改款", "")  # Ignore "改款"
    model_name = re.sub(r'\d\.\dT', '', model_name)  # Ignore "*T" patterns like "1.5T"
    model_name = model_name.replace("版", "型")  # Treat "版" and "型" as the same
    model_name = ''.join(model_name.split())  # Remove all spaces
    return model_name


if __name__ == '__main__':
    str = "2024款 1.5T P300e 插电式电动混合版"
    print(process_model_name(str))
