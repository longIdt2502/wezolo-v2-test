import random

from django.core.files.base import ContentFile
from django.db import models
from common.core.subquery import SubqueryJsonAgg

from common.s3 import AwsS3
from user.models import User
from workspace.models import Workspace
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta

from user.models import Address

created_at_field = models.DateTimeField(_("Created at"), auto_now_add=True)


class CodeVerifier(models.Model):
    workspace_id = models.IntegerField(default=0)
    code_verifier = models.CharField(max_length=255, null=True, blank=True)
    code_challenge = models.CharField(max_length=255, null=True, blank=True)


class IPWhitelist(models.Model):
    ip = models.GenericIPAddressField()
    is_active = models.BooleanField(_("Is active"), default=True)
    website = models.TextField(_("Website"), blank=True, null=True, default="")

    def __str__(self):
        if self.website:
            return self.website
        return self.ip


class SendBy(models.IntegerChoices):
    OA = 1
    USER = 2


class ZaloOA(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Chờ đăng ký'
        REGISTERING = 'REGISTERING', 'Đang đăng ký'
        NOT_CONNECTED = 'NOT_CONNECTED', 'Chưa kết nối'
        CONNECTED = 'CONNECTED', 'Đã kết nối'
        DISCONNECTED = 'DISCONNECTED', 'Ngừng kết nối'

    class Active(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Hoạt động'
        INACTIVE = 'INACTIVE', 'Không hoạt động'
        EXPIRED = 'EXPIRED', 'Hết hạn gói'

    class SynsStatus(models.TextChoices):
        SYNC = 'SYNC', 'Đang đồng bộ'
        ERROR = 'ERROR', 'Ngưng đồng bộ'
        DONE = 'DONE', 'Đã đồng bộ'

    company = models.ForeignKey(
        Workspace,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="zalo_company")
    code_ref = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, choices=Status.choices, default=Status.PENDING)
    active = models.CharField(max_length=255, choices=Active.choices, default=Active.ACTIVE, null=True)
    app_id = models.CharField(max_length=255, null=True, blank=True)
    uid_zalo_oa = models.CharField(max_length=255, null=True, blank=True)
    oa_name = models.CharField(max_length=255, null=True, blank=True)
    oa_avatar = models.URLField(max_length=200, blank=True, null=True)
    oa_cover = models.URLField(max_length=200, blank=True, null=True)
    cate_name = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    giay_dang_ky = models.URLField(max_length=200, blank=True, null=True)
    cccd_truoc = models.URLField(max_length=200, blank=True, null=True)
    cccd_sau = models.URLField(max_length=200, blank=True, null=True)
    ho_chieu = models.URLField(max_length=200, blank=True, null=True)
    cong_van = models.URLField(max_length=200, blank=True, null=True)
    chung_minh = models.URLField(max_length=200, blank=True, null=True)
    sync_status = models.CharField(max_length=255, choices=SynsStatus.choices, default=SynsStatus.SYNC, null=False)
    oa_type = models.IntegerField(default=2)
    expiry_date = models.DateTimeField(null=True)
    pause_date = models.DateTimeField(null=True)
    dev_note = models.CharField(max_length=255, null=True, blank=True)
    message_remain = models.IntegerField(null=True)
    message_quota = models.IntegerField(null=True)
    message_expired = models.FloatField(null=True)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    num_follower = models.IntegerField(default=0)
    package_name = models.CharField(max_length=255, null=True, blank=True)
    package_valid_through_date = models.DateField(null=True)
    package_auto_renew_date = models.DateField(null=True)
    activate = models.BooleanField(default=False)
    refresh_token = models.TextField(null=True, blank=True)
    access_token = models.TextField(null=True, blank=True)
    retry = models.IntegerField(null=True, blank=True)
    token_expired_at = models.DateTimeField(null=True, blank=True)
    verify_hook_url = models.CharField(max_length=255, null=True, blank=True)
    verify_html_file = models.FileField(null=True, blank=True, upload_to="zaloa/verify")
    secret_app = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user_create_oa')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user_update_oa')

    def sync_data_info(self):
        from utils.zalo_oa import get_oa_infor
        res = get_oa_infor(self)
        if isinstance(res, dict):
            for key, value in res.items():
                if key == "avatar":
                    setattr(self, "oa_img", value)
                if key == "name":
                    setattr(self, "oa_name", value)
                else:
                    setattr(self, key, value)
        self.save()

    def upload_file(self, file, name):
        file_name = name
        image_file = ContentFile(file.read(), name=file_name)
        uploaded_file_name = AwsS3.upload_file(image_file, f'zalo_oa/{self.code_ref}/')
        return uploaded_file_name

    def update_from_json(self, data):
        zalo_oa = self
        zalo_oa.cate_name = data.get('cate_name', zalo_oa.cate_name)
        zalo_oa.num_follower = data.get('num_follower', zalo_oa.num_follower)
        zalo_oa.description = data.get('description', zalo_oa.description)
        zalo_oa.package_name = data.get('access_token', zalo_oa.package_name)
        zalo_oa.oa_type = data.get('oa_type', zalo_oa.oa_type)

        zalo_oa.access_token = data.get('access_token', zalo_oa.access_token)
        zalo_oa.refresh_token = data.get('refresh_token', zalo_oa.refresh_token)
        expires_in_seconds = int(data.get("expires_in", 0))
        zalo_oa.token_expired_at = datetime.now() + timedelta(seconds=expires_in_seconds)
        zalo_oa.save()
        return zalo_oa

    def to_json(self):
        return {
            'id': self.id,
            'uid_zalo_oa': self.uid_zalo_oa,
            'oa_name': self.oa_name,
            'cate_name': self.cate_name,
            'oa_avatar': self.oa_avatar,
            'oa_cover': self.oa_cover,
        }


