from payos import PayOS
import os

PAY_OS_CLIENT_ID = '5a2c1b39-1217-442e-b933-20720bd0531c'
PAY_OS_API_KEY = '8a0eeaf0-34ff-45b2-bed5-93008bf27441'
PAY_OS_CHECK_SUM_KEY = 'e9ef4634856e3175561da56eb63c7aba1621760aa84fe073629420f756a76174'

payOS = PayOS(client_id=PAY_OS_CLIENT_ID, api_key=PAY_OS_API_KEY, checksum_key=PAY_OS_CHECK_SUM_KEY)
