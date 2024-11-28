import json
from datetime import datetime

from rest_framework.views import APIView
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Subquery, OuterRef
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from utils.convert_response import convert_response
from workspace.models import Workspace, Role
from wallet.models import Wallet, WalletTransaction
from package.models import Package
from user.models import Address


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

        ws = Workspace.objects.filter(created_by=user, name__icontains=search)[offset: offset + page_size].values().annotate(
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
                if ws_count > 0 and wallet.balance < 1500000:
                    raise ValidationError('Đã sở hữu và không đủ tiền trong tài khoản ví')
                data['created_by'] = user.id
                ws = Workspace().from_json(data)
                files = request.FILES.get('image')
                ws = ws.save_image(files)
                if address_data:
                    address_ins = Address().create_from_json(address_data)
                    ws.address = address_ins

                if ws_count == 0 and not user.package:
                    package = Package.objects.get(code='FREE_TRIAL')
                    user.package = package
                    user.package_start = datetime.now()
                    user.package_active = True
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