class UserZalo(models.Model):
    name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=('zname'))
    prefix_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    user_zalo_id = models.CharField(
        max_length=300, blank=True, null=True, verbose_name=('UID'))
    avatar_small = models.URLField(max_length=200, blank=True, null=True)
    avatar_big = models.URLField(max_length=200, blank=True, null=True)
    last_message_time = models.DateTimeField(null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10, blank=True, null=True, verbose_name='gender')
    oa = models.ForeignKey(ZaloOA, on_delete=models.CASCADE, null=True)
    is_follower = models.BooleanField(default=False, null=False)
    # address = models.ForeignKey(Address, null=True, on_delete=models.SET_NULL)
    address = models.TextField(null=True, blank=True)
    message_quota_type = models.CharField(max_length=255, null=True, blank=True)
    message_remain = models.IntegerField(null=True, blank=True)
    message_quota = models.IntegerField(null=True, blank=True)
    chatbot = models.BooleanField(default=False, null=False)
    created_at = created_at_field
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    # def save(self, *args, **kwargs):
    #     super(UserZalo, self).save(*args, **kwargs)
    #     _id = self.pk
    #     other_users = UserZalo.objects.filter(user_zalo_id=self.user_zalo_id, oa_id=self.oa_id).exclude(
    #         pk=self.pk)
    #     if other_users.count() > 0:
    #         other_users.delete()

    def to_json(self):
        from tags.models import TagUserZalo
        from zalo_messages.models import Message
        tags = TagUserZalo.objects.filter(user_zalo_id=self.id)
        tags_json = []
        for item in tags:
            tags_json.append(item.to_json())
        last_message_subquery = Message.objects.filter(models.Q(from_id=self.user_zalo_id) | models.Q(to_id=self.user_zalo_id)).order_by('-id').first()
        return {
            'id': self.id,
            'name': self.name,
            'prefix_name': self.prefix_name,
            'phone': self.phone,
            'user_zalo_id': self.user_zalo_id,
            'avatar_small': self.avatar_small,
            'avatar_big': self.avatar_big,
            'last_message_time': last_message_subquery.to_json() if last_message_subquery else None,
            'is_follower': self.is_follower,
            'chatbot': self.chatbot,
            'oa': self.oa.to_json() if self.oa else None,
            'tags': tags_json,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }


class UserZaloTag(models.Model):
    user_zalo = models.ForeignKey(UserZalo, on_delete=models.CASCADE)
    tag_id = models.IntegerField(null=True, blank=True)


