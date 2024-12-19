import requests
import json


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


def send_zns_campain_job(access_token, phone, template, params):
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
        if response.get('error') == -216:
            raise Exception('token OA đã hết hạn')
        return response
    except Exception as e:
        print(str(e))
        return str(e)