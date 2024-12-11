import random

from django.core.files.base import ContentFile

from common.s3 import AwsS3
from .models import *


def createZnsComponent(zns, data) -> ZnsComponentZns:
    component = ZnsComponent.objects.get(
        type=data.get('type'),
        layout=data.get('layout'),
    )
    zns_component_zns = ZnsComponentZns.objects.create(
        zns=zns,
        component=component,
        order=data.get('index')
    )
    return zns_component_zns


def createZnsFieldTitle(zns, data) -> str:
    pk = data.get('id')
    if pk:
        zns_field = ZnsFieldTitle.objects.filter(id=pk).first()
        if not zns_field:
            return 'component không tồn tại'
        if data.get('action') == 'delete':
            zns_field.delete()
            return 'delete success'
        zns_field.value = data.get('value')
        zns_field.save()
        return 'update success'
    zns_component_zns = createZnsComponent(zns, data)
    ZnsFieldTitle.objects.create(
        value=data.get('value'),
        component=zns_component_zns,
    )
    return 'create success'


def createZnsFieldParagraph(zns, data) -> str:
    pk = data.get('id')
    if pk:
        zns_field = ZnsFieldParagraph.objects.filter(id=pk).first()
        if not zns_field:
            return 'component không tồn tại'
        if data.get('action') == 'delete':
            zns_field.delete()
            return 'delete success'
        zns_field.value = data.get('value')
        zns_field.save()
        return 'success'
    zns_component_zns = createZnsComponent(zns, data)
    ZnsFieldParagraph.objects.create(
        value=data.get('value'),
        component=zns_component_zns,
    )
    return 'success'


def createZnsFieldOTP(zns, data) -> str:
    pk = data.get('id')
    if pk:
        zns_field = ZnsFieldOTP.objects.filter(id=pk).first()
        if not zns_field:
            return 'component không tồn tại'
        if data.get('action') == 'delete':
            zns_field.delete()
            return 'delete success'
        zns_field.value = data.get('value')
        zns_field.save()
        return 'success'
    zns_component_zns = createZnsComponent(zns, data)
    ZnsFieldOTP.objects.create(
        value=data.get('value'),
        component=zns_component_zns,
    )
    return 'success'


# TODO: Khó
def createZnsFieldTable(zns, data) -> str:
    pk = data.get('id')
    zns_component_zns = ZnsComponentZns.objects.get(id=pk)
    if not pk:
        zns_component_zns = createZnsComponent(zns, data)
    rows = data.get('rows', [])
    for item in rows:
        pk = data.get('id')
        if pk:
            zns_field = ZnsFieldTable.objects.get(id=pk)
            zns_field.value = item.get('value'),
            zns_field.index = item.get('index'),
            zns_field.title = item.get('title'),
            zns_field.row_type = item.get('row_type'),
            zns_field.save()
        else:
            ZnsFieldTable.objects.create(
                value=item.get('value'),
                component=zns_component_zns,
                row_order=item.get('index'),
                title=item.get('title'),
                row_type=item.get('row_type'),
            )
    return 'success'


def createZnsFieldLogo(zns, data, logo_light, logo_dark) -> str:
    r = random.randint(100000, 999999)
    file_name = f"logo_light_{r}.png"
    image_file_light = ContentFile(logo_light.read(), name=file_name)
    uploaded_file_name_light = AwsS3.upload_file(image_file_light, f'zns_image/{zns.id}/')

    file_name = f"logo_dark_{r}.png"
    image_file_dark = ContentFile(logo_dark.read(), name=file_name)
    uploaded_file_name_dark = AwsS3.upload_file(image_file_dark, f'zns_image/{zns.id}/')
    if data.get('id'):
        zns_field = ZnsFieldLogo.objects.filter(id=data.get('id')).first()
        zns_field.light = uploaded_file_name_light
        zns_field.dark = uploaded_file_name_dark
        zns_field.save()
        return 'success'

    zns_component_zns = createZnsComponent(zns, data)
    ZnsFieldLogo.objects.create(
        component=zns_component_zns,
        light=uploaded_file_name_light,
        dark=uploaded_file_name_dark
    )
    return 'success'


def createZnsFieldImage(zns, data, files) -> str:
    zns_component_zns = createZnsComponent(zns, data)
    for file in files:

        r = random.randint(100000, 999999)
        file_name = f"image_{zns_component_zns.id}_{r}.png"
        image_file_light = ContentFile(file.read(), name=file_name)
        uploaded_file_name = AwsS3.upload_file(image_file_light, f'zns_image/{zns_component_zns.id}/')

        if data.get('id'):
            zns_field = ZnsFieldImage.objects.filter(id=data.get('id')).first()
            zns_field.item = uploaded_file_name
            zns_field.save()
            return 'success'

        ZnsFieldImage.objects.create(
            component=zns_component_zns,
            item=uploaded_file_name,
        )
    return 'success'


def createZnsFieldButton(zns, data) -> str:
    zns_component_zns = createZnsComponent(zns, data)
    items = data.get('items')
    for item in items:
        ZnsFieldButton.objects.create(
            component=zns_component_zns,
            button_order=item.get('index'),
            type=item.get('type'),
            content=item.get('content'),
            title=item.get('title')
        )
    return 'success'


def createZnsFieldPayment(zns, data) -> str:
    zns_component_zns = createZnsComponent(zns, data)
    bank = Banks.objects.get(bin_code=data.get('bank_code'))
    ZnsFieldPayment.objects.create(
        bank_code=bank,
        component=zns_component_zns,
        account_name=data.get('account_name'),
        bank_account=data.get('account_number'),
        amount=data.get('amount'),
        note=data.get('note'),
    )
    return 'success'


def createZnsFieldVoucher(zns, data) -> str:
    zns_component_zns = createZnsComponent(zns, data)
    ZnsFieldVoucher.objects.create(
        component=zns_component_zns,
        name=data.get('name'),
        condition=data.get('condition'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        voucher_code=data.get('voucher_code'),
        display_code=data.get('display_code'),
    )
    return 'success'
