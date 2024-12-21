import datetime

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.db.models import OuterRef, Q

from common.core.subquery import *
from progress.models import ProgressTagUserZalo
from tags.models import TagUserZalo
from utils.convert_response import convert_response
from workspace.models import Role
from zalo.models import UserZalo
from employee.models import Employee, EmployeeUserZalo, ZaloOA
from user.models import User
from customer.models import Customer, CustomerUserZalo


class ZaloUserCreate(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        phone = data.get('phone')
        user_zalo = UserZalo.objects.filter(user_zalo_id=data.get('user_zalo_id')).first()
        if user_zalo:
            user_zalo.name = data.get('name')
            user_zalo.phone = phone if phone != 0 else None
            user_zalo.user_zalo_id = data.get('user_zalo_id')
            user_zalo.avatar_small = data.get('avatar_small')
            user_zalo.avatar_big = data.get('avatar_big')
            user_zalo.is_follower = data.get('is_follower')
            user_zalo.last_message_reply=data.get('last_message_reply')
            user_zalo.message_quota_type=data.get('message_quota_type')
            user_zalo.message_remain=data.get('message_remain')
            user_zalo.message_quota=data.get('message_quota')
            user_zalo.save()
            return convert_response('user_zalo_id tồn tại đã được cập nhật', 200)
        user_zalo = UserZalo.objects.create(
            name=data.get('name'),
            phone=phone if phone != 0 else None,
            user_zalo_id=data.get('user_zalo_id'),
            avatar_small=data.get('avatar_small'),
            avatar_big=data.get('avatar_big'),
            oa_id=data.get('oa_id'),
            is_follower=data.get('is_follower'),
            last_message_reply=data.get('last_message_reply'),
            message_quota_type=data.get('message_quota_type'),
            message_remain=data.get('message_remain'),
            message_quota=data.get('message_quota'),
        )

        oa = ZaloOA.objects.get(id=data.get('oa_id'))

        if phone :
            if len(phone) > 10:
                customer = Customer.objects.create(
                    prefix_name=data.get('name'),
                    phone=phone,
                    address=data.get('address'),
                    workspace=oa.company,
                )
                CustomerUserZalo.objects.create(
                    user_zalo=user_zalo,
                    oa=oa,
                    customer=customer
                )

        oa_id = data.get('oa_id')
        total_user = UserZalo.objects.filter(oa_id=oa_id).count()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'oa_{str(oa_id)}',
            {
                'type': 'message_handler',
                'message': {
                    'sync_done': total_user,
                }
            },
        )
        return convert_response('success', 200, data=user_zalo.id)


class ZaloUserSendSyncProcess(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        oa_id = request.data.get('oa_id')
        if not oa_id:
            return convert_response('yêu cầu oa id', 400)
        total_user = request.data.get('total_user', 0)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'oa_{str(oa_id)}',
            {
                'type': 'message_handler',
                'message': {
                    'total_sync': total_user,
                }
            },
        )
        return convert_response('success', 200)
        pass


