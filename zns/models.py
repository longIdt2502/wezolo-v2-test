from django.db import models

from bank.models import Banks
from user.models import User
from zalo.models import ZaloOA


class Zns(models.Model):
    class Meta:
        db_table = 'zns'
        verbose_name = 'ZNS'
        verbose_name_plural = 'ZNS'

    STATUS_CHOICES = [
        ('DRAFT', 'Nháp'),
        ('PENDING_WZL', 'Chờ duyệt'),
        ('PENDING_REVIEW', 'Đang duyệt'),
        ('APPROVED', 'Đã duyệt'),
        ('REJECTED', 'Đã từ chối'),
        ('LOCKED', 'Bị khóa'),
    ]

    TYPE_CHOICES = [
        (1, 'ZNS tùy chỉnh'),
        (2, 'ZNS xác thực'),
        (3, 'ZNS yêu cầu thanh toán'),
        (4, 'ZNS voucher'),
        (5, 'ZNS Đánh giá dịch vụ'),
    ]

    TAG_CHOICES = [
        (1, 'Transaction'),
        (2, 'Customer care'),
        (3, 'Promotion'),
    ]

    oa = models.ForeignKey(ZaloOA, on_delete=models.CASCADE, null=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0], null=False)
    template = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=60, null=True, blank=True)
    type = models.IntegerField(choices=TYPE_CHOICES, help_text="Loại mẫu tin.")
    tag = models.IntegerField(choices=TAG_CHOICES, help_text="Tag mẫu tin.")
    note = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, null=False, on_delete=models.CASCADE, related_name='user_created_zns')
    updated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='user_updated_zns')


class ZnsComponent(models.Model):
    class Meta:
        db_table = 'zns_component'
        verbose_name = 'ZnsComponent'

    TYPE_CHOICES = [
        ('TITLE', 'Tiêu đề'),
        ('PARAGRAPH', 'Đoạn văn bản'),
        ('OTP', 'Mã OTP'),
        ('TABLE', 'Bảng'),
        ('LOGO', 'Logo'),
        ('IMAGES', 'Ảnh'),
        ('BUTTONS', 'Nút bấm'),
        ('PAYMENT', 'Thanh toán'),
        ('VOUCHER', 'Phiếu quà tặng'),
    ]

    LAYOUT_CHOICES = [
        ('HEADER', 'Phần tiêu đề đầu tin'),
        ('BODY', 'Nội dung chính'),
        ('FOOTER', 'Phần cuối tin'),
    ]

    name = models.CharField(max_length=60, null=True, blank=True)
    type = models.CharField(max_length=255, choices=TYPE_CHOICES, null=True, blank=True)
    layout = models.CharField(max_length=255, choices=LAYOUT_CHOICES, null=True, blank=True)


class ZnsComponentZns(models.Model):
    class Meta:
        db_table = 'zns_component_zns'
        verbose_name = 'ZnsComponentZns'

    zns = models.ForeignKey(Zns, on_delete=models.CASCADE, null=False)
    component = models.ForeignKey(ZnsComponent, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=60, null=True, blank=True)
    order = models.IntegerField(null=True)


class ZnsFieldTitle(models.Model):
    class Meta:
        db_table = 'zns_field_title'
        verbose_name = 'ZnsFieldTitle'

    component = models.ForeignKey(ZnsComponentZns, on_delete=models.CASCADE, null=False)
    value = models.CharField(max_length=65, null=False, blank=False)


class ZnsFieldParagraph(models.Model):
    class Meta:
        db_table = 'zns_field_paragraph'
        verbose_name = 'ZnsFieldParagraph'

    component = models.ForeignKey(ZnsComponentZns, on_delete=models.CASCADE, null=False)
    value = models.TextField(null=False, blank=False)


class ZnsFieldOTP(models.Model):
    class Meta:
        db_table = 'zns_field_otp'
        verbose_name = 'ZnsFieldOTP'

    component = models.ForeignKey(ZnsComponentZns, on_delete=models.CASCADE, null=False)
    value = models.CharField(max_length=10, null=False, blank=False)


class ZnsFieldTable(models.Model):
    class Meta:
        db_table = 'zns_field_table'
        verbose_name = 'ZnsFieldTable'

    TYPE_CHOICES = [
        (0, 'Không có hiệu ứng'),
        (1, 'Thành công'),
        (2, 'Cập nhật'),
        (3, 'Lưu ý'),
        (4, 'Báo lỗi'),
        (5, 'Cơ bản'),
    ]

    component = models.ForeignKey(ZnsComponentZns, on_delete=models.CASCADE, null=False)
    title = models.CharField(max_length=36, null=False, blank=False)
    value = models.CharField(max_length=90, null=False, blank=False)
    row_type = models.IntegerField(choices=TYPE_CHOICES, null=True)


