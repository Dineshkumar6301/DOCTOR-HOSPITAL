from web3 import Web3
from django.conf import settings

def process_refund(booking, admin_private_key):
    w3 = Web3(Web3.HTTPProvider(settings.WEB3_RPC_URL))

    account = w3.eth.account.from_key(admin_private_key)

    tx = {
        "to": booking.user.wallet_address,
        "value": w3.to_wei(booking.crypto_amount, "ether"),
        "gas": 21000,
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": settings.CHAIN_ID
    }

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

    booking.status = "REFUNDED"
    booking.save()

    return tx_hash.hex()
