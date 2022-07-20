import csv
from core.models import MarketQuote

def parse_value(v):
    try:
        value = int(v)
    except:
        value = None
    try:
        float(v)
    except:
        value = None
    try:
        value = str(v)
    except:
        value = None
    
    if value:
        return value
    else:
        return None

def change(exchange_token,new_price,old_price_dict):
    if exchange_token in old_price_dict:
        return float(new_price) - float(old_price_dict[exchange_token])
    else:
        return 0

def injest_market_data():

    MarketQuote.objects.all().delete()

    with open('market_data.csv') as f:
        market_data = [{k: parse_value(v) for k, v in row.items()}
            for row in csv.DictReader(f, skipinitialspace=True)]
        market_data = [x for x in market_data if x["exchange"] in  ["NSE","BSE"] and x["name"]]
        old_price_dict = {x["exchange_token"] : x["price"] for x in market_data}

        print(market_data[0])

    obj_list = [MarketQuote(**data,data_from="yesterday") for data in market_data]
    objs = MarketQuote.objects.bulk_create(obj_list)

    with open('market_data_today.csv') as f:
        market_data_today = [{k: parse_value(v) for k, v in row.items()}
            for row in csv.DictReader(f, skipinitialspace=True)]
        market_data_today = [x for x in market_data_today if x["exchange"] in  ["NSE","BSE"] and x["name"]]
        market_data_today = [{**x,"change":change(x["exchange_token"],x["price"],old_price_dict)} for x in market_data_today]

    obj_list = [MarketQuote(**data,data_from="today") for data in market_data]
    objs = MarketQuote.objects.bulk_create(obj_list)
