from django.db import models


class Package(models.Model):
    class Meta:
        verbose_name = 'Package'
        db_table = 'package'

    name = models.CharField(max_length=255, null=False, blank=False)
    code = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=False, blank=False)
    price = models.IntegerField(default=0, null=False, blank=False)
    date_validity = models.IntegerField(null=True, blank=True)
    points_reward = models.BigIntegerField(default=0, null=False, blank=False)

    def from_json(self, data):
        Package.objects.create(
            name=data.get('name'),
            code=data.get('code'),
            description=data.get('description'),
            price=data.get('price'),
            date_validity=data.get('date_validity'),
            points_reward=data.get('points_reward'),
        )

    def to_json(self):
        return {
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "price": self.price,
            "date_validity": self.date_validity,
            "points_reward": self.points_reward,
        }


class Price(models.Model):
    class Meta:
        verbose_name = 'Price'
        db_table = 'price'

    class Type(models.TextChoices):
        ZNS = 'ZNS', 'Đơn giá gửi ZNS'
        CREATE_OA = 'CREATE_OA', 'Tạo zalo OA'
        CONNECT_OA = 'CONNECT_OA', 'Kết nối zalo OA'
        CREATE_WS = 'CREATE_WS', 'Tạo wordspace'
        OA_PREMIUM = 'OA_PREMIUM', 'Nâng cấp OA Premium'
        MESS = 'MESS', 'Tin nhắn vượt khung'
        START = 'START', 'Phí khởi tạo'

    type = models.CharField(max_length=255, choices=Type.choices, default=Type.ZNS, null=False, blank=False)
    value = models.IntegerField(default=0, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
