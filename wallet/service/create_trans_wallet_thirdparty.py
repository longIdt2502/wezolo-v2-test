import os
import requests
import jwt

def create_transaction_third_party(wallet_trans, metadata):
    from wallet.models import WalletTransaction
    wallet = wallet_trans.wallet
    wallet_url = os.environ.get('WALLET_URL')
    url = f"{wallet_url}/v1/api/internal/wallets/transactions/"
    amount = wallet_trans.total_amount
    if wallet_trans.type not in [
        WalletTransaction.Type.DEPOSIT,
        WalletTransaction.Type.IN_PACKAGE,
        WalletTransaction.Type.IN_ZNS,
        WalletTransaction.Type.IN_MESSAGE,
    ]:
        amount = -amount
    payload = {
        "amount": amount,
        "metadata": metadata
    }
    if not wallet.wallet_authorization:
        public_key_bytes = wallet.private_key.encode()
        payload = {"uid": wallet.wallet_uid}
        encode_string = jwt.encode(payload, key=public_key_bytes, algorithm='RS256')
        wallet.wallet_authorization = encode_string
        wallet.save()
    headers = {
        'Client-Code': wallet.wallet_uid,
        'Access-Token': wallet.wallet_authorization
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    except Exception:
        return {}