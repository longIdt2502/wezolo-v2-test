from datetime import datetime
import json
from typing import Optional

from common.zalo.event_name import ZaloEventName
from ws.event import send_message_to_ws
from zalo.models import ZaloOA, UserZalo
from user.models import Address, City, District, Ward
from zalo.utils import revert_phone
from zns.models import Zns, ZnsLog
from zalo_messages.models import Message


def handle_user_submit_info(data) -> Optional[str]:
    try:
        user_id = data.get('sender').get('id')
        uid_zalo_oa = data.get('recipient').get('id')
        user_zalo = UserZalo.objects.get(user_zalo_id=user_id, oa__uid_zalo_oa=uid_zalo_oa)
        info = data.get('info')
        user_zalo.phone = revert_phone(str(info.get('phone'))) if info.get('phone') else None
        user_zalo.prefix_name = info.get('name', user_zalo.prefix_name)
        user_zalo.address = f"{info.get('address')}, {info.get('ward')}, {info.get('district')}, {info.get('city')}"
        user_zalo.save()
        return None
    except Exception as e:
        return str(e)


def handle_follow_event(data) -> Optional[str]:
    event_type = data.get('event_name')
    user_id = data.get('follower').get('id')
    uid_zalo_oa = data.get('oa_id')
    is_follow = True if event_type == ZaloEventName.follow else False
    try:
        user_zalo = UserZalo.objects.get(user_zalo_id=user_id, oa__uid_zalo_oa=uid_zalo_oa)
        user_zalo.is_follower = is_follow
        user_zalo.save()
        return None
    except Exception as e:
        return str(e)


def handle_user_submit_info(data) -> [str, int]:
    info = data.get('info')
    user_id = data.get('sender').get('id')
    uid_zalo_oa = data.get('recipient').get('id')
    try:
        user_zalo = UserZalo.objects.get(user_zalo_id=user_id, oa__uid_zalo_oa=uid_zalo_oa)
        user_zalo.phone = info.get('phone')
        user_zalo.name = info.get('name')

        ward_name = info.get('ward')
        district_name = info.get('district')
        city_name = info.get('city')
        if city_name and district_name:
            city = City.objects.filter(name=city_name)
            district = District.objects.filter(name_with_type__icontains=district_name)
            ward = Ward.objects.filter(name_with_type__icontains=ward_name)
            address = Address.objects.create(
                city=city,
                district=district,
                ward=ward,
                address=info.get('address')
            )
            user_zalo.address = address
        user_zalo.save()
        return 'success', 200
    except Exception as e:
        return str(e), 400


# TODO: ZNS handle hook
def handle_change_template_status(data) -> [str, int]:
    try:
        zns = Zns.objects.get(template=data.get('template_id'), oa__uid_zalo_oa=data.get('oa_id'))
        prev_status = data.get('status').get('prev_status')
        new_status = data.get('status').get('new_status')
        if new_status == 'DRAFT' and prev_status == 'REJECT':
            zns.status = 'REJECTED'
        if new_status == 'PENDING_REVIEW' and prev_status == 'REJECT':
            zns.status = 'PENDING_REVIEW'
        if new_status == 'REJECT' and prev_status == 'PENDING_REVIEW':
            zns.status = 'REJECTED'
        if new_status == 'ENABLE' and prev_status == 'PENDING_REVIEW':
            zns.status = 'APPROVED'
        if new_status == 'DISABLE' and prev_status == 'ENABLE':
            zns.status = 'LOCKER'
        if new_status == 'DRAFT' and prev_status == 'DELETE':
            zns.status = 'REJECTED'
        if new_status == 'REJECT' and prev_status == 'DELETE':
            zns.status = 'REJECTED'
        zns.save()
        ZnsLog.objects.create(
            zns=zns,
            type=zns.status,
            content=data.get('reason'),
            action_at=datetime.fromtimestamp(int(data.get('timestamp')) / 1000)
        )
        return 'success', 200
    except Exception as e:
        return str(e), 400


