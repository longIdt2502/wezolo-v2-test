import requests

def detail_zns(access_token, template_id):
    url = f"https://business.openapi.zalo.me/template/info/v2?template_id={template_id}"

    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'access_token': access_token
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()