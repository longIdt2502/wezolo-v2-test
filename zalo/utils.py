import json
import os

import requests

from common.pref_keys import PrefKeys
from user.models import WeZoloAppConfig

url_zalo_openai = 'https://openapi.zalo.me'
url_list_user = f'{url_zalo_openai}/v3.0/oa/user/getlist'
url_detail_user = f'{url_zalo_openai}/v3.0/oa/user/detail'
url_list_message = f'{url_zalo_openai}/v2.0/oa/conversation'


def get_token_from_code(code, code_verifier):
    url = "https://oauth.zaloapp.com/v4/oa/access_token"

    app_id = os.environ.get(PrefKeys.ZALO_APP_ID)
    secret_key = os.environ.get(PrefKeys.ZALO_APP_SECRET)
    payload = f'code={code}&app_id={app_id}&grant_type=authorization_code&code_verifier={code_verifier}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'secret_key': secret_key
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json()


def get_token_from_refresh(refresh_token: str) -> [str, str]:
    url = "https://oauth.zaloapp.com/v4/oa/access_token"

    app_id = os.environ.get(PrefKeys.ZALO_APP_ID)
    secret_key = os.environ.get(PrefKeys.ZALO_APP_SECRET)
    payload = f'app_id={app_id}&grant_type=refresh_token&refresh_token={refresh_token}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'secret_key': secret_key
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response = response.json()
    new_access = response.get('access_token')
    new_refresh = response.get('refresh_token')
    if new_refresh and new_refresh:
        return new_access, new_refresh
    return None, None


def get_oa_info(access_token, refresh_token):
    # example json response => example/zalo_example_response.json => get_oa_info
    url = 'https://openapi.zalo.me/v2.0/oa/getoa'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'access_token': access_token
    }
    response = requests.request("GET", url, headers=headers)
    return response.json()


def oa_list_customer(access_token, offset):
    # example json response => example/zalo_example_response.json => get_list_user
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'access_token': access_token
    }
    params = {
        "data": f'{{"offset":{offset},"count":50}}'
    }
    response = requests.request("GET", url_list_user, headers=headers, params=params)
    return response.json()


def oa_detail_customer(access_token, user_id):
    # example json response => example/zalo_example_response.json => get_list_user
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'access_token': access_token
    }
    params = {
        "data": f'{{"user_id": {user_id}}}'
    }
    response = requests.request("GET", url_detail_user, headers=headers, params=params)
    return response.json()


def oa_list_message_in_conversation(access_token, user_id, offset):
    # example json response => example/zalo_example_response.json => get_list_user
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'access_token': access_token
    }
    params = {"data": f'{{"user_id": {user_id}, "count": 10, "offset": {offset}}}'}
    response = requests.request("GET", url_list_message, headers=headers, params=params)
    return response.json()


def send_zns_otp(otp: str, phone: str):
    """
    Do ZNS OTP sẽ được gửi từ OA của WEZOLO nên biến access_token sẽ được lấy từ môi trường
    """
    zalo_app_id = os.environ.get('ZALO_APP_ID')
    config = WeZoloAppConfig.objects.get(zalo_app_id=zalo_app_id)
    access_token = config.access_token
    refresh_token = config.refresh_token
    headers = {
        'Content-Type': 'application/json',
        'access_token': access_token
    }
    payload = json.dumps({
        "phone": convert_phone(phone),
        "template_id": "385354",
        "template_data": {
            "otp": otp
         },
        "tracking_id": "tracking_id"
    })
    url = os.environ.get('ZALO_ZNS_URL')
    response = requests.post(url, headers=headers, data=payload)
    response = response.json()
    if response.get('error') == -124:
        new_access_token, new_refresh_token = get_token_from_refresh(refresh_token)
        if new_access_token and new_refresh_token:
            config.access_token = new_access_token
            config.refresh_token = new_refresh_token
            config.save()
            return send_zns_otp(otp, phone)
    return response


def convert_phone(phone: str) -> str:
    if phone.startswith("84"):
        return phone

    elif phone.startswith("0"):
        return "84" + phone[1:]

    return phone
