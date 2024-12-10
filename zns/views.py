import json
from typing import Optional

from django.db import transaction
from django.db.models import OuterRef, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.core.subquery import *

from employee.models import Employee
from utils.convert_response import convert_response
from zalo.models import ZaloOA
from zns.models import Zns, ZnsComponentZns, ZnsComponent, ZnsParams
from zns.utils import (
    createZnsFieldTitle, createZnsFieldParagraph, createZnsFieldOTP,
    createZnsFieldTable, createZnsFieldLogo, createZnsFieldImage,
    createZnsFieldButton, createZnsFieldPayment, createZnsFieldVoucher
)


class ZnsApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = request.GET.copy()
        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size
        ws = Employee.objects.filter(
            account=user
        ).values_list('workspace_id', flat=True)

        oas = ZaloOA.objects.filter(company_id__in=ws).values_list('id', flat=True)

        zns = Zns.objects.filter(oa_id__in=oas)
        search = data.get('search')
        if search:
            zns = zns.filter(Q(name__icontains=search) | Q(template__icontains=search))
        total = zns.count()

        oa_query = data.get('oa')
        if oa_query:
            zns = zns.filter(oa_id=oa_query)

        status = data.get('status')
        if status:
            zns = zns.filter(status=status)

        type_zns = data.get('type')
        if type_zns:
            zns = zns.filter(type=type_zns)

        tag = data.get('tag')
        if tag:
            zns = zns.filter(tag=tag)

        oa_subquery = SubqueryJson(
            ZaloOA.objects.filter(id=OuterRef('oa_id')).values(
                'id', 'oa_name', 'oa_avatar'
            )[:1]
        )

        zns = zns.order_by('-id')[offset: offset + page_size].values().annotate(
            oa_data=oa_subquery
        )

        return convert_response('success', 200, data=zns, total=total)


class ZnsCreateApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data.copy()
        data = json.loads(request.POST.get('data'))
        files = request.FILES.getlist('images', None)
        logo_light = request.FILES.get('logo_light', None)
        logo_dark = request.FILES.get('logo_dark', None)

        try:
            with transaction.atomic():
                zns = Zns.objects.create(
                    name=data.get('name'),
                    type=data.get('type'),
                    tag=data.get('tag'),
                    oa_id=data.get('oa'),
                    note=data.get('note'),
                    created_by=user,
                )

                components = data.get('components', [])
                for item in components:
                    err = create_zns_field(zns, item, files, logo_light, logo_dark)
                    if err:
                        raise Exception(err)

                params = data.get('params', [])
                for item in params:
                    ZnsParams.objects.create(
                        zns=zns,
                        name=item.get('name'),
                        type=item.get('type'),
                        sample_value=item.get('sample_value')
                    )

                return convert_response('success', 201, data=zns.id)
        except Exception as e:
            return convert_response(str(e), 400)


def create_zns_field(zns: Zns, data, files, logo_light, logo_dark) -> Optional[str]:
    type_field = data.get('type')
    if type_field == 'TITLE':
        createZnsFieldTitle(zns=zns, data=data)
    elif type_field == 'PARAGRAPH':
        createZnsFieldParagraph(zns=zns, data=data)
    elif type_field == 'OTP':
        createZnsFieldOTP(zns=zns, data=data)
    elif type_field == 'TABLE':
        createZnsFieldTable(zns=zns, data=data)
    elif type_field == 'LOGO':
        if not logo_dark or not logo_light:
            return 'Thiếu trường ảnh Logo sáng/tối'
        createZnsFieldLogo(zns=zns, data=data, logo_light=logo_light, logo_dark=logo_dark)
    elif type_field == 'IMAGES':
        if not files or len(files) == 0:
            return 'Thiếu trường ảnh'
        createZnsFieldImage(zns=zns, data=data, files=files)
    elif type_field == 'BUTTON':
        createZnsFieldButton(zns=zns, data=data)
    elif type_field == 'PAYMENT':
        createZnsFieldPayment(zns=zns, data=data)
    elif type_field == 'VOUCHER':
        createZnsFieldVoucher(zns=zns, data=data)
    return None
