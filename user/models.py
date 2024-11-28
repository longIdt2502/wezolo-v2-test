import json
from datetime import timedelta
import random

from django.apps import apps
from django.core.files.base import ContentFile

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from vi_address.models import City, District, Ward
import uuid

from common.s3 import AwsS3


class Gender(models.TextChoices):
    MALE = 'Male', 'Nam'
    FEMALE = 'Female', 'Nữ'
    

class Address(models.Model):
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)

    @classmethod
    def create_from_json(cls, data):
        if isinstance(data, str):
            data = json.loads(data)
        district_id = data.get('district')
        ward_id = data.get('ward')
        city_id = data.get('city')
        address = data.get('address')
        instance = cls()
        if district_id:
            district = District.objects.get(pk=district_id)
            instance.district = district
        if ward_id:
            ward = Ward.objects.get(pk=ward_id)
            instance.ward = ward
        if city_id:
            city = City.objects.get(pk=city_id)
            instance.city = city
        instance.address = address
        instance.save()
        return instance

    def update_from_json(self, data):
        district_id = data.get('district')
        ward_id = data.get('ward')
        city_id = data.get('city')
        address = data.get('address')
        instance = self
        instance.district_id = district_id
        instance.ward_id = ward_id
        instance.city_id = city_id
        instance.address = address
        instance.save()
        return instance

    def to_json(self):
        city = City.objects.get(id=self.city.id)
        district = District.objects.get(id=self.district.id)
        ward = Ward.objects.get(id=self.ward.id)
        return {
            "address": self.address,
            "city": {
                "name": city.name,
                "type": city.type,
                "code": city.code
            },
            "district": {
                "name": district.name,
                "type": district.type,
                "code": district.code
            },
            "ward": {
                "name": ward.name,
                "type": ward.type,
                "code": ward.code
            }
        }


class User(AbstractUser):
    uid = models.UUIDField(default=uuid.uuid4, blank=False, null=False, editable=False, unique=True)
    phone = models.CharField(max_length=20, blank=False, null=False, unique=True)
    full_name = models.CharField(max_length=255, blank=False, null=False)
    email = models.EmailField(_('email address'), null=True, blank=True)
    gender = models.CharField(max_length=12, choices=Gender.choices, null=True, blank=True)
    avatar = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False, null=False, blank=False)
    is_superuser = models.BooleanField(default=False, null=False, blank=False)
    level = models.ForeignKey("reward.RewardTier", on_delete=models.SET_NULL, null=True)
    package = models.ForeignKey("package.Package", on_delete=models.SET_NULL, null=True)
    package_start = models.DateTimeField(null=True)
    package_active = models.BooleanField(default=False, null=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username

    def fromJson(self, data):
        user = self
        user.username = data.get('phone')
        user.phone = data.get('phone')
        user.full_name = data.get('full_name')
        user.email = data.get('email')
        user.gender = data.get('gender')
        user.set_password(data.get('password'))
        user.uid = uuid.uuid4()
        user.save()
        return user

    def to_json(self):
        wallet = apps.get_model('wallet', 'Wallet')
        wallet_ins = wallet.objects.filter(
            owner_id=self.id
        ).values('id', 'wallet_uid', 'balance').first()
        return {
            "uid": str(self.uid),
            "phone": self.phone,
            "full_name": self.full_name,
            "email": self.email,
            "gender": self.gender,
            "avatar": self.avatar if self.avatar else None,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "wallet": wallet_ins,
            "package": self.package.to_json() if self.package else None,
            "package_start": self.package_start,
            "package_active": self.package_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def update_from_json(self, request):
        user = self
        user.full_name = request.get('full_name', user.full_name)
        user.email = request.get('email', user.email)
        user.gender = request.get('gender', user.gender)
        user.save()

    def upload_image(self, file):
        r = random.randint(100000, 999999)
        file_name = f"{self.username}_{r}.png"
        image_file = ContentFile(file.read(), name=file_name)
        # AwsS3.delete_file(file_name)
        uploaded_file_name = AwsS3.upload_file(image_file, 'users/')
        self.avatar = uploaded_file_name
        self.save()
        return self


class Verify(models.Model):

    class VerifyType(models.TextChoices):
        REGISTER = 'REGISTER', 'Đăng ký'
        FORGOT_PASSWORD = 'FORGOT_PASSWORD', 'Quên mật khẩu'

    class Meta:
        verbose_name = "Verify"
        db_table = "verify"

    email = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=False, null=False)
    otp = models.CharField(max_length=6, blank=False, null=False)
    status = models.BooleanField(default=False, blank=False, null=False)
    type = models.CharField(choices=VerifyType, null=True, blank=True)
    expired_at = models.DateTimeField(default=timezone.now() + timedelta(seconds=90))


class Sessions(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(default=timezone.now())
    logout_time = models.DateTimeField()
    ip_address = models.CharField(max_length=255, null=False, blank=False)
    user_agent = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20)
    token = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(timezone.now())
    updated_at = models.DateTimeField()
