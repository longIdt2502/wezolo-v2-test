import json
from datetime import datetime

from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import OuterRef, Count, Sum, IntegerField, FloatField, Value
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from common.core.subquery import *
from employee.models import Employee

from utils.check_financial_capacity import checkFinancialCapacity
from utils.convert_response import convert_response
from workspace.models import Workspace, Role
from wallet.models import Wallet, WalletTransaction
from package.models import Package, Price
from user.models import Address
from zalo.models import ZaloOA
from reward.models import RewardTier, RewardBenefit


class Workspaces(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = request.GET.copy()
        user = request.user
        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size
        search = data.get('search', '')
        type = data.get('type', Role.Code.OWNER)

        roles_list = Role.objects.exclude(code=Role.Code.OWNER).values_list('id', flat=True)

        if type == Role.Code.OWNER:
            ws = Workspace.objects.filter(created_by_id=user.id)
        else:
            in_workspaces = Employee.objects.filter(account_id=user.id, role_id__in=roles_list).values_list('workspace_id', flat=True)
            ws = Workspace.objects.filter(id__in=in_workspaces)
            
        ws = ws.filter(name__icontains=search)
        status = data.get('status')
        if status:
            ws = ws.filter(status=status)

        category = data.get('category')
        if category:
            ws = ws.filter(category=category)

        # "created_at" | "-created_at"
        order_by_time = data.get('order_by_time')
        if order_by_time:
            ws = ws.order_by(order_by_time)

        total_money_spent_query = Coalesce(
            Subquery(
                WalletTransaction.objects.filter(
                    oa__company_id=OuterRef('id')
                ).values('total_amount').annotate(
                    total=Sum('total_amount')
                ).values('total')[:1],
                output_field=FloatField()
            ),
            Value(0),
            output_field=FloatField()
        )

        role_data = SubqueryJson(
            Employee.objects.filter(account_id=user.id, workspace_id=OuterRef('id')).values('id')[:1]
            .annotate(
                role_data=SubqueryJson(
                    Role.objects.filter(id=OuterRef('role')).values()[:1]
                )
            )
        )
        ws = ws.values().annotate(
            total_money_spent=total_money_spent_query,
            role=role_data
        )

        order_by_money_spent = data.get('order_by_money_spent')
        if order_by_money_spent:
            ws = ws.order_by(order_by_money_spent)

        total = ws.count()
        ws = ws[offset: offset + page_size]

        return convert_response('success', 200, data=ws, total=total)

    def post(self, request):
        try:
            with transaction.atomic():
                data = json.loads(request.POST.get('data'))
                user = request.user
                wallet = Wallet.objects.filter(owner=user).first()
                ws_count = Workspace.objects.filter(created_by=user).count()
                if ws_count > 0:
                    can_transact, wallet, benefit = checkFinancialCapacity(user, Price.Type.CREATE_WS)
                    if not can_transact:
                        raise Exception('Số dư ví không đủ để thực hiện thao tác')
                    # wallet.balance = wallet.balance - benefit.value.value
                    # wallet.save()

                data['created_by'] = user.id
                ws = Workspace().from_json(data)
                role = Role.objects.get(code=Role.Code.OWNER)
                Employee.objects.create(
                    status=Employee.Status.ACTIVE,
                    account=user,
                    created_by=user,
                    role=role,
                    workspace=ws
                )
                files = request.FILES.get('image')
                ws = ws.save_image(files)

                address_data = request.POST.get('address')
                if address_data:
                    address_data = json.loads(request.POST.get('address'))
                    address_ins = Address().create_from_json(address_data)
                    ws.address = address_ins
                    ws.save()

                if ws_count == 0 and not user.package:
                    package = Package.objects.get(code='FREE_TRIAL')
                    reward_tier = RewardTier.objects.get(code='BRONZE')
                    user.package = package
                    user.package_start = datetime.now()
                    user.package_active = True
                    user.level = user.level if user.level else reward_tier
                    user.save()
                else:
                    WalletTransaction.objects.create(
                        user=user,
                        type=WalletTransaction.Type.OUT_CREATE_WS,
                        method='TRANSFER',
                        amount=1500000,
                        total_amount=1500000,
                        wallet=wallet,
                    )
                return convert_response('Tạo workspace thành công', 201, data=ws.to_json())

        except Exception as e:
            return convert_response(str(e), 400)


class WorkspaceDetail(APIView):

    def get(self, request, pk):
        ws = Workspace.objects.filter(id=pk).first()
        if not ws:
            return convert_response('workspace không tồn tại hoặc đã bị vô hiệu', 404)
        res = ws.to_json()
        return convert_response('success', 200, data=res)

    def put(self, request, pk):
        ws = Workspace.objects.filter(id=pk).first()
        data = json.loads(request.POST.get('data'))
        ws.update_from_json(data)

        files = request.FILES.get('image')
        if files:
            ws = ws.save_image(files)

        address_data = request.POST.get('address')
        if address_data:
            address_data = json.loads(request.POST.get('address'))
            if ws.address:
                address_ins = ws.address.update_from_json(address_data)
                ws.address = address_ins
            else:
                address_ins = Address().create_from_json(address_data)
                ws.address = address_ins
        ws.save()

        return convert_response('success', 200, data=ws.to_json())


class WorkspaceCheck(APIView):

    def post(self, request):
        user = request.user
        data = request.data.copy()
        type_check = data.get('type_check')
        if type_check == 'NAME_UNIQUE':
            name = data.get('name')
            if not name:
                return convert_response('Kiểm tra thông tin cần dữ liệu tên công ty', 400)
            ws = Workspace.objects.filter(name=name).first()
            if not ws:
                return convert_response('Tên công ty không tồn tại', 404)
        if type_check == 'CREATE':
            ws = Workspace.objects.filter(created_by=user)
            wallet = Wallet.objects.filter(owner=user).first()
            ws_count = ws.count()
            if ws_count > 0 and wallet.balance < 1500000:
                return convert_response('Không đủ điều kiện tạo thêm workspace', 200, data=False)
            return convert_response('success', 200, data=True)
        return convert_response('mã check không tồn tại (NAME_UNIQUE | CREATE)', 400)


class WorkspacePriceCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        ws = Workspace.objects.filter(created_by=user)
        if len(ws) == 0:
            return convert_response('success', 200, data={
                "price": 0,
                "discount": 1500000
            })

        rb = RewardBenefit.objects.filter(tier_id=user.level, type='CREATE_WS').exclude(value__value=0).first()
        if not rb:
            return convert_response('Không tim thấy gói giá phù hợp', 400)

        return convert_response('success', 200, data={
            "price": rb.value.value,
            "discount": 0,
            "tier": user.level.name
        })


class RoleAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, _):
        roles = Role.objects.filter().exclude(code=Role.Code.OWNER).values()
        return convert_response('success', 200, data=roles)


