from datetime import datetime

from common.zalo.event_name import ZaloEventName
from zalo.models import ZaloOA, UserZalo
from user.models import Address, City, District, Ward
from zns.models import Zns, ZnsLog


def handle_follow_event(data) -> [str, int]:
    event_type = data.get('event_name')
    user_id = data.get('follower').get('id')
    uid_zalo_oa = data.get('oa_id')
    is_follow = True if event_type == ZaloEventName.follow else False
    try:
        user_zalo = UserZalo.objects.get(user_zalo_id=user_id, oa__uid_zalo_oa=uid_zalo_oa)
        user_zalo.is_follower = is_follow
        user_zalo.save()
        return 'success', 200
    except Exception as e:
        return str(e), 400


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
