import json
from datetime import datetime

from rest_framework.views import APIView
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import OuterRef, Count, Sum, IntegerField
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from common.core.subquery import *

from utils.check_financial_capacity import CheckFinancialCapacity
from utils.convert_response import convert_response
from workspace.models import Workspace, Role
from wallet.models import Wallet, WalletTransaction
from package.models import Package, Price
from user.models import Address
from zalo.models import ZaloOA
from reward.models import RewardTier


class Workspaces(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = request.GET.copy()
        user = request.user
        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size
        search = data.get('search', '')
        # total_money_spent_query = Subquery(
        #     WalletTransaction.objects.filter(
        #
        #     )
        #     Workspace.objects.filter(
        #         id=OuterRef('id'),
        #         orders_in_wp__created_at__gte=last_filter_start,
        #         orders_in_wp__created_at__lte=last_filter_end,
        #     ).annotate(total=Sum('orders_in_wp__total_amount')).values('total')[:1],
        #     output_field=FloatField()
        # )
        ws = Workspace.objects.filter(created_by=user, name__icontains=search)

        status = data.get('status')
        if status:
            ws = ws.filter(status=status)

        ws = ws[offset: offset + page_size].values().annotate(
            # total_money_spent=total_money_spent_query,
        )

        return convert_response('success', 200, data=ws)

    def post(self, request):
        try:
            with transaction.atomic():
                data = json.loads(request.POST.get('data'))
                address_data = json.loads(request.POST.get('address'))
                user = request.user
                wallet = Wallet.objects.filter(owner=user).first()
                ws_count = Workspace.objects.filter(created_by=user).count()
                if ws_count > 0:
                    can_transact, wallet, benefit = CheckFinancialCapacity(user, Price.Type.CREATE_WS)
                    if not can_transact:
                        raise Exception('Số dư ví không đủ để thực hiện thao tác')
                    # wallet.balance = wallet.balance - benefit.value.value
                    # wallet.save()

                data['created_by'] = user.id
                ws = Workspace().from_json(data)
                files = request.FILES.get('image')
                ws = ws.save_image(files)
                if address_data:
                    address_ins = Address().create_from_json(address_data)
                    ws.address = address_ins

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
                        type='EXPENDITURE',
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


class RoleAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, _):
        roles = Role.objects.filter().values()
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
