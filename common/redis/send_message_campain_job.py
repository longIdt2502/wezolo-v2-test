import os
import requests
import json
# from campaign.models import StatusMessage

from common.pref_keys import PrefKeys


def send_message_campain_job(access_token, user_id, message):
    try:
        url = "https://openapi.zalo.me/v3.0/oa/message/cs"
        payload = json.dumps({
            "recipient": {
                "user_id": user_id
            },
            "message": message
        })
        headers = {
            'Content-Type': 'application/json',
            'access_token': access_token
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        response = response.json()
        if response.get('error') == -216:
            raise Exception('token OA đã hết hạn')
        return response
    except Exception as e:
        print(str(e))
        return str(e)


def send_zns_campain_job(access_token, phone, template, params, campaign_zns_id):
    try:
        url = "https://business.openapi.zalo.me/message/template"
        payload = json.dumps({
            "phone": phone,
            "template_id": template,
            "template_data": params,
            "tracking_id": "tracking_id"
        })
        headers = {
            'Content-Type': 'application/json',
            'access_token': access_token
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        response = response.json()
        domain = os.environ.get(PrefKeys.DOMAIN_URL)
        url = f'{domain}/v1/campaign/zns/{campaign_zns_id}'
        print(response)
        print(response.get('error'))
        status = 'SENT' if response.get('error') == 0 else 'REJECT'
        payload = json.dumps({
            'status': status
        })
        headers = {'Content-Type': 'application/json'}
        res = requests.put(url, data=payload, headers=headers)
        print(res)
        return response
    except Exception as e:
        print(str(e))
        return str(e)