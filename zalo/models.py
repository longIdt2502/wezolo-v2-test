from django.db import models

from user.models import User
from workspace.models import Workspace
from django.utils.translation import gettext_lazy as _

created_at_field = models.DateTimeField(_("Created at"), auto_now_add=True)
from datetime import datetime


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
    company = models.ForeignKey(
        Workspace, on_delete=models.SET_NULL, null=True, blank=True, related_name="zalo_company")
    secret_app = models.CharField(max_length=255, null=True, blank=True)
    url_callback = models.CharField(max_length=255, null=True, blank=True)
    app_id = models.CharField(max_length=255, null=True, blank=True)
    oa_id = models.CharField(max_length=255, null=True, blank=True)
    oa_name = models.CharField(max_length=255, null=True, blank=True)
    oa_img = models.URLField(max_length=200, blank=True, null=True)
    cate_name = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    oa_type = models.IntegerField(default=2)
    num_follower = models.IntegerField(default=0)
    package_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = created_at_field
    activate = models.BooleanField(default=False)
    refresh_token = models.TextField(null=True, blank=True)
    access_token = models.TextField(null=True, blank=True)
    retry = models.IntegerField(null=True, blank=True)
    token_expired_at = models.DateTimeField(null=True, blank=True)
    verify_hook_url = models.CharField(max_length=255, null=True, blank=True)
    verify_html_file = models.FileField(null=True, blank=True, upload_to="zaloa/verify")

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


class UserZalo(models.Model):
    zalo_name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=('zname'))
    phone = models.CharField(max_length=20, null=True, blank=True)
    user_id = models.CharField(
        max_length=300, blank=True, null=True, verbose_name=('UID'))
    created_at = created_at_field
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    zalo_img = models.URLField(max_length=200, blank=True, null=True)
    last_message_time = models.DateTimeField(null=True, blank=True)
    user_gender = models.CharField(
        max_length=10, blank=True, null=True, verbose_name=('gender'))
    activate = models.BooleanField(default=True)
    oa_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    oa_instance = models.ForeignKey(
        ZaloOA, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        super(UserZalo, self).save(*args, **kwargs)
        _id = self.pk
        other_users = UserZalo.objects.filter(user_id=self.user_id, oa_id=self.oa_id).exclude(
            pk=self.pk)
        if other_users.count() > 0:
            other_users.delete()


class UserZaloTag(models.Model):
    user_zalo = models.ForeignKey(UserZalo, on_delete=models.CASCADE)
    tag_id = models.IntegerField(null=True, blank=True)


class Message(models.Model):
    send_by = models.IntegerField(choices=SendBy.choices, default=SendBy.USER)
    send_at = models.DateTimeField(_("Sent at"), null=True, blank=True)
    user = models.ForeignKey(
        UserZalo, on_delete=models.SET_NULL, null=True, blank=True)
    user_uid = models.CharField(null=True, blank=True, max_length=50, db_index=True)
    oa_uid = models.CharField(max_length=50, null=True, blank=True)
    oa = models.ForeignKey(
        ZaloOA, on_delete=models.SET_NULL, null=True, blank=True)
    message_id = models.CharField(max_length=255, null=True, blank=True)
    tracking_id = models.CharField(max_length=255, null=True, blank=True)
    message_text = models.TextField(null=True, blank=True)
    timestamp = models.FloatField(null=True, blank=True, db_index=True)
    read = models.BooleanField(default=False)
    success = models.BooleanField(default=False)
    use_oa_send = models.BooleanField(default=True)

    def convert_ts_to_datetime(self):
        if self.timestamp is None:
            return
        dt = datetime.fromtimestamp(self.timestamp)
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
