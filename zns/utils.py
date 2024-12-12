import random
from typing import Optional

from django.core.files.base import ContentFile

from common.s3 import AwsS3
from .models import *


def createZnsComponent(zns, data) -> ZnsComponentZns:
    """
    Input: zns: Zns, data: json
    This def output is: `{ZnsComponentZns}`
    First this def check in DB ZnsComponentZns has already existed or not ?
    -> if not -> this def create a new ZnsComponentZns
    """
    component = ZnsComponent.objects.get(
        type=data.get('type'),
        layout=data.get('layout'),
    )
    zns_component_zns = ZnsComponentZns.objects.filter(
        zns=zns,
        component=component
    ).first()
    if not zns_component_zns:
        zns_component_zns = ZnsComponentZns.objects.create(
            zns=zns,
            component=component,
            order=data.get('index')
        )
    return zns_component_zns


def createZnsFieldTitle(zns, data) -> Optional[str]:
    pk = data.get('id')
    if pk:
        zns_field = ZnsFieldTitle.objects.filter(id=pk).first()
        if not zns_field:
            return 'component không tồn tại'
        if data.get('action') == 'delete':
            zns_field.delete()
            return None
        zns_field.value = data.get('value')
        zns_field.save()
        return None
    zns_component_zns = createZnsComponent(zns, data)
    ZnsFieldTitle.objects.create(
        value=data.get('value'),
        component=zns_component_zns,
    )
    return None


def createZnsFieldParagraph(zns, data) -> Optional[str]:
    pk = data.get('id')
    if pk:
        zns_field = ZnsFieldParagraph.objects.filter(id=pk).first()
        if not zns_field:
            return 'component không tồn tại'
        if data.get('action') == 'delete':
            zns_field.delete()
            return None
        zns_field.value = data.get('value')
        zns_field.save()
        return None
    zns_component_zns = createZnsComponent(zns, data)
    ZnsFieldParagraph.objects.create(
        value=data.get('value'),
        component=zns_component_zns,
    )
    return None


def createZnsFieldOTP(zns, data) -> Optional[str]:
    pk = data.get('id')
    if pk:
        zns_field = ZnsFieldOTP.objects.filter(id=pk).first()
        if not zns_field:
            return 'component OTP không tồn tại'
        if data.get('action') == 'delete':
            zns_field.delete()
            return None
        zns_field.value = data.get('value')
        zns_field.save()
        return None
    zns_component_zns = createZnsComponent(zns, data)
    ZnsFieldOTP.objects.create(
        value=data.get('value'),
        component=zns_component_zns,
    )
    return None


def createZnsFieldTable(zns, data) -> Optional[str]:
    zns_component_zns = createZnsComponent(zns, data)
    if data.get('action') == 'delete':
        zns_component_zns.delete()
        zns_fields = ZnsFieldTable.objects.filter(component=zns_component_zns)
        for item in zns_fields:
            item.delete()
        return None
    rows = data.get('rows', [])
    for item in rows:
        pk = item.get('id')
        if pk:
            zns_field = ZnsFieldTable.objects.filter(id=pk).first()
            if not zns_field:
                return 'Component Bảng, không tìm thấy hàng yêu cầu'
            if data.get('action') == 'delete':
                zns_field.delete()
            else:
                zns_field.value = item.get('value', zns_field.value)
                zns_field.title = item.get('title', zns_field.title)
                zns_field.row_type = item.get('row_type', zns_field.row_type)
                zns_field.save()
        else:
            ZnsFieldTable.objects.create(
                value=item.get('value'),
                component=zns_component_zns,
                row_type=item.get('row_type'),
                title=item.get('title'),
            )
    return None


def createZnsFieldLogo(zns, data, logo_light, logo_dark) -> Optional[str]:
    if data.get('id'):
        zns_field = ZnsFieldLogo.objects.filter(id=data.get('id')).first()
        if zns_field:
            zns_field.delete()
        else:
            return 'component Logo không tồn tại'

    r = random.randint(100000, 999999)
    file_name = f"logo_light_{r}.png"
    image_file_light = ContentFile(logo_light.read(), name=file_name)
    uploaded_file_name_light = AwsS3.upload_file(image_file_light, f'zns_image/{zns.id}/')

    file_name = f"logo_dark_{r}.png"
    image_file_dark = ContentFile(logo_dark.read(), name=file_name)
    uploaded_file_name_dark = AwsS3.upload_file(image_file_dark, f'zns_image/{zns.id}/')

    zns_component_zns = createZnsComponent(zns, data)
    ZnsFieldLogo.objects.create(
        component=zns_component_zns,
        light=uploaded_file_name_light,
        dark=uploaded_file_name_dark
    )
    return None


