from common.zalo.event_name import ZaloEventName
from zalo.models import ZaloOA, UserZalo


def handle_follow_event(data) -> [str, int]:
    event_type = data.get('event_name')
    user_id = data.get('follower').get('id')
    uid_zalo_oa = data.get('oa_id')
    is_follow = True if event_type == ZaloEventName.follow else False
    try:
        user_zalo = UserZalo.objects.get(user_zalo_id=user_id, oa__uid_zalo_oa=uid_zalo_oa)
        user_zalo.is_follower = is_follow
        user_zalo.save()
    except Exception as e:
        return str(e), 400
