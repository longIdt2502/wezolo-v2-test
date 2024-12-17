import json
import os

import requests

url = "https://openapi.zalo.me/v3.0/oa/message/cs"

def send_message_text(access_token):
    url = "https://oauth.zaloapp.com/v4/oa/access_token"

    payload = json.dumps({
        "recipient": {
            "user_id": "2512523625412515"
        },
        "message": {
            "text": "hello, world!"
        }
    })
    headers = {
        'Content-Type': 'application/json',
        'access_token': access_token
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json()