#TODO: Message handle hook
def handle_message_hook(data) -> Optional[str]:
    try:
        print(data)
        sender = data.get('sender').get('id')
        recipient = data.get('recipient').get('id')
        message = data.get('message')

        message_json = {
            'message_id': message.get('msg_id'),
            'user_zalo_id': sender,
            'src': Message.Src.USER,
            'type_send': Message.TypeSend.USER,
            'send_at': data.get('timestamp'),
            'from_id': sender,
            'to_id': recipient,
            'quote_msg_id': data.get('message').get('quote_msg_id')
        }

        type_message =  data.get('event_name')
        message_json['message_text'] = message.get('text')
        if type_message == 'user_send_text':
            type_message = Message.Type.TEXT
        if type_message == 'user_send_image':
            type_message = Message.Type.PHOTO
            message_json['message_url'] = json.dumps(message.get('attachments'))
        if type_message == 'user_send_link':
            type_message = Message.Type.LINK
            message_json['message_links'] = json.dumps(message.get('attachments'))
        if type_message == 'user_send_audio':
            type_message = Message.Type.VOICE
            message_json['message_url'] = json.dumps(message.get('attachments'))
        if type_message == 'user_send_video':
            type_message = Message.Type.VIDEO
            message_json['message_url'] = json.dumps(message.get('attachments'))
        if type_message == 'user_send_sticker':
            type_message = Message.Type.STICKER
            message_json['message_url'] = json.dumps(message.get('attachments'))
        if type_message == 'user_send_location':
            type_message = Message.Type.LOCATION
            message_json['message_location'] = json.dumps(message.get('attachments'))
        if type_message == 'user_send_business_card':
            type_message = Message.Type.BUSINESS_CARD
            message_json['message_url'] = json.dumps(message.get('attachments'))
        if type_message == 'user_send_file':
            type_message = Message.Type.FILE
            message_json['message_url'] = json.dumps(message.get('attachments'))

        oa = ZaloOA.objects.get(uid_zalo_oa=recipient)

        message_json['type_message'] = type_message
        message_json['oa'] = oa.id
        Message().from_json(message_json)

        return None
    except Exception as e:
        print(e)
        return str(e)


def handle_seen_message(data) -> Optional[str]:
    try:
        print(data)
        sender = data.get('sender').get('id')
        recipient = data.get('recipient').get('id')
        message = data.get('message')

        messages = Message.objects.filter(message_id__in=message.get('msg_ids'))
        for mess in messages:
            mess.read_at = datetime.fromtimestamp(data.get('timestamp'))
            mess.save()
        
        send_message_to_ws(f'message_{recipient}', 'message_handler', {
            'last_seen': datetime.now(),
        })

        return None
    except Exception as e:
        print(e)
        return str(e)


def handle_message_oa_send_hook(data) -> Optional[str]:
    try:
        print(data)
        sender = data.get('sender').get('id')
        recipient = data.get('recipient').get('id')
        message = data.get('message')

        message_json = {
            'message_id': message.get('msg_id'),
            'user_zalo_id': recipient,
            'src': Message.Src.OA,
            'type_send': Message.TypeSend.USER,
            'send_at': data.get('timestamp'),
            'from_id': sender,
            'to_id': recipient,
            'quote_msg_id': data.get('message').get('quote_msg_id')
        }

        type_message =  data.get('event_name')
        message_json['message_text'] = message.get('text')
        if type_message == 'oa_send_text':
            type_message = Message.Type.TEXT
        if type_message == 'oa_send_image':
            type_message = Message.Type.PHOTO
            message_json['message_url'] = json.dumps(message.get('attachments'))
        if type_message == 'oa_send_link':
            type_message = Message.Type.LINK
            message_json['message_links'] = json.dumps(message.get('attachments'))
        if type_message == 'oa_send_audio':
            type_message = Message.Type.VOICE
            message_json['message_url'] = json.dumps(message.get('attachments'))
        if type_message == 'oa_send_video':
            type_message = Message.Type.VIDEO
            message_json['message_url'] = json.dumps(message.get('attachments'))
        if type_message == 'oa_send_sticker':
            type_message = Message.Type.STICKER
            message_json['message_url'] = json.dumps(message.get('attachments'))
        if type_message == 'oa_send_location':
            type_message = Message.Type.LOCATION
            message_json['message_location'] = json.dumps(message.get('attachments'))
        if type_message == 'oa_send_business_card':
            type_message = Message.Type.BUSINESS_CARD
            message_json['message_url'] = json.dumps(message.get('attachments'))
        if type_message == 'oa_send_file':
            type_message = Message.Type.FILE
            message_json['message_url'] = json.dumps(message.get('attachments'))

        oa = ZaloOA.objects.get(uid_zalo_oa=sender)

        message_json['type_message'] = type_message
        message_json['oa'] = oa.id
        Message().from_json(message_json)

        return None
    except Exception as e:
        print(e)
        return str(e)