from decimal import Decimal
import requests
from django.core.cache import cache

BNB_CACHE_KEY = "bnb_inr_price"
BNB_CACHE_TTL = 30  # seconds (VERY IMPORTANT)

def inr_to_bnb(inr_amount: Decimal) -> Decimal:
    price = cache.get(BNB_CACHE_KEY)

    if not price:
        res = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "binancecoin", "vs_currencies": "inr"},
            timeout=10
        )

        data = res.json()
        if "binancecoin" not in data:
            raise ValueError("BNB price unavailable")

        price = Decimal(str(data["binancecoin"]["inr"]))
        cache.set(BNB_CACHE_KEY, price, BNB_CACHE_TTL)

    return (inr_amount / price).quantize(Decimal("0.00000001"))
