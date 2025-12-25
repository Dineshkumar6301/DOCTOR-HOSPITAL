from decimal import Decimal
import requests

def inr_to_bnb(inr_amount: Decimal) -> Decimal:
    """
    Convert INR → BNB using Binance official price
    """

    # BNB/USDT price
    price_res = requests.get(
        "https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT",
        timeout=10
    )
    price_res.raise_for_status()
    bnb_usdt = Decimal(price_res.json()["price"])

    # USDT/INR price
    inr_res = requests.get(
        "https://api.binance.com/api/v3/ticker/price?symbol=USDTINR",
        timeout=10
    )
    inr_res.raise_for_status()
    usdt_inr = Decimal(inr_res.json()["price"])

    bnb_inr = bnb_usdt * usdt_inr

    return (inr_amount / bnb_inr).quantize(Decimal("0.00000001"))