class WorkspacesAdmin(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = request.GET.copy()
        user = request.user
        if not user.is_superuser:
            return convert_response('Truy cập bị từ chối', 403)
        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size
        search = data.get('search', '')
        user_query = data.get('user')

        ws = Workspace.objects.filter()
        total = ws.count()

        if user_query:
            ws = ws.filter(created_by_id=user_query)
            total = ws.count()

        ws = ws.filter(name__icontains=search)[offset: offset + page_size].values().annotate(
            # total_money_spent=total_money_spent_query,
            total_oa=Subquery(
                ZaloOA.objects.filter(company_id=OuterRef('id')).values('id').annotate(
                    total=Count('id')
                ).values('total')[:1],
                output_field=IntegerField()
            ),
            total_money_spent=Subquery(
                WalletTransaction.objects.filter(
                    oa_id__company=OuterRef('id')
                ).values('total_amount').annotate(total=Sum('total_amount')).values('total')[:1],
                output_field=IntegerField()
            ),
            total_money_spent_mmonth=Subquery(
                WalletTransaction.objects.filter(
                    oa_id__company=OuterRef('id'), created_at__gte=datetime.now().replace(day=1)
                ).values('total_amount').annotate(total=Sum('total_amount')).values('total')[:1],
                output_field=IntegerField()
            ),
        )

        return convert_response('success', 200, data=ws, count=total)


class WorkspacesAdminAction(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        data = request.data.copy()
        user = request.user
        if not user.is_superuser:
            return convert_response('Truy cập bị từ chối', 403)

        ws = Workspace.objects.get(id=pk)

        ws.status = data.get('status', ws.status)
        ws.dev_note = data.get('dev_note', ws.dev_note)
        ws.save()
        return convert_response('success', 200, data=ws.to_json())


class Workplace(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = request.GET.copy()
        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size
        search = data.get('search', '')

        employee = Employee.objects.filter(account=user).exclude(role__code=Role.Code.OWNER)
        ws_ids = employee.values_list('workspace_id', flat=True)
        ws = Workspace.objects.filter(id__in=ws_ids)
        total = ws.count()
        ws = ws.filter(name__icontains=search)
        ws = ws[offset: offset + page_size].values()
        return convert_response('success', 200, data=ws, total=total)


