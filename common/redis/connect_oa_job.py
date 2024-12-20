from datetime import datetime, timedelta
import json
import os

import django_rq

import requests
from asgiref.sync import async_to_sync

from common.pref_keys import PrefKeys
from zalo.utils import oa_list_customer, oa_detail_customer, oa_list_message_in_conversation
from channels.layers import get_channel_layer


domain = os.environ.get(PrefKeys.DOMAIN_URL)


def list_message_oa_job(access_token, user_zalo_oa: str):
    try:
        url = f'{domain}/v1/zalo/zalo_message/create_multi'
        offset = 0
        item_count = 10
        while item_count == 10:
            res = oa_list_message_in_conversation(access_token, user_zalo_oa, offset)
            if res.get('error') != 0:
                break
            messages_valid = []
            messages = res.get('data', [])
            for item in messages:
                if item.get('type') == 'text':
                    item['user_zalo_oa'] = user_zalo_oa
                    messages_valid.append(item)
            payload = json.dumps(messages_valid)
            headers = {'Content-Type': 'application/json'}
            requests.post(url, data=payload, headers=headers)
            offset += item_count
            item_count = len(messages)
    except Exception as e:
        print(str(e))


def detail_customer_oa_job(access_token, user_id, oa: int):
    try:
        res = oa_detail_customer(access_token, user_id)
        if res['error'] == 0:
            customer = res['data']
            url = f'{domain}/v1/zalo/zalo_user/create'
            payload = {
                "name": customer['display_name'],
                "phone": customer['shared_info']['phone'] if customer['shared_info']['phone'] != 0 else None,
                "address": customer['shared_info']['address'],
                "user_zalo_id": user_id,
                "avatar_small": customer['avatars']['120'],
                "avatar_big": customer['avatars']['240'],
                "oa_id": oa,
                "is_follower": customer['user_is_follower'],
                "last_message_reply": datetime.strptime(customer['user_last_interaction_date'], "%d/%m/%Y").timestamp() if customer['user_last_interaction_date'] else None
            }
            # Xử lý để tìm ra được quota_type message của user_zalo
            if customer['user_last_interaction_date']:
                last_interaction = datetime.strptime(customer['user_last_interaction_date'], "%d/%m/%Y")
                now = datetime.now()
                # Tính khoảng cách thời gian
                time_difference = now - last_interaction
                # Kiểm tra điều kiện
                if time_difference <= timedelta(hours=48):
                    payload['message_quota_type'] = 'reply'
                elif timedelta(hours=48) < time_difference <= timedelta(days=7):
                    payload['message_quota_type'] = 'sub_quota'
                else:
                    payload['message_quota_type'] = 'false'
                payload['message_remain'] = 8
                payload['message_quota'] = 8
            res_cus = requests.post(url, data=payload)
            res_cus_json = res_cus.json()
            if res_cus_json.get('data'):
                django_rq.enqueue(list_message_oa_job, access_token, user_id)
    except Exception as e:
        print(str(e))


def connect_oa_job(access_token, oa: int):
    try:
        offset = 0
        item_count = 50
        total_user = 0
        while item_count == 50:
            res = oa_list_customer(access_token, 0)
            items = res['data']['users']
            for item in items:
                django_rq.enqueue(detail_customer_oa_job, access_token, item['user_id'], oa)
            item_count = res['data']['total']
            total_user += item_count
            offset += item_count

        # Send message total user need sync process by socket
        url = f'{domain}/v1/zalo/zalo_user/send_sync_process'
        payload = {
            "oa_id": oa,
            "total_user": total_user,
        }
        requests.post(url, data=payload)
    except Exception as e:
        print(str(e))
