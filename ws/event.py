from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_message_to_ws(group_name: str, message_type: str, message: dict):
    """
    Gửi một tin nhắn tới một nhóm cụ thể qua channel layer.

    Args:
        group_name (str): Tên nhóm để gửi tin nhắn.
        message_type (str): Loại thông báo (type) sẽ được xử lý trong consumer.
        message (dict): Nội dung tin nhắn gửi đi.
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        raise ValueError("Channel layer is not configured.")

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': message_type,
            'message': message,
        },
    )
