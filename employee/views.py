from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Subquery, OuterRef, IntegerField, Count, Q
from common.core.subquery import SubqueryJsonAgg, SubqueryJson
from utils.convert_response import convert_response

from employee.models import Employee, EmployeeOa, EmployeeUserZalo
from user.models import User
from workspace.models import Role


class Employees(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = request.GET.copy()
        workspace = data.get('workspace')
        if not workspace:
            return convert_response('Yêu cầu thông tin workspace', 400)

        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size
        search = data.get('search', '')
        total_customer_query = Subquery(
            EmployeeUserZalo.objects.filter(employee_id=OuterRef('id'))
            .values('employee_id')
            .annotate(count=Count('id'))
            .values('count'),
            output_field=IntegerField()
        )

        oa_query = SubqueryJsonAgg(
            EmployeeOa.objects.filter(employee_id=OuterRef('id')).values(),
        )

        employees_in_ws = Employee.objects.filter(workspace_id=workspace)
        data = request.GET.copy()
        # filter by Role
        role_query = data.get('role')
        if role_query:
            employees_in_ws = employees_in_ws.filter(role_id=role_query)
        # filter by Status
        status_query = data.get('status')
        if status_query:
            employees_in_ws = employees_in_ws.filter(status=status_query)
        zalo_oa_query = data.get('zalo_oa')
        if zalo_oa_query:
            employee_oa = EmployeeOa.objects.filter(oa_id=zalo_oa_query).values_list('employee_id', flat=True)
            employees_in_ws = employees_in_ws.filter(id__in=employee_oa)
        employees = employees_in_ws.filter(
            Q(account__full_name__icontains=search) |
            Q(account__phone__icontains=search)
        )[
            offset: offset + page_size
        ].values().annotate(
            account=SubqueryJson(
                User.objects.filter(id=OuterRef('account_id')).values(
                    'id', 'username', 'full_name', 'avatar', 'phone'
                )[:1]
            ),
            role_data=SubqueryJson(
                Role.objects.filter(id=OuterRef('role')).values()[:1]
            ),
            total_customer=total_customer_query,
            oa_take_care=oa_query,
        )

        return convert_response('success', 200, data=employees, count=employees_in_ws.count())

    def post(self, request):
        user_req = request.user
        data = request.data.copy()
        phone = data.get('phone')
        if not phone:
            return convert_response('Vui lòng nhập số điện thoại', 400)
        workspace = data.get('workspace')
        if not workspace:
            return convert_response('Yêu cầu thông tin workspace', 400)
        role = data.get('role')
        if not role:
            return convert_response('Yêu cầu thông tin vai trò', 400)
        user = User.objects.filter(phone=phone).first()
        if not user:
            return convert_response('Số điện thoại chưa được đăng ký tài khoản', 400)
        employee = Employee.objects.filter(account=user, workspace_id=workspace).first()
        if employee:
            return convert_response('Tài khoản đã là nhân viên của Workspace', 400)
        try:
            employee = Employee.objects.create(
                created_by=user_req,
                account=user,
                workspace_id=workspace,
                role_id=role,
            )
        except Exception as e:
            return convert_response(str(e), 400)
        return convert_response('success', 200, data=employee.id)


class EmployeeDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee = Employee.objects.filter(id=pk).values().annotate(
            account=SubqueryJson(
                User.objects.filter(id=OuterRef('account_id')).values(
                    'id', 'phone', 'full_name', 'email', 'avatar'
                )[:1]
            )
        ).first()
        if not employee:
            return convert_response('Nhân viên không tồn tại', 404)
        return convert_response('success', 200, data=employee)

    def put(self, request, pk):
        user = request.user
        data = request.data.copy()
        employee = Employee.objects.filter(id=pk).first()
        if not employee:
            return convert_response('Nhân viên không tồn tại', 404)
        employee.role_id = data.get('role', employee.role_id)
        employee.status = data.get('status', employee.status)
        employee.save()
        return convert_response('success', 200)

    def delete(self, request, pk):
        employee = Employee.objects.filter(id=pk).first()
        if not employee:
            return convert_response('Nhân viên không tồn tại', 404)
        employee.delete()
        return convert_response('success', 200)
