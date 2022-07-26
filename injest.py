import json


def get_stocks_data():

    with open("zerodha_stocks_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)["data"]

    stocks_data = []
    for k, v in data.items():
        exchange, symbol = k.split(":")
        instrument_token = v["instrument_token"]
        price = v["average_price"]
        stocks_data.append(
            {
                "instrument_token": instrument_token,
                "trading_symbol": symbol,
                "price": price,
                "exchange": exchange,
            }
        )

    return stocks_data