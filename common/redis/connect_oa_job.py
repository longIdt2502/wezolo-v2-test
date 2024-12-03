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
            res = oa_list_message_in_conversation(access_token, user_zalo_oa, 0)
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
                "phone": customer['shared_info']['phone'],
                "user_zalo_id": user_id,
                "avatar_small": customer['avatars']['120'],
                "avatar_big": customer['avatars']['240'],
                "oa_id": oa,
                "is_follower": customer['user_is_follower']
            }
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
        while item_count == 50:
            res = oa_list_customer(access_token, 0)
            offset += 50
            items = res['data']['users']
            for item in items:
                django_rq.enqueue(detail_customer_oa_job, access_token, item['user_id'], oa)
            item_count = res['data']['total']
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'oa_{str(oa)}',
            {
                'type': 'message_handler',
                'message': {
                    'sync_done': 0,
                    'total_sync': offset + item_count
                }
            },
        )
    except Exception as e:
        print(str(e))
