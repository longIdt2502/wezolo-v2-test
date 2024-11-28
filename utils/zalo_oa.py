import json
from threading import Thread

import requests
import os
from datetime import datetime, timedelta, timezone

from django.core.cache import cache
from django.utils import timezone as tz

from zalo.models import Message, SendBy, UserZalo, ZaloOaLog, SendMessageLog


def format_currency_vnd(number):
    if number != "":
        integer_part = int(number)

        formatted_integer = '{:,}'.format(integer_part)

        formatted_number = f'{formatted_integer} ₫'

        return formatted_number.replace(",", ".")
    return ""


def get_oa_infor(oa):
    zalo_oa_me = os.environ.get("ZALO_OPENAPI")
    url = f"{zalo_oa_me}/v2.0/oa/getoa"
    headers = {
        "access_token": oa.access_token
    }
    response = requests.request(
        "GET", url, headers=headers)
    data = json.loads(response.text)
    reload = check_grant_token(json.loads(response.text), oa)
    res = {}
    if reload:
        response = requests.request(
            "GET", url, headers=headers)
        data = json.loads(response.text)
    if "error" in data:
        error = data["error"]
        if error != 0:
            return error
    if "data" in data:
        response_data = data["data"]
        fields = ["num_follower", "package_name", "oa_type",
                  "cate_name", "num_follower", "package_name", "description", "name", "avatar"]
        for field in fields:
            res[field] = response_data[field]
        res["oa_name"] = response_data["name"]
        res["oa_img"] = response_data["avatar"]
    return res


def update_access_token_zalo_oa(zalo_oa):
    try:
        zalo_oa_auth = os.environ.get("ZALO_OA_AUTH")
        url = f"{zalo_oa_auth}/v4/oa/access_token"
        payload = f"refresh_token={zalo_oa.refresh_token}&app_id={zalo_oa.app_id}&grant_type=refresh_token"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'secret_key': zalo_oa.secret_app
        }
        response = requests.request(
            "POST", url, headers=headers, data=payload)
        data = json.loads(response.text)
        print("grant access token response =================> ", data)
        if 'expires_in' in data:
            seconds = data["expires_in"]
            current_time = datetime.now()
            expire_time = current_time + timedelta(seconds=int(seconds))
            zalo_oa.token_expired_at = expire_time
        zalo_oa.access_token = data["access_token"]
        zalo_oa.refresh_token = data["refresh_token"]
        zalo_oa.save()
        return True
    except Exception as e:
        print("error griant access token ======> ", str(e))
        return False


def check_grant_token(data, oa):
    success = False
    if "error" in data and int(data["error"]) not in [0]:
        success = update_access_token_zalo_oa(oa)
    return success


def get_profile(user_id, oa_id, zalo_oa):
    zalo_openapi = os.getenv('ZALO_OPENAPI')
    url = f"{zalo_openapi}/v3.0/oa/user/detail"
    headers = {
        'access_token': zalo_oa.access_token
    }
    payload = json.dumps({
        "user_id": user_id
    })
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.text


def send_zns(oa, template_id, content, phone, tracking_id):
    headers = {
        'access_token': oa.access_token,
    }
    if phone.startswith('0'):
        phone = phone.replace('0', '84', 1)
    url = os.environ.get("ZALO_ZNS_URL")
    payload = json.dumps(
        {
            "phone": phone,
            "mode": "development",
            "template_id": template_id,
            "template_data": content,
            "tracking_id": tracking_id
        })
    response = requests.request("POST", url, headers=headers, data=payload)
    log = ZaloOaLog()
    log.data = response.json()
    log.save()
    return response.json()


def send_zns_product(oa, template_id, content, phone, tracking_id):
    headers = {
        'access_token': oa.access_token,
    }
    if phone.startswith('0'):
        phone = phone.replace('0', '84', 1)
    url = os.environ.get("ZALO_ZNS_URL")
    payload = json.dumps(
        {
            "phone": phone,
            "template_id": template_id,
            "template_data": content,
            "tracking_id": tracking_id
        })
    response = requests.request("POST", url, headers=headers, data=payload)
    log = ZaloOaLog()
    log.data = response.json()
    log.save()
    return response.text


def generate_example_message(content):
    current = datetime.now()
    order_code = content.get('order_code', '')
    order_amount = content.get('order_amount', '')
    order_amount = format_currency_vnd(order_amount)
    created_at = content.get(
        'created_at', current.strftime("%H:%M:%S %d/%m/%Y"))
    order_status = content.get("order_status", 'DXN')
    message = f"Thông báo xác nhận đơn hàng\nBạn vừa đặt hàng qua hệ thống KAFA\nChi tiết:\nMã đơn hàng: {order_code}\nTrị giá đơn hàng: {order_amount}\nThời gian tạo đơn: {created_at}\nTrạng thái đơn hàng: {order_status}"
    return message


