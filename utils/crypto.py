import requests
from decimal import Decimal

def inr_to_bnb(inr_amount):
    res = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": "binancecoin", "vs_currencies": "inr"},
        timeout=10
    )
    price = Decimal(res.json()["binancecoin"]["inr"])
    return (Decimal(inr_amount) / price).quantize(Decimal("0.00000001"))
