import datetime

from django.db.models import OuterRef, Count, IntegerField, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.core.subquery import *
from utils.convert_response import convert_response

from tags.models import Tag, TagCustomer, TagUserZalo
from employee.models import Employee
from workspace.models import Workspace
from zalo.models import ZaloOA
from user.models import User


class TagsApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            data = request.GET.copy()
            page_size = int(data.get('page_size', 20))
            offset = (int(data.get('page', 1)) - 1) * page_size
            employee = Employee.objects.filter(account=user)
            ws = employee.values_list('workspace_id', flat=True)
            oas = ZaloOA.objects.filter(company_id__in=ws).values_list('id', flat=True)
            oas = list(oas)
            tags = Tag.objects.filter()

            oa_query = data.get('oa')
            if int(oa_query) not in oas and oa_query:
                raise Exception('Không có quyền truy cập Oa đã chọn')
            if oa_query:
                tags = tags.filter(oa_id=oa_query)
            else:
                tags = tags.filter(oa_id__in=oas)

            search = data.get('search')
            if search:
                tags = tags.filter(title__icontains=search)

            tag_userzalo_query = Coalesce(
                Subquery(
                    TagCustomer.objects.filter(tag_id=OuterRef('id')).values('tag_id').annotate(
                        total=Count('tag_id')
                    ).values('total')[:1],
                    output_field=IntegerField()
                ),
                Value(0),
                output_field=IntegerField()
            )

            tag_customer_query = Coalesce(
                Subquery(
                    TagUserZalo.objects.filter(tag_id=OuterRef('id')).values('tag_id').annotate(
                        total=Count('tag_id')
                    ).values('total')[:1],
                    output_field=IntegerField()
                ),
                Value(0),
                output_field=IntegerField()
            )

            oa_subquery = SubqueryJson(
                ZaloOA.objects.filter(id=OuterRef('oa_id')).values(
                    'oa_name', 'oa_avatar'
                )[:1]
            )

            user_create_subquery = SubqueryJson(
                User.objects.filter(id=OuterRef('created_by_id')).values(
                    'full_name', 'avatar'
                )
            )

            total = tags.count()
            tags = tags.order_by('-id')
            tags = tags[offset: offset + page_size].values().annotate(
                tag_userzalo=tag_userzalo_query,
                tag_customer=tag_customer_query,
                oa_data=oa_subquery,
                user_create=user_create_subquery,
            )

            return convert_response('success', 200, total=total, data=tags)
        except Exception as e:
            return convert_response(str(e), 400)

    def post(self, request):
        try:
            user = request.user
            data = request.data.copy()

            ws = data.get('workspace')
            if not ws:
                raise Exception('Yêu cầu thông tin workspace')
            ws = Workspace.objects.filter(id=ws).first()
            if not ws:
                raise Exception('Workspace không tồn tại')

            employee = Employee.objects.filter(workspace_id=ws, account=user).first()
            if not employee:
                raise Exception('Bạn không thuộc workspace đã chọn')

            oa = ZaloOA.objects.filter(id=data.get('oa')).first()
            if not oa:
                raise Exception('Oa không tồn tại')

            if oa.company != ws:
                raise Exception('Oa không thuộc Workspace')

            if not data.get('title') or not data.get('oa') or not data.get('color'):
                raise Exception('Thông tin không đúng')

            tag_duplicate = Tag.objects.filter(title=data.get('title')).first()
            if tag_duplicate:
                raise Exception('Tag đã tồn tại')

            tag = Tag.objects.create(
                title=data.get('title'),
                color_text=data.get('color_text'),
                color_fill=data.get('color_fill'),
                color_border=data.get('color_border'),
                oa_id=data.get('oa'),
                created_by=user,
            )

            return convert_response('Thêm mới tag thường thành công', 200, data=tag.to_json())

        except Exception as e:
            return convert_response(str(e), 400)


class TagDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, _, pk):
        pass

    def put(self, request, pk):
        try:
            user = request.user
            data = request.data.copy()

            tag = Tag.objects.get(id=pk)
            if tag.created_by != user:
                employee = Employee.objects.filter(
                    workspace=tag.oa.company, account=user
                ).exclude(role__code='SALE').first()
                if not employee:
                    raise Exception('Không có quyền chỉnh sửa')

            tag_duplicate = Tag.objects.filter(title=data.get('title')).first()
            if tag_duplicate:
                raise Exception('Tên Tag đã tồn tại')

            tag.title = data.get('title', tag.title)
            tag.color_text = data.get('color_text', tag.color_text)
            tag.color_fill = data.get('color_fill', tag.color_fill)
            tag.color_border = data.get('color_border', tag.color_border)
            tag.updated_by = user,
            tag.updated_at = datetime.datetime.now()
            tag.save()

            return convert_response('Chỉnh sửa tag thường thành công', 200, data=tag.to_json())

        except Exception as e:
            return convert_response(str(e), 400)

    def delete(self, request, pk):
        try:
            user = request.user

            tag = Tag.objects.get(id=pk)
            if tag.created_by != user:
                employee = Employee.objects.filter(
                    workspace=tag.oa.company, account=user
                ).exclude(role__code='SALE').first()
                if not employee:
                    raise Exception('Không có quyền chỉnh sửa')

            tag.delete()

            return convert_response('Chỉnh sửa tag thường thành công', 200)

        except Exception as e:
            return convert_response(str(e), 400)
