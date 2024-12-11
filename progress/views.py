import datetime

from django.db import transaction
from django.db.models import OuterRef, Count, IntegerField, Value
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.core.subquery import *
from utils.convert_response import convert_response

from .models import *
from employee.models import Employee
from workspace.models import Workspace
from zalo.models import ZaloOA
from user.models import User


class ProgressApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            data = request.GET.copy()
            page_size = int(data.get('page_size', 20))
            offset = (int(data.get('page', 1)) - 1) * page_size
            employee = Employee.objects.filter(account=user)
            ws = employee.values_list('workspace_id', flat=True)
            oas = ZaloOA.objects.filter(company__in=ws).values_list('id', flat=True)

            progress = Progress.objects.filter()

            oa_query = data.get('oa')
            if oa_query not in oas and oa_query:
                raise Exception('Không có quyền truy cập Oa đã chọn')
            if oa_query:
                progress = progress.filter(oa_id=oa_query)
            else:
                progress = progress.filter(oa_id__in=oas)

            search = data.get('search')
            if search:
                progress = progress.filter(title__icontains=search)

            # tag_userzalo_query = Coalesce(
            #     Subquery(
            #         ProgressTagUserZalo.objects.filter(tag_id=OuterRef('id')).values('tag_id').annotate(
            #             total=Count('tag_id')
            #         ).values('total')[:1],
            #         output_field=IntegerField()
            #     ),
            #     Value(0),
            #     output_field=IntegerField()
            # )
            #
            # tag_customer_query = Coalesce(
            #     Subquery(
            #         ProgressTagCustomer.objects.filter(tag_id=OuterRef('id')).values('tag_id').annotate(
            #             total=Count('tag_id')
            #         ).values('total')[:1],
            #         output_field=IntegerField()
            #     ),
            #     Value(0),
            #     output_field=IntegerField()
            # )

            tags_subquery = SubqueryJsonAgg(
                ProgressTag.objects.filter(progress_id=OuterRef('id')).order_by('order').values()
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

            total = progress.count()
            progress = progress.order_by('-id')
            progress = progress[offset: offset + page_size].values().annotate(
                # tag_userzalo=tag_userzalo_query,
                # tag_customer=tag_customer_query,
                oa_data=oa_subquery,
                user_create=user_create_subquery,
                tags=tags_subquery,
            )

            return convert_response('success', 200, total=total, data=progress)
        except Exception as e:
            return convert_response(str(e), 400)

    def post(self, request):
        try:
            with transaction.atomic():
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
                if employee.role.code == 'SALE':
                    raise Exception('Không có quyền tạo tiến trình')

                oa = ZaloOA.objects.filter(id=data.get('oa')).first()
                if not oa:
                    raise Exception('Oa không tồn tại')

                if oa.company != ws:
                    raise Exception('Oa không thuộc Workspace')

                if not data.get('title') or not data.get('oa'):
                    raise Exception('Thông tin không đúng')

                progress_duplicate = Progress.objects.filter(title=data.get('title')).first()
                if progress_duplicate:
                    raise Exception('Tiến trình đã tồn tại')

                progress = Progress.objects.create(
                    title=data.get('title'),
                    oa=oa,
                    created_by=user,
                )

                tags = data.get('tags', [])
                tag_begin = 0
                tag_middle = 0
                tag_end = 0
                for item in tags:
                    tag_dup = ProgressTag.objects.filter(title=item.get('title'), progress=progress)
                    if len(tag_dup) > 1:
                        raise Exception(f'Tag {tag_dup.title} đã tồn tại')
                    tag_type = item.get('type')
                    if tag_type == ProgressTag.Type.BEGIN:
                        tag_begin += 1
                    elif tag_type == ProgressTag.Type.MIDDLE:
                        tag_middle += 1
                    elif tag_type == ProgressTag.Type.END:
                        tag_end += 1
                    else:
                        raise Exception('Loại tag tiến trình không đúng')
                    if tag_begin > 1 or tag_middle > 5 or tag_end > 4:
                        raise Exception('Số lượng tag tiến trình không đúng')
                    ProgressTag.objects.create(
                        title=item.get('title'),
                        color_text=item.get('color_text'),
                        color_fill=item.get('color_fill'),
                        color_border=item.get('color_border'),
                        type=tag_type,
                        progress=progress,
                        oa=oa,
                        # order=item.get('order'),
                        created_by=user,
                    )

                return convert_response('Thêm tiến trình thành công', 200, data=progress.id)

        except Exception as e:
            return convert_response(str(e), 400)


class ProgressDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, _, pk):
        pass

    def put(self, request, pk):
        try:
            user = request.user
            data = request.data.copy()

            progress = Progress.objects.get(id=pk)
            if progress.created_by != user:
                employee = Employee.objects.filter(
                    workspace=progress.oa.company, account=user
                ).exclude(role__code='SALE').first()
                if not employee:
                    raise Exception('Không có quyền chỉnh sửa')

            tag_duplicate = Tag.objects.filter(title=data.get('title'))
            if len(tag_duplicate) > 1:
                raise Exception('Tên Tag đã tồn tại')

            progress.title = data.get('title', progress.title)
            progress.updated_by = user
            progress.updated_at = datetime.datetime.now()
            progress.save()

            tags_delete = data.get('tags_delete', [])
            tags_delete = ProgressTag.objects.filter(id__in=tags_delete)
            for item in tags_delete:
                item.delete()

            tags = data.get('tags', [])
            tag_begin = 0
            tag_middle = 0
            tag_end = 0
            for item in tags:
                tag_dup = ProgressTag.objects.filter(title=item.get('title'), progress=progress)
                if len(tag_dup) > 1:
                    raise Exception(f'Tag {tag_dup.title} đã tồn tại')
                tag_type = item.get('type')
                if tag_type == ProgressTag.Type.BEGIN:
                    tag_begin += 1
                elif tag_type == ProgressTag.Type.MIDDLE:
                    tag_middle += 1
                elif tag_type == ProgressTag.Type.END:
                    tag_end += 1
                else:
                    raise Exception('Loại tag tiến trình không đúng')
                if tag_begin > 1 or tag_middle > 5 or tag_end > 4:
                    raise Exception('Số lượng tag tiến trình không đúng')

                if item.get('id'):
                    progress_tag = ProgressTag.objects.get(id=item.get('id'))
                    progress_tag.title = item.get('title', progress_tag.title)
                    progress_tag.color_text = item.get('color_text', progress_tag.color_text)
                    progress_tag.color_fill = item.get('color_fill', progress_tag.color_fill)
                    progress_tag.type = tag_type
                    progress_tag.title = item.get('title', progress_tag.title)
                    progress_tag.updated_by = user
                    progress_tag.updated_at = datetime.datetime.now()

                else:
                    ProgressTag.objects.create(
                        title=item.get('title'),
                        color_text=item.get('color_text'),
                        color_fill=item.get('color_fill'),
                        color_border=item.get('color_border'),
                        type=tag_type,
                        progress=progress,
                        oa=progress.oa,
                        # order=item.get('order'),
                        created_by=user,
                    )

            return convert_response('Chỉnh sửa tiến trình thành công', 200, data=progress.id)

        except Exception as e:
            return convert_response(str(e), 400)

    def delete(self, request, pk):
        try:
            user = request.user

            progress = Progress.objects.get(id=pk)
            if progress.created_by != user:
                employee = Employee.objects.filter(
                    workspace=progress.oa.company, account=user
                ).exclude(role__code='SALE').first()
                if not employee:
                    raise Exception('Không có quyền chỉnh sửa')

            progress_tag = ProgressTag.objects.filter(progress=progress)
            for item in progress_tag:
                item.delete()

            progress.delete()

            return convert_response('Xoá tiến trình thành công', 200)

        except Exception as e:
            return convert_response(str(e), 400)
