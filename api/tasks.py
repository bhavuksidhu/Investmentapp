import requests
from celery import shared_task
from core.models import (
    InvestmentInsight,
    MarketQuote,
    Stock,
    User,
    UserSubscription,
    ZerodhaData,
)
from core.utils import send_notification
from django.utils import timezone


@shared_task
def update_stock_prices():
    latest_zerodha_data: ZerodhaData = ZerodhaData.objects.first()

    access_token = latest_zerodha_data.access_token
    api_key = latest_zerodha_data.api_key
    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {api_key}:{access_token}",
    }

    stocks = MarketQuote.objects.values_list("trading_symbol")
    stocks = [_[0] for _ in stocks]
    query_string = ""
    for stock in stocks:
        query_string = query_string + f"&i=NSE:{stock}"

    query_string = query_string.strip("&")
    response = requests.get(
        f"https://api.kite.trade/quote?{query_string}", headers=headers
    )

    if response.status_code == 200:
        for k, v in response.json().items():
            exchange, symbol = k.split(":")
            price = v["average_price"]

            try:
                market_quote: MarketQuote = MarketQuote.objects.get(
                    trading_symbol=symbol
                )
                old_price = market_quote.price
                change = old_price - price
                market_quote.price = price
                market_quote.change = change
                market_quote.save()
            except MarketQuote.DoesNotExist:
                print(f"Failed to update MarketQuote for {symbol}")
    else:
        print("Unable to refresh stocks data from Zerodha")


@shared_task
def calculate_portfolio_value():
    market_quotes = MarketQuote.objects.all().values()
    for user in User.objects.all():
        transactions = user.transactions.filter(verified=True)
        if not transactions:
            continue

        transaction_data = {}
        for transaction in transactions:
            symbol = transaction.trading_symbol
            if symbol in transaction_data:
                if transaction.transaction_type == "SELL":
                    transaction_data[symbol]["quantity"] -= transaction.quantity
                else:
                    transaction_data[symbol]["quantity"] += transaction.quantity
            else:
                transaction_data[symbol] = {
                    "trading_symbol": symbol,
                    "quantity": 0,
                }
                if transaction.transaction_type == "SELL":
                    transaction_data[symbol]["quantity"] = -transaction.quantity
                else:
                    transaction_data[symbol]["quantity"] = transaction.quantity

        portfolio_list = [v for k, v in transaction_data.items() if v["quantity"] != 0]

        portfolio_value = 0
        for entry in portfolio_list:
            trading_symbol = entry["trading_symbol"]
            price = [
                x["price"]
                for x in market_quotes
                if x["trading_symbol"] == trading_symbol
            ]
            if not price:
                continue
            price = price[0]
            portfolio_value += price * entry["quantity"]

        InvestmentInsight.objects.create(user=user, value=portfolio_value)


@shared_task
def deactivate_subscriptions():
    current_datetime = timezone.now()
    expired_subscriptions = UserSubscription.objects.filter(
        date_to__lte=current_datetime
    )

    # Mark expired subscriptions as inactive
    UserSubscription.objects.filter(date_to__lte=current_datetime).update(active=False)

    # Send notifictaions
    for subscription in expired_subscriptions:
        user_settings = subscription.user.settings

        head = f"Subscription Expired!"
        body = f" Alert! Your subscription has ended. Subscribe again if you wish to continue with premium service."

        registration_id = user_settings.device_token
        if registration_id:
            send_notification(
                registration_id=registration_id, message_title=head, message_body=body
            )
        else:
            print("No device_token exist for user, aborting notification service.")

@shared_task
def temp():
    return "Working!"