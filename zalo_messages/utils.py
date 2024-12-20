import json
import os

import requests

from common.zalo.request import update_token_oa
from zalo.models import ZaloOA

url = "https://openapi.zalo.me/v3.0/oa/message/cs"

def send_message_text(oa: ZaloOA, user_id, message):
    payload = json.dumps({
        "recipient": {
            "user_id": user_id
        },
        "message": message
    })
    headers = {
        'Content-Type': 'application/json',
        'access_token': oa.access_token
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response = response.json()
    if response.get('error') == -216:
        oa = update_token_oa(oa.uid_zalo_oa)
        response = send_message_text(oa, user_id, message)

    return response


def send_request_info(oa: ZaloOA, user_id):
    payload = json.dumps({
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "attachment": {
            "type": "template",
            "payload": {
                "template_type": "request_user_info",
                "elements": [
                {
                    "title": "WeZolo thông báo",
                    "subtitle": "Hãy chia sẻ thông tin của mình",
                    "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR1pb-qVaXaLJyJJAWV6jsx1yHQ-0iZS_PzAg&s"
                }
                ]
            }
            }
        }
    })
    headers = {
        'Content-Type': 'application/json',
        'access_token': oa.access_token
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response = response.json()
    if response.get('error') == -216:
        oa = update_token_oa(oa.uid_zalo_oa)
        response = send_request_info(oa, user_id)
    return response
