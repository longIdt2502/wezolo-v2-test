import os
import uuid

from utils.zalo_oa import send_zns, send_zns_product
from zalo.models import ZaloOA


def send_verify_otp(phone, otp):
    """
    Send verify otp to phone number using a third-party service.

    Args:
        phone (str): Phone number to send otp.
        otp (str): OTP code to send.

    Returns:
        bool: True if send successful, False otherwise.
    """
    # Replace the following with your actual implementation
    # Use a third-party service to send otp
    # For example, using requests library to send HTTP POST request
    oa_id = os.environ.get("OA_WEZOLO")
    template_id = os.environ.get("OA_TEMPLATE_ID")
    res = {}
    oa = ZaloOA.objects.get(id=int(oa_id))
    tracking = str(uuid.uuid4())
    if phone in os.environ.get("PHONE_ADMIN", "").split(","):
        res = send_zns(oa,
                       template_id, {
                           "otp": otp,
                       }, phone, tracking)
    else:
        res = send_zns_product(
            oa,
            template_id, {
                "otp": otp,
            }, phone, tracking
        )