class ZnsFieldLogo(models.Model):
    class Meta:
        db_table = 'zns_field_logo'
        verbose_name = 'ZnsFieldLogo'

    component = models.ForeignKey(ZnsComponentZns, on_delete=models.CASCADE, null=False)
    light = models.CharField(max_length=255, null=False, blank=False)
    dark = models.CharField(max_length=255, null=False, blank=False)


class ZnsFieldImage(models.Model):
    class Meta:
        db_table = 'zns_field_image'
        verbose_name = 'ZnsFieldImage'

    component = models.ForeignKey(ZnsComponentZns, on_delete=models.CASCADE, null=False)
    item = models.CharField(max_length=255, null=False, blank=False)


class ZnsFieldButton(models.Model):
    class Meta:
        db_table = 'zns_field_button'
        verbose_name = 'ZnsFieldButton'

    TYPE_CHOICES = [
        (1, 'Đến trang của doanh nghiệp'),
        (2, 'Gọi điện'),
        (3, 'Đến trang thông tin OA'),
        (4, 'Đến ứng dụng Zalo Mini App của doanh nghiệp'),
        (5, 'Đến trang tải ứng dụng'),
        (6, 'Đến trang phân phối sản phẩm'),
        (7, 'Đến trang web/Zalo Mini App khác'),
        (8, 'Đến ứng dụng khác'),
    ]

    component = models.ForeignKey(ZnsComponentZns, on_delete=models.CASCADE, null=False)
    button_order = models.IntegerField(null=False)
    type = models.IntegerField(choices=TYPE_CHOICES, null=True)
    content = models.CharField(max_length=255, null=False)
    title = models.CharField(max_length=30, null=False)


class ZnsFieldPayment(models.Model):
    class Meta:
        db_table = 'zns_field_payment'
        verbose_name = 'ZnsFieldPayment'

    component = models.ForeignKey(ZnsComponentZns, on_delete=models.CASCADE, null=False)
    bank_code = models.ForeignKey(Banks, on_delete=models.CASCADE, null=False)
    account_name = models.CharField(max_length=100, null=False, blank=False)
    bank_account = models.CharField(max_length=100, null=False, blank=False)
    amount = models.CharField(max_length=12, null=False, blank=False)
    note = models.CharField(max_length=90, null=False, blank=False)


class ZnsFieldVoucher(models.Model):
    class Meta:
        db_table = 'zns_field_voucher'
        verbose_name = 'ZnsFieldVoucher'

    CODE = [
        (1, 'QR code'),
        (2, 'Bar code'),
        (3, 'Text only'),
    ]

    component = models.ForeignKey(ZnsComponentZns, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=30, null=False, blank=False)
    condition = models.CharField(max_length=40, null=False, blank=False)
    start_date = models.CharField(max_length=255, null=True)
    end_date = models.CharField(max_length=255, null=True)
    voucher_code = models.CharField(max_length=25, null=False, blank=False)
    display_code = models.IntegerField(choices=CODE, null=False, default=1)


class ZnsParams(models.Model):
    class Meta:
        db_table = 'zns_params'
        verbose_name = 'ZnsParams'

    TYPE = [
        ('1', 'Tên khách hàng (30)'),
        ('2', 'Số điện thoại (15)'),
        ('3', 'Địa chỉ (200)'),
        ('4', 'Mã số (30)'),
        ('5', 'Nhãn tùy chỉnh (30)'),
        ('6', 'Trạng thái giao dịch (30)'),
        ('7', 'Thông tin liên hệ (50)'),
        ('8', 'Giới tính / Danh xưng (5)'),
        ('9', 'Tên sản phẩm / Thương hiệu (200)'),
        ('10', 'Số lượng / Số tiền (20)'),
        ('11', 'Thời gian (20)'),
        ('12', 'OTP (10)'),
        ('13', 'URL (200)'),
        ('14', 'Tiền tệ (VNĐ) (12)'),
        ('15', 'Bank transfer note (90)'),
    ]

    zns = models.ForeignKey(Zns, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=60, null=True, blank=True)
    type = models.CharField(max_length=10, null=False, choices=TYPE)
    sample_value = models.CharField(max_length=200, null=True, blank=True)


class ZnsRejectLog(models.Model):
    class Meta:
        verbose_name = 'ZnsRejectLog'
        db_table = 'zns_reject_log'

    zns = models.ForeignKey(Zns, on_delete=models.CASCADE, null=False)
    reject_date = models.DateField(auto_now_add=True)
    reject_reason = models.TextField(null=True, blank=True)
