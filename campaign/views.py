from datetime import datetime
import json
import random
from django.db.models import OuterRef, Q, F
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.files.base import ContentFile
from employee.models import EmployeeOa, Employee
from package.models import Price
from utils.check_financial_capacity import checkFinancialCapacity
from utils.convert_response import convert_response
from common.core.subquery import *
from common.s3 import AwsS3
from wallet.models import Wallet, WalletTransaction
from workspace.models import Role
from zalo.models import ZaloOA
from customer.models import CustomerUserZalo, Customer
from .models import Campaign, CampaignMessage, CampaignZns, StatusMessage

# Create your views here.
class CampaignApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            data = request.GET.copy()

            page_size = int(data.get('page_size', 20))
            offset = (int(data.get('page', 1)) - 1) * page_size

            ws = data.get('workspace')
            if not ws:
                raise Exception('Yêu cầu thông tin Workspace')
            employee = Employee.objects.filter(account=user, workspace_id=ws).first()
            if not employee:
                raise Exception('Không có quyền truy cập Campaign trong Workspace')

            campaign = Campaign.objects.filter(oa__company_id=ws)

            oa = data.get('oa')
            if oa:
                if employee.role == Role.Code.SALE:
                    employee_oa = EmployeeOa.objects.filter(employee=employee).values_list('oa_id', flat=True)
                    if oa not in employee_oa:
                        raise Exception('Không có quyền truy cập Campaign trong OA')
                campaign = campaign.filter(oa_id=oa)
            
            total_campaign_message = campaign.filter(type=Campaign.Type.MESSAGE).count()
            total_campaign_zns = campaign.filter(type=Campaign.Type.ZNS).count()
            
            search = data.get('search')
            if search:
                campaign = campaign.filter(name__icontains=search)

            status = data.get('status')
            if status:
                campaign = campaign.filter(status=status)
            
            type_campaign = data.get('type_campaign')
            if type_campaign:
                campaign = campaign.filter(type=type_campaign)
            
            campaign = campaign[offset: offset + page_size].values().annotate(
                user_created=F('created_by__full_name')
            )
            
            return convert_response('success', 200, data=campaign, total_campaign_zns=total_campaign_zns, total_campaign_message=total_campaign_message)
        except Exception as e:
            return convert_response(str(e), 400)

    def post(self, request):

        try:
            user = request.user
            data = json.loads(request.POST.get('data'))

            # Check wallet balance
            oa = ZaloOA.objects.get(id=data.get('oa'))
            employee = Employee.objects.filter(account=user, workspace=oa.company).first()
            if not employee:
                raise Exception('Bạn không có quyền thực hiện')
            if employee.role == Role.Code.SALE:
                employee_oa = EmployeeOa.objects.filter(employee__account=user, oa=oa).first()
                if not employee_oa and employee_oa.employee.role == Role.Code.SALE:
                    raise Exception('Bạn không có quyền thực hiện')
            owner = employee.workspace.created_by
            wallet = Wallet.objects.get(owner=owner)

            price_zns = data.get('price_zns', 0)
            if not isinstance(price_zns, (int, float)):
                raise Exception('Giá trị `price_zns` không hợp lệ.')

            if wallet.balance < price_zns:
                raise Exception('Số dư ví không đử để chạy chiến dịch')

            image = request.FILES.get('image')
            if image:
                r = random.randint(100000, 999999)
                file_name = f"{r}.png"
                file = ContentFile(image.read(), name=file_name)
                url_file = AwsS3.upload_file(file, 'campaign/')
                data['message_file'] = {
                    "type": "template",
                    "payload": {
                        "template_type": "media",
                        "elements": [{
                            "media_type": "image",
                            "url": url_file
                        }]
                    }
                }
            token_file = data.get('token_file')
            if token_file:
                data['message_file'] = {
                    "type": "file",
                    "payload": {
                        "token": token_file
                    }
                }
            data['created_by'] = user.id
            campaign = Campaign().from_json(data=data)
            
            if campaign.type == Campaign.Type.MESSAGE:
                user_zalos = data.get('user_zalos', [])
                for id in user_zalos: 
                    CampaignMessage.objects.create(
                        campaign=campaign,
                        user_zalo_id=id,
                        status=StatusMessage.PENDING
                    )
            
            # get price to sent 1 zns message
            _, _, price = checkFinancialCapacity(owner, Price.Type.ZNS)
            if campaign.type == Campaign.Type.ZNS:
                customers = data.get('customers', [])
                for id in customers:
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        user=owner,
                        type=WalletTransaction.Type.OUT_ZNS,
                        method=WalletTransaction.Method.CASH,
                        oa=oa,
                        used_at=datetime.now(),
                        amount=price.value.value,
                        total_amount=price.value.value,
                    )
                    CampaignZns.objects.create(
                        campaign=campaign,
                        customer_id=id,
                        zns_params=data.get('zns_params'),
                        status=StatusMessage.PENDING,
                        zns_id=data.get('zns')
                    )

            return convert_response('success', 200, data=campaign.id)
        except Exception as e:
            return convert_response(str(e), 400)


class CampaignDetailApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            user = request.user

            campaign = Campaign.objects.get(id=pk)

            employee = Employee.objects.filter(account=user, workspace=campaign.oa.company).first()
            if not employee:
                raise Exception('Không có quyền truy cập Campaign trong Workspace')


            if employee.role == Role.Code.SALE:
                employee_oa = EmployeeOa.objects.filter(employee=employee).values_list('oa_id', flat=True)
                if campaign.oa not in employee_oa:
                    raise Exception('Không có quyền truy cập Campaign trong OA')
            
            return convert_response('success', 200, data=campaign.to_json())
        except Exception as e:
            return convert_response(str(e), 400)


class CampaignListMessageApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            user = request.user
            data = request.GET.copy()
            page_size = int(data.get('page_size', 20))
            offset = (int(data.get('page', 1)) - 1) * page_size

            campaign = Campaign.objects.get(id=pk)
            messages = []
            total = 0
            search = data.get('search', '')
            if campaign.type == Campaign.Type.ZNS:
                customer_user_zalo_subquery = SubqueryJson(
                    CustomerUserZalo.objects.filter(customer_id=OuterRef('customer_id')).values(
                        'user_zalo__name', 'user_zalo__avatar_small', 'user_zalo__avatar_big', 'user_zalo__phone'
                    )
                )
                customer_subquery = SubqueryJson(
                    Customer.objects.filter(id=OuterRef('customer_id')).values(
                        'id', 'prefix_name', 'phone', 'email'
                    )[:1]
                )
                messages = CampaignZns.objects.filter(campaign=campaign).filter(
                    Q(customer__prefix_name__icontains=search) | Q(customer__phone__icontains=search)
                )
                total = messages.count()
                messages = messages[offset: offset + page_size].values(

                ).annotate(
                    customer=customer_subquery,
                    user_zalo=customer_user_zalo_subquery,
                    zns_preview=F('zns__preview')
                )
            if campaign.type == Campaign.Type.MESSAGE:
                messages = CampaignMessage.objects.filter(campaign=campaign).filter(
                    Q(user_zalo__name__icontains=search) | Q(user_zalo__phone__icontains=search)
                )
                total = messages.count()
                messages = messages[offset: offset + page_size].values(
                    'user_zalo__name', 'user_zalo__avatar_small', 'user_zalo__avatar_big',
                    'user_zalo__phone', 'status'
                )

            return convert_response('success', 200, data=messages, total=total)
        except Exception as e:
            return convert_response(str(e), 400)


class CampaignZnsDetailApi(APIView):
    permission_classes = [AllowAny]

    def put(self, request, pk):
        data = request.data.copy()
        status = data.get('status')
        campaign_zns = CampaignZns.objects.get(id=pk)
        campaign = campaign_zns.campaign
        campaign_zns.status = status
        oa = campaign_zns.campaign.oa
        wallet = Wallet.objects.get(owner=oa.company.created_by)
        # get price to sent 1 zns message
        _, _, price = checkFinancialCapacity(oa.company.created_by, Price.Type.ZNS)
        if campaign_zns.status == 'PENDING':
            if status == StatusMessage.REJECT:
                WalletTransaction.objects.create(
                    wallet=wallet,
                    user=oa.company.created_by,
                    type=WalletTransaction.Type.IN_ZNS,
                    method=WalletTransaction.Method.CASH,
                    oa=oa,
                    used_at=datetime.now(),
                    amount=price.value.value,
                    total_amount=price.value.value,
                )
                campaign.total_refund = (campaign.total_refund if campaign.total_refund else 0) + price.value.value
            else:
                campaign.total_success = (campaign.total_success if campaign.total_success else 0) + 1
        campaign.save()
        campaign_zns.save()
        return convert_response('success', 200)