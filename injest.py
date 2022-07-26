import json


def get_stocks_data():

    with open("final_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data