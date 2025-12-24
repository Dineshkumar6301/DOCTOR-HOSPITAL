from web3 import Web3
from django.conf import settings

def confirm_transaction(tx_hash):
    w3 = Web3(Web3.HTTPProvider(settings.WEB3_RPC_URL))

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except Exception:
        return False

    if not receipt or receipt.status != 1:
        return False

    tx = w3.eth.get_transaction(tx_hash)

    if Web3.to_checksum_address(tx["to"]) != Web3.to_checksum_address(
        settings.SERVICE_WALLET_ADDRESS
    ):
        return False

    if w3.eth.chain_id != settings.CHAIN_ID:
        return False

    return True