def createZnsFieldImage(zns, data, files) -> Optional[str]:
    zns_component_zns = createZnsComponent(zns, data)

    components = data.get('component_data')
    if components:
        for item in components:
            if item.get('action') == 'delete':
                zns_field = ZnsFieldImage.objects.get(id=item.get('id'))
                zns_field.delete()
                return None

    for file in files:
        r = random.randint(100000, 999999)
        file_name = f"image_{r}.png"
        image_file_light = ContentFile(file.read(), name=file_name)
        uploaded_file_name = AwsS3.upload_file(image_file_light, f'zns_image/{zns.id}/')

        ZnsFieldImage.objects.create(
            component=zns_component_zns,
            item=uploaded_file_name,
        )

    zns_fields = ZnsFieldImage.objects.filter(component=zns_component_zns)
    if zns_fields.count() == 0:
        zns_component_zns.delete()

    return None


def createZnsFieldButton(zns, data) -> Optional[str]:
    zns_component_zns = createZnsComponent(zns, data)
    items = data.get('items')
    if data.get('action') == 'delete':
        zns_fields = ZnsFieldButton.objects.filter(component=zns_component_zns)
        for item in zns_fields:
            item.delete()
        return None
    for item in items:
        if item.get('id'):
            zns_field = ZnsFieldButton.objects.filter(id=item.get('id')).first()
            if not zns_field:
                return 'Component Button không tồn tại'
            if item.get('action') == 'delete':
                zns_field.delete()
                continue
            zns_field.component = zns_component_zns
            zns_field.button_order = item.get('index')
            zns_field.type = item.get('type')
            zns_field.content = item.get('content')
            zns_field.title = item.get('title')
            zns_field.save()
        else:
            ZnsFieldButton.objects.create(
                component=zns_component_zns,
                button_order=item.get('index'),
                type=item.get('type'),
                content=item.get('content'),
                title=item.get('title')
            )
    return None


def createZnsFieldPayment(zns, data) -> Optional[str]:
    zns_component_zns = createZnsComponent(zns, data)
    bank = Banks.objects.get(bin_code=data.get('bank_code'))
    if data.get('id'):
        zns_field = ZnsFieldPayment.objects.filter(id=data.get('id')).first()
        if not zns_field:
            return 'component Thanh toán không tồn tại'
        if data.get('action') == 'delete':
            zns_field.delete()
            zns_component_zns.delete()
            return None
        zns_field.bank_code = bank
        zns_field.account_name = data.get('account_name')
        zns_field.bank_account = data.get('account_number')
        zns_field.amount = data.get('amount')
        zns_field.note = data.get('note')
        zns_field.save()
        return None

    ZnsFieldPayment.objects.create(
        bank_code=bank,
        component=zns_component_zns,
        account_name=data.get('account_name'),
        bank_account=data.get('account_number'),
        amount=data.get('amount'),
        note=data.get('note'),
    )
    return None


def createZnsFieldVoucher(zns, data) -> Optional[str]:
    zns_component_zns = createZnsComponent(zns, data)
    if data.get('id'):
        zns_field = ZnsFieldVoucher.objects.filter(id=data.get('id')).first()
        if not zns_field:
            return 'component Khuyến mãi không tồn tại'
        if data.get('action') == 'delete':
            zns_field.delete()
            zns_component_zns.delete()
            return None
        zns_field.name = data.get('name')
        zns_field.condition = data.get('condition')
        zns_field.start_date = data.get('start_date')
        zns_field.end_date = data.get('end_date')
        zns_field.voucher_code = data.get('voucher_code')
        zns_field.display_code = data.get('display_code')
        zns_field.save()
        return None
    ZnsFieldVoucher.objects.create(
        component=zns_component_zns,
        name=data.get('name'),
        condition=data.get('condition'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        voucher_code=data.get('voucher_code'),
        display_code=data.get('display_code'),
    )
    return None