def send_message(id, user_id, content, message_id, zalo_oa):
    zalo_openapi = os.getenv('ZALO_OPENAPI')
    url = f"{zalo_openapi}/v3.0/oa/message/cs"
    if message_id:
        payload = json.dumps({
            "recipient": {
                "message_id": message_id
            },
            "message": {
                "text": content
            }
        })
    else:
        payload = json.dumps({
            "recipient": {
                "user_id": user_id
            },
            "message": {
                "text": generate_example_message(content)
            }
        })
    headers = {
        'Content-Type': 'application/json',
        'access_token': zalo_oa.access_token
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    try:
        json_response = json.loads(response.text)
        reload = check_grant_token(json_response, zalo_oa)
        if reload:
            return send_message(id, user_id, content, message_id, zalo_oa)
        else:
            return json_response.get("error", 1) == 0 and json_response.get("message", "") == "Success"
    except Exception:
        return False


def send_message_v2(oa, user_id, message, tracking_id, attachments=None):
    is_sent = SendMessageLog.objects.filter(tracking_id=tracking_id).exists()
    if is_sent:
        return True
    if attachments is None:
        attachments = []
    zalo_openapi = os.getenv('ZALO_OPENAPI')
    url = f"{zalo_openapi}/v3.0/oa/message/cs"
    payload = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "text": message
        }
    }
    if attachments and len(attachments) > 0:
        elements = []
        for item in attachments:
            item["media_type"] = "image"
            elements.append(item)
        attachment_payload = {
            "type": "template",
            "payload": {
                "template_type": "media",
                "elements": elements
            }
        }
        payload["message"]["attachment"] = attachment_payload
    headers = {
        'Content-Type': 'application/json',
        'access_token': oa.access_token
    }
    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    json_response = json.loads(response.text)
    is_success = json_response.get("message", "") == "Success" and int(
        json_response.get("error", 1)) == 0
    log = ZaloOaLog()
    log.data = {
        "res": json_response,
        "event": "socket chat"
    }
    log.save()
    SendMessageLog.objects.create(tracking_id=tracking_id)
    return json_response
    # try:
    #     user = UserZalo.objects.filter(user_id=user_id).first()
    #     message_instance = Message()
    #     message_instance.oa = oa
    #     message_instance.tracking_id = tracking_id
    #     message_instance.user = user
    #     message_instance.send_by = SendBy.OA
    #     message_instance.message_id = json_response["data"]["message_id"]
    #     message_instance.user_uid = user_id
    #     message_instance.oa_uid = oa.oa_id
    #     message_instance.message_text = message
    #     message_instance.success = True
    #     message_instance.save()
    #     message_instance.convert_ts_to_datetime()
    #     print(message_instance.id)
    #     if user:
    #         user.updated_at = tz.now()
    #         user.save()
    #     return json_response
    # except Exception as e:
    #     print(str(e))
    #     return json_response


def request_share_info(user_id, zalo_oa):
    zalo_openapi = os.getenv('ZALO_OPENAPI')
    url = f"{zalo_openapi}/v3.0/oa/message/cs"
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
                            "title": zalo_oa.oa_name,
                            "subtitle": "Đang yêu cầu thông tin từ bạn",
                            "image_url": "https://developers.zalo.me/web/static/zalo.png"
                        }
                    ]
                }
            }
        }
    })
    headers = {
        'Content-Type': 'application/json',
        'access_token': zalo_oa.access_token,
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    try:
        json_response = json.loads(response.text)
        reload = check_grant_token(json_response, zalo_oa)
        if reload:
            return request_share_info(user_id, zalo_oa)
        else:
            return response.text
    except Exception:
        return None


def get_list_template(oa, page, per_page):
    zns_api = os.getenv('ZALO_ZNS_URL')
    per_page = int(per_page)
    page = int(page)
    limit = (per_page)
    offset = (page - 1) * per_page
    url = f"https://business.openapi.zalo.me/template/all?offset={offset}&limit={limit}"
    headers = {
        'Content-Type': 'application/json',
        'access_token': oa.access_token
    }
    response = requests.get(url, headers=headers)
    # try:
    json_response = json.loads(response.text)
    # reload = check_grant_token(json_response, oa)
    # if reload:
    #     return get_list_template(oa, page, per_page)
    # else:
    return json_response
    # except Exception as e:
    #     return {"error": 1, "message": str(e), 'response': json.loads(response.text)}


def get_detail_template(oa, template_id):
    url = f"https://business.openapi.zalo.me/template/info?template_id={template_id}"
    headers = {
        'Content-Type': 'application/json',
        'access_token': oa.access_token
    }
    response = requests.get(url, headers=headers)
    try:
        json_response = json.loads(response.text)
        reload = check_grant_token(json_response, oa)
        if reload:
            return get_detail_template(oa, template_id)
        else:
            return json_response
    except Exception as e:
        return {"error": 1, "message": str(e)}


def get_template_sample(oa, template_id):
    url = f"https://business.openapi.zalo.me/template/sample-data?template_id={template_id}"
    headers = {
        'Content-Type': 'application/json',
        'access_token': oa.access_token
    }
    response = requests.get(url, headers=headers)
    try:
        json_response = json.loads(response.text)
        reload = check_grant_token(json_response, oa)
        if reload:
            return get_template_sample(oa, template_id)
        else:
            return json_response
    except Exception:
        return None


def get_list_followers(oa, offset, limit):
    zalo_openapi = os.getenv('ZALO_OPENAPI')
    url = f'{zalo_openapi}/v2.0/oa/getfollowers?data={"offset":{offset},"count":{limit}}'
    headers = {
        'Content-Type': 'application/json',
        'access_token': oa.access_token
    }
    response = requests.get(url, headers=headers)
    try:
        json_response = json.loads(response.text)
        reload = check_grant_token(json_response, oa)
        if reload:
            return get_list_followers(oa, offset, limit)
        else:
            return json_response
    except Exception:
        return False


def get_detail_follower_info(oa, user_id):
    zalo_openapi = os.getenv('ZALO_OPENAPI')
    url = f'{zalo_openapi}/v2.0/oa/getprofile?data={"user_id":{user_id}}'
    headers = {
        'Content-Type': 'application/json',
        'access_token': oa.access_token
    }
    response = requests.get(url, headers=headers)
    try:
        json_response = json.loads(response.text)
        reload = check_grant_token(json_response, oa)
        if reload:
            return get_detail_follower_info(oa, user_id)
        else:
            return json_response
    except Exception:
        return False
