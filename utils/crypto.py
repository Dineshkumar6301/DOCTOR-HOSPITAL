from decimal import Decimal
import requests
from django.core.cache import cache

BNB_CACHE_KEY = "bnb_inr_price"
BNB_CACHE_TTL = 30  # seconds

# SAFE fallback (update once manually if needed)
FALLBACK_BNB_INR = Decimal("25000")  # approx value

def inr_to_bnb(inr_amount: Decimal) -> Decimal:
    price = cache.get(BNB_CACHE_KEY)

    if not price:
        try:
            res = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "binancecoin", "vs_currencies": "inr"},
                timeout=10
            )
            data = res.json()

            if "binancecoin" in data:
                price = Decimal(str(data["binancecoin"]["inr"]))
                cache.set(BNB_CACHE_KEY, price, BNB_CACHE_TTL)
            else:
                # API responded but no price
                price = cache.get(BNB_CACHE_KEY) or FALLBACK_BNB_INR

        except Exception:
            # Network / timeout / block
            price = cache.get(BNB_CACHE_KEY) or FALLBACK_BNB_INR

    return (inr_amount / price).quantize(Decimal("0.00000001"))
