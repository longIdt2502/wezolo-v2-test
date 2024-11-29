from payos import PayOS
import os

client_id = os.environ.get('PAY_OS_CLIENT_ID', '')
api_key = os.environ.get('PAY_OS_API_KEY', '')
checksum_key = os.environ.get('PAY_OS_CHECK_SUM_KEY', '')

payOS = PayOS(client_id=client_id, api_key=api_key, checksum_key=checksum_key)
