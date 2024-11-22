import json
import os
import random
import requests
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.authtoken.models import Token
from common.pref_keys import PrefKeys

from user.util import send_verify_otp
from utils.convert_response import convert_response
from user.serializers import UserSerializer
from rest_framework.permissions import AllowAny
from django.utils import timezone

from user.models import User, Verify, City, District, Ward
from wallet.models import Wallet


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        username = request.data.get("phone", None)
        password = request.data.get("password", None)
        if not (username and password):
            return convert_response("Required username and password", 400)
        digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        otp = ''.join(random.choice(digits) for i in range(6))
        otp = '123456'
        try:
            user = User.objects.get(phone=username)
            if user.is_active:
                return convert_response('username already exist', 400)
            else:
                verify = Verify.objects.get(phone_number=username)
                verify.otp = otp
                verify.expired_at = datetime.now() + timedelta(seconds=90)
                verify.save()
                # send_verify_otp(username, otp)
                return convert_response('success', 200, data={"verify_id": verify.id})
        except Exception:
            User().fromJson(data)
            verify = Verify.objects.create(
                email=data.get('email'),
                phone_number=username,
                otp=otp,
                type='REGISTER'
            )
            # send_verify_otp(username, otp)
            return convert_response('success', 200, data={"verify_id": verify.id})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", None)
        password = request.data.get("password", None)
        if not (username and password):
            return convert_response("Required username and password", 400)
        user = User.objects.filter(phone=username).first()
        if not user:
            return convert_response(f"User not found with username {username}", 400)
        if not user.check_password(password):
            return convert_response("Password is wrong", 400)
        if not user.is_active:
            return convert_response("User not verify", 400)
        token, _ = Token.objects.get_or_create(user=user)
        user.last_login = datetime.now()
        user.save()
        return convert_response('Success',
                                200,
                                data={
                                    "token": token.key,
                                    "user": user.to_json(),
                                    # "workspaces": user.workspace_account.all().count()
                                    }
                                )


class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        verify_id = data.get('verify')
        otp = data.get('otp')
        try:
            verify = Verify.objects.get(id=verify_id)
            if verify.otp == otp and verify.expired_at > timezone.now():
                verify.status = True
                verify.save()
                user = User.objects.get(phone=verify.phone_number)
                # create wallet in service Wallet
                wallet_payload = {
                  "name": user.phone,
                  "metadata": {},
                  "source": "WZL"
                }
                wallet_url = os.getenv(PrefKeys.WALLET_URL)
                response = requests.request("POST", f'{wallet_url}/v1/api/external/wallets-create/', headers={}, data=wallet_payload)
                response = response.json()['data']
                print(response)
                # create wallet in db
                if response:
                    Wallet.objects.create(
                        wallet_uid=response['uid'],
                        private_key=response['privateKey'],
                        balance=0,
                        owner=user
                    )

                # update user info
                user.is_active = True
                user.last_login = datetime.now()
                user.save()
                token, _ = Token.objects.get_or_create(user=user)
                return convert_response('success', 200, data={
                                    "token": token.key,
                                    "user": user.to_json(),
                                    # "workspaces": user.workspace_account.all().count()
                                    })
            else:
                return convert_response('OTP invalid or expired', 400)
        except Exception as e:
            return convert_response(f'not find verify Id: {str(e)}', 404)


class ResendOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        phone = request.data.get("phone", None)
        type_verify = request.data.get("type_verify", None)
        verify = Verify.objects.filter(phone_number=phone, type=type_verify).first()
        if not verify:
            return convert_response('can not find verify user', 404)
        digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        otp = ''.join(random.choice(digits) for i in range(6))
        otp = '123456'
        verify.otp = otp
        verify.expired_at = datetime.now() + timedelta(seconds=90)
        verify.save()
        return convert_response('success', 200)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return convert_response('success', 200, data=user.to_json())

    def put(self, request):
        user = request.user
        data = json.loads(request.POST.get('data'))
        image = request.FILES.get('image')
        user.update_from_json(data)
        if image:
            user.upload_image(image)
        res = user.to_json()
        return convert_response('success', 200, data=res)


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        phone = request.data.get("phone", None)
        digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        otp = ''.join(random.choice(digits) for i in range(6))
        otp = '123456'
        verify = Verify.objects.create(
            phone_number=phone,
            otp=otp,
            type='FORGOT_PASSWORD'
        )
        return convert_response('success', 200, data={"verify_id": verify.id})


class ForgotPasswordConfirmOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        verify_id = data.get("verify_id", None)
        otp = data.get("otp", None)
        try:
            verify = Verify.objects.get(id=verify_id)
            if verify.otp == otp and verify.expired_at > timezone.now():
                verify.status = True
                verify.save()
                return convert_response('success', 200)
            else:
                return convert_response('OTP invalid or expired', 400)
        except Exception:
            return convert_response('not find verify Id', 404)


class SetNewPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        phone = request.data.get("phone", None)
        password = request.data.get("password", None)
        password_new = request.data.get("password_new", None)
        verify_id = request.data.get("verify_id", None)
        user = User.objects.get(phone=phone)
        if user.check_password(password):
            user.set_password(password_new)
            user.save()
            return convert_response('success', 200)
        try:
            verify = Verify.objects.get(id=verify_id)
            if not verify.status:
                return convert_response('can not verify action', 400)
            user.set_password(password_new)
            user.save()
            return convert_response('success', 200)
        except Exception:
            return convert_response('user not exist', 404)


class CityListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cities = City.objects.all().order_by('id')
        search = request.GET.get('search')
        if search:
            cities = cities.filter(nam_icoe_ntains=search)
        cities = cities.values(
            "name", "slug", "type", "name_with_type", "code", "id"
        )
        return convert_response('Success', 200, data=cities)


class DistrictListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        city_id = request.GET.get('city')
        search = request.GET.get('search')
        districts = City.objects.get(id=city_id).districts.all().order_by('id')
        if search:
            districts = districts.filter(name__icontains=search)
        districts = districts.values("name", "slug", "type", "name_with_type", "code", "id")
        return convert_response('Success', 200, data=districts)


class WardListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        district_id = request.GET.get('district')
        search = request.GET.get('search')
        wards = District.objects.get(id=district_id).wards.all().order_by('id')
        if search:
            wards = wards.filter(name__icontains=search)
        wards = wards.values("name", "slug", "type", "name_with_type", "code", "id")
        return convert_response('Success', 200, data=wards)
