import json
import os

import requests

url = "https://openapi.zalo.me/v3.0/oa/message/cs"

def send_message_text(access_token, user_id, message):
    url = "https://oauth.zaloapp.com/v4/oa/access_token"

    payload = json.dumps({
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "text": message
        }
    })
    headers = {
        'Content-Type': 'application/json',
        'access_token': access_token
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.json())
    return response.json()