class Message(models.Model):
    class Type(models.TextChoices):
        TEXT = 'TEXT', 'tin nhắn văn bản'
        VOICE = 'VOICE', 'tin nhắn thoại'
        PHOTO = 'PHOTO', 'tin nhắn ảnh'
        GIF = 'GIF', 'tin nhắn GIF'
        LINK = 'LINK', 'tin nhắn có nội dung là đường link'
        LINKS = 'LINKS', 'tin nhắn theo mẫu đính kèm danh sách'
        STICKER = 'STICKER', 'tin nhắn sticker'
        LOCATION = 'LOCATION', 'tin nhắn chia sẻ location'

    class TypeSend(models.TextChoices):
        USER = 'USER', 'Người dùng gửi'
        CAMPAIGN = 'CAMPAIGN', 'Chiến dịch gửi'
        BOT = 'BOT', 'Bot gửi'

    message_id = models.CharField(max_length=255, null=True, blank=True)
    src = models.IntegerField(choices=SendBy.choices, default=SendBy.USER)
    time = models.FloatField(null=True, blank=True, db_index=True)
    send_at = models.DateTimeField(null=True, blank=True)
    type_message = models.CharField(max_length=255, choices=Type.choices, default=Type.TEXT, null=False)
    type_send = models.CharField(max_length=255, choices=TypeSend.choices, default=TypeSend.USER, null=False)
    message_text = models.TextField(null=True, blank=True)
    message_thumb = models.URLField(max_length=255, null=True, blank=True)
    message_url = models.URLField(max_length=255, null=True, blank=True)
    message_links = models.CharField(max_length=255, null=True, blank=True)
    message_location = models.TextField(null=True, blank=True)
    message_description_photo = models.TextField(max_length=255, null=True, blank=True)
    from_id = models.CharField(max_length=255, null=True)
    to_id = models.CharField(max_length=255, null=True)
    success = models.BooleanField(default=False, null=False)
    send_by = models.ForeignKey(UserZalo, null=False, on_delete=models.CASCADE)
    oa = models.ForeignKey(ZaloOA, null=True, on_delete=models.CASCADE)
    seen = models.BooleanField(default=True, null=False)

    def convert_ts_to_datetime(self):
        if self.time is None:
            return
        dt = datetime.fromtimestamp(self.time)
        self.send_at = dt
        self.save()

    def save(self, *args, **kwargs):
        super(Message, self).save(*args, **kwargs)
        # _id = self.pk
        # timestamp = self.timestamp
        # user_uid = self.user_uid
        # oa_uid = self.oa_uid
        # other_messages = Message.objects.filter(timestamp=timestamp, user_uid=user_uid, oa_uid=oa_uid).exclude(
        #     pk=self.pk)
        # other_messages.delete()

    @classmethod
    def update_data(cls):
        messages = cls.objects.filter(
            oa_id__isnull=True, oa__isnull=False, user__isnull=False)
        for message in messages:
            message.oa_id = message.oa.oa_id
            message.user_id = message.user.user_id
            message.save()

    @classmethod
    def check_exist(cls, message_id):
        return cls.objects.filter(message_id=message_id).count() > 0


class MessageAttachment(models.Model):
    user_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    send_by = models.CharField(max_length=255, null=True, blank=True)
    oa_uid = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True)
    msg_id = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    thumbnail = models.URLField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True, null=True, blank=True)


class ZaloOaLog(models.Model):
    data = models.JSONField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    in_queue = models.BooleanField(default=False)

    def __str__(self) -> str:
        return str(self.created_at)


# use for zns
class ZaloMessageQueue(models.Model):
    retry = models.BooleanField(default=True)
    times = models.IntegerField(default=0)
    phone = models.CharField(max_length=255, null=True, blank=True)
    sended = models.BooleanField(default=False)
    success = models.BooleanField(default=False)
    oa = models.ForeignKey(ZaloOA, on_delete=models.SET_NULL,
                           null=True, blank=True, related_name="zmq_oa")
    message = models.TextField(null=True, blank=True)
    template_id = models.CharField(max_length=255, null=True, blank=True)
    content = models.JSONField(null=True, blank=True)
    tracking_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = created_at_field


class ZaloOAMessageQueue(models.Model):
    oa_id = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    success = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)
    tracking_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = created_at_field


class TemplateTypes(models.TextChoices):
    CONFIRM_ORDER = 'confirm_order'
    SEND_OTP = 'send_otp'
    LHE_SENT_ORDER = 'lhe_sent_order'
    LHE_CONFIRM_ORDER = 'lhe_confirm_order'
    LHE_CREATED_ORDER = 'lhe_created_order'


