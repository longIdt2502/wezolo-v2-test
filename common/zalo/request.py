import os
import requests
from typing import List
from common.pref_keys import PrefKeys
from zalo.models import ZaloOA


def get_token_from_refresh(refresh_token: str) -> List[str]:
    url = "https://oauth.zaloapp.com/v4/oa/access_token"
    app_id = os.environ.get(PrefKeys.ZALO_APP_ID)
    secret_key = os.environ.get(PrefKeys.ZALO_APP_SECRET)
    payload = f'app_id={app_id}&grant_type=refresh_token&refresh_token={refresh_token}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'secret_key': secret_key
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response = response.json()
    new_access = response.get('access_token')
    new_refresh = response.get('refresh_token')
    if new_refresh and new_refresh:
        return new_access, new_refresh
    return None, None

def update_token_oa(oa_zalo_id: str) -> ZaloOA:
    oa = ZaloOA.objects.get(uid_zalo_oa=oa_zalo_id)
    access_token, refresh_token = get_token_from_refresh(oa.refresh_token)
    if access_token and refresh_token:
        oa.access_token = access_token
        oa.refresh_token = refresh_token
        oa.save()
    return oa