class ZaloUserList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            data = request.GET.copy()
            page_size = int(data.get('page_size', 20))
            offset = (int(data.get('page', 1)) - 1) * page_size
            oa = data.get('oa')
            oa_ins = ZaloOA.objects.get(id=oa)
            if not oa:
                raise Exception('thiếu thông tin Oa')
            customers = UserZalo.objects.filter(oa_id=oa)

            employee_user = Employee.objects.filter(account=user, workspace=oa_ins.company).first()
            if not employee_user:
                raise Exception('Bạn không có quyền truy cập Oa')
            
            if employee_user.role == Role.Code.SALE:
                employee_userzalo = EmployeeUserZalo.objects.filter(employee=employee)
                customers_id = employee_userzalo.values_list('customer_id', flat=True)
                customers = customers.filter(id__in=customers_id)

            is_follow = data.get('is_follow')
            if is_follow:
                is_follow = True if is_follow == 'true' else False
                customers = customers.filter(is_follower=is_follow)

            search = data.get('search')
            if search:
                customers = customers.filter(Q(name__icontains=search) | Q(phone__icontains=search))

            employee = data.get('employee')
            if employee:
                employee_customer = EmployeeUserZalo.objects.filter(employee_id=employee)
                customers_id = employee_customer.values_list('customer_id', flat=True)
                customers = customers.filter(id__in=customers_id)

            user_subquery = SubqueryJson(
                User.objects.filter(id=OuterRef('employee__account_id')).values(
                    'phone', 'full_name', 'avatar', 'email'
                )
            )

            employee_subquery = SubqueryJsonAgg(
                EmployeeUserZalo.objects.filter(customer_id=OuterRef('id')).values().annotate(
                    user=user_subquery
                )
            )

            tags_subquery = SubqueryJsonAgg(
                TagUserZalo.objects.filter(user_zalo_id=OuterRef('id')).values(
                    'tag__title', 'tag__color_text', 'tag__color_fill', 'tag__color_border'
                )
            )

            progress_tag_subquery = SubqueryJson(
                ProgressTagUserZalo.objects.filter(user_zalo_id=OuterRef('id')).values(
                    'tag__progress__title', 'tag__type', 'tag__title', 'tag__color_text', 'tag__color_fill', 'tag__color_border'
                )[:1]
            )

            total = customers.count()
            customers = customers.order_by('-id').values()[offset: offset + page_size].annotate(
                employee=employee_subquery,
                tags=tags_subquery,
                progress=progress_tag_subquery,
            )
            return convert_response('success', 200, data=customers, total=total)
        except Exception as e:
            return convert_response(str(e), 400)


class ZaloUserDetail(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        user = request.user
        data = request.data.copy()
        try:
            user_zalo = UserZalo.objects.get(id=pk)
            user_zalo.name = data.get('name', user_zalo.name)
            user_zalo.phone = data.get('phone', user_zalo.phone)
            user_zalo.prefix_name = data.get('prefix_name', user_zalo.prefix_name)
            user_zalo.address = data.get('address', user_zalo.address)
            user_zalo.gender = data.get('gender', user_zalo.gender)
            user_zalo.birthday = datetime.datetime.strptime(data.get('birthday'), "%d/%m/%Y") if data.get('birthday') else None
            user_zalo.updated_at = datetime.datetime.now()

            if data.get('phone'):
                customer_ins = Customer.objects.filter(phone=data.get('phone', user_zalo.phone)).first()
                if not customer_ins:
                    Customer.objects.create(
                        prefix_name=data.get('name', user_zalo.name),
                        phone=data.get('phone', user_zalo.phone),
                        address=data.get('address', user_zalo.address),
                        gender=data.get('gender', user_zalo.gender),
                        birthday=datetime.datetime.strptime(data.get('birthday'), "%d/%m/%Y") if data.get('birthday') else None,
                        workspace=user_zalo.oa.company,
                        created_by=user,
                    )

            tags = data.get('tags', [])
            for tag in tags:
                tag_user_zalo = TagUserZalo.objects.filter(user_zalo=user_zalo, tag_id=tag).first()
                if not tag_user_zalo:
                    TagUserZalo.objects.create(
                        user_zalo=user_zalo,
                        tag_id=tag,
                        created_by=user
                    )
            
            tags = data.get('tags_remove', [])
            for tag in tags:
                tag_user_zalo = TagUserZalo.objects.filter(user_zalo=user_zalo, tag_id=tag).first()
                if tag_user_zalo:
                    tag_user_zalo.delete()

            tag_progress = data.get('tag_progress')
            if tag_progress:
                tag_user_zalo_ins = ProgressTagUserZalo.objects.filter(user_zalo=user_zalo)
                for item in tag_user_zalo_ins:
                    item.delete()
                tag_user_zalo = ProgressTagUserZalo.objects.filter(tag_id=tag_progress, user_zalo=user_zalo).first()
                if not tag_user_zalo:
                    ProgressTagUserZalo.objects.create(
                        tag_id=tag_progress,
                        user_zalo=user_zalo,
                        created_by=user,
                    )
            tag_progress = data.get('tag_progress_remove')
            if tag_progress:
                tag_user_zalo = ProgressTagUserZalo.objects.filter(tag_id=tag_progress, user_zalo=user_zalo).first()
                if tag_user_zalo:
                    tag_user_zalo.delete()

            user_zalo.save()
            return convert_response('success', 200)
        except Exception as e:
            return convert_response(str(e), 400)
