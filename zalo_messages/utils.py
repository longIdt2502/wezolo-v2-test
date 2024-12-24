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
        if oa:
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
        if oa:
            response = send_request_info(oa, user_id)
    return response


def send_zns(oa, template_id, content, phone, tracking_id, mode):
    if not oa.activate:
        return None
    headers = {
        'access_token': oa.access_token,
    }
    if phone.startswith('0'):
        phone = phone.replace('0', '84', 1)
    url = os.environ.get("ZALO_ZNS_URL")
    payload = {
        "phone": phone,
        "template_id": template_id,
        "template_data": content,
        "tracking_id": tracking_id
    }
    payload = json.dumps(
        {
            "phone": phone,
            "template_id": template_id,
            "template_data": content,
            "tracking_id": tracking_id
        })
    if mode == 'development':
        payload['mode'] = mode
    payload = json.dumps(payload)
    response = requests.request("POST", url, headers=headers, data=payload)
    # log = ZaloOaLog()
    # log.source = phone
    # log.request_data = json.loads(payload)
    # log.oa = oa.oa_id
    # log.data = response.json()
    # log.type = "zns"
    # log.mode = "production"
    # log.save()
    return response.json()