class ZNSTemplate(models.Model):
    template_id = models.CharField(max_length=255, null=True, blank=True)
    template_name = models.CharField(max_length=255, null=True, blank=True)
    variables = models.JSONField(default=dict)
    content = models.TextField(null=True, blank=True)
    oa = models.ForeignKey(ZaloOA, on_delete=models.SET_NULL,
                           null=True, blank=True, related_name="zn_template")
    type = models.CharField(max_length=255, null=True, blank=True, choices=TemplateTypes.choices,
                            default=TemplateTypes.CONFIRM_ORDER)

    def __str__(self):
        return str(self.pk)


class ZNSSendLog(models.Model):
    oa = models.ForeignKey(ZaloOA, on_delete=models.SET_NULL,
                           null=True, blank=True, related_name="zn_send_log")
    data = models.JSONField(default=None, null=True, blank=True)
    res = models.JSONField(default=None, null=True, blank=True)
    template_id = models.CharField(max_length=255, blank=True, null=True)
    mode = models.CharField(max_length=255, blank=True, null=True)
    to = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.oa.oa_name + " to " + self.to


class ZNSWebhookLog(models.Model):
    oa = models.CharField(max_length=255, null=True, blank=True)
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ZNSTemplateType(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    price = models.IntegerField(null=True, blank=True)

    def __str__(self):
        if self.name:
            return self.name
        return super(ZNSTemplateType, self).__str__()


class ZNSTemplatePurpose(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    level = models.IntegerField(null=True, blank=True)

    def __str__(self):
        if self.name:
            return self.name
        return super(ZNSTemplatePurpose, self).__str__()


class ZNSWorkspaceCustom(models.Model):
    DRAFT = 'draft'
    IN_PROGRESS = 'in_progress'
    CANCELLED = 'cancelled'
    APPROVED = 'approved'

    STATUS_CHOICES = (
        (DRAFT, 'Draft'),
        (IN_PROGRESS, 'In Progress'),
        (CANCELLED, 'Cancelled'),
        (APPROVED, 'Approved'),
    )
    uid = models.CharField(max_length=10, null=True, blank=True)
    zns_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    template_id = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    oa = models.ForeignKey(ZaloOA, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    type = models.ForeignKey(
        ZNSTemplateType, on_delete=models.SET_NULL, null=True, blank=True
    )
    purpose = models.ForeignKey(ZNSTemplatePurpose, on_delete=models.SET_NULL, null=True, blank=True)
    preview_url = models.URLField(null=True, blank=True)
    logo_dark = models.ImageField(
        upload_to="zns/logos/",
        null=True,
        blank=True,
        verbose_name="Dark Logo",
        help_text="Upload a dark version of the logo."
    )
    logo_light = models.ImageField(
        upload_to="zns/logos/",
        null=True,
        blank=True,
        verbose_name="Light Logo",
        help_text="Upload a light version of the logo."
    )
    image1 = models.ImageField(
        upload_to="zns/images/",
        null=True,
        blank=True,
        verbose_name="Image 1",
        help_text="Upload the first image."
    )
    image2 = models.ImageField(
        upload_to="zns/images/",
        null=True,
        blank=True,
        verbose_name="Image 2",
        help_text="Upload the second image."
    )
    image3 = models.ImageField(
        upload_to="zns/images/",
        null=True,
        blank=True,
        verbose_name="Image 3",
        help_text="Upload the third image."
    )
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        if self.name:
            return self.name
        return super().__str__()


class ZNSWorkspaceCustomContent(models.Model):
    zns = models.ForeignKey(ZNSWorkspaceCustom, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    index = models.IntegerField(null=True, blank=True)
    table_content = models.JSONField(null=True, blank=True)


class ExceptionLog(models.Model):
    error_message = models.TextField(null=True, blank=True)
    stack_trace = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    oa_id = models.CharField(max_length=255, null=True, blank=True)
    tracking_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Error logged at {self.timestamp}"


class FileLog(models.Model):
    file = models.ImageField(upload_to="zns/files/", null=True, blank=True)


class SendMessageLog(models.Model):
    tracking_id = models.CharField(max_length=255, null=True, blank